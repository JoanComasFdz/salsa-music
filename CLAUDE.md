# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

Several unrelated projects live side by side. Only the first one is published.

- **`salsa-guide.html`** (repo root) — a standalone, single-file static site published via GitHub Pages at `https://joancomasfdz.github.io/salsa-music/salsa-guide.html`. All markup, CSS, translations, and JS are inline in this one file. `og-image.png` is the social-preview image referenced by the Open Graph / Twitter meta tags.
- **`src/emusicality-scrapper/`** — a Dockerized Playwright scraper that dumps the assets and network traffic of a song page on emusicality.co.uk. Used to reverse-engineer how that site delivers its stems/metadata. *Not* part of the published site.
- **`src/musicality-player-babalu/`** — an early, standalone prototype player built from what the scraper revealed. Plays 8 synced stems for one song (Babalu) with a section/phrase/beat UI. *Not* published; lives here purely as a working reference.
- **`src/songs-breakdown/`** — research notes (one Markdown file) compiling published timestamped section breakdowns for salsa songs. Reference material, not code.

Development environment: the devcontainer (`.devcontainer/devcontainer.json`) preinstalls the Live Server VS Code extension (`ritwickdey.liveserver`), rooted at `/` on port 8000 (forwarded). Use it to serve `salsa-guide.html` or the prototype player — the latter requires HTTP because it `fetch()`es JSON and audio stems.

## Commit conventions

Git commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <subject>`. Types in use here include `feat`, `fix`, `docs`, `style`, `refactor`, `chore`. Scope is the affected area (e.g. `preview`, `history`, `upload`, `i18n`, `scraper`, `player`). Subject is lowercase, imperative, no trailing period.

## salsa-guide.html

### Deployment
There is no build step. GitHub Pages serves `salsa-guide.html` directly from `main`. Publishing is just `git push`. The Open Graph `og:url` and `og:image` URLs are absolute and point at the GitHub Pages host, so if you rename files or move the repo, update those tags.

### Internationalisation architecture (important)
The page supports English / German / Spanish via a hand-rolled i18n layer — there is no framework. When editing user-visible copy, you must keep the HTML defaults and the `translations` object in sync.

- Translatable text lives inline in HTML via two attributes:
  - `data-i18n="key"` — replaced via `textContent` (escapes HTML).
  - `data-i18n-html="key"` — replaced via `innerHTML` (used when the string contains `<br>`, `<em>`, `<strong>`, etc.).
- The big `const translations = { en: {...}, de: {...}, es: {...} }` object near the bottom of the file holds every string, keyed by the same names used in the attributes.
- `setLanguage(lang)` walks both attribute sets and swaps content. On load, an IIFE picks the language from `localStorage['salsaGuideLang']`, falling back to `navigator.language`'s first two chars, defaulting to `en`.
- The language switcher hides the currently-active button (`display: none`) rather than just styling it — keep that behaviour if you touch the switcher.

Rules of thumb when editing copy:
1. If you add a new translatable element, add a `data-i18n[-html]` attribute **and** add the key to all three language dicts. Missing keys silently leave the HTML default in place, which looks like a bug in the other languages.
2. Use `data-i18n-html` only when the translation actually needs inline HTML — otherwise prefer `data-i18n` so the content is HTML-escaped.
3. The HTML default (what sits between the tags) should match the English translation, since English is the source of truth shown before JS runs.

## src/emusicality-scrapper/ (scraper)

Standalone Playwright + headless Chromium scraper. Run via Docker:

```bash
cd src/emusicality-scrapper
docker build -t emusicality-scraper .
mkdir -p ./out
docker run --rm -u "$(id -u):$(id -g)" -v "$(pwd)/out:/out" emusicality-scraper
# Override target / playback window:
docker run --rm -u "$(id -u):$(id -g)" -v "$(pwd)/out:/out" \
  -e TARGET_URL="https://www.emusicality.co.uk/songs/<slug>" \
  -e PLAY_SECONDS=45 \
  emusicality-scraper
```

The `-u "$(id -u):$(id -g)"` flag is important: without it, the container runs as root and writes root-owned files into `./out` on the host, which you then can't delete without `sudo`.

Output is `out/site_dump.zip` containing `_SUMMARY.txt`, `_manifest.json`, `_rendered_dom.html`, `_screenshot.png`, plus every response body laid out by host/path. `_SUMMARY.txt` is the intended entry point — start there when investigating a dump.

The script presses play by trying a list of selectors, then falls back to calling `.play()` on any `<audio>`/`<video>` element, so autoplay-blocked pages still trigger stem loads. See `src/emusicality-scrapper/README.md` for the "what to look at first" triage flow and recovery steps if a run returns 0 bytes.

## src/musicality-player-babalu/ (prototype player)

A from-scratch single-file reproduction of the emusicality.co.uk player, built from what the scraper revealed. Serves as the working prototype that an eventual "salsa musicality" feature would be based on.

Layout:
- `index.html` — the entire player (HTML + CSS + JS, no build step).
- `assets/songs/babalu/breakdown.json` — section/phrase/track metadata.
- `assets/songs/babalu/cover.jpg` — album art.
- `assets/songs/babalu/track0.trk`…`track7.trk` — 8 audio stems (M4A/AAC, renamed `.trk`).

How it works:
- All 8 stems are fetched, decoded to `AudioBuffer`s, and started in the same JS tick via `AudioBufferSourceNode.start()` — the Web Audio API schedules them sample-accurately, and `audioCtx.currentTime` drives the UI clock. Mute/unmute toggles `gainNode.gain.value` without touching the sources, so sync is preserved.
- The active song is selected by the `SONG_SLUG` + `SONG_META` constants near the top of `index.html` (around line 145). Adding another song means creating `assets/songs/<slug>/` with a matching `breakdown.json` + stems, then updating those two constants.
- `breakdown.json` schema (summary): `trim` (global audio offset seconds), `beatsPerMeasure` (beats per phrase, e.g. 8 for bachata), `tracks` (array of strings *or* `{title, groups}` objects), `sections` (array of `{title, phrases, structure?}` where each `phrases` entry is either a number `N` meaning *N phrases of `beatsPerMeasure` beats each*, or `[frameworkLabel, ...beatCounts]` listing explicit beat counts under that framework label). Full schema in the project's own `README.md`.

Running it: needs a local HTTP server (CORS blocks `fetch()` on `file://`). Either right-click `index.html` → "Open with Live Server" in VS Code, or `cd src/musicality-player-babalu && python3 -m http.server 8000`.

## src/songs-breakdown/

A single Markdown file (`salsa-song-structure-breakdowns.md`) with research notes on timestamped section breakdowns for salsa songs — source compilation and per-song annotations. Pure reference material; no code.
