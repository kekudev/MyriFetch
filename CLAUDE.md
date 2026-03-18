# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

MyriFetch is a personal fork of a ROM manager/downloader for the Myrient (Erista) repository. It's a single-file Python desktop app (`MyriFetch.py`) built with `customtkinter` (a themed `tkinter` wrapper). The companion `myrient_launcher.py` is a headless wrapper script used by RetroBat/EmulationStation for on-demand ROM downloading.

## Running and Building

**Run from source** (requires Python 3.10+):
```bash
pip install -r requirements.txt
python MyriFetch.py
```

**Build on Windows** (produces `dist/MyriFetch.exe`):
```bat
Build_Windows.bat
```

**Build on Linux** (produces `MyriFetch-x86_64.AppImage`):
```bash
chmod +x build_appimage.sh
./build_appimage.sh
```

Both build scripts create an isolated `build_venv` to avoid polluting the system Python, then invoke PyInstaller with `--collect-all customtkinter`.

The CI workflows (`.github/workflows/`) build for all three platforms on every push to `main`.

## Architecture

The entire GUI application lives in `MyriFetch.py`. There is no module split — everything is one large file. Key structural elements:

**Global constants (top of file):**
- `CONSOLES` — maps friendly console names → Myrient URL paths (e.g., `'PlayStation 1'` → `'Redump/Sony - PlayStation/'`)
- `RETROBAT_ROM_FOLDERS` — maps console names → RetroBat `roms\` subfolder names
- `LB_NAMES` / `SHORT_NAMES` — LaunchBox and short display names for the same consoles
- `SYSTEM_TO_MYRIENT` / `SYSTEM_TO_CONSOLE` — reverse lookups derived from the above
- `THEMES` — dict of color palettes; active theme is copied into global `C`
- `BASE_URL` — `https://myrient.erista.me/files/`
- `NUM_THREADS = 4`, `CHUNK_SIZE = 256KB` — Hydra download engine config

**Core classes:**
- `UltimateApp(ctk.CTk)` — the main application window (line ~1710). All tabs/panels (Home, Browser, Queue, Library, Settings, RetroBat) are methods on this class. UI state is stored as instance attributes. Uses `after()` for all cross-thread UI updates.
- `_OwnershipCache` — single-pass directory scanner that caches which ROMs are owned. Replaces per-file `stat()` calls.
- `RAManager` — RetroAchievements API integration (profile, points, rank).
- `TwitchManager` — IGDB (via Twitch OAuth) integration for box art and metadata in the tooltip/details panel. Still used for `show_game_details` and hover tooltips.
- `ScreenScraperManager` — ScreenScraper.fr API integration for full media scraping (see below).
- `DownloadPopup(ctk.CTk)` — standalone headless download progress window used by the on-demand launcher (line ~5600).
- `GameTooltip`, `CustomPopup`, `ThemedDirBrowser` — helper UI widgets.

**`myrient_launcher.py`** — standalone script that intercepts EmulationStation game launches. If the ROM file is a stub (starts with `MYRIFETCH_STUB_MAGIC`), it calls `MyriFetch.py --headless-download` to fetch the ROM, then passes through to `emulatorLauncher.exe`. Contains its own copy of the system mappings to avoid importing the full app.

**Config persistence:** Stored in `%APPDATA%\MyriFetch\myrient_ultimate.json` (Windows) or `~/.config/MyriFetch/` (Linux/macOS). Written atomically via a temp file + rename to prevent data loss on crash.

**Stub files:** Placeholder ROM files are 17 bytes starting with `b'MYRIFETCH_STUB\nv1\n'`. The on-demand launcher detects them to trigger downloads. The `_is_myrifetch_stub()` helper fast-paths by skipping the open() for files larger than the stub size.

**Download engine:** The "Hydra" engine splits files into `NUM_THREADS` byte-range requests. Files under `SINGLE_STREAM_THRESHOLD_BYTES` (768 MiB) or from hosts in `HOST_RANGE_THREAD_CAPS` use fewer threads. Thread control uses `threading.Event` objects (`_cancel_event`, `_pause_event`).

