# Library System Tabs + Debug Logging Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the library console dropdown with a tab bar that groups games by system, and add a debug/logging mode that captures detailed scrape failure info to a log file.

**Architecture:** All changes are in the monolithic `MyriFetch.py`. The library tab bar uses a `ctk.CTkFrame` of `CTkButton` tabs rendered after each scan; a `_library_games` cache avoids re-scanning on tab switches. Debug logging uses Python's `logging` module with a `FileHandler` toggled via a Settings switch; a `_debug_log()` helper is passed as `log_cb` into `ScreenScraperManager` methods which already accept it.

**Tech Stack:** Python 3.11, customtkinter, Python `logging` module (stdlib)

---

## File Map

| File | Change |
|------|--------|
| `MyriFetch.py` line 1–28 | Add `import logging` |
| `MyriFetch.py` line 38–47 | Add `LOG_FILE` constant after `APP_DATA` |
| `MyriFetch.py` ~2104 (`__init__`) | Add `self._library_games = None` cache field |
| `MyriFetch.py` ~2468 (library header) | Remove `lib_sort_menu` CTkOptionMenu; add `lib_tab_frame` |
| `MyriFetch.py` ~2849 (`_load_library_async`) | Cache scan result in `self._library_games` |
| `MyriFetch.py` ~3174 (`_update_lib_sort_menu`) | Replace with `_build_lib_tabs(sorted_consoles)` |
| `MyriFetch.py` ~3179 (`render_library_grid`) | Use cache when tabs clicked (no rescan) |
| `MyriFetch.py` ~3339 (`scrape_game_art`) | Pass `log_cb=self._debug_log` |
| `MyriFetch.py` ~3288 (`_do_scrape_missing` / `scrape_missing_art`) | Pass `log_cb=self._debug_log` |
| `MyriFetch.py` ~3564 (`render_settings`) | Add `DEBUG LOGGING` toggle + Open Log button |
| `MyriFetch.py` ~4050 (`_toggle_bool_setting`) | Call `_setup_logging()` when key == `debug_mode` |
| `MyriFetch.py` new methods | `_setup_logging()`, `_debug_log()`, `_build_lib_tabs()`, `_on_lib_tab_click()` |
| `MyriFetch.py` ~1581 (`ScreenScraperManager.lookup_game`) | Log request URL, HTTP status, full traceback |
| `MyriFetch.py` ~1641 (`ScreenScraperManager.download_media`) | Log URL, HTTP status, full traceback |

---

## Task 1: Add `logging` import and LOG_FILE constant

**Files:**
- Modify: `MyriFetch.py:1-28` (imports)
- Modify: `MyriFetch.py:38-47` (constants after APP_DATA)

> No automated tests exist in this project. Each task includes a manual verification step.

- [ ] **Step 1: Add `import logging` to the imports block**

Find the imports block (lines 1–27) and add after `import traceback`:

```python
import logging
```

- [ ] **Step 2: Add LOG_FILE constant after APP_DATA is set (~line 47)**

```python
LOG_FILE = os.path.join(APP_DATA, 'myrifetch_debug.log')
```

- [ ] **Step 3: Verify syntax**

```bash
python -c "import ast; ast.parse(open('MyriFetch.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add MyriFetch.py
git commit -m "feat: add logging import and LOG_FILE constant"
```

---

## Task 2: Add debug logging infrastructure to UltimateApp

**Files:**
- Modify: `MyriFetch.py` — `__init__`, new `_setup_logging`, new `_debug_log` methods

- [ ] **Step 1: Add `self._library_games = None` and logger init to `__init__`**

In `__init__` near line 2104 where `self.library_widgets = []` is set, add:

```python
self._library_games = None   # cache – avoids rescan on tab switch
self._logger = None          # set up by _setup_logging()
self._setup_logging()
```

- [ ] **Step 2: Add `_setup_logging` method** (add after `load_config`, ~line 2185)

