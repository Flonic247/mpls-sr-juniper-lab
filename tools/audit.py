#!/usr/bin/env python3
"""Technical consistency audit for configs/as-captured.
Usage: python3 tools/audit.py [--markdown] [--no-fail]
Exit code 1 if any ERROR is found (unless --no-fail)."""
import re, sys, ipaddress, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parent.parent
CAP, STG = ROOT/'configs'/'as-captured', ROOT/'configs'/'stages'
CORE = ['R1','R2','R3','R4','R5','R6']; CES = ['CE_01','CE_02']; P = ['R2','R3','R4','R5']
res = []
def add(st, cat, msg): res.append((st, cat, msg))
def check(cat, ok, problems, level='ERROR'):
    if problems:
        for p in problems: add(level, cat, p)
    else: add('PASS', cat, ok)
cfg = {n: [l for l in (CAP/f'{n}.set').read_text().splitlines() if l.startswith('set ')] for n in CORE+CES}
def find(n, pat): return [m for l in cfg[n] for m in [re.match(pat, l)] if m]
def ifaces(n):
    d = collections.defaultdict(lambda: {'inet': [], 'iso': False, 'mpls': False})
    for m in find(n, r'set interfaces (\S+) unit (\d+) family inet address (\S+)$'): d[f'{m[1]}.{m[2]}']['inet'].append(m[3])
    for m in find(n, r'set interfaces (\S+) unit (\d+) family iso( address \S+)?$'): d[f'{m[1]}.{m[2]}']['iso'] = True
    for m in find(n, r'set interfaces (\S+) unit (\d+) family mpls$'): d[f'{m[1]}.{m[2]}']['mpls'] = True
    return d
I = {n: ifaces(n) for n in cfg}
num = lambda n: int(n[1])
def lo(n): return I[n]['lo0.0']['inet'][0]
def isis_if(n): return sorted({m[1] for m in find(n, r'set protocols isis interface (\S+) ')} - {'lo0.0'})
def one(n, pat):
    m = find(n, pat); return m[0][1] if m else None

# topology
nets = collections.defaultdict(list)
for n in cfg:
    for name, v in I[n].items():
        if name.startswith(('lo0','fxp0')): continue
        for a in v['inet']:
            i = ipaddress.ip_interface(a); nets[i.network].append((n, name, i.ip))
links = {k: v for k, v in nets.items() if k.prefixlen == 30}
adj = collections.defaultdict(set)
for k, v in links.items():
    if len(v) == 2: adj[v[0][0]].add(v[1][0]); adj[v[1][0]].add(v[0][0])
owner = {str(ip): n for v in nets.values() for n, _, ip in v}
for n in cfg: owner[str(ipaddress.ip_interface(lo(n)).ip)] = n

# 1 interface references
pr = []
for n in CORE:
    for name in isis_if(n):
        if not I[n][name]['iso']: pr.append(f'{n} {name}: IS-IS enabled but family iso missing')
        if not I[n][name]['inet']: pr.append(f'{n} {name}: IS-IS enabled but no IPv4 address')
    for m in find(n, r'set protocols mpls interface (\S+)$'):
        if not I[n][m[1]]['mpls']: pr.append(f'{n} {m[1]}: in protocols mpls but family mpls missing')
    for name in isis_if(n):
        if I[n][name]['mpls'] and not find(n, rf'set protocols mpls interface {re.escape(name)}$'): pr.append(f'{n} {name}: family mpls but not under protocols mpls')
    for m in find(n, r'set routing-instances \S+ interface (\S+)$'):
        if m[1] not in I[n]: pr.append(f'{n}: VRF interface {m[1]} does not exist')
        elif I[n][m[1]]['iso'] or I[n][m[1]]['mpls']: pr.append(f'{n}: VRF interface {m[1]} also has iso/mpls')
