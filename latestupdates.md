# MyriFetch — Latest Updates

## Stub Visibility & CHD Drift Overhaul (previous session)

### Problems Solved

1. **`[Download]` prefix was ugly and fragile** — sorted all stubs to the top alphabetically, polluted game names, wasn't a persistent toggle.
2. **Genre pollution** — stub genre tag was overwriting real IGDB genre data on scraped games.
3. **CHD drift** — after `.zip` → `.chd` conversion, gamelist.xml still pointed at `.zip`. Next cold launch triggered download again.
4. **No dedicated "storefront" view** — no clean way to browse all downloadable titles across all systems.

### Changes

**`_write_gamelist_xml`** — Stubs now get `<hidden>true</hidden>` instead of `[Download]` prefix. Revealed via UI Settings → Show Hidden Games (persistent, theme-agnostic toggle). Genre tag preserved as secondary filter. Extension priority order fixed (`.chd` before `.zip`). Atomic write via `.tmp` + `os.replace()`.

**`gamelist_writeback()`** — New module-level function. Called after every successful download. Finds game's XML entry by base name, updates `<path>`, removes `<hidden>`, removes stub genre. Permanently closes CHD drift.

**`_generate_collection_cfg()`** — New class method. Writes ES autolist collection file creating an "Available to Download" system in the ES main menu.

**`sync_retrobat_gamelists`** — Calls `_generate_collection_cfg()` after every sync.

**`run_cli_download`** — Calls `gamelist_writeback()` after every successful on-demand download.

**`myrient_launcher.py`** — Post-download ROM detection expanded from `.chd` only to all alternate extensions (`.chd`, `.rvz`, `.iso`, `.cso`, `.cue`, `.bin`, `.gdi`), consistent with `_write_gamelist_xml` priority order.

---

## Latest Session — 5 Improvements

### 1. Region Filtering at Sync Time

**Problem:** Myrient catalogs contain every region variant of every game — `(USA)`, `(Europe)`, `(Japan)`, `(Rev 1)`, `(Beta)` etc. A full PS2 sync previously created ~4,000 stubs. Most users only want one region per title.

**New: `_apply_region_filter(file_list, preference)`** — Module-level function. Four modes:
- `All` — unchanged, full catalog (previous behaviour)
- `Best` — smart deduplication: one entry per title, priority order USA → World → En → Europe → Australia → Japan → first available. Revision/alternate entries of the winning region are kept.
- `USA` / `Europe` / `Japan` — simple inclusion filter for that region plus `(World)` titles.

**`sync_retrobat_gamelists`** — Now reads `sync_region_pref` from config and passes the catalog through `_apply_region_filter` before writing gamelists. Default is `Best`.

**Settings UI** — New **SYNC REGION FILTER** dropdown below the existing browser region filter. Options: `Best`, `All`, `USA`, `Europe`, `Japan`. Takes effect on next sync.

**Result:** PS2 goes from ~4,000 stubs → ~1,800 with `Best` mode.

---

### 2. Stub Thumbnail

**Problem:** Stubs had no thumbnail — black box in grid/wall themes, visually indistinct from corrupted or unscraped owned games.

**New: `_ensure_stub_thumbnail()`** — Module-level function. Generates a 200×200 PNG on first call: dark card, cyan rounded border, cyan download arrow, "AVAILABLE / TO DOWNLOAD" label. Cached to `APP_DATA/myrifetch_stub_thumb.png` — generated once, reused forever.

**`_write_gamelist_xml`** — Now calls `_ensure_stub_thumbnail()` once per sync and writes `<thumbnail>` tag on every stub entry.

**Result:** Stub games show a distinctive cyan download icon in any grid/wall theme. When Skraper scrapes real artwork later, it only overwrites owned games — stubs keep the download icon automatically.

---

### 3. Skraper — Proper Artwork (external tool, no code)

Full setup guide in `SETUP_GUIDE.md`. Key points:
- Matches by file hash not filename — handles Redump names perfectly where ES's built-in scraper fails
- Filter out files under 1 KB in Skraper to skip stubs, avoiding wasted ScreenScraper API credits
- Run after MyriFetch sync — merges into existing `gamelist.xml` by `<path>`, leaving stub entries untouched
- Pulls box art, video snaps, fanart, and wheel images in one pass

---

### 4. Auto-Writeback on GUI Downloads

**Problem:** `gamelist_writeback()` only fired on on-demand launcher downloads. Downloading via the MyriFetch GUI left `<hidden>true</hidden>` in place until the next manual sync — the game wouldn't appear in ES immediately.

**`DownloadPopup._download_thread`** — Added `gamelist_writeback()` call immediately after `self.success = True`, before `self.destroy()`. Covers both GUI and on-demand launcher paths. Non-fatal — logged as no-op if gamelist entry isn't found.

**Result:** Download via GUI → restart ES → game immediately visible. No manual sync required.

---

### 5. RetroArch Shaders Per System (configuration, no code)

Full setup guide in `SETUP_GUIDE.md`. Key points:
- Best method: Quick Menu → Shaders → Save Core Preset inside RetroArch during a game session
- Recommended: `crt-royale` / `crt-guest-advanced` for PS1/PS2/SNES/Dreamcast, `sharp-bilinear-simple` for GameCube/Wii/Xbox, `lcd3x` for GBA/PSP/3DS
- Always enable integer scaling before applying any shader
- CRT shaders require 1080p minimum — use `crt-simple` at 720p

---

## End-to-End Flow (current state)

| Scenario | Experience |
|---|---|
| Normal browsing | Only owned games visible. Clean library, correct Skraper artwork. |
| "What can I download for PS2?" | UI Settings → Show Hidden. Stubs appear with cyan download icon. With `Best` mode ~1,800 titles not ~4,000. |
| Browse all downloadable games | "Available to Download" collection in ES main menu. |
| Launch a stub | Launcher intercepts, MyriFetch downloads with progress popup. |
| Download completes (any path) | `gamelist_writeback()` fires: path updated, `<hidden>` removed. |
| Next launch | Fast path. No drift. Correct shader for the system. |