```python
def _setup_logging(self):
    """Configure (or tear down) the file logger based on the debug_mode setting."""
    enabled = bool(self.folder_mappings.get('debug_mode', False))
    logger = logging.getLogger('MyriFetch')
    # Remove all existing handlers first to avoid duplicates on toggle
    for h in list(logger.handlers):
        logger.removeHandler(h)
        h.close()
    if enabled:
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            '%(asctime)s  %(levelname)-8s  %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(fh)
        logger.debug('--- Debug logging started ---')
    else:
        logger.setLevel(logging.CRITICAL)  # effectively silent
    self._logger = logger
```

- [ ] **Step 3: Add `_debug_log` method** (right after `_setup_logging`)

```python
def _debug_log(self, msg: str):
    """Write a debug message to the log file if debug mode is on."""
    if self._logger:
        self._logger.debug(msg)
```

- [ ] **Step 4: Verify syntax**

```bash
python -c "import ast; ast.parse(open('MyriFetch.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add MyriFetch.py
git commit -m "feat: add _setup_logging and _debug_log infrastructure"
```

---

## Task 3: Add debug mode toggle to Settings UI

**Files:**
- Modify: `MyriFetch.py` — `render_settings` (~line 3642), `_toggle_bool_setting` (~line 4050)

- [ ] **Step 1: Add `DEBUG LOGGING` to the toggles loop in `render_settings`**

Find the toggles list (around line 3643):
```python
for label, key, default in [
    ("FINISH CHIME", 'notif_sound', True),
    ("FILTER DEMOS", 'filter_demos', False),
    ("FILTER REVISIONS", 'filter_revs', False),
    ("GAME SUBFOLDERS", 'subfolder_per_game', True),
]:
```
Add a new entry at the end of the list:
```python
    ("DEBUG LOGGING", 'debug_mode', False),
```

- [ ] **Step 2: Add "Open Log File" button right after the toggles loop, before the separator**

Find the separator line right after the toggles loop (`sep = ctk.CTkFrame(self.settings_scroll ...`). Insert before it:

```python
# Open log file button (only shown when debug mode is on)
if self.folder_mappings.get('debug_mode', False):
    log_row = _row("DEBUG LOG FILE", cyan=False)
    ctk.CTkButton(
        log_row, text="📋 Open Log",
        fg_color=C['card'], hover_color=C['cyan'],
        font=('Arial', 12), width=120,
        command=lambda: (
            os.startfile(LOG_FILE) if os.name == 'nt'
            else subprocess.Popen(['xdg-open', LOG_FILE])
        ) if os.path.exists(LOG_FILE) else None
    ).pack(side='left', padx=10)
    ctk.CTkLabel(
        log_row,
        text=LOG_FILE, text_color=C['dim'], font=('Arial', 9)
    ).pack(side='left', padx=5)
    self.settings_widgets.append(log_row)
```

- [ ] **Step 3: Update `_toggle_bool_setting` to re-initialise logging when debug_mode changes**

Find `_toggle_bool_setting` (~line 4050):
```python
def _toggle_bool_setting(self, key, var):
    self.folder_mappings[key] = var.get()
    self.save_config()
    if key in ('filter_demos', 'filter_revs'):
        self.filter_list()
```
Add a new branch:
```python
    if key == 'debug_mode':
        self._setup_logging()
        self.render_settings()  # refresh to show/hide the Open Log button
```

- [ ] **Step 4: Verify syntax**

```bash
python -c "import ast; ast.parse(open('MyriFetch.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Manual verification**

Launch the app → Settings → toggle DEBUG LOGGING on → confirm LOG_FILE is created:
```bash
python -c "import os; p=os.path.join(os.environ.get('APPDATA','~'), 'MyriFetch', 'myrifetch_debug.log'); print('exists:', os.path.exists(p))"
```
Expected: `exists: True`

- [ ] **Step 6: Commit**

```bash
git add MyriFetch.py
git commit -m "feat: add debug logging toggle to Settings with Open Log button"
```

---

## Task 4: Enhance ScreenScraperManager to emit richer debug logs

**Files:**
- Modify: `MyriFetch.py` — `ScreenScraperManager.lookup_game` (~line 1581), `ScreenScraperManager.download_media` (~line 1641)

- [ ] **Step 1: Enhance `lookup_game` to log request details and full tracebacks**

Find the `try:` block inside `lookup_game` (~line 1597). Replace it with:

```python
        # Sanitised URL for logging (no passwords)
        safe_params = {k: v for k, v in params.items()
                       if k not in ('devpassword', 'sspassword')}
        log(f'ScreenScraper → GET systemeid={params["systemeid"]} romnom={params["romnom"]!r}')
        log(f'  params (sanitised): {safe_params}')
        try:
            r = self._session.get(
                self.SS_API, params=params, timeout=20
            )
            log(f'  HTTP {r.status_code}')
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            log(f'ScreenScraper API error: {type(e).__name__}: {e}')
            log(traceback.format_exc())
            return None
