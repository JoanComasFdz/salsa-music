#!/usr/bin/env python3
"""
Scrapes emusicality.co.uk (or any similar SPA) by:
  1. Loading the page in a real headless Chromium (bypasses 403 bot blocks)
  2. Recording every network request + response
  3. Clicking play and letting the song run, so audio stems actually load
  4. Saving HTML, JS, CSS, JSON, audio, images to disk
  5. Zipping everything up into /out/site_dump.zip
"""
import asyncio
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse, unquote
from playwright.async_api import async_playwright

TARGET_URL   = os.environ.get("TARGET_URL", "https://www.emusicality.co.uk/songs/babalu")
PLAY_SECONDS = int(os.environ.get("PLAY_SECONDS", "20"))
OUT_DIR      = Path("/out")
WORK_DIR     = Path("/tmp/dump")

# Reset workspace
if WORK_DIR.exists():
    shutil.rmtree(WORK_DIR)
WORK_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

manifest = []            # list of dicts describing every request
seen_urls = set()        # dedupe
saved_count = 0


def safe_path_for_url(url: str) -> Path:
    """Turn a URL into a sensible on-disk path under WORK_DIR/<host>/..."""
    p = urlparse(url)
    host = p.netloc or "local"
    path = unquote(p.path)
    if not path or path.endswith("/"):
        path += "index.html"
    # Strip leading slash, replace bad chars
    rel = re.sub(r"[^A-Za-z0-9._/\-]", "_", path.lstrip("/"))
    # Keep query as suffix so different params don't collide
    if p.query:
        qhash = re.sub(r"[^A-Za-z0-9]", "_", p.query)[:40]
        rel = f"{rel}__q_{qhash}"
    full = WORK_DIR / host / rel
    full.parent.mkdir(parents=True, exist_ok=True)
    return full


async def save_response(response):
    global saved_count
    url = response.url
    if url in seen_urls:
        return
    seen_urls.add(url)

    try:
        status = response.status
        headers = dict(response.headers)
        ctype = headers.get("content-type", "")

        entry = {
            "url": url,
            "status": status,
            "method": response.request.method,
            "resource_type": response.request.resource_type,
            "content_type": ctype,
            "size": None,
            "saved_to": None,
        }

        # Only save successful bodies
        if status < 400 and response.request.method == "GET":
            try:
                body = await response.body()
                entry["size"] = len(body)
                dest = safe_path_for_url(url)
                dest.write_bytes(body)
                entry["saved_to"] = str(dest.relative_to(WORK_DIR))
                saved_count += 1
                # Log interesting stuff as it streams in
                if any(k in ctype for k in ("audio", "json", "javascript", "html", "css")):
                    print(f"  [{saved_count}] {status} {response.request.resource_type:>8} {ctype.split(';')[0]:<25} {url[:90]}")
            except Exception as e:
                entry["error"] = f"body read: {e}"

        manifest.append(entry)
    except Exception as e:
        print(f"  !! error processing {url}: {e}")


async def main():
    print(f"=== Scraping {TARGET_URL} ===")
    print(f"=== Playing for {PLAY_SECONDS}s to capture audio stems ===\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--autoplay-policy=no-user-gesture-required",  # allow autoplay
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="en-GB",
        )

        # Hide webdriver flag — some bot-check scripts sniff this
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        page = await context.new_page()
        page.on("response", lambda r: asyncio.create_task(save_response(r)))
        page.on("pageerror", lambda e: print(f"  !! page error: {e}"))
        page.on("console",   lambda m: None)  # silence console

        # --- Load the page ---
        print(f"[1/4] Loading page...")
        try:
            await page.goto(TARGET_URL, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"  warning during load: {e}")
        print(f"  status: loaded, title = {await page.title()!r}")

        # --- Try to press play ---
        print(f"\n[2/4] Attempting to start playback...")
        clicked = False
        play_selectors = [
            'button[aria-label*="play" i]',
            'button[title*="play" i]',
            '[class*="play" i]:not([class*="playing"])',
            'svg[class*="play" i]',
            'button:has(svg)',
        ]
        for sel in play_selectors:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    try:
                        if await el.is_visible():
                            await el.click(timeout=1500)
                            print(f"  clicked: {sel}")
                            clicked = True
                            break
                    except Exception:
                        continue
                if clicked:
                    break
            except Exception:
                continue
        if not clicked:
            # Last resort: try to .play() any <audio> element directly
            try:
                n = await page.evaluate(
                    "Array.from(document.querySelectorAll('audio,video'))"
                    ".map(a => { try { a.play(); return 1 } catch(e) { return 0 } })"
                    ".reduce((a,b)=>a+b, 0)"
                )
                print(f"  forced .play() on {n} media element(s)")
            except Exception as e:
                print(f"  could not force play: {e}")

        # --- Let it run so stems load ---
        print(f"\n[3/4] Waiting {PLAY_SECONDS}s for audio streams...")
        await page.wait_for_timeout(PLAY_SECONDS * 1000)

        # --- Also grab the fully-rendered DOM after JS ran ---
        try:
            rendered = await page.content()
            (WORK_DIR / "_rendered_dom.html").write_text(rendered, encoding="utf-8")
            print(f"\n  saved rendered DOM ({len(rendered)} bytes)")
        except Exception as e:
            print(f"  could not capture rendered DOM: {e}")

        # Screenshot for visual confirmation
        try:
            await page.screenshot(path=str(WORK_DIR / "_screenshot.png"), full_page=True)
        except Exception:
            pass

        await browser.close()

    # --- Write manifest + summary ---
    print(f"\n[4/4] Writing manifest and zipping...")
    (WORK_DIR / "_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # Group by type for a quick summary
    by_type = {}
    for e in manifest:
        t = (e.get("content_type") or "").split(";")[0] or "unknown"
        by_type.setdefault(t, []).append(e["url"])

    summary_lines = [
        f"Target: {TARGET_URL}",
        f"Total requests: {len(manifest)}",
        f"Saved bodies:   {saved_count}",
        "",
        "By content-type:",
    ]
    for t, urls in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
        summary_lines.append(f"  {len(urls):4d}  {t}")
    # Highlight likely audio stems
    audio_urls = [e["url"] for e in manifest if "audio" in (e.get("content_type") or "")]
    if audio_urls:
        summary_lines += ["", "Audio resources (likely stems):"]
        summary_lines += [f"  {u}" for u in audio_urls]

    summary = "\n".join(summary_lines)
    (WORK_DIR / "_SUMMARY.txt").write_text(summary, encoding="utf-8")
    print("\n" + summary)

    # --- Zip it ---
    zip_path = OUT_DIR / "site_dump.zip"
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", WORK_DIR)
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Done. Zip: {zip_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    asyncio.run(main())