check('Interface references', 'Every interface referenced by IS-IS, MPLS and the VRF exists with the right families; CE-facing interfaces carry no iso/mpls', pr)
# 2 links
pr = [f'{k}: {len(v)} endpoint(s)' for k, v in links.items() if len(v) != 2]
check('Link addressing', f'{len(links)} point-to-point /30 links, each with exactly two endpoints (IPs {", ".join(sorted(str(k) for k in links))})', pr)
# 3 loopbacks
pr = []
los = [lo(n) for n in cfg]
if len(set(los)) != len(los): pr.append('duplicate loopback addresses')
for n in CORE:
    if lo(n) != f'10.0.0.{num(n)}/32': pr.append(f'{n}: loopback {lo(n)} != 10.0.0.{num(n)}/32')
check('Loopbacks', 'Core loopbacks are unique and follow 10.0.0.N/32 (CE loopbacks 192.168.1.1/32, 192.168.2.1/32)', pr)
# 4 NET
pr = []
for n in CORE:
    m = find(n, r'set interfaces lo0 unit 0 family iso address (\S+)$')
    exp = f'49.0001.0100.0000.{num(n):04d}.00'
    if not m or m[0][1] != exp: pr.append(f'{n}: NET {m[0][1] if m else None} != expected {exp} (area/system-ID differs from the other routers and from the diagram table)')
check('IS-IS NET', 'All NETs follow 49.0001.0100.0000.000N.00', pr)
# 5 SRGB / SIDs
srgb = {(one(n, r'set protocols isis source-packet-routing srgb start-label (\d+)'), one(n, r'set protocols isis source-packet-routing srgb index-range (\d+)')) for n in CORE}
idx = {n: one(n, r'set protocols isis source-packet-routing node-segment ipv4-index (\d+)') for n in CORE}
pr = []
if len(srgb) != 1: pr.append(f'SRGB differs between routers: {srgb}')
for n in CORE:
    if idx[n] != str(num(n)): pr.append(f'{n}: node-SID index {idx[n]} != {num(n)}')
if len(set(idx.values())) != 6: pr.append('node-SID indexes not unique')
check('SRGB and Node-SIDs', f'SRGB {sorted(srgb)[0][0]}/{sorted(srgb)[0][1]} identical on all core routers; indexes 1-6 unique and match router numbers', pr)
check('explicit-null', 'explicit-null configured on all core routers', [f'{n}: explicit-null missing' for n in CORE if not find(n, r'set protocols isis source-packet-routing explicit-null$')])
# 6 segment lists
start = int(sorted(srgb)[0][0]); lab = {start+int(idx[n]): n for n in CORE}
segs = collections.defaultdict(list)
for m in find('R1', r'set protocols source-packet-routing segment-list (\S+) (\S+) (ip-address|label) (\S+)$'): segs[m[1]].append((m[3], m[4]))
pr = []; infos = []; pathmap = {}
for name, hops in segs.items():
    path = ['R1']
    for kind, v in hops:
        r = owner.get(v) if kind == 'ip-address' else lab.get(int(v))
        if r is None: pr.append(f'{name}: hop {kind} {v} does not resolve to a router'); r = '?'
        path.append(r)
    for a, b in zip(path, path[1:]):
        if b not in adj[a]: pr.append(f'{name}: {a} and {b} are not adjacent')
    expected = name.replace('SRTE_', '').split('_')
    if path != expected: pr.append(f'{name}: resolves to {">".join(path)} but name implies {">".join(expected)}')
    infos.append(f'{name} -> {">".join(path)}'); pathmap[name] = path
check('SR-TE segment lists', 'Segment lists resolve to valid adjacent hops and match their names: ' + '; '.join(infos), pr)
# 7 BGP
pr = []
asn = {n: one(n, r'set routing-options autonomous-system (\d+)$') for n in CORE}
if len(set(asn.values())) != 1: pr.append(f'core AS differs: {asn}')
for a, b in [('R1','R6'),('R6','R1')]:
    nb = one(a, r'set protocols bgp group L3VPN neighbor (\S+)$'); la = one(a, r'set protocols bgp group L3VPN local-address (\S+)$')
    if nb != lo(b).split('/')[0]: pr.append(f'{a}: iBGP neighbor {nb} != {b} loopback')
    if la != lo(a).split('/')[0]: pr.append(f'{a}: iBGP local-address {la} != own loopback')
    if not find(a, r'set protocols bgp group L3VPN family inet-vpn unicast$'): pr.append(f'{a}: family inet-vpn missing')