```

- [ ] **Step 2: Enhance `download_media` to log URL and full tracebacks**

Find the `try:` block inside `download_media` (~line 1651). Replace it with:

```python
        log(f'ScreenScraper → downloading {url}')
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            r = self._session.get(url, timeout=30, stream=True)
            log(f'  HTTP {r.status_code}')
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
            log(f'Saved: {dest_path}')
            return True
        except Exception as e:
            log(f'Media download failed ({url}): {type(e).__name__}: {e}')
            log(traceback.format_exc())
            return False
```

- [ ] **Step 3: Verify syntax**

```bash
python -c "import ast; ast.parse(open('MyriFetch.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add MyriFetch.py
git commit -m "feat: enhance ScreenScraperManager to log request details and tracebacks"
```

---

## Task 5: Wire `_debug_log` into scraping call sites

**Files:**
- Modify: `MyriFetch.py` — `scrape_game_art` (~line 3339), `_do_scrape_missing` (~line 3288)

The `ScreenScraperManager.scrape_game()` already accepts a `log_cb` parameter, but the call sites don't pass one. Fix that.

- [ ] **Step 1: Pass `log_cb` in `scrape_game_art`**

Find `_fetch()` inside `scrape_game_art` (~line 3362):
```python
        def _fetch():
            meta = ss.scrape_game(game, rom_dir, config)
```
Replace with:
```python
        def _fetch():
            meta = ss.scrape_game(game, rom_dir, config, log_cb=self._debug_log)
```

- [ ] **Step 2: Verify `_do_scrape_missing` is covered**

`_do_scrape_missing` calls `self.scrape_game_art(game, done_cb=_on_done)` which we fixed in Step 1. No direct change needed — the log_cb propagates automatically.

- [ ] **Step 3: Verify syntax**

```bash
python -c "import ast; ast.parse(open('MyriFetch.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Manual verification**

1. Enable debug mode in Settings
2. Trigger a scrape (single game or bulk)
3. Check log file for detailed output:

```bash
python -c "
import os
lf = os.path.join(os.environ.get('APPDATA','~'), 'MyriFetch', 'myrifetch_debug.log')
print(open(lf).read()[-2000:] if os.path.exists(lf) else 'NOT FOUND')
"
```
Expected: Lines showing `ScreenScraper → GET systemeid=... romnom=...`, `HTTP 200` (or error + traceback).

- [ ] **Step 5: Commit**

```bash
git add MyriFetch.py
git commit -m "feat: wire debug log_cb through scrape_game_art"
```

---

## Task 6: Replace library dropdown with system tab bar

**Files:**
- Modify: `MyriFetch.py` — library header setup (~line 2468), `_update_lib_sort_menu` (~line 3174), `render_library_grid` (~line 3179), `_load_library_async` (~line 2849), `show_library` (~line 2843)

- [ ] **Step 1: Replace the library header dropdown with a tab frame**

Find the `# Library` section (~line 2468–2494). The current header has a `lib_sort_menu` CTkOptionMenu and `lib_sort_var`. Replace the whole Library setup block:

