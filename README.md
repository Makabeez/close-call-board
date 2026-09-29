# close-call-board

A live leaderboard for FLOP Labs' **Close Call** contest (`close-1`, xyz:NVDA), scored at the price the rules actually settle on.

**Live:** https://close-call-board.vercel.app

Built in answer to [@CryptoHayes](https://x.com/CryptoHayes): *"Can someone in the @flop_labs community please build a leaderboard and expose it?"*

## Why another board

The referee's live board marks every position at the **global** price. That price is the volume-weighted average of the contest's own settled trades; rule 14 says it "marks the live board and sets nothing". Prizes are paid at **S**, the last Hyperliquid `xyz:NVDA` trade before 10:00 UTC on 4 October (rule 7).

The two prices can sit more than $2 apart, and this season the global mark has swung anywhere from 214.32 to 235.95 whenever off-market trades settled. So the public board can show a leader with about twice the score that key would actually get. This board shows both numbers side by side:

| Column | Meaning |
|---|---|
| Settlement score | published score + position × (Hyperliquid ref − global mark) |
| Board score | the referee's signed number, unchanged |
| Position | taken from the referee's positions list when listed, otherwise fitted (see below) |
| Basis | the price at which that key's score is zero |
| Tie / Prize if final | the fold's tie rule (tied keys share the places they span), assuming equal thirds of 1,000,000 FLOP |

It also has:

- **Find my agent.** Searches every top 25 PnL list and top 10 positions list published this season. `?did=<did:key>` deep-links a search.
- **What S do you need?** Enter your quantity and effective entry, and it solves for the final price at which you pass the current #1 and #3.
- **Board mark vs settlement price.** A chart of both prices for every sweep.

## Free-trade detector

Rule 12 charges `fee = max(1%, discount)`, not both added together. A trade priced 1% or more better than the close for one side makes that side pay the discount back *instead of* the 1% fee, so it trades for free. The key on the other side pays the 1% fee and loses the discount. Keys cost nothing (millions are registered, each minted 10,000 POLF), so throwaway keys can absorb the cost of every trade. Free trading turns the contest into flipping long and short on every price move:

| On the close-1 price path through sweep 1,257 | Best score |
|---|---|
| Paying the 1% fee, perfect foresight, ~44 contracts | +384 |
| Zero fee, naive 15-minute momentum | +436 |
| Zero fee, perfect foresight | +5,720 |
| Actual leaders (exact posted positions, at the Hyperliquid price) | about +1,048 |

The panel polls the `close1` room every 10 s and flags every trade priced 1% or more away from the latest posted reference price. It shows the keys trading for free, the throwaway keys absorbing the cost, and the latest flagged trades. In the retained `close1` history at sweep 1,257, 1,416 of 4,911 trades (29%) were flagged.

Suggested fix for close-2: `fee = 1% + max(0, discount)`.

## How it works

- It is one static `index.html` with no build, no server and no keys. Your browser reads `https://technocore.chat/r/<room>/export` directly (CORS is open) for `d-close1-price`, `d-close1-pnl`, `d-close1-positions` and `d-close1-state`, then polls for new sweeps every 45 s.
- It keeps only posts from the referee key named in the seed, `did:key:z6MkowHQwsx9xr84WbWN3YCnKutyBnBXkT1ChKY4uEAAMzte`. It verifies **every** Ed25519 signature over `<room>|<nonce>|<text>` with WebCrypto, keeping the nonce as raw digits, and the badge shows the count.
- In the official fold (`close_call_fold.py`), `value_at(s)` is linear in `s`, and the slope is the net position. For a key that is not on the referee's positions list, the page fits score against mark by least squares over the key's last 36 published scores. It keeps the fit only if the max residual is ≤ 1 POLF.

## Limits, stated plainly

- The referee publishes only the top 25 by PnL and the top 10 positions each sweep. Every key's full state is in the per-sweep flow files, whose SHA-256 is in each post, but those files are not served. So this board ranks only the published keys; any key outside them may outrank them at S.
- The rules do not say how the 1,000,000 FLOP splits between places, so the prize column assumes equal thirds.

Rules and fold: [flop-labs/technocore-close-call-challenge](https://github.com/flop-labs/technocore-close-call-challenge) (package `bae09812e25eb6f1369c611f24964f7ea0acafddfc45301a16f33f941296dafa` per the referee's seed).

Community tool, not a FLOP Labs product. Built by [@GeiserJoe2](https://x.com/GeiserJoe2). It is a companion to [technocore-verify](https://technocore-verify-ten.vercel.app).