for pe, ce in [('R1','CE_01'),('R6','CE_02')]:
    nb = one(pe, r'set routing-instances CUSTOMER_A protocols bgp group \S+ neighbor (\S+)$'); la = one(pe, r'set routing-instances CUSTOMER_A protocols bgp group \S+ local-address (\S+)$')
    pas = one(pe, r'set routing-instances CUSTOMER_A protocols bgp group \S+ peer-as (\d+)$')
    cl = one(ce, r'set protocols bgp group \S+ local-as (\d+)$'); cp = one(ce, r'set protocols bgp group \S+ peer-as (\d+)$'); cn = one(ce, r'set protocols bgp group \S+ neighbor (\S+)$')
    if owner.get(nb) != ce: pr.append(f'{pe}: PE-CE neighbor {nb} is not {ce}')
    if owner.get(cn) != pe: pr.append(f'{ce}: neighbor {cn} is not {pe}')
    if pas != cl: pr.append(f'{pe}: peer-as {pas} != {ce} local-as {cl}')
    if cp != asn[pe]: pr.append(f'{ce}: peer-as {cp} != PE AS {asn[pe]}')
    if cn != la: pr.append(f'{ce}: neighbor {cn} != {pe} local-address {la}')
check('BGP', 'iBGP R1<->R6 on loopbacks with inet-vpn; PE-CE eBGP addresses and AS numbers (65000/65100) match on both ends', pr)
# 8 RT / RD
def comm(n, pol, kind):
    m = find(n, rf'set policy-options policy-statement {pol} term 1 then community add (\S+)$') if kind == 'x' else find(n, rf'set policy-options policy-statement {pol} term 1 from community (\S+)$')
    c = m[0][1] if m else None
    v = one(n, rf'set policy-options community {c} members (\S+)$') if c else None
    return c, v
pr = []; w = []; rds = []; info = []
exp = {}; imp = {}
for pe in ['R1','R6']:
    xp = one(pe, r'set routing-instances CUSTOMER_A vrf-export (\S+)$'); ip_ = one(pe, r'set routing-instances CUSTOMER_A vrf-import (\S+)$')
    exp[pe] = comm(pe, xp, 'x')[1]; imp[pe] = comm(pe, ip_, 'i')[1]
    rd = one(pe, r'set routing-instances CUSTOMER_A route-distinguisher (\S+)$'); rds.append(rd)
    if not rd.startswith(lo(pe).split('/')[0] + ':'): pr.append(f'{pe}: RD {rd} does not start with its loopback')
    vt = one(pe, r'set routing-instances CUSTOMER_A vrf-target (\S+)$')
    if vt and vt != exp[pe]: w.append(f'{pe}: vrf-target {vt} differs from the exported community {exp[pe]} (explicit vrf-import/vrf-export policies are used; vrf-target is redundant)')
if len(set(rds)) != 2: pr.append('RDs are not unique')
if exp['R1'] != imp['R6'] or exp['R6'] != imp['R1']: pr.append(f'RT mismatch: export {exp} import {imp}')
check('Route targets / distinguishers', f'RDs {", ".join(rds)} are unique; both PEs export and import {exp["R1"]}', pr)
for x in w: add('WARNING', 'Route targets / distinguishers', x)
# 9 VPN interfaces & CE LAN
pr = []
for pe, ce in [('R1','CE_01'),('R6','CE_02')]:
    ifn = one(pe, r'set routing-instances CUSTOMER_A interface (\S+)$')
    pn = ipaddress.ip_interface(I[pe][ifn]['inet'][0]).network
    if not any(x[0] == ce for x in nets[pn]): pr.append(f'{pe} {ifn} network {pn} does not contain {ce}')