**Download sources:** Configurable via `SOURCE_MODE_*` constants — can fall back from Myrient to Archive.org, optionally with qBittorrent torrent fallback.

---

## Session State — Last Updated: 2026-03-18

### ⚠️ CRITICAL: Myrient shuts down March 31, 2026

### User Setup
- Windows, `C:\RetroBat`, `C:\Users\keku\localdev\myrifetch\`
- Python 3.14, venv at `.venv\Scripts\pythonw.exe`
- RetroBat/EmulationStation with Xbox 360 controller
- `3ds` uses `azahar` emulator, `wii` uses `dolphin`
- ScreenScraper account: `keylesskeku` (auto-imported from RetroBat on first launch)

### Current Version
`v1.4.1` — 6699 lines

---

## ScreenScraper Integration (added this session)

### Background — confirmed RetroBat media structure
Read live from `C:\RetroBat\emulationstation\.emulationstation\es_settings.cfg`
and `C:\RetroBat\roms\3ds\`:

```
roms/<system>/
  ├── images/
  │   ├── GameName-image.png    ← sstitle screenshot  → <image>
  │   ├── GameName-marquee.png  ← wheel/marquee art   → <marquee>
  │   └── GameName-thumb.png    ← ES internal thumb
  ├── videos/
  │   └── GameName-video.mp4    ← video snap          → <video>
  ├── manuals/
  │   └── GameName-manual.pdf
  ├── GameName.jpg              ← box-3D art next to ROM → <thumbnail>
  └── gamelist.xml
```

**es_settings.cfg scraper settings:**
- `ScrapperImageSrc = sstitle`   → title/gameplay screenshot
- `ScrapperThumbSrc = box-3D`   → 3D box art saved as `<n>.jpg` next to ROM
- `ScrapeVideos = true`
- `ScrapeManual = true`
- Scraper: ScreenScraper (`ScreenScraperUser: keylesskeku`, `ScreenScraperPass: VoZuBCZibx7746`)

### New: `SCREENSCRAPER_SYSTEM_IDS` (line ~1475)
Maps MyriFetch console names → ScreenScraper platform IDs. `CONSOLE_TO_SS_ID` is an alias used throughout.

### New: `ScreenScraperManager` class (line ~1546)
- API endpoint: `https://www.screenscraper.fr/api2/jeuInfos.php`
- Auth: `ssid` + `sspassword` + `devid` + `devpassword` (all use SS credentials)
- `lookup_game(rom_name, system_id, log_cb)` — queries by filename + system ID
- `_find_media(jeu, media_type)` — picks best URL by region priority `wor→us→en→eu→jp`
- `download_media(url, dest_path, log_cb)` — streams to disk with `os.makedirs`
- `scrape_game(game, rom_dir, config, log_cb, progress_cb)` — downloads all 4 media types + extracts text metadata. Returns dict with keys: `image`, `thumbnail`, `marquee`, `video`, `desc`, `genre`, `developer`, `publisher`, `releasedate`, `players`, `rating`

### New: Module-level SS helper functions
- `_ss_pick_name(jeu)` — best region name from `jeu['noms']`
- `_ss_pick_text(items, lang)` — best synopsis for given language (falls back en→fr)
- `_ss_pick_genres(jeu)` — comma-joined genre names (up to 3)
- `_ss_pick_company(jeu, key)` — developer (`developpeur`) or publisher (`editeur`) name
- `_ss_pick_date(jeu)` — ES-format date string `YYYYMMDDTHHMMSS` from `jeu['dates']`
- `_ss_pick_rating(jeu)` — normalised 0.0–1.0 from SS 0–20 scale

