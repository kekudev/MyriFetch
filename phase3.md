# Phase 3: On-Demand Download Launcher for RetroBat

MyriFetch intercepts EmulationStation game launches for missing ROMs, downloads them from Myrient with a minimal progress popup, optionally compresses to CHD, then auto-launches via emulatorLauncher.exe — all seamless to the user.

---

## Objective

When a user selects a game in EmulationStation that doesn't exist on disk (listed via gamelist.xml sync from Phase 2), a wrapper script detects the missing file, invokes MyriFetch in headless download mode, shows a minimal progress window, and after download + optional CHD compression, launches the game normally.

## Acceptance Criteria

1. User selects a missing game in ES → minimal popup appears showing download progress (filename, speed, bar, cancel)
2. Download completes → CHD compression runs if enabled for that system → game auto-launches via `emulatorLauncher.exe`
3. If user cancels download → returns cleanly to EmulationStation (no orphan files)
4. Works for all 12 MyriFetch consoles: PS1, PS2, PS3, PSP, GameCube, Wii, Dreamcast, Xbox, SNES, GBA, NDS, 3DS
5. MyriFetch Settings has "Enable On-Demand Launcher" button that auto-patches `es_systems.cfg` (with `.bak` backup)
6. MyriFetch Settings has "Restore Original es_systems.cfg" button to undo
7. If ROM already exists → wrapper passes through to `emulatorLauncher.exe` with zero overhead
8. No regressions to existing MyriFetch GUI functionality

## Scope

### In Scope
- `myrient_launcher.py` — standalone wrapper script (new file)
- `MyriFetch.py` — CLI mode (`--download`), Settings UI for enable/restore, es_systems.cfg patching
- `es_systems.cfg` — auto-patched `<command>` for 12 systems
- Minimal Tkinter progress popup (reuses existing theme constants)

### Out of Scope
- Linux/macOS support (RetroBat is Windows-only)
- Scraping metadata during on-demand download
- Batch/queue downloads from ES (single game only)
- Modifying `emulatorLauncher.exe` or RetroBat core code

## Constraints

- **Windows-only** — RetroBat doesn't run on other platforms
- **No new dependencies** — must work with existing MyriFetch requirements (requests, beautifulsoup4, customtkinter, Pillow)
- **Startup speed** — wrapper must check file existence and pass through in <100ms for owned games
- **ES blocks on `<command>`** — EmulationStation waits for the command to exit before resuming, so the wrapper must be synchronous
- **Config path** — `es_systems.cfg` lives at `{retrobat_path}\emulationstation\.emulationstation\es_systems.cfg`
- **Encoding** — es_systems.cfg is UTF-8 XML; must preserve all non-MyriFetch systems untouched

---

## Architecture

```
EmulationStation
    │
    ▼  <command> (patched)
myrient_launcher.py --rom %ROM% --system %SYSTEM% --emulator %EMULATOR% --core %CORE% ...
    │
    ├─ ROM exists? ──YES──▶ exec emulatorLauncher.exe (original args) ──▶ return to ES
    │
    └─ ROM missing? ──▶ Resolve Myrient URL from system + filename
                        │
                        ▼
                   Minimal Tk popup (download + optional CHD)
                        │
                        ├─ Success ──▶ exec emulatorLauncher.exe ──▶ return to ES
                        └─ Cancel  ──▶ cleanup partial files ──▶ return to ES (exit 0)
```

---

## Implementation Plan

### Task 1: Add CLI argument parsing to MyriFetch.py
**File:** `MyriFetch.py` (modify `if __name__ == '__main__'` block)

- Add `argparse` to handle `--download <rom_path> --system <system_name> --myrient-path <myrient_dir>`
- When CLI args present: skip GUI, run headless download + CHD, exit
- When no CLI args: launch full GUI as today
- The CLI mode needs access to: `session`, `HEADERS`, `BASE_URL`, `NUM_THREADS`, config (for chdman path, CHD enabled systems)
- Extract download logic into a reusable function callable from both GUI and CLI

```
Steps:
1. Add `import argparse` at top
2. Create `parse_cli_args()` function
3. Create `headless_download(rom_name, myrient_path, dest_dir, config)` function
   - Reuses existing HTTP session + Hydra multi-thread download logic
   - Returns (success: bool, local_path: str)
4. Create `headless_chd_compress(file_path, chdman_path)` function
   - Reuses existing CHD logic
   - Returns (success: bool, chd_path: str)
5. Modify `if __name__ == '__main__'` to branch on CLI args
```