**Old (lines ~2468–2494):**
```python
        # Library
        self.lib_header = ctk.CTkFrame(self.frame_library, fg_color='transparent')
        self.lib_header.pack(fill='x', pady=10)
        ctk.CTkLabel(
            self.lib_header, text="GAME LIBRARY",
            font=('Arial', 20, 'bold'), text_color=C['cyan']
        ).pack(side='left')
        self.lib_sort_var = ctk.StringVar(value="All Consoles")
        self.lib_sort_menu = ctk.CTkOptionMenu(
            self.lib_header, variable=self.lib_sort_var,
            values=['All Consoles'], command=self.render_library_grid,
            fg_color=C['card'], button_color=C['cyan'],
            button_hover_color=C['pink'], text_color='white', width=160
        )
        self.lib_sort_menu.pack(side='right')
        # Scrape all missing art button
        self.btn_scrape_all = ctk.CTkButton(
            self.lib_header, text="🎨 Scrape Missing Art",
            fg_color=C['card'], hover_color=C['pink'],
            font=('Arial', 12), width=170,
            command=self.scrape_missing_art
        )
        self.btn_scrape_all.pack(side='right', padx=(0, 8))
        self.lib_scroll = ctk.CTkScrollableFrame(
            self.frame_library, fg_color=C['card']
        )
        self.lib_scroll.pack(fill='both', expand=True)
        self.bind_scroll(self.lib_scroll, self.lib_scroll)
```

**New:**
```python
        # Library
        self.lib_sort_var = ctk.StringVar(value="All")
        self.lib_header = ctk.CTkFrame(self.frame_library, fg_color='transparent')
        self.lib_header.pack(fill='x', pady=(10, 4))
        ctk.CTkLabel(
            self.lib_header, text="GAME LIBRARY",
            font=('Arial', 20, 'bold'), text_color=C['cyan']
        ).pack(side='left')
        # Scrape all missing art button (top-right)
        self.btn_scrape_all = ctk.CTkButton(
            self.lib_header, text="🎨 Scrape Missing Art",
            fg_color=C['card'], hover_color=C['pink'],
            font=('Arial', 12), width=170,
            command=self.scrape_missing_art
        )
        self.btn_scrape_all.pack(side='right', padx=(0, 8))
        # Horizontal tab bar for system filtering
        self.lib_tab_frame = ctk.CTkFrame(self.frame_library, fg_color='transparent')
        self.lib_tab_frame.pack(fill='x', pady=(0, 6))
        self.lib_scroll = ctk.CTkScrollableFrame(
            self.frame_library, fg_color=C['card']
        )
        self.lib_scroll.pack(fill='both', expand=True)
        self.bind_scroll(self.lib_scroll, self.lib_scroll)
```

- [ ] **Step 2: Add `_build_lib_tabs` method** (to replace `_update_lib_sort_menu`)

Find `def _update_lib_sort_menu(self, sorted_consoles, current_sort):` (~line 3174). Replace the entire method:

```python
    def _build_lib_tabs(self, sorted_consoles: list[str], current_sort: str):
        """Rebuild the horizontal system tab bar. Called on the main thread."""
        for w in self.lib_tab_frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        # Ensure "All" is always first
        tabs = ['All'] + [c for c in sorted_consoles if c != 'All']
        for label in tabs:
            is_active = label == current_sort
            btn = ctk.CTkButton(
                self.lib_tab_frame, text=label,
                fg_color=C['cyan'] if is_active else C['card'],
                text_color='black' if is_active else 'white',
                hover_color=C['pink'],
                height=28, corner_radius=6, font=('Arial', 11),
                command=lambda c=label: self._on_lib_tab_click(c)
            )
            btn.pack(side='left', padx=3, pady=3)
```

- [ ] **Step 3: Add `_on_lib_tab_click` method** (right after `_build_lib_tabs`)

```python
    def _on_lib_tab_click(self, console: str):
        """Switch the library view to the selected system tab without rescanning."""
        self.lib_sort_var.set(console)
        if self._library_games is not None:
            # Re-render using the cache — no filesystem scan needed
            self._build_lib_tabs(
                sorted({g['console'] for g in self._library_games}),
                console
            )
            self._render_library_with_games(self._library_games)
        else:
            self._load_library_async()
```

- [ ] **Step 4: Update `_update_lib_sort_menu` call in `scan_library`**

Find in `scan_library` (~line 3170):
```python
        self.after(0, lambda sc=sorted_consoles, cs=current_sort:
            self._update_lib_sort_menu(sc, cs))
```
Replace with:
```python
        self.after(0, lambda sc=sorted_consoles, cs=current_sort:
            self._build_lib_tabs(sc, cs))
```

- [ ] **Step 5: Update `scan_library` to build the `found_consoles` set without `"All Consoles"` sentinel**