### Updated: `UltimateApp` methods
- `_get_ss_manager()` — returns `ScreenScraperManager` from `folder_mappings['ss_user']`/`['ss_password']`, or None
- `scrape_game_art(game, done_cb)` — now uses SS; calls `done_cb(bool)` on main thread via `after()`
- `_writeback_scraped_meta(game, rom_dir, meta)` — writes all 11 gamelist.xml tags; converts abs paths to relative; removes stub `genre` tag
- `_scrape_single_and_refresh(game, card)` — per-card "🎨 Scrape Art" button handler (fixed from broken state)
- `scrape_missing_art()` — checks `_get_ss_manager()` instead of Twitch creds
- `_do_scrape_missing(missing)` — unchanged, 300ms rate limit between games

### Updated: `DownloadPopup._download_cover_art`
Now uses ScreenScraper instead of IGDB. Downloads box-3D + sstitle + marquee + video immediately after each ROM download, then calls `_writeback_scraped_meta_popup()` to update gamelist.xml.

### New: Settings UI — ScreenScraper section
Added after the RetroAchievements API section in `render_settings()`:
- `entry_ss_user` / `entry_ss_password` fields (password masked)
- Subtitle: "same account you use in RetroBat"
- "Save ScreenScraper Credentials" button → `save_ss_creds()`
- `save_ss_creds()` — saves to config, runs async verification ping to `ssuserInfos.php`, shows success/failure popup

### New: `_try_import_ss_creds_from_retrobat()`
Called from `load_config()` on first run if `ss_user` not already set. Reads `ScreenScraperUser` and `ScreenScraperPass` from `C:\RetroBat\emulationstation\.emulationstation\es_settings.cfg` automatically. User never needs to re-enter credentials.

---

## Full gamelist.xml Tag Schema (as written by MyriFetch)

```xml
<game>
  <path>./GameName.zip</path>
  <n>Clean Game Name</n>
  <image>./images/GameName-image.png</image>
  <thumbnail>./GameName.jpg</thumbnail>
  <marquee>./images/GameName-marquee.png</marquee>
  <video>./videos/GameName-video.mp4</video>
  <desc>Game description text...</desc>
  <genre>Action, Adventure</genre>
  <developer>Developer Name</developer>
  <publisher>Publisher Name</publisher>
  <releasedate>19960101T000000</releasedate>
  <players>2</players>
  <rating>0.85</rating>
</game>
```

Stub entries (not yet downloaded) have `<hidden>true</hidden>` and `<genre>Available to Download</genre>`. The `_writeback_scraped_meta` methods remove the stub genre once real data is scraped.

---

## Config Keys (folder_mappings / myrient_ultimate.json)

```json
{
  "ss_user":        "keylesskeku",
  "ss_password":    "VoZuBCZibx7746",
  "twitch_id":      "...",
  "twitch_secret":  "...",
  "ra_user":        "...",
  "ra_key":         "...",
  "retrobat_path":  "C:\\retrobat",
  "app_theme":      "Cyber Dark"
}
```

---

## Known Issues / Next Steps

1. **TeknoParrot scraping** — `.parrot` files passed as `rom_name` to SS will not match. Need to strip ` [...] [TP].parrot` suffix and query by game title instead.
2. **Missing SS system IDs** — TeknoParrot, MSX2+, PC-88, PC-98, Amiga 500/1200 not yet in `SCREENSCRAPER_SYSTEM_IDS`.
3. **Video downloads are large** — SS video snaps are 20–50 MB. Consider adding a "scrape videos" toggle in Settings (default on to match RetroBat behaviour).
4. **Rate limiting** — SS enforces thread limits for free accounts. `_do_scrape_missing` has `time.sleep(0.3)`. May need to increase for large libraries.
5. **Manual PDFs not fetched** — SS has `manual` media type. Not currently requested in `scrape_game()`.
6. **Tooltip/details still use IGDB** — `fetch_and_show_tooltip` and `show_game_details` summary panel still query Twitch/IGDB. This is intentional (different feature). Could unify to SS later.