### Task 2: Create minimal download progress popup
**File:** `MyriFetch.py` (new class `DownloadPopup`)

- Standalone Tk window (not CTk — lighter weight, no theme dep for fast startup)
  - Actually use CTk since it's already imported and matches the MyriFetch aesthetic
- Shows: game name, system, download speed, progress bar, ETA, Cancel button
- Communicates with download thread via `threading.Event` (reuse pattern from Phase 1 fixes)
- Window is ~400x200px, centered on screen, always-on-top
- On cancel: sets cancel event, cleans up partial files, exits with code 0
- On completion: auto-closes, returns control to caller

```
Steps:
1. Create `DownloadPopup(ctk.CTk)` class with:
   - Title bar: "MyriFetch — Downloading..."
   - Label: game name + system
   - Progress bar (determinate, 0-100%)
   - Speed label: "12.3 MB/s"
   - ETA label: "~2:34 remaining"
   - Cancel button
2. Download runs in background thread, updates popup via `after()`
3. Add CHD compression phase: progress bar switches to indeterminate, label says "Compressing to CHD..."
```

### Task 3: Create myrient_launcher.py wrapper script
**File:** `myrient_launcher.py` (new file in project root)

This is the script that es_systems.cfg `<command>` points to. It must be fast for the pass-through case.

```
Steps:
1. Parse command-line args matching EmulationStation's format:
   -rom, -system, -emulator, -core, -gameinfo, and controller config
2. Check if ROM file exists at the path given by -rom
3. If EXISTS:
   - Build original emulatorLauncher.exe command
   - subprocess.run() it (blocking — ES waits)
   - Exit with emulatorLauncher's exit code
4. If MISSING:
   - Determine the Myrient path from system name using RETROBAT_ROM_FOLDERS + CONSOLES mapping
   - Determine the ROM filename from the -rom path
   - Determine the destination directory from the -rom path's parent
   - Launch MyriFetch.py in CLI mode:
     `python MyriFetch.py --download <rom_filename> --myrient-path <path> --dest <dir> --system <system>`
   - If MyriFetch exits 0 (success):
     - ROM now exists → run emulatorLauncher.exe
   - If MyriFetch exits non-zero (cancel/error):
     - Exit 0 (return to ES cleanly)
5. Include the CONSOLES and RETROBAT_ROM_FOLDERS mappings (or import from MyriFetch)
   - To avoid import complexity, embed a minimal reverse-lookup dict
```

**Critical: fast path.** For existing ROMs, this script must:
- `os.path.isfile(rom_path)` → True → `subprocess.run(emulatorLauncher...)` 
- Total overhead: ~50ms Python startup + one stat call

### Task 4: Resolve ROM filename → Myrient URL
**File:** `MyriFetch.py` (new method or function)

The gamelist.xml `<path>` contains `./Filename.zip`. The wrapper needs to turn that into a downloadable Myrient URL.

```
Steps:
1. Create mapping: RetroBat system name → MyriFetch CONSOLES myrient_path
   SYSTEM_TO_MYRIENT = {
     'psx': 'Redump/Sony - PlayStation/',
     'ps2': 'Redump/Sony - PlayStation 2/',
     'ps3': 'Redump/Sony - PlayStation 3/',
     'psp': 'Redump/Sony - PlayStation Portable/',
     'gamecube': 'Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]/',
     'wii': 'Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]/',
     'dreamcast': 'Redump/Sega - Dreamcast/',
     'xbox': 'Redump/Microsoft - Xbox/',
     'snes': 'No-Intro/Nintendo - Super Nintendo Entertainment System/',
     'gba': 'No-Intro/Nintendo - Game Boy Advance/',
     'nds': 'No-Intro/Nintendo - Nintendo DS (Decrypted)/',
     '3ds': 'No-Intro/Nintendo - Nintendo 3DS (Decrypted)/',
   }
2. URL = BASE_URL + myrient_path + quote(filename)
3. Validate URL with a HEAD request before starting download
```

### Task 5: Auto-patch es_systems.cfg
**File:** `MyriFetch.py` (new methods in `UltimateApp`)

