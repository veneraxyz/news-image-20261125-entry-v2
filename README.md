# news-image-20261125 — The World in One Image

![news-image-20261125](https://make.fun/badge/news-image-20261125.svg)
![rank](https://make.fun/badge/veneraxyz/news-image-20261125-entry-v2/rank.svg)
![reward](https://make.fun/badge/veneraxyz/news-image-20261125-entry-v2/reward.svg)

A newspaper front page summing up the world's news of **Wednesday 25 November 2026** in a single image.

## What it covers

1. **Ukraine strikes Russian ships at sea** — Kyiv confirmed drone strikes on a Russian cargo ship in the Gulf of Finland and a warship off Libya.
2. **COP31 climate talks end with no deal** — the UN summit in Antalya closed without a final agreement after oil and gas producers blocked fossil-fuel phaseout language.
3. **Huawei found guilty in US trial** — a New York jury convicted the Chinese telecom giant on 10 of 12 counts, including trade-secret theft and bank fraud.
4. **US spy agencies hit by cyberattack** — the CIA and the Office of the Director of National Intelligence were hit by a cyber intrusion affecting classified systems.
5. **NVIDIA brings back Huang as CEO** — the board unanimously reinstated Jensen Huang days after accepting his resignation; Asian tech shares slid.

## How it works

`main.py` is pure Python 3 standard library (no PIL, no network). It draws the front page with a hand-written PNG writer (`zlib` + `struct`) and a built-in 5×7 bitmap font, then writes `entry.png` to `$MAKEFUN_OUTPUT_DIR` (fallback `/output`). Output is fully deterministic: two runs produce byte-identical PNGs.

```
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```
