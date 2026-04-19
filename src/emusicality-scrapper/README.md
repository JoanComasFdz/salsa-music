# Emusicality Scraper

Headless Chromium + Playwright. Loads the page, presses play, records every network request for 20 seconds, saves everything to a zip.

## Build & run

Put `Dockerfile`, `scrape.py`, and this README in the same folder. Then:

```bash
docker build -t emusicality-scraper .

# Create an output folder on your host and mount it:
mkdir -p ./out
docker run --rm -v "$(pwd)/out:/out" emusicality-scraper
```

When it finishes, you'll have `./out/site_dump.zip` on your host.

## What's in the zip

```
_SUMMARY.txt          ← start here, lists counts + audio URLs
_manifest.json        ← every request: URL, status, content-type, size, saved path
_rendered_dom.html    ← the DOM *after* JS ran (the SPA's real output)
_screenshot.png       ← full-page screenshot for sanity check
www.emusicality.co.uk/
    ├── songs/babalu/index.html
    ├── <all the JS bundles>
    ├── <CSS>
    └── <audio stems, if any>
<other CDN hosts>/
    └── ...
```

## Tweaks

```bash
# Different song
docker run --rm -v "$(pwd)/out:/out" \
  -e TARGET_URL="https://www.emusicality.co.uk/songs/some-other-song" \
  emusicality-scraper

# Let it play longer (catches more audio)
docker run --rm -v "$(pwd)/out:/out" -e PLAY_SECONDS=45 emusicality-scraper
```

## What to look at first

Open `_SUMMARY.txt`. The section "Audio resources (likely stems)" is the key finding — it will tell you:

- **Are there 8 separate MP3s per song?** → They're shipping pre-separated stems, straightforward to reproduce.
- **One big file streamed as ranges?** → Probably a multi-channel WAV/OGG or HLS with stem tracks.
- **No audio URLs at all?** → Autoplay was blocked; re-run with `PLAY_SECONDS=45` and add a click interaction, or the audio is generated client-side (Web Audio API).

Then check `_manifest.json` for any `application/json` responses — that's where the song structure metadata (section timings, BPM, framework per section) almost certainly lives.

## If you get 0 bytes or errors

The site may have stronger bot protection than expected. If so:
1. Bump to `PLAY_SECONDS=60` and re-run
2. Check the screenshot — if it shows a Cloudflare challenge, we'd need to switch to `playwright-stealth` or `undetected-chromedriver`
3. The `_rendered_dom.html` will still give us the SPA structure even if audio didn't load