```
Steps:
1. Add `patch_es_systems_cfg(self)` method:
   a. Read es_systems.cfg path: `{retrobat_path}/emulationstation/.emulationstation/es_systems.cfg`
   b. Create backup: `es_systems.cfg.myrient.bak` (only if .bak doesn't already exist)
   c. Parse XML with ElementTree
   d. For each <system> whose <name> matches a RETROBAT_ROM_FOLDERS value:
      - Save original <command> text as a new <myrient_original_command> element (for restore)
      - Replace <command> with:
        `python "{myrifetch_dir}\myrient_launcher.py" -gameinfo %GAMEINFOXML% %CONTROLLERSCONFIG% -system %SYSTEM% -emulator %EMULATOR% -core %CORE% -rom %ROM%`
      - Actually: use `pythonw` or the frozen exe path to avoid console flash
   e. Write patched XML back (preserving encoding declaration)
   f. Show success popup with count of patched systems

2. Add `restore_es_systems_cfg(self)` method:
   a. Copy .bak back to es_systems.cfg
   b. Show success popup

3. Add `is_es_systems_patched(self)` method:
   - Quick check: does any <command> reference myrient_launcher?
   - Used to show correct button state in Settings
```

### Task 6: Settings UI for On-Demand Launcher
**File:** `MyriFetch.py` (modify `render_settings`)

```
Steps:
1. Add new section "ON-DEMAND LAUNCHER" after RetroBat Integration section
2. Status label: "Enabled ✔" / "Not configured"
3. Button: "Enable On-Demand Launcher" (calls patch_es_systems_cfg)
   - Changes to "Restore Original" if already patched
4. Info label: "Intercepts ES game launches for missing ROMs. Requires RetroBat restart."
5. Button: "Test Launcher" — simulates a missing ROM scenario to verify the wrapper works
```

### Task 7: Handle edge cases and cleanup
**File:** `MyriFetch.py`, `myrient_launcher.py`

```
Steps:
1. Partial download cleanup:
   - On cancel/error, delete .part files and incomplete downloads
   - If subfolder_per_game is enabled, clean up empty game subfolders
2. Handle frozen exe vs script mode:
   - If MyriFetch is compiled (PyInstaller), use sys.executable
   - If running from source, use `pythonw MyriFetch.py`
   - Wrapper must detect this and use correct invocation
3. Handle missing chdman:
   - If CHD enabled but chdman not found, skip compression, launch raw file
   - Log warning
4. Handle network errors:
   - Show error in popup with Retry/Cancel
5. Handle ES restart requirement:
   - After patching, show popup: "RetroBat must be restarted for changes to take effect"
6. Path handling:
   - All paths use os.path for Windows compatibility
   - Handle spaces in paths (quoted args)
   - Handle unicode filenames (Japanese game titles)
```

### Task 8: Update README.md
**File:** `README.md`

```
Steps:
1. Update RetroBat Integration section:
   - Add step 4: On-Demand Launcher setup instructions
2. Update "Planned" section → mark as implemented
3. Add to v1.4.1 changelog (or create v1.4.2 section)
```

---

## File Changes Summary

| File | Action | Description |
|---|---|---|
| `MyriFetch.py` | Modify | Add argparse CLI mode, DownloadPopup class, headless download/CHD functions, es_systems.cfg patch/restore methods, Settings UI section |
| `myrient_launcher.py` | **Create** | Wrapper script: check ROM → pass-through or trigger download |
| `README.md` | Modify | Document on-demand launcher setup and usage |

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| RetroBat update overwrites es_systems.cfg | Backup stored as `.myrient.bak`; "Enable" button can re-apply; detect on MyriFetch startup |
| Python startup adds latency for owned games | Use `pythonw.exe` to skip console; keep wrapper minimal; consider compiling to .exe later |
| ES sends unexpected args | Wrapper passes all unknown args through to emulatorLauncher unchanged |
| Large PS3 games (30GB+) timeout | Reuse Hydra 4-thread engine; show ETA in popup so user knows |
| CHD compression fails mid-way | Launch raw file as fallback; log error; compress on next MyriFetch open |
| es_systems.cfg XML format changes | Use ElementTree for robust parsing; don't regex-replace |

## Task Order

1. **Task 1** — CLI arg parsing (foundation)
2. **Task 2** — Download popup (UX)
3. **Task 4** — URL resolution (data layer)
4. **Task 3** — Wrapper script (integration)
5. **Task 5** — es_systems.cfg patching (setup)
6. **Task 6** — Settings UI (user-facing)
7. **Task 7** — Edge cases (polish)
8. **Task 8** — README (docs)
