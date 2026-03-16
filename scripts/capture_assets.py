"""Capture announcement assets for FlowSurgeon v0.6.0.

Produces:
    docs/screenshots/routes-home.png
    docs/screenshots/request-detail-sql.png
    docs/demo/demo.gif

Run with:
    uv run --group screenshots python scripts/capture_assets.py
"""

import os
import shutil
import subprocess
import sys
import time

from pathlib import Path
from playwright.sync_api import sync_playwright


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
SCREENSHOTS_DIR = ROOT / "docs" / "screenshots"
DEMO_DIR = ROOT / "docs" / "demo"
FRAMES_DIR = DEMO_DIR / "frames"
PALETTE_PATH = DEMO_DIR / "palette.png"
GIF_PATH = DEMO_DIR / "demo.gif"

BASE_URL = "http://127.0.0.1:8765"
FS_URL = f"{BASE_URL}/flowsurgeon"


# ---------------------------------------------------------------------------
# Frame capture helpers
# ---------------------------------------------------------------------------

frame_num = 0


def capture_frames(page, frames_dir: Path, count: int) -> None:
    """Capture `count` identical frames for a hold effect."""
    global frame_num
    for _ in range(count):
        page.screenshot(path=str(frames_dir / f"frame_{frame_num:04d}.png"))
        frame_num += 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    global frame_num

    # Ensure output directories exist
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Start demo server
    # ------------------------------------------------------------------
    print("Starting FastAPI demo server on port 8765...")
    server = subprocess.Popen(
        [
            "uv",
            "run",
            "--group",
            "examples",
            "uvicorn",
            "examples.fastapi.demo_fastapi:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(ROOT),
    )

    try:
        # Wait for server to be ready
        time.sleep(3)
        print("Server ready.")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                color_scheme="dark",
            )
            page = context.new_page()

            # ----------------------------------------------------------
            # Seed data by visiting each demo route
            # ----------------------------------------------------------
            print("Seeding data...")
            for path in ["/books", "/books/1", "/books/duplicates", "/books/slow", "/slow"]:
                try:
                    page.goto(f"{BASE_URL}{path}", timeout=10000)
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception as e:
                    print(f"  Warning: seeding {path} failed: {e}", file=sys.stderr)
            time.sleep(1)
            print("Data seeding complete.")

            # ----------------------------------------------------------
            # Screenshot 1: Routes home
            # ----------------------------------------------------------
            print("Capturing routes-home.png...")
            page.goto(FS_URL, timeout=10000)
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_selector(".tr", timeout=5000)
            page.wait_for_timeout(500)
            page.screenshot(
                path=str(SCREENSHOTS_DIR / "routes-home.png"),
                full_page=False,
            )
            print("  Saved docs/screenshots/routes-home.png")

            # ----------------------------------------------------------
            # Screenshot 2: Request detail SQL tab
            # ----------------------------------------------------------
            print("Capturing request-detail-sql.png...")
            page.goto(FS_URL, timeout=10000)
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_selector(".tr", timeout=5000)
            page.wait_for_timeout(500)

            # Click the /books/slow route row
            page.locator("a.tr", has_text="/books/slow").first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_selector("a.tr", timeout=5000)
            page.wait_for_timeout(300)

            # Click the first request row
            page.locator("a.tr").first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_timeout(300)

            # Click the SQL tab
            page.locator(".subnav-item", has_text="SQL").click()
            page.wait_for_timeout(500)

            page.screenshot(
                path=str(SCREENSHOTS_DIR / "request-detail-sql.png"),
                full_page=False,
            )
            print("  Saved docs/screenshots/request-detail-sql.png")

            # ----------------------------------------------------------
            # GIF frame capture
            # ----------------------------------------------------------
            print("Capturing GIF frames...")
            frame_num = 0

            # Step 1: Routes home page — hold 2 seconds (20 frames)
            page.goto(FS_URL, timeout=10000)
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_selector(".tr", timeout=5000)
            page.wait_for_timeout(500)
            capture_frames(page, FRAMES_DIR, 20)
            print(f"  Routes home: {frame_num} frames")

            # Step 2: Click /books/slow route — hold 1.5 seconds (15 frames)
            page.locator("a.tr", has_text="/books/slow").first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_selector("a.tr", timeout=5000)
            page.wait_for_timeout(300)
            capture_frames(page, FRAMES_DIR, 15)
            print(f"  Route detail: {frame_num} frames")

            # Step 3: Click first request — hold 1.5 seconds (15 frames)
            page.locator("a.tr").first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            page.wait_for_timeout(300)
            capture_frames(page, FRAMES_DIR, 15)
            print(f"  Request detail: {frame_num} frames")

            # Step 4: Click SQL tab — hold 2.5 seconds (25 frames)
            page.locator(".subnav-item", has_text="SQL").click()
            page.wait_for_timeout(500)
            capture_frames(page, FRAMES_DIR, 25)
            print(f"  SQL tab: {frame_num} frames total")

            browser.close()

        # ------------------------------------------------------------------
        # GIF assembly via ffmpeg two-pass palette
        # ------------------------------------------------------------------
        print("Assembling GIF with ffmpeg two-pass palette...")

        # Pass 1: Generate palette
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                "10",
                "-i",
                str(FRAMES_DIR / "frame_%04d.png"),
                "-vf",
                "scale=1280:-1:flags=lanczos,palettegen=max_colors=256:stats_mode=diff",
                str(PALETTE_PATH),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("  Palette generated.")

        # Pass 2: Generate GIF using palette
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                "10",
                "-i",
                str(FRAMES_DIR / "frame_%04d.png"),
                "-i",
                str(PALETTE_PATH),
                "-lavfi",
                "fps=10,scale=1280:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                str(GIF_PATH),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("  GIF assembled.")

        # Clean up frames and palette
        shutil.rmtree(str(FRAMES_DIR), ignore_errors=True)
        PALETTE_PATH.unlink(missing_ok=True)
        print("  Cleaned up frames and palette.")

        # ------------------------------------------------------------------
        # Report
        # ------------------------------------------------------------------
        gif_size = GIF_PATH.stat().st_size
        print()
        print("Assets captured:")
        print(f"  docs/screenshots/routes-home.png — {(SCREENSHOTS_DIR / 'routes-home.png').stat().st_size:,} bytes")
        print(f"  docs/screenshots/request-detail-sql.png — {(SCREENSHOTS_DIR / 'request-detail-sql.png').stat().st_size:,} bytes")
        print(f"  docs/demo/demo.gif — {gif_size:,} bytes ({gif_size / 1_000_000:.1f} MB)")

        if gif_size >= 10_000_000:
            print("WARNING: GIF exceeds 10 MB limit!", file=sys.stderr)
            sys.exit(1)
        else:
            print("All assets within size limits.")

    finally:
        print("Stopping server...")
        server.terminate()
        server.wait()
        print("Done.")


if __name__ == "__main__":
    main()