The existing code adds `'All Consoles'` to `found_consoles` at line 3098. Find:
```python
        found_consoles = {'All Consoles'}
```
Replace with:
```python
        found_consoles = set()
```
(The `_build_lib_tabs` method always prepends "All" itself.)

Also find where `current_sort` is read in `scan_library`:
```python
        current_sort = self.lib_sort_var.get()
```
The `lib_sort_var` default value is now `"All"` (changed in Task 6 Step 1), so this still works.

- [ ] **Step 6: Update `_render_library_with_games` filter condition**

Find (~line 3192):
```python
        filter_console = self.lib_sort_var.get()
        filtered = [
            g for g in games
            if filter_console == "All Consoles" or g['console'] == filter_console
        ]
```
Replace with:
```python
        filter_console = self.lib_sort_var.get()
        filtered = [
            g for g in games
            if filter_console == "All" or g['console'] == filter_console
        ]
```

- [ ] **Step 7: Cache the game list in `_load_library_async`**

Find in `_load_library_async` (~line 2870):
```python
        def _scan():
            games = self.scan_library()
            self.after(0, lambda: self._render_library_with_games(games))
```
Replace with:
```python
        def _scan():
            games = self.scan_library()
            self._library_games = games   # cache for tab switching
            self.after(0, lambda: self._render_library_with_games(games))
```

- [ ] **Step 8: Clear cache when library page is opened fresh**

Find `show_library` (~line 2843):
```python
    def show_library(self):
        self.hide_all()
        self.frame_library.grid(row=1, column=0, sticky='nsew')
        self.btn_library.configure(fg_color=C['cyan'], text_color='black')
        self._load_library_async()
```
Replace with:
```python
    def show_library(self):
        self.hide_all()
        self.frame_library.grid(row=1, column=0, sticky='nsew')
        self.btn_library.configure(fg_color=C['cyan'], text_color='black')
        self._library_games = None  # force fresh scan on each visit
        self._load_library_async()
```

- [ ] **Step 9: Update `render_library_grid` to use cache when available**

Find (~line 3179):
```python
    def render_library_grid(self, _=None):
        """Public entry point — always goes through the async loader."""
        self._load_library_async()
```
Replace with:
```python
    def render_library_grid(self, _=None):
        """Re-render the grid. Uses cached games if available, else rescans."""
        if self._library_games is not None:
            self._render_library_with_games(self._library_games)
        else:
            self._load_library_async()
```

> ⚠️ **Step ordering note:** Steps 2 (rename `_update_lib_sort_menu` → `_build_lib_tabs`) and Step 4 (update the call site in `scan_library`) must be applied together before running the app. All of Task 6 is committed as one unit in Step 12 — do not run the app between steps 2 and 4.

- [ ] **Step 10: Verify syntax**

```bash
python -c "import ast; ast.parse(open('MyriFetch.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 11: Manual verification**

1. Launch app → Library → confirm tab bar appears with "All" active
2. Confirm tabs only show for systems where you have games
3. Click a system tab → games filter without triggering "Scanning..." spinner
4. Scrape art → confirm "Scrape Missing Art" button still works
5. Navigate away and back → confirm tabs rebuild correctly on fresh visit

- [ ] **Step 12: Commit**

```bash
git add MyriFetch.py
git commit -m "feat: replace library console dropdown with horizontal system tab bar"
```

---

## Final verification

- [ ] **Run the app end-to-end**

```bash
python MyriFetch.py
```

Checklist:
- [ ] Library page shows tab bar ("All" + per-system tabs for systems with games)
- [ ] Switching tabs re-filters instantly (no spinner)
- [ ] Returning to Library page triggers fresh scan (spinner appears)
- [ ] "🎨 Scrape Missing Art" button still visible and functional
- [ ] Settings → DEBUG LOGGING toggle works; log file created on enable
- [ ] Log file shows detailed ScreenScraper requests, HTTP status codes, tracebacks on failure
- [ ] "📋 Open Log" button appears in Settings when debug mode is on
- [ ] Syntax clean: `python -c "import ast; ast.parse(open('MyriFetch.py').read()); print('OK')"`
