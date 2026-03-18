#!/usr/bin/env python3
"""
MyriFetch On-Demand Launcher — wrapper script for RetroBat/EmulationStation.

Sits between EmulationStation's <command> and emulatorLauncher.exe.
If the ROM exists, passes through to emulatorLauncher.exe immediately.
If the ROM is missing, launches MyriFetch in headless download mode,
then auto-launches the game after download completes.

Usage (from es_systems.cfg <command>):
  pythonw "path/to/myrient_launcher.py" -system %SYSTEM% -rom %ROM%
      -emulator %EMULATOR% -core %CORE% -gameinfo %GAMEINFOXML% %CONTROLLERSCONFIG%
"""

import os
import sys
import subprocess
import json
from datetime import datetime

try:
    import tkinter as tk
except Exception:
    tk = None

# ---------------------------------------------------------------------------
# Minimal reverse mappings (duplicated from MyriFetch.py to avoid import overhead)
# ---------------------------------------------------------------------------

MYRIFETCH_STUB_MAGIC = b'MYRIFETCH_STUB\n'
APP_NAME = 'MyriFetch'

if os.name == 'nt':
    APP_DATA = os.path.join(
        os.environ.get('APPDATA', os.path.expanduser('~')), APP_NAME
    )
else:
    APP_DATA = os.path.join(os.path.expanduser('~'), '.config', APP_NAME)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LAUNCHER_LOG_FILE = os.path.join(PROJECT_ROOT, 'on_demand_launcher.log')

SYSTEM_TO_MYRIENT = {
    # Sony
    'ps3':  'Redump/Sony - PlayStation 3/',
    'ps2':  'Redump/Sony - PlayStation 2/',
    'psx':  'Redump/Sony - PlayStation/',
    'psp':  'Redump/Sony - PlayStation Portable/',
    # Nintendo
    'nes':        'No-Intro/Nintendo - Nintendo Entertainment System/',
    'snes':       'No-Intro/Nintendo - Super Nintendo Entertainment System/',
    'n64':        'No-Intro/Nintendo - Nintendo 64 (BigEndian)/',
    'n64dd':      'No-Intro/Nintendo - Nintendo 64DD/',
    'gamecube':   'Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]/',
    'wii':        'Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]/',
    'wiiu':       'Redump/Nintendo - Wii U - WUX/',
    'gba':        'No-Intro/Nintendo - Game Boy Advance/',
    'gb':         'No-Intro/Nintendo - Game Boy/',
    'gbc':        'No-Intro/Nintendo - Game Boy Color/',
    'nds':        'No-Intro/Nintendo - Nintendo DS (Decrypted)/',
    '3ds':        'No-Intro/Nintendo - Nintendo 3DS (Decrypted)/',
    'virtualboy': 'No-Intro/Nintendo - Virtual Boy/',
    'fds':        'No-Intro/Nintendo - Family Computer Disk System (FDS)/',
    # Sega
    'megadrive':    'No-Intro/Sega - Mega Drive - Genesis/',
    'mastersystem': 'No-Intro/Sega - Master System - Mark III/',
    'saturn':       'Redump/Sega - Saturn/',
    'dreamcast':    'Redump/Sega - Dreamcast/',
    'megacd':       'Redump/Sega - Mega CD & Sega CD/',
    'gamegear':     'No-Intro/Sega - Game Gear/',
    'sega32x':      'No-Intro/Sega - 32X/',
    'sg1000':       'No-Intro/Sega - SG-1000/',
    # Microsoft
    'xbox':    'Redump/Microsoft - Xbox/',
    'xbox360': 'Redump/Microsoft - Xbox 360/',
    # SNK
    'neogeocd': 'Redump/SNK - Neo Geo CD/',
    'ngp':      'No-Intro/SNK - Neo Geo Pocket/',
    'ngpc':     'No-Intro/SNK - Neo Geo Pocket Color/',
    # Atari
    'atari2600':  'No-Intro/Atari - Atari 2600/',
    'atari5200':  'No-Intro/Atari - Atari 5200/',
    'atari7800':  'No-Intro/Atari - Atari 7800 (BIN)/',
    'lynx':       'No-Intro/Atari - Atari Lynx (LNX)/',
    'jaguar':     'No-Intro/Atari - Atari Jaguar (J64)/',
    'jaguarcd':   'Redump/Atari - Jaguar CD Interactive Multimedia System/',
    # NEC
    'pcengine':   'No-Intro/NEC - PC Engine - TurboGrafx-16/',
    'supergrafx': 'No-Intro/NEC - PC Engine SuperGrafx/',
    'pcenginecd': 'Redump/NEC - PC Engine CD & TurboGrafx CD/',
    'pcfx':       'Redump/NEC - PC-FX & PC-FXGA/',
    # Bandai
    'wswan':  'No-Intro/Bandai - WonderSwan/',
    'wswanc': 'No-Intro/Bandai - WonderSwan Color/',
    # Panasonic
    '3do': 'Redump/Panasonic - 3DO Interactive Multiplayer/',
    # Philips
    'cdi': 'Redump/Philips - CD-i/',
    # Commodore
    'amigacd32': 'Redump/Commodore - Amiga CD32/',
    # Other
    'colecovision':  'No-Intro/Coleco - ColecoVision/',
    'intellivision': 'No-Intro/Mattel - Intellivision/',
    'vectrex':       'No-Intro/GCE - Vectrex/',
    'msx1':          'No-Intro/Microsoft - MSX/',
    'msx2':          'No-Intro/Microsoft - MSX2/',
    # Arcade
    'teknoparrot':   'TeknoParrot/',
}

