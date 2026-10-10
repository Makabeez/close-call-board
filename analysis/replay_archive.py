#!/usr/bin/env python3
"""Stream the close-1 sweep archive and replay every public trade with the official fold's account logic.

Output (JSON): season fee statistics, how often a side skipped the 1% fee by paying the clawback instead,
per-key free/sink counts, and an approximate score for every key that traded (keys whose trades were in
private rooms are redacted in the archive, so their scores can be incomplete).

Usage (about 7 minutes and 6 GB of RAM; it streams 7.6 GB and stores none of it):
    curl -s https://challenges.technocore.chat/close-1/index.json -o index.json
    python3 -I replay_archive.py index.json out.json 234.69 [did:key:...,did:key:...]
The optional last argument lists keys whose exact score and approximate rank to report.
"""
import json, sys, time, urllib.request, collections
from concurrent.futures import ThreadPoolExecutor

BASE = "https://challenges.technocore.chat/close-1/"
if len(sys.argv) < 3:
    sys.exit(__doc__)
idx = json.load(open(sys.argv[1]))["sweeps"]
out_path = sys.argv[2]
S = float(sys.argv[3]) if len(sys.argv) > 3 else 234.69
idx.sort(key=lambda s: s["n"])

def fetch(s):
    for attempt in range(5):
        try:
            req = urllib.request.Request(BASE + s["path"], headers={"User-Agent": "close1-replay/1"})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            i, o = d["input"], d["output"]
            rows = []
            for t, res in zip(i["trades"], o["trades"]):
                if "redacted" in t or res.get("outcome") != "settled":
                    rows.append(None if "redacted" not in t else "R")
                    continue
                rows.append((t["maker"], t["countersigner"], 1 if t["side"] == "buy" else -1,
                             float(t["qty"]), float(t["px"]), float(res["maker_fee"]), float(res["taker_fee"])))
            return s["n"], o.get("close", i.get("close")), rows
        except Exception as e:
            err = e; time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"sweep {s['n']}: {err}")

acct = {}                                     # key -> [cash, lots (list of (qty, px) tuples, one sign), trades, free, sink]
st = dict(sweeps=0, settled=0, redacted=0, self_trades=0, fees=0.0, waived_fills=0, base_skipped=0.0,
          gap_paid_by_free_side=0.0, base_paid_by_sink_side=0.0, settled_notional=0.0)

def rec(k):
    r = acct.get(k)
    if r is None:
        r = acct[k] = [0.0, [], 0, 0, 0]
    return r

def apply(r, side, qty, px, fee):
    r[0] -= fee
    L = r[1]; left = qty
    while left > 1e-12 and L and L[0][0] * side < 0:
        lq, lp = L[0]; size = min(left, abs(lq))
        r[0] += size * px if side < 0 else size * (2 * lp - px)
        left -= size
        if abs(size - abs(lq)) < 1e-12: L.pop(0)
        else: L[0] = (lq + side * size, lp)
    if left > 1e-12:
        r[0] -= left * px; L.append((side * left, px))

t0 = time.time()
with ThreadPoolExecutor(6) as ex:
    for c0 in range(0, len(idx), 24):
        for n, close, rows in ex.map(fetch, idx[c0:c0 + 24]):
            st["sweeps"] += 1
            for r in rows:
                if r is None: continue
                if r == "R": st["redacted"] += 1; continue
                mk, tk, side, q, px, fm, ft = r
                st["settled"] += 1; st["fees"] += fm + ft; st["settled_notional"] += q * px
                rm, rt = rec(mk), rec(tk)
                rm[2] += 1; rt[2] += 1
                if mk == tk:
                    st["self_trades"] += 1; rm[0] -= fm + ft; continue
                base = 0.01 * q * px
                for fee, me, other, ofee in ((fm, rm, rt, ft), (ft, rt, rm, fm)):
                    if fee > base + 1e-6:          # this side paid the gap instead of the 1% fee
                        st["waived_fills"] += 1; st["base_skipped"] += base; st["gap_paid_by_free_side"] += fee
                        me[3] += 1; other[4] += 1; st["base_paid_by_sink_side"] += ofee
                apply(rm, side, q, px, fm); apply(rt, -side, q, px, ft)
        print(f"{st['sweeps']}/{len(idx)} sweeps, {st['settled']:,} settled, {time.time()-t0:.0f}s", flush=True)

import heapq, array
JOE = sys.argv[4].split(",") if len(sys.argv) > 4 else []
def value(r):
    return r[0] + sum(q * S if q > 0 else -q * (2 * p - S) for q, p in r[1])
top = []; vals = array.array("d"); free_top = []; sink_top = []
joe = {}
for k, r in acct.items():
    v = value(r); vals.append(v)
    item = (v, k, round(sum(q for q, _ in r[1]), 2), r[2], r[3], r[4])
    if len(top) < 300: heapq.heappush(top, item)
    elif v > top[0][0]: heapq.heapreplace(top, item)
    for H, c in ((free_top, r[3]), (sink_top, r[4])):
        if c:
            it = (c, k, r[2], round(v, 2))
            if len(H) < 50: heapq.heappush(H, it)
            elif c > H[0][0]: heapq.heapreplace(H, it)
    if k in JOE: joe[k] = item
free_keys = sum(1 for r in acct.values() if r[3]); sink_keys = sum(1 for r in acct.values() if r[4])
both = sum(1 for r in acct.values() if r[3] and r[4])
vs = sorted(vals)
def rank_of(v): import bisect; return len(vs) - bisect.bisect_right(vs, v) + 1
json.dump(dict(stats=st, S=S, traded_keys=len(acct), free_keys=free_keys, sink_keys=sink_keys, both=both,
               positive_keys=sum(1 for v in vs if v > 0), pct=[vs[int(len(vs) * f)] for f in (0.5, 0.9, 0.99, 0.999)],
               top=sorted(top, reverse=True), top_free=sorted(free_top, reverse=True), top_sink=sorted(sink_top, reverse=True),
               joe={k: dict(score=it[0], pos=it[2], trades=it[3], free=it[4], sink=it[5], rank=rank_of(it[0])) for k, it in joe.items()}),
          open(out_path, "w"))
print("done", time.time() - t0)