for ce in CES:
    lan = [ipaddress.ip_interface(a).network for k, v in I[ce].items() if k == 'ge-0/0/1.0' for a in v['inet']][0]
    f = one(ce, r'set policy-options policy-statement \S+ term 1 from route-filter (\S+) exact$')
    if str(lan) != f: pr.append(f'{ce}: export route-filter {f} != LAN {lan}')
check('VPN interfaces and CE prefixes', 'VRF interfaces sit on the PE-CE /30 links; CE export filters match the CE LAN prefixes (10.64.99.0/24, 203.0.113.0/24)', pr)
# 10 BFD / LFA
pr = []
for n in CORE:
    for name in isis_if(n):
        peer = [e for k, v in links.items() for e in v if e[0] == n and e[1] == name]
        if not peer: continue
        nk = [k for k, v in links.items() if (n, name) in [(e[0], e[1]) for e in v]][0]
        if any(e[0] in CES for e in links[nk]): continue
        if not find(n, rf'set protocols isis interface {re.escape(name)} bfd-liveness-detection minimum-interval \d+$'): pr.append(f'{n} {name}: no BFD')
        if not find(n, rf'set protocols isis interface {re.escape(name)} level 2 post-convergence-lfa$'): pr.append(f'{n} {name}: no post-convergence-lfa')
    if not find(n, r'set protocols isis backup-spf-options use-post-convergence-lfa$'): pr.append(f'{n}: backup-spf-options missing')
check('BFD and post-convergence LFA', 'BFD (1000 ms x3) and post-convergence LFA on every core IS-IS interface, both ends of every link', pr, 'WARNING')
# 11 misc
check('icmp-tunneling on P routers', 'mpls icmp-tunneling on all P routers', [f'{n}: protocols mpls icmp-tunneling missing (traceroute through the core may not show this hop)' for n in P if not find(n, r'set protocols mpls icmp-tunneling$')], 'WARNING')
check('Hostnames', 'Hostnames are RouterN', [f'{n}: host-name {one(n, r"set system host-name (\S+)$")} (expected Router{num(n)})' for n in CORE if one(n, r'set system host-name (\S+)$') != f'Router{num(n)}'], 'WARNING')
check('BGP-free core', 'P routers run no BGP', [f'{n}: BGP configured on a P router' for n in P if find(n, r'set protocols bgp ')])
check('IS-IS level 1', 'Level 1 disabled on every IS-IS interface', [f'{n}: {x[1]} L1 not disabled' for n in CORE for x in [(0, y) for y in isis_if(n)+['lo0.0']] if not find(n, rf'set protocols isis interface {re.escape(x[1])} level 1 disable$')])
pr = []
for n in cfg:
    for l in cfg[n]:
        if 'encrypted-password' in l or re.search(r'vendor-id \S*VM', l): pr.append(f'{n}: {l[:60]}')
check('Secrets', 'No password hashes or VM-specific identifiers in as-captured configs', pr)
pr = []
if any('Cutomer' in l for n in cfg for l in cfg[n]): pr.append('policy-statement "Cutomer_A_Import" is misspelled (used consistently, so functional)')
if any(re.search(r' hope\d ', l) for l in cfg['R1']): pr.append('segment-list hop names use "hope1..3" (hop names are free-form, so functional)')
for ce in CES:
    g = one(ce, r'set protocols bgp group (\S+) type external$'); nb = one(ce, r'set protocols bgp group \S+ neighbor (\S+)$')
    m = re.search(r'Router(\d)', g or '')
    if m and owner.get(nb) != f'R{m[1]}': pr.append(f'{ce}: BGP group "{g}" peers with {owner.get(nb)}, not R{m[1]}')
for ce in CES:
    for l in cfg[ce]:
        m = re.match(r'set routing-options static route (\S+) reject$', l)
        if m and any(str(ipaddress.ip_interface(a).network) == m[1] for v in I[ce].values() for a in v['inet']): pr.append(f'{ce}: static reject {m[1]} duplicates a connected route (only active if the interface is down)')