SOURCE_MODE_MYRIENT_ONLY = 'myrient_only'
SOURCE_MODE_MYRIENT_ARCHIVE = 'myrient_archive'
SOURCE_MODE_ARCHIVE_ONLY = 'archive_only'
SOURCE_MODE_MYRIENT_ARCHIVE_QBIT = 'myrient_archive_qbit'
SOURCE_MODE_LABELS = {
    SOURCE_MODE_MYRIENT_ONLY: 'Myrient only',
    SOURCE_MODE_MYRIENT_ARCHIVE: 'Myrient -> Archive.org',
    SOURCE_MODE_ARCHIVE_ONLY: 'Archive.org only',
    SOURCE_MODE_MYRIENT_ARCHIVE_QBIT: 'Myrient -> Archive.org -> qBittorrent',
}
DEFAULT_SOURCE_MODE = SOURCE_MODE_MYRIENT_ARCHIVE


def _log(message):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] [launcher] {message}'
    try:
        os.makedirs(APP_DATA, exist_ok=True)
        with open(LAUNCHER_LOG_FILE, 'a', encoding='utf-8', errors='replace') as f:
            f.write(line + '\n')
    except OSError:
        pass
    print(line, file=sys.stderr)


def _format_cmd(cmd):
    return ' '.join(f'"{part}"' if ' ' in str(part) else str(part) for part in cmd)


def load_launcher_config():
    cfg_path = os.path.join(APP_DATA, 'myrient_ultimate.json')
    try:
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception as e:
        _log(f'WARN: Failed to read config ({type(e).__name__}: {e})')
    return {}


def choose_source_mode_dialog(config, system, rom_name):
    """
    Show a minimal launcher dialog allowing source-mode override.
    Returns selected mode string, or None if user cancels.
    """
    default_mode = str(config.get('download_source_mode', DEFAULT_SOURCE_MODE)).strip()
    if default_mode not in SOURCE_MODE_LABELS:
        default_mode = DEFAULT_SOURCE_MODE
    if tk is None:
        _log('Source chooser skipped: tkinter unavailable, using configured default mode')
        return default_mode

    result = {'mode': None, 'cancelled': False}
    root = tk.Tk()
    root.title("MyriFetch Source Selection")
    root.geometry("520x300")
    root.resizable(False, False)
    root.configure(bg='#101014')
    try:
        root.attributes('-topmost', True)
    except Exception:
        pass

    mode_var = tk.StringVar(value=default_mode)
    txt_color = '#f4f4f5'
    dim_color = '#a1a1aa'
    cyan = '#00f2ff'
    bg = '#101014'

    title = tk.Label(
        root,
        text=f"{system.upper()}  |  {rom_name}",
        bg=bg,
        fg=cyan,
        font=('Arial', 11, 'bold'),
        wraplength=490,
        justify='left'
    )
    title.pack(anchor='w', padx=15, pady=(12, 6))

    tk.Label(
        root,
        text='Choose download source mode for this launch:',
        bg=bg,
        fg=txt_color,
        font=('Arial', 10)
    ).pack(anchor='w', padx=15, pady=(0, 8))

    options_frame = tk.Frame(root, bg=bg)
    options_frame.pack(fill='x', padx=15)
    for mode_key, label in SOURCE_MODE_LABELS.items():
        rb = tk.Radiobutton(
            options_frame,
            text=label,
            variable=mode_var,
            value=mode_key,
            bg=bg,
            fg=txt_color,
            activebackground=bg,
            activeforeground=txt_color,
            selectcolor='#18181b',
            anchor='w',
            justify='left',
            font=('Arial', 10)
        )
        rb.pack(fill='x', pady=2)

    tk.Label(
        root,
        text='Tip: Disable this prompt in MyriFetch Settings if you want silent launches.',
        bg=bg,
        fg=dim_color,
        font=('Arial', 9)
    ).pack(anchor='w', padx=15, pady=(10, 0))

    btn_row = tk.Frame(root, bg=bg)
    btn_row.pack(side='bottom', fill='x', pady=14)

    def _start():
        result['mode'] = mode_var.get().strip()
        root.destroy()

    def _cancel():
        result['cancelled'] = True
        root.destroy()

    tk.Button(
        btn_row, text='Cancel Launch', command=_cancel,
        bg='#2a2a2e', fg=txt_color, relief='flat', padx=12
    ).pack(side='right', padx=(0, 15))
    tk.Button(
        btn_row, text='Download + Launch', command=_start,
        bg=cyan, fg='black', relief='flat', padx=12
    ).pack(side='right', padx=8)

    root.protocol("WM_DELETE_WINDOW", _cancel)
    root.mainloop()

    if result['cancelled']:
        return None
    chosen = result['mode'] or default_mode
    if chosen not in SOURCE_MODE_LABELS:
        chosen = default_mode
    return chosen


