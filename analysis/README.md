# close-1 archive replay

`replay_archive.py` streams every sweep record Flop Labs published at https://challenges.technocore.chat/close-1/. It replays every public trade with the official fold's account logic (`close_call_fold.py`: FIFO lots, a short's collateral, the clawback fee) and scores every key at S = 234.69.

**Check:** the replay reproduces 24 of the 25 final scores the referee posted, to 0.0001 POLF. The 25th, `did:key:z6Mkw8HuAX84pVtptarfWgGB1XtGiBkXSPoCgAMoXWsjCCC9` (#9), traded in private rooms. The archive redacts those 499,321 trades, so scores and ranks for keys that used private rooms are approximate.

## What it found (`close-1-results.json`)

| | |
|---|---|
| Settled public trades | 7,606,301 |
| Fees on them | 1,622,085,448.91 POLF (95.7% of the 1,695,366,972.51 reported) |
| Trade sides that paid the discount back instead of the 1% fee (rule 12's `max`) | 5,154,479, one in three |
| 1% fees skipped that way, paid instead by the key on the other side | 452,949,720.47 POLF |
| Fills of the final top 25 on the fee-free side | 772 of 772 |
| Keys that traded / ever fee-free / ever paid for another key's fee | 9,405,335 / 2,061,542 / 3,236,971 |
| Score at the 50th / 90th / 99th percentile of keys that traded | −109.07 / +182.63 / +442.76 |

On close-1's price path, trading about 44 contracts:

| Strategy | Paying 1% a side | Trading free |
|---|---|---|
| Perfect foresight of every sweep's close | +589 | +11,639 |
| Long if the close rose over the last 15 minutes, else short | −129,129 | +1,027 |

The proposed fix for the next contest is `fee = 1% + max(0, discount)`. It is submitted upstream as `fee_rule: "clawback_plus"` in flop-labs/technocore-close-call-challenge.
