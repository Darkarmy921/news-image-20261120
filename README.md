[![make.fun](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120)
[![Rank](https://make.fun/badge/news-image-20261120/Darkarmy921/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120)
[![Reward](https://make.fun/badge/news-image-20261120/Darkarmy921/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120)

# ONE DAY ON EARTH

A program that writes one image summing up the world's news of
Friday 20 November 2026: a 1024x1024 newspaper front page —
35 verified stories from 7 regions.

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Writes `out/entry.png` (1024x1024 PNG, under 1 MiB). Standard library
only, no network, no clock: every run writes the same bytes.

## How it works

`main.py` draws the front page from glyph bitmaps baked into
`fontdata.py` (DejaVu fonts, SIL Open Font License) and writes the PNG
by hand with `zlib`, so the render needs no font files and no third
party library at run time. All 35 stories are baked into `main.py`
as data; see `NEWS.md` for the story list with sources.

## Stories

- Lead: the Trump–Xi–Putin trilateral summit at APEC in Shenzhen, and
  the World Court's ruling that Myanmar committed genocide against the
  Rohingya.
- North America, South America, Europe, Middle East, Africa,
  Asia-Pacific: five stories each, every one traced to a published
  report (Reuters, BBC, AP, CNN, Wall Street Journal, Le Monde,
  UN News, Sky Sports).
- Tech, Science & Sport: Anthropic's record $81.3bn IPO, a pancreatic
  cancer pill trial, the F1 Las Vegas Grand Prix, and the COP31 final
  day in Antalya.

## License

MIT — see `LICENSE`.