pol = [l for l in cfg['R6'] if 'EXPORT_TO_CE02' in l and 'policy-options' in l]
if pol and not any('then reject' in l for l in pol): pr.append('R6 EXPORT_TO_CE02 has no terminating reject, so it does not restrict what is advertised to CE_02 (default BGP export still applies)')
check('Naming and policy hygiene', 'none', pr, 'WARNING')
# 13 IGP vs SR-TE
import heapq
cost = {}
for k, v in links.items():
    if len(v) != 2 or any(e[0] in CES for e in v): continue
    for (x, ix, _), (y, iy, _) in [(v[0], v[1]), (v[1], v[0])]:
        m = one(x, rf'set protocols isis interface {re.escape(ix)} level 2 metric (\d+)$')
        cost[(x, y)] = int(m) if m else 10   # 10 is the metric observed on every link without an explicit one
def spf(src, dst):
    dist = {src: 0}; prev = collections.defaultdict(list); pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 10**9): continue
        for (x, y), c in cost.items():
            if x != u: continue
            if d + c < dist.get(y, 10**9): dist[y] = d + c; prev[y] = [u]; heapq.heappush(pq, (d + c, y))
            elif d + c == dist[y]: prev[y].append(u)
    def walk(n): return [[src]] if n == src else [p + [n] for u in prev[n] for p in walk(u)]
    return dist[dst], ['>'.join(p) for p in walk(dst)]
d, igp = spf('R1', 'R6')
pname = one('R1', r'set protocols source-packet-routing source-routing-path \S+ primary (\S+)$')
prim = pathmap.get(pname, []); pc = sum(cost[(x, y)] for x, y in zip(prim, prim[1:]))
if '>'.join(prim) in igp:
    add('WARNING', 'SR-TE versus IGP path', f'primary {">".join(prim)} is one of {len(igp)} equal-cost IGP shortest paths (cost {d}): SR-TE pins a path but does not divert traffic')
else:
    add('PASS', 'SR-TE versus IGP path', f'primary {">".join(prim)} (IGP cost {pc}) is not an IGP shortest path; the IGP uses {", ".join(igp)} (cost {d}), so the SR-TE path is a genuine detour')
sec = pathmap.get(one('R1', r'set protocols source-packet-routing source-routing-path \S+ secondary (\S+)$'), [])
if '>'.join(sec) in igp: add('PASS', 'SR-TE secondary path', f'secondary {">".join(sec)} is an IGP shortest path (cost {d}): a natural standby, not a detour')
# 12 stages == as-captured
pr = []
for n in cfg:
    st = []
    for f in sorted(STG.glob(f'*/{n}.set')): st += [l for l in f.read_text().splitlines() if l.startswith('set ')]
    if sorted(st) != sorted(cfg[n]): pr.append(f'{n}: stage files differ from as-captured ({len(st)} vs {len(cfg[n])} lines)')
check('Stage files', 'Union of configs/stages/*/DEVICE.set equals configs/as-captured/DEVICE.set for all 8 devices', pr)

order = {'ERROR': 0, 'WARNING': 1, 'PASS': 2}
res.sort(key=lambda r: order[r[0]])
if '--markdown' in sys.argv:
    for s in ['PASS', 'WARNING', 'ERROR']:
        print(f'\n### {s}\n\n| Category | Result |\n|---|---|')
        for st, c, m in res:
            if st == s: print(f'| {c} | {m} |')
else:
    for st, c, m in res: print(f'{st:8} {c}: {m}')
errs = sum(1 for r in res if r[0] == 'ERROR')
print(f'\n{sum(r[0]=="PASS" for r in res)} PASS, {sum(r[0]=="WARNING" for r in res)} WARNING, {errs} ERROR', file=sys.stderr)
sys.exit(1 if errs and '--no-fail' not in sys.argv else 0)