def find_myrifetch():
    """Locate MyriFetch.py relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, 'MyriFetch.py')
    if os.path.exists(candidate):
        return candidate
    return None


def find_emulator_launcher(retrobat_path=None, config=None):
    """Locate emulatorLauncher.exe inside RetroBat."""
    if not retrobat_path:
        # Try to read from MyriFetch config
        try:
            cfg = config if isinstance(config, dict) else load_launcher_config()
            retrobat_path = cfg.get('retrobat_path', r'C:\retrobat')
        except Exception:
            retrobat_path = r'C:\retrobat'

    launcher = os.path.join(retrobat_path, 'emulationstation', 'emulatorLauncher.exe')
    if os.path.exists(launcher):
        return launcher
    return None


def parse_es_args(argv):
    """
    Parse EmulationStation-style arguments.
    ES uses single-dash args: -system psx -rom "path" -emulator libretro -core mednafen
    Returns a dict of known args.
    """
    known_keys = {'-system', '-rom', '-emulator', '-core', '-gameinfo'}
    parsed = {}
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in known_keys:
            key = arg.lstrip('-')
            next_token = argv[i + 1] if (i + 1) < len(argv) else None
            # Some emulator entries pass valueless switches (e.g. "-core" then "-rom").
            # Treat those as empty and keep scanning so "-rom" is still parsed correctly.
            if next_token is not None and not str(next_token).startswith('-'):
                parsed[key] = next_token
                i += 2
            else:
                parsed[key] = ''
                i += 1
            continue
        i += 1
    return parsed


def build_launcher_cmd(launcher_exe, raw_args, rom_override=None):
    """
    Reconstruct emulatorLauncher.exe command while preserving original arg order.
    Optional rom_override replaces the value immediately after -rom.
    """
    args = list(raw_args)
    if rom_override is not None:
        for i in range(len(args) - 1):
            if args[i] == '-rom':
                args[i + 1] = rom_override
                break
    cmd = [launcher_exe] + args
    return cmd


def is_stub_rom(path):
    """Return True if path is a MyriFetch placeholder ROM stub."""
    try:
        with open(path, 'rb') as f:
            return f.read(len(MYRIFETCH_STUB_MAGIC)) == MYRIFETCH_STUB_MAGIC
    except OSError:
        return False


def main():
    raw_args = sys.argv[1:]
    parsed = parse_es_args(raw_args)
    _log(f'Invocation args: {raw_args!r}')
    _log(f'Log file: {LAUNCHER_LOG_FILE}')
    config = load_launcher_config()

    rom_path = parsed.get('rom', '')
    system = parsed.get('system', '')
    _log(f'Parsed system={system!r}, rom={rom_path!r}')

    if not rom_path:
        _log('ERROR: No -rom argument provided')
        print("[MyriFetch Launcher] No -rom argument provided", file=sys.stderr)
        return 1

    # --- Fast path: ROM exists and is real → pass through to emulatorLauncher.exe ---
    if os.path.isfile(rom_path) and not is_stub_rom(rom_path):
        _log('Fast path: real ROM exists, launching emulator directly')
        launcher = find_emulator_launcher(config=config)
        if not launcher:
            _log('ERROR: emulatorLauncher.exe not found for fast path')
            print("[MyriFetch Launcher] emulatorLauncher.exe not found", file=sys.stderr)
            return 1
        cmd = build_launcher_cmd(launcher, raw_args)
        _log(f'Running: {_format_cmd(cmd)}')
        result = subprocess.run(cmd)
        _log(f'emulatorLauncher exit code: {result.returncode}')
        return result.returncode

    # --- Slow path: ROM missing → download via MyriFetch ---
    if os.path.isfile(rom_path) and is_stub_rom(rom_path):
        _log('Slow path: detected MyriFetch stub file, download required')
    else:
        _log('Slow path: ROM missing on disk, download required')

    myrient_path = SYSTEM_TO_MYRIENT.get(system)
    if not myrient_path:
        _log(f"ERROR: System '{system}' not supported for on-demand download")
        print(f"[MyriFetch Launcher] System '{system}' not supported for on-demand download",
              file=sys.stderr)
        return 1

    myrifetch = find_myrifetch()
    if not myrifetch:
        _log('ERROR: MyriFetch.py not found')
        print("[MyriFetch Launcher] MyriFetch.py not found", file=sys.stderr)
        return 1

    rom_name = os.path.basename(rom_path)
    dest_dir = os.path.dirname(rom_path)
    _log(f'Resolved myrient_path={myrient_path!r}, rom_name={rom_name!r}, dest={dest_dir!r}')

    # Determine Python executable — prefer pythonw to avoid console flash
    python_exe = sys.executable
    if os.name == 'nt':
        pythonw = python_exe.replace('python.exe', 'pythonw.exe')
        if os.path.exists(pythonw):
            python_exe = pythonw
    _log(f'Using python executable: {python_exe}')

    # Launch MyriFetch in headless download mode
    dl_cmd = [
        python_exe, myrifetch,
        '--download', rom_name,
        '--system', system,
        '--myrient-path', myrient_path,
        '--dest', dest_dir,
    ]

    source_override = None
    prompt_enabled = bool(config.get('launcher_prompt_source_choice', True))
    if prompt_enabled:
        _log('Launcher source chooser enabled; opening source selection dialog')
        source_override = choose_source_mode_dialog(config, system, rom_name)
        if source_override is None:
            _log('Source chooser cancelled by user; returning to EmulationStation')
            return 0
        _log(f'Source override selected: {source_override!r}')
        dl_cmd.extend(['--source-mode', source_override])
    else:
        _log('Launcher source chooser disabled by config; using default source mode')

    si = None
    if os.name == 'nt':
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    _log(f'Running downloader: {_format_cmd(dl_cmd)}')
    result = subprocess.run(dl_cmd, startupinfo=si)
    _log(f'Downloader exit code: {result.returncode}')

    if result.returncode != 0:
        # Download cancelled or failed — return to ES cleanly
        _log('Downloader reported failure/cancel; returning to EmulationStation')
        return 0

    # Download succeeded — now launch the game.
    # MyriFetch.py (run_cli_download) already called gamelist_writeback() to fix
    # the gamelist.xml path, so future launches will always hit the fast path.
    if os.path.isfile(rom_path) and not is_stub_rom(rom_path):
        _log(f'Download succeeded, found ROM at {rom_path!r}')
        launcher = find_emulator_launcher(config=config)
        if launcher:
            cmd = build_launcher_cmd(launcher, raw_args)
            _log(f'Running: {_format_cmd(cmd)}')
            game_result = subprocess.run(cmd)
            _log(f'emulatorLauncher exit code: {game_result.returncode}')
            return game_result.returncode
        _log('ERROR: emulatorLauncher.exe missing after successful download')
    else:
        # Original .zip stub was replaced by a converted file (.chd, .rvz, .iso, etc.)
        # or a .parrot file (TeknoParrot). Check all known alternate extensions in the
        # same priority order used by MyriFetch._write_gamelist_xml.
        _ALT_EXTS = ('.parrot', '.chd', '.rvz', '.iso', '.cso', '.cue', '.bin', '.gdi')
        rom_base = os.path.splitext(rom_path)[0]
        converted_path = None
        for ext in _ALT_EXTS:
            candidate = rom_base + ext
            if os.path.isfile(candidate):
                converted_path = candidate
                break

        if converted_path:
            _log(f'ROM converted; launching {converted_path!r}')
            launcher = find_emulator_launcher(config=config)
            if launcher:
                cmd = build_launcher_cmd(launcher, raw_args, rom_override=converted_path)
                _log(f'Running: {_format_cmd(cmd)}')
                game_result = subprocess.run(cmd)
                _log(f'emulatorLauncher exit code: {game_result.returncode}')
                return game_result.returncode
            _log('ERROR: emulatorLauncher.exe missing while launching converted ROM')
        else:
            _log(f'ERROR: Download finished but no usable ROM found at base path {rom_base!r}')

    _log('Returning 0 to EmulationStation (no launch performed)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
