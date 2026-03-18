import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import os
import json
import threading
import time
from urllib.parse import unquote, quote, urlparse, parse_qs, urlencode, urlunparse
from PIL import Image
import urllib3
import shutil
import traceback
import logging
import subprocess
import platform
import sys
import re
import webbrowser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import zipfile
import tempfile
import collections
import argparse
import base64
import xml.etree.ElementTree as ET

try:
    import winsound
except ImportError:
    winsound = None

ctk.set_appearance_mode('Dark')
ctk.set_default_color_theme('dark-blue')
# NOTE: Do NOT call urllib3.disable_warnings globally — removed.

APP_NAME = 'MyriFetch'

if os.name == 'nt':
    APP_DATA = os.path.join(
        os.environ.get('APPDATA', os.path.expanduser('~')), APP_NAME
    )
else:
    APP_DATA = os.path.join(os.path.expanduser('~'), '.config', APP_NAME)

os.makedirs(APP_DATA, exist_ok=True)

LOG_FILE = os.path.join(APP_DATA, 'myrifetch_debug.log')

# ---------------------------------------------------------------------------
# Mappings
# ---------------------------------------------------------------------------

LB_NAMES = {
    # Sony
    'PlayStation 1': 'Sony Playstation',
    'PlayStation 2': 'Sony Playstation 2',
    'PlayStation 3': 'Sony Playstation 3',
    'PSP': 'Sony PSP',
    # Nintendo
    'NES': 'Nintendo Entertainment System',
    'SNES': 'Super Nintendo (SNES)',
    'N64': 'Nintendo 64',
    'N64DD': 'Nintendo 64DD',
    'GameCube': 'Nintendo GameCube',
    'Wii': 'Nintendo Wii',
    'Wii U': 'Nintendo Wii U',
    'GBA': 'Nintendo Game Boy Advance',
    'Game Boy': 'Nintendo Game Boy',
    'Game Boy Color': 'Nintendo Game Boy Color',
    'Nintendo DS': 'Nintendo DS',
    'Nintendo 3DS': 'Nintendo 3DS',
    'New Nintendo 3DS': 'Nintendo New 3DS',
    'Virtual Boy': 'Nintendo Virtual Boy',
    'Famicom Disk System': 'Nintendo Famicom Disk System',
    # Sega
    'Mega Drive': 'Sega Genesis/Mega Drive',
    'Master System': 'Sega Master System',
    'Saturn': 'Sega Saturn',
    'Dreamcast': 'Sega Dreamcast',
    'Mega CD': 'Sega CD',
    'Game Gear': 'Sega Game Gear',
    'Sega 32X': 'Sega 32X',
    'SG-1000': 'Sega SG-1000',
    # Microsoft
    'Xbox': 'Microsoft Xbox',
    'Xbox 360': 'Microsoft Xbox 360',
    # SNK
    'Neo Geo CD': 'SNK Neo Geo CD',
    'Neo Geo Pocket': 'SNK Neo Geo Pocket',
    'Neo Geo Pocket Color': 'SNK Neo Geo Pocket Color',
    # Atari
    'Atari 2600': 'Atari 2600',
    'Atari 5200': 'Atari 5200',
    'Atari 7800': 'Atari 7800',
    'Atari Lynx': 'Atari Lynx',
    'Atari Jaguar': 'Atari Jaguar',
    'Atari Jaguar CD': 'Atari Jaguar',
    # NEC
    'PC Engine': 'NEC TurboGrafx-16',
    'PC Engine SG': 'NEC SuperGrafx',
    'PC Engine CD': 'NEC TurboGrafx-CD',
    'PC-FX': 'NEC PC-FX',
    # Bandai
    'WonderSwan': 'Bandai WonderSwan',
    'WonderSwan Color': 'Bandai WonderSwan Color',
    # Panasonic
    '3DO': 'Panasonic 3DO Interactive Multiplayer',
    # Philips
    'CD-i': 'Philips CD-i',
    # Commodore
    'Amiga CD32': 'Commodore Amiga CD32',
    # Other
    'ColecoVision': 'Coleco ColecoVision',
    'Intellivision': 'Mattel Intellivision',
    'Vectrex': 'GCE Vectrex',
    'MSX': 'Microsoft MSX',
    'MSX2': 'Microsoft MSX2',
    # Arcade
    'TeknoParrot': 'Arcade',
}

CONSOLES = {
    # Sony
    'PlayStation 1': 'Redump/Sony - PlayStation/',
    'PlayStation 2': 'Redump/Sony - PlayStation 2/',
    'PlayStation 3': 'Redump/Sony - PlayStation 3/',
    'PSP':           'Redump/Sony - PlayStation Portable/',
    # Nintendo
    'NES':                  'No-Intro/Nintendo - Nintendo Entertainment System/',
    'SNES':                 'No-Intro/Nintendo - Super Nintendo Entertainment System/',
    'N64':                  'No-Intro/Nintendo - Nintendo 64 (BigEndian)/',          # FIXED: was bare path
    'N64DD':                'No-Intro/Nintendo - Nintendo 64DD/',
    'GameCube':             'Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]/',
    'Wii':                  'Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]/',
    'Wii U':                'Redump/Nintendo - Wii U - WUX/',                         # FIXED: WUX format
    'GBA':                  'No-Intro/Nintendo - Game Boy Advance/',
    'Game Boy':             'No-Intro/Nintendo - Game Boy/',
    'Game Boy Color':       'No-Intro/Nintendo - Game Boy Color/',
    'Nintendo DS':          'No-Intro/Nintendo - Nintendo DS (Decrypted)/',
    'Nintendo 3DS':         'No-Intro/Nintendo - Nintendo 3DS (Decrypted)/',
    'New Nintendo 3DS':     'No-Intro/Nintendo - New Nintendo 3DS (Decrypted)/',
    'Virtual Boy':          'No-Intro/Nintendo - Virtual Boy/',
    'Famicom Disk System':  'No-Intro/Nintendo - Family Computer Disk System (FDS)/', # FIXED: correct folder name
    # Sega
    'Mega Drive':    'No-Intro/Sega - Mega Drive - Genesis/',
    'Master System': 'No-Intro/Sega - Master System - Mark III/',
    'Saturn':        'Redump/Sega - Saturn/',
    'Dreamcast':     'Redump/Sega - Dreamcast/',
    'Mega CD':       'Redump/Sega - Mega CD & Sega CD/',                              # FIXED: correct folder name
    'Game Gear':     'No-Intro/Sega - Game Gear/',
    'Sega 32X':      'No-Intro/Sega - 32X/',
    'SG-1000':       'No-Intro/Sega - SG-1000/',
    # Microsoft
    'Xbox':     'Redump/Microsoft - Xbox/',
    'Xbox 360': 'Redump/Microsoft - Xbox 360/',
    # SNK
    'Neo Geo CD':           'Redump/SNK - Neo Geo CD/',
    'Neo Geo Pocket':       'No-Intro/SNK - Neo Geo Pocket/',
    'Neo Geo Pocket Color': 'No-Intro/SNK - Neo Geo Pocket Color/',
    # Atari
    'Atari 2600':    'No-Intro/Atari - Atari 2600/',                      # FIXED
    'Atari 5200':    'No-Intro/Atari - Atari 5200/',
    'Atari 7800':    'No-Intro/Atari - Atari 7800 (BIN)/',                # FIXED: correct format path
    'Atari Lynx':    'No-Intro/Atari - Atari Lynx (LNX)/',                # FIXED: correct format path
    'Atari Jaguar':  'No-Intro/Atari - Atari Jaguar (J64)/',              # FIXED: correct format path
    'Atari Jaguar CD': 'Redump/Atari - Jaguar CD Interactive Multimedia System/',
    # NEC
    'PC Engine':       'No-Intro/NEC - PC Engine - TurboGrafx-16/',
    'PC Engine SG':    'No-Intro/NEC - PC Engine SuperGrafx/',
    'PC Engine CD':    'Redump/NEC - PC Engine CD & TurboGrafx CD/',      # FIXED: correct folder name
    'PC-FX':           'Redump/NEC - PC-FX & PC-FXGA/',
    # Bandai
    'WonderSwan':       'No-Intro/Bandai - WonderSwan/',
    'WonderSwan Color': 'No-Intro/Bandai - WonderSwan Color/',
    # Panasonic
    '3DO': 'Redump/Panasonic - 3DO Interactive Multiplayer/',
    # Philips
    'CD-i': 'Redump/Philips - CD-i/',
    # Commodore
    'Amiga CD32': 'Redump/Commodore - Amiga CD32/',
    # Other home consoles
    'ColecoVision': 'No-Intro/Coleco - ColecoVision/',
    'Intellivision': 'No-Intro/Mattel - Intellivision/',
    'Vectrex':       'No-Intro/GCE - Vectrex/',
    'MSX':           'No-Intro/Microsoft - MSX/',
    'MSX2':          'No-Intro/Microsoft - MSX2/',
    # Arcade
    'TeknoParrot':   'TeknoParrot/',
}

SHORT_NAMES = {
    # Sony
    'PlayStation 1': 'PS1',
    'PlayStation 2': 'PS2',
    'PlayStation 3': 'PS3',
    'PSP': 'PSP',
    # Nintendo
    'NES': 'NES',
    'SNES': 'SNES',
    'N64': 'N64',
    'N64DD': 'N64DD',
    'GameCube': 'GCN',
    'Wii': 'Wii',
    'Wii U': 'WiiU',
    'GBA': 'GBA',
    'Game Boy': 'GB',
    'Game Boy Color': 'GBC',
    'Nintendo DS': 'NDS',
    'Nintendo 3DS': '3DS',
    'New Nintendo 3DS': 'N3DS',
    'Virtual Boy': 'VB',
    'Famicom Disk System': 'FDS',
    # Sega
    'Mega Drive': 'MD',
    'Master System': 'SMS',
    'Saturn': 'Saturn',
    'Dreamcast': 'DC',
    'Mega CD': 'MCD',
    'Game Gear': 'GG',
    'Sega 32X': '32X',
    'SG-1000': 'SG-1000',
    # Microsoft
    'Xbox': 'Xbox',
    'Xbox 360': 'X360',
    # SNK
    'Neo Geo CD': 'NGCD',
    'Neo Geo Pocket': 'NGP',
    'Neo Geo Pocket Color': 'NGPC',
    # Atari
    'Atari 2600': '2600',
    'Atari 5200': '5200',
    'Atari 7800': '7800',
    'Atari Lynx': 'Lynx',
    'Atari Jaguar': 'Jaguar',
    'Atari Jaguar CD': 'JagCD',
    # NEC
    'PC Engine': 'PCE',
    'PC Engine SG': 'PCESG',
    'PC Engine CD': 'PCECD',
    'PC-FX': 'PCFX',
    # Bandai
    'WonderSwan': 'WS',
    'WonderSwan Color': 'WSC',
    # Panasonic
    '3DO': '3DO',
    # Philips
    'CD-i': 'CD-i',
    # Commodore
    'Amiga CD32': 'CD32',
    # Other
    'ColecoVision': 'ColecoVision',
    'Intellivision': 'Intellivision',
    'Vectrex': 'Vectrex',
    'MSX': 'MSX',
    'MSX2': 'MSX2',
    # Arcade
    'TeknoParrot': 'TP',
}

RETROBAT_ROM_FOLDERS = {
    # Sony
    'PlayStation 3': 'ps3',
    'PlayStation 2': 'ps2',
    'PlayStation 1': 'psx',
    'PSP':           'psp',
    # Nintendo
    'NES':                 'nes',
    'SNES':                'snes',
    'N64':                 'n64',
    'N64DD':               'n64dd',
    'GameCube':            'gamecube',
    'Wii':                 'wii',
    'Wii U':               'wiiu',
    'GBA':                 'gba',
    'Game Boy':            'gb',
    'Game Boy Color':      'gbc',
    'Nintendo DS':         'nds',
    'Nintendo 3DS':        '3ds',
    'New Nintendo 3DS':    '3ds',   # shares folder with 3DS in RetroBat
    'Virtual Boy':         'virtualboy',
    'Famicom Disk System': 'fds',
    # Sega
    'Mega Drive':    'megadrive',
    'Master System': 'mastersystem',
    'Saturn':        'saturn',
    'Dreamcast':     'dreamcast',
    'Mega CD':       'megacd',
    'Game Gear':     'gamegear',
    'Sega 32X':      'sega32x',
    'SG-1000':       'sg1000',
    # Microsoft
    'Xbox':     'xbox',
    'Xbox 360': 'xbox360',
    # SNK
    'Neo Geo CD':           'neogeocd',
    'Neo Geo Pocket':       'ngp',
    'Neo Geo Pocket Color': 'ngpc',
    # Atari
    'Atari 2600':    'atari2600',
    'Atari 5200':    'atari5200',
    'Atari 7800':    'atari7800',
    'Atari Lynx':    'lynx',
    'Atari Jaguar':  'jaguar',
    'Atari Jaguar CD': 'jaguarcd',
    # NEC
    'PC Engine':    'pcengine',
    'PC Engine SG': 'supergrafx',
    'PC Engine CD': 'pcenginecd',
    'PC-FX':        'pcfx',
    # Bandai
    'WonderSwan':       'wswan',
    'WonderSwan Color': 'wswanc',
    # Panasonic
    '3DO': '3do',
    # Philips
    'CD-i': 'cdi',
    # Commodore
    'Amiga CD32': 'amigacd32',
    # Other
    'ColecoVision': 'colecovision',
    'Intellivision': 'intellivision',
    'Vectrex':       'vectrex',
    'MSX':           'msx1',
    'MSX2':          'msx2',
    # Arcade
    'TeknoParrot':   'teknoparrot',
}

# Reverse lookup: RetroBat system name → Myrient catalog path
SYSTEM_TO_MYRIENT = {v: CONSOLES[k] for k, v in RETROBAT_ROM_FOLDERS.items()}

# Reverse lookup: RetroBat system name → MyriFetch console name
SYSTEM_TO_CONSOLE = {v: k for k, v in RETROBAT_ROM_FOLDERS.items()}

CONFIG_FILE = os.path.join(APP_DATA, 'myrient_ultimate.json')
ICON_DIR = os.path.join(APP_DATA, 'icons')
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_URL = 'https://myrient.erista.me/files/'
NUM_THREADS = 4
CHUNK_SIZE = 256 * 1024
MIN_VALID_BYTES = 4096
MYRIFETCH_STUB_MAGIC = b'MYRIFETCH_STUB\n'
MYRIFETCH_STUB_CONTENT = MYRIFETCH_STUB_MAGIC + b'v1\n'
ON_DEMAND_LOG_FILE = os.path.join(PROJECT_ROOT, 'on_demand_launcher.log')
_ON_DEMAND_LOG_LOCK = threading.Lock()
RATE_LIMIT_DEFAULT_BACKOFF = 20
RATE_LIMIT_MIN_BACKOFF = 3
RATE_LIMIT_MAX_BACKOFF = 120
SINGLE_STREAM_THRESHOLD_BYTES = 768 * 1024 * 1024
_HOST_DOWNLOAD_POLICY = {}
_HOST_DOWNLOAD_POLICY_LOCK = threading.Lock()
HOST_RANGE_THREAD_CAPS = {
    'f5.erista.me': 2,
}
HOST_RANGE_MIN_MULTI_BYTES = {
    # Keep small/medium files single-stream; allow limited parallelism on large files.
    'f5.erista.me': 1024 * 1024 * 1024,  # 1 GiB
}
HOST_RANGE_THREAD_STAGGER_SEC = {
    # Stagger starting ranged requests to reduce burst-triggered 429 responses.
    'f5.erista.me': 0.75,
}

SOURCE_MODE_MYRIENT_ONLY = 'myrient_only'
SOURCE_MODE_MYRIENT_ARCHIVE = 'myrient_archive'
SOURCE_MODE_ARCHIVE_ONLY = 'archive_only'
SOURCE_MODE_MYRIENT_ARCHIVE_QBIT = 'myrient_archive_qbit'
DEFAULT_DOWNLOAD_SOURCE_MODE = SOURCE_MODE_MYRIENT_ARCHIVE
DOWNLOAD_SOURCE_MODE_LABELS = {
    SOURCE_MODE_MYRIENT_ONLY: 'Myrient only',
    SOURCE_MODE_MYRIENT_ARCHIVE: 'Myrient -> Archive.org',
    SOURCE_MODE_ARCHIVE_ONLY: 'Archive.org only',
    SOURCE_MODE_MYRIENT_ARCHIVE_QBIT: 'Myrient -> Archive.org -> qBittorrent',
}
DOWNLOAD_SOURCE_LABEL_TO_MODE = {
    v: k for k, v in DOWNLOAD_SOURCE_MODE_LABELS.items()
}
CHDMAN_CONSOLE_KEY_ALIASES = {
    # PlayStation 1
    'playstation1': 'ps1', 'ps1': 'ps1', 'psx': 'ps1',
    # PlayStation 2
    'playstation2': 'ps2', 'ps2': 'ps2',
    # PSP
    'psp': 'psp', 'playstationportable': 'psp',
    # Dreamcast
    'dreamcast': 'dreamcast',
    # Saturn
    'saturn': 'saturn', 'segasaturn': 'saturn',
    # Mega CD / Sega CD
    'megacd': 'megacd', 'segacd': 'megacd',
    'mega cd': 'megacd', 'sega cd': 'megacd',
    'mega cd  sega cd': 'megacd',
    # Neo Geo CD
    'neogeocd': 'neogeocd', 'neo geo cd': 'neogeocd',
    # PC Engine CD
    'pcenginecd': 'pcenginecd', 'turbografxcd': 'pcenginecd',
    'pc engine cd': 'pcenginecd',
    'pc engine cd  turbografx cd': 'pcenginecd',
    # PC-FX
    'pcfx': 'pcfx', 'pc-fx': 'pcfx',
    # 3DO
    '3do': '3do', 'panasonic3do': '3do',
    # Atari Jaguar CD
    'jaguarcd': 'jaguarcd', 'atari jaguar cd': 'jaguarcd',
    # Amiga CD32
    'amigacd32': 'amigacd32', 'commodore amiga cd32': 'amigacd32',
    # CD-i
    'cdi': 'cdi', 'philips cd-i': 'cdi', 'cd-i': 'cdi',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Referer': 'https://myrient.erista.me/',
    'Origin': 'https://myrient.erista.me',
    'Connection': 'keep-alive'
}

THEMES = {
    'Cyber Dark': {
        'bg': '#09090b', 'card': '#18181b', 'cyan': '#00f2ff',
        'pink': '#ff0055', 'text': '#ffffff', 'dim': '#71717a', 'success': '#00e676'
    },
    'Gruvbox': {
        'bg': '#282828', 'card': '#3c3836', 'cyan': '#d79921',
        'pink': '#cc241d', 'text': '#ebdbb2', 'dim': '#a89984', 'success': '#98971a'
    },
    'Matrix': {
        'bg': '#000000', 'card': '#111111', 'cyan': '#00ff41',
        'pink': '#008f11', 'text': '#e0e0e0', 'dim': '#333333', 'success': '#003b00'
    },
    'Nord': {
        'bg': '#2e3440', 'card': '#3b4252', 'cyan': '#88c0d0',
        'pink': '#bf616a', 'text': '#eceff4', 'dim': '#4c566a', 'success': '#a3be8c'
    }
}

C = THEMES['Cyber Dark'].copy()


def _is_myrifetch_stub(path: str) -> bool:
    """Return True if file starts with the MyriFetch stub marker.
    Fast-path: files larger than the stub content are never stubs,
    so we skip the open() entirely — this is critical for large ROM folders.
    """
    try:
        if os.path.getsize(path) > len(MYRIFETCH_STUB_CONTENT) + 4:
            return False
        with open(path, 'rb') as f:
            return f.read(len(MYRIFETCH_STUB_MAGIC)) == MYRIFETCH_STUB_MAGIC
    except OSError:
        return False



# ---------------------------------------------------------------------------
# Region filtering for gamelist sync
# ---------------------------------------------------------------------------

# Region tags that appear in Myrient/Redump/No-Intro filenames (parenthesised).
# Order here defines priority when SYNC_REGION_PREFERENCE is 'Best'.
_REGION_PRIORITY = ['USA', 'World', 'En', 'Europe', 'Australia', 'Japan']

# All tags we recognise as region indicators
_REGION_TAGS = {
    'usa', 'world', 'europe', 'japan', 'australia', 'en',
    'uk', 'france', 'germany', 'spain', 'italy', 'korea',
    'brazil', 'netherlands', 'sweden', 'norway', 'denmark',
    'canada', 'china', 'taiwan', 'hong kong',
}

_PAREN_TAG_RE = re.compile(r'\(([^)]+)\)')


def _extract_region_tags(filename):
    """Return a set of lower-cased region tags found inside parentheses."""
    found = set()
    for m in _PAREN_TAG_RE.finditer(filename):
        tag = m.group(1).strip().lower()
        if tag in _REGION_TAGS:
            found.add(tag)
    return found


def _strip_tags(filename):
    """Return base title: strip parenthesised tags and extension."""
    base = os.path.splitext(filename)[0]
    base = _PAREN_TAG_RE.sub('', base)
    return base.strip()


def _apply_region_filter(file_list, preference):
    """
    Filter a Myrient catalog file list down to one entry per game title
    according to `preference`:

      'All'    — return the full list unchanged (default, current behaviour)
      'Best'   — one entry per title; USA > World > En > Europe > Australia > Japan
                 > first available.  Revisions/betas kept alongside the winner.
      'USA'    — keep only titles that contain (USA) or (World) or have no region tag
      'Europe' — keep only titles that contain (Europe) or (World)
      'Japan'  — keep only titles that contain (Japan)

    For 'Best' mode: when a preferred region is found the other region variants
    of the same base title are dropped, but revision/alternate entries of the
    winning region are kept.  This cuts stub counts dramatically on large
    catalogs (PS2 goes from ~4 k → ~2 k entries) while keeping full coverage.
    """
    if preference == 'All':
        return file_list

    # --- Simple inclusion filter for single-region modes ---
    if preference in ('USA', 'Europe', 'Japan'):
        pref_lower = preference.lower()
        result = []
        for fname in file_list:
            tags = _extract_region_tags(fname)
            if not tags:
                result.append(fname)       # no region tag → keep (homebrew, etc.)
                continue
            if pref_lower in tags or 'world' in tags:
                result.append(fname)
        return result

    # --- 'Best' mode: smart deduplication ----------------------------------------
    # Group files by stripped base title.
    groups = collections.defaultdict(list)
    for fname in file_list:
        key = _strip_tags(fname).lower()
        groups[key].append(fname)

    result = []
    for _base, entries in groups.items():
        if len(entries) == 1:
            result.extend(entries)
            continue

        # Score each entry by region priority.
        def _score(fname):
            tags = _extract_region_tags(fname)
            for i, region in enumerate(_REGION_PRIORITY):
                if region.lower() in tags:
                    return i
            if not tags:
                return len(_REGION_PRIORITY)     # no region tag — neutral
            return len(_REGION_PRIORITY) + 1     # other region

        best_score = min(_score(f) for f in entries)
        # Keep all entries that match the best score (handles Rev 1/Rev 2 etc.)
        result.extend(f for f in entries if _score(f) == best_score)

    # Preserve original catalog order.
    order = {fname: i for i, fname in enumerate(file_list)}
    result.sort(key=lambda f: order.get(f, 0))
    return result


# ---------------------------------------------------------------------------
# Stub thumbnail generation
# ---------------------------------------------------------------------------

_STUB_THUMB_FILENAME = 'myrifetch_stub_thumb.png'
_stub_thumb_path_cache = None


def _ensure_stub_thumbnail() -> str | None:
    """
    Return the absolute path to the shared stub thumbnail PNG, generating it
    on first call.  Returns None if PIL is unavailable or generation fails.

    The thumbnail is a 200×200 dark card with a cyan download arrow and
    "AVAILABLE" label — visually distinctive in any ES grid/wall theme.
    Stored once in APP_DATA; all gamelist entries for stubs point here.
    """
    global _stub_thumb_path_cache
    if _stub_thumb_path_cache and os.path.isfile(_stub_thumb_path_cache):
        return _stub_thumb_path_cache

    out_path = os.path.join(APP_DATA, _STUB_THUMB_FILENAME)

    try:
        from PIL import Image, ImageDraw, ImageFont
        SIZE = 200
        img = Image.new('RGB', (SIZE, SIZE), color='#18181b')
        draw = ImageDraw.Draw(img)

        # Outer rounded-rect border in cyan
        border = 6
        draw.rounded_rectangle(
            [border, border, SIZE - border, SIZE - border],
            radius=14, outline='#00f2ff', width=2
        )

        # Download arrow: shaft + head
        cx = SIZE // 2
        shaft_top = 54
        shaft_bot = 108
        arrow_w = 28
        head_h = 22
        draw.rectangle([cx - 5, shaft_top, cx + 5, shaft_bot], fill='#00f2ff')
        draw.polygon([
            (cx - arrow_w // 2, shaft_bot),
            (cx + arrow_w // 2, shaft_bot),
            (cx, shaft_bot + head_h)
        ], fill='#00f2ff')

        # Horizontal line under arrow
        draw.rectangle([cx - 22, shaft_bot + head_h + 6,
                         cx + 22, shaft_bot + head_h + 9], fill='#00f2ff')

        # "AVAILABLE" label
        try:
            font = ImageFont.truetype('arial.ttf', 16)
        except Exception:
            font = ImageFont.load_default()
        label = 'AVAILABLE'
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((SIZE - tw) // 2, 148), label, fill='#00f2ff', font=font)

        # Smaller "TO DOWNLOAD" sub-label
        sub = 'TO DOWNLOAD'
        try:
            small_font = ImageFont.truetype('arial.ttf', 11)
        except Exception:
            small_font = font
        sub_bbox = draw.textbbox((0, 0), sub, small_font)
        sw = sub_bbox[2] - sub_bbox[0]
        draw.text(((SIZE - sw) // 2, 169), sub, fill='#71717a', font=small_font)

        img.save(out_path, 'PNG')
        _stub_thumb_path_cache = out_path
        return out_path

    except Exception:
        return None


def gamelist_writeback(rom_dir: str, stub_filename: str, real_path: str) -> bool:
    """
    Update a gamelist.xml entry after a successful on-demand download.

    Finds the <game> entry whose <path> matched the stub filename, then:
      - Updates <path> to point at the real downloaded file.
      - Removes <hidden>true</hidden> so the game becomes visible in ES.
      - Removes the stub genre tag ("Available to Download") if present.
      - Updates <n> to a clean base name (no prefix artefacts).

    This permanently fixes CHD drift: the next ES launch will always hit the
    fast path in myrient_launcher.py because the XML now points at the real file.

    Returns True on success, False if the gamelist was not found or not updated.
    """
    gamelist_path = os.path.join(rom_dir, 'gamelist.xml')
    if not os.path.isfile(gamelist_path):
        return False

    try:
        tree = ET.parse(gamelist_path)
        root = tree.getroot()
    except Exception:
        return False

    stub_base = os.path.splitext(os.path.basename(stub_filename))[0].lower()
    real_filename = os.path.basename(real_path)
    real_base = os.path.splitext(real_filename)[0]

    updated = False
    for game in root.findall('game'):
        path_el = game.find('path')
        if path_el is None:
            continue
        # Match on basename without extension to handle zip→chd drift.
        entry_base = os.path.splitext(
            os.path.basename((path_el.text or '').lstrip('./\\'))
        )[0].lower()
        if entry_base != stub_base:
            continue

        # Update path to real file.
        path_el.text = f'./{real_filename}'

        # Clean display name.
        name_el = game.find('n')
        if name_el is not None:
            name_el.text = real_base

        # Remove hidden tag.
        hidden_el = game.find('hidden')
        if hidden_el is not None:
            game.remove(hidden_el)

        # Remove stub genre tag.
        for genre_el in game.findall('genre'):
            if (genre_el.text or '').strip().lower() == 'available to download':
                game.remove(genre_el)
                break

        updated = True
        break

    if not updated:
        return False

    tmp_path = gamelist_path + '.tmp'
    try:
        tree.write(tmp_path, encoding='utf-8', xml_declaration=True)
        os.replace(tmp_path, gamelist_path)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return False
    return True


def _append_on_demand_log(source: str, message: str) -> None:
    """Append a timestamped on-demand launcher log entry."""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] [{source}] {message}'
    try:
        with _ON_DEMAND_LOG_LOCK:
            with open(ON_DEMAND_LOG_FILE, 'a', encoding='utf-8', errors='replace') as f:
                f.write(line + '\n')
    except OSError:
        pass


def _parse_retry_after_seconds(value):
    """Parse HTTP Retry-After header into seconds, or return None if unavailable."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if raw.isdigit():
        return max(0, int(raw))
    try:
        dt = parsedate_to_datetime(raw)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, int((dt - datetime.now(timezone.utc)).total_seconds()))
    except Exception:
        return None


def _remaining_host_cooldown(host):
    if not host:
        return 0
    with _HOST_DOWNLOAD_POLICY_LOCK:
        state = _HOST_DOWNLOAD_POLICY.get(host)
        if not state:
            return 0
        return max(0, int(state.get('cooldown_until', 0) - time.time()))


def _choose_headless_threads(host, total_length):
    """Choose ranged thread count using file size and per-host rate-limit policy."""
    reasons = []
    threads = NUM_THREADS
    host_min_multi = HOST_RANGE_MIN_MULTI_BYTES.get(host, 0)
    if 0 < total_length <= SINGLE_STREAM_THRESHOLD_BYTES:
        threads = 1
        reasons.append(
            f'file <= {SINGLE_STREAM_THRESHOLD_BYTES // (1024 * 1024)} MB threshold'
        )
    elif host_min_multi and 0 < total_length < host_min_multi:
        threads = 1
        reasons.append(
            f'file below host multi-thread threshold '
            f'({host_min_multi // (1024 * 1024)} MB)'
        )
    host_cap = HOST_RANGE_THREAD_CAPS.get(host)
    if host_cap is not None and host_cap < threads:
        threads = max(1, int(host_cap))
        reasons.append(f'host default cap={threads}')
    with _HOST_DOWNLOAD_POLICY_LOCK:
        state = _HOST_DOWNLOAD_POLICY.get(host) if host else None
        if state:
            host_cap = max(1, int(state.get('max_threads', NUM_THREADS)))
            if host_cap < threads:
                threads = host_cap
                reasons.append(f'host cap={host_cap}')
    cooldown_left = _remaining_host_cooldown(host)
    if cooldown_left > 0:
        threads = 1
        reasons.append(f'cooldown active ({cooldown_left}s remaining)')
    return max(1, threads), reasons, cooldown_left


def _mark_host_rate_limited(host, retry_after_seconds=None):
    """Record host-side 429 and return (cooldown_seconds, host_429_count)."""
    if not host:
        return RATE_LIMIT_DEFAULT_BACKOFF, 0
    if retry_after_seconds is None:
        cooldown = RATE_LIMIT_DEFAULT_BACKOFF
    else:
        cooldown = max(
            RATE_LIMIT_MIN_BACKOFF,
            min(RATE_LIMIT_MAX_BACKOFF, int(retry_after_seconds))
        )
    now = time.time()
    with _HOST_DOWNLOAD_POLICY_LOCK:
        state = _HOST_DOWNLOAD_POLICY.setdefault(
            host, {'max_threads': NUM_THREADS, 'cooldown_until': 0, '429_count': 0}
        )
        state['max_threads'] = 1
        state['429_count'] = int(state.get('429_count', 0)) + 1
        state['cooldown_until'] = max(float(state.get('cooldown_until', 0)), now + cooldown)
        return cooldown, state['429_count']


def _get_download_source_mode(config):
    mode = str((config or {}).get(
        'download_source_mode', DEFAULT_DOWNLOAD_SOURCE_MODE
    )).strip()
    if mode not in DOWNLOAD_SOURCE_MODE_LABELS:
        mode = DEFAULT_DOWNLOAD_SOURCE_MODE
    return mode


def _source_mode_order(mode):
    order_map = {
        SOURCE_MODE_MYRIENT_ONLY: ['myrient'],
        SOURCE_MODE_MYRIENT_ARCHIVE: ['myrient', 'archive'],
        SOURCE_MODE_ARCHIVE_ONLY: ['archive'],
        SOURCE_MODE_MYRIENT_ARCHIVE_QBIT: ['myrient', 'archive', 'qbittorrent'],
    }
    return order_map.get(mode, ['myrient', 'archive'])


def _resolve_chd_console_key(console_type):
    """Normalize console name/suffix to the CHD setting key suffix."""
    if console_type is None:
        return None
    normalized = re.sub(r'[^a-z0-9]+', '', str(console_type).lower())
    if not normalized:
        return None
    return CHDMAN_CONSOLE_KEY_ALIASES.get(normalized)


def _use_chdman_for_console(config, console_type):
    """Return (enabled, setting_key) for a console CHD setting."""
    key_suffix = _resolve_chd_console_key(console_type)
    if not key_suffix:
        return False, None
    setting_key = f'use_chdman_{key_suffix}'
    return bool((config or {}).get(setting_key, False)), setting_key


def _headers_for_url(url):
    headers = HEADERS.copy()
    host = (urlparse(url).hostname or '').lower()
    if host not in ('myrient.erista.me', 'f5.erista.me'):
        headers.pop('Referer', None)
        headers.pop('Origin', None)
    return headers


def _archive_find_direct_url(session, rom_name, log_cb=None, max_items=20):
    """
    Find an Archive.org direct download URL for an exact ROM filename match.
    Returns URL string or None.
    """
    def log(msg):
        if log_cb:
            try:
                log_cb(msg)
            except Exception:
                pass

    rom_lower = rom_name.lower()
    base_name = os.path.splitext(rom_name)[0]
    queries = [
        f'"{rom_name}"',
        f'title:"{base_name}"',
    ]

    for query in queries:
        try:
            params = [
                ('q', query),
                ('fl[]', 'identifier'),
                ('rows', str(max_items)),
                ('page', '1'),
                ('output', 'json'),
            ]
            r = session.get(
                'https://archive.org/advancedsearch.php',
                params=params,
                timeout=20
            )
            r.raise_for_status()
            docs = (r.json().get('response') or {}).get('docs', []) or []
        except Exception as e:
            log(f'Archive search failed for query={query!r} ({type(e).__name__}: {e})')
            continue

        log(f'Archive search query={query!r} returned {len(docs)} candidate item(s)')
        for doc in docs:
            identifier = (doc or {}).get('identifier')
            if not identifier:
                continue
            try:
                meta = session.get(
                    f'https://archive.org/metadata/{quote(identifier)}',
                    timeout=20
                )
                meta.raise_for_status()
                files = meta.json().get('files', []) or []
            except Exception:
                continue

            for file_item in files:
                name = str((file_item or {}).get('name') or '')
                if not name:
                    continue
                candidate = os.path.basename(name).lower()
                if candidate == rom_lower:
                    url = (
                        f'https://archive.org/download/'
                        f'{quote(identifier)}/{quote(name, safe="/")}'
                    )
                    log(f'Archive exact match found in item={identifier!r}: {name!r}')
                    return url
    log(f'Archive search found no exact filename match for {rom_name!r}')
    return None


def _parse_btih_from_magnet(magnet_url):
    m = re.search(r'xt=urn:btih:([A-Za-z0-9]+)', magnet_url or '')
    if not m:
        return None
    btih = m.group(1).strip()
    if len(btih) == 40 and re.fullmatch(r'[A-Fa-f0-9]{40}', btih):
        return btih.lower()
    if len(btih) == 32:
        try:
            raw = base64.b32decode(btih.upper())
            return raw.hex().lower()
        except Exception:
            return None
    return None


def _torznab_search_candidates(session, rom_name, config, log_cb=None):
    def log(msg):
        if log_cb:
            try:
                log_cb(msg)
            except Exception:
                pass

    torznab_url = str((config or {}).get('torznab_url', '')).strip()
    torznab_api_key = str((config or {}).get('torznab_api_key', '')).strip()
    torznab_cat = str((config or {}).get('torznab_category', '')).strip()
    if not torznab_url or not torznab_api_key:
        log('Torznab not configured (need torznab_url + torznab_api_key)')
        return []

    params = {
        't': 'search',
        'q': rom_name,
        'apikey': torznab_api_key,
        'limit': '20',
    }
    if torznab_cat:
        params['cat'] = torznab_cat

    try:
        r = session.get(torznab_url, params=params, timeout=25)
        r.raise_for_status()
    except Exception as e:
        log(f'Torznab query failed ({type(e).__name__}: {e})')
        return []

    try:
        root = ET.fromstring(r.text)
    except Exception as e:
        log(f'Torznab response XML parse failed ({type(e).__name__}: {e})')
        return []

    candidates = []
    base_name = os.path.splitext(rom_name)[0].lower()
    for item in root.findall('.//item'):
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        enclosure = item.find('enclosure')
        enclosure_url = ''
        if enclosure is not None:
            enclosure_url = (enclosure.attrib.get('url') or '').strip()
        torrent_url = enclosure_url or link
        if not torrent_url:
            continue
        if not (
            torrent_url.startswith('magnet:') or
            torrent_url.startswith('http://') or
            torrent_url.startswith('https://')
        ):
            continue

        seeders = 0
        for node in item.iter():
            tag = str(node.tag).lower()
            if not tag.endswith('attr'):
                continue
            attr_name = str(node.attrib.get('name', '')).lower()
            if attr_name in ('seeders', 'seed', 'peers'):
                try:
                    seeders = max(seeders, int(float(node.attrib.get('value', '0'))))
                except ValueError:
                    pass

        score = seeders
        title_l = title.lower()
        if base_name and base_name in title_l:
            score += 10000
        if rom_name.lower() == title_l:
            score += 20000
        candidates.append({
            'title': title or torrent_url,
            'url': torrent_url,
            'seeders': seeders,
            'score': score,
        })

    candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
    log(f'Torznab returned {len(candidates)} candidate(s)')
    return candidates


def _best_downloaded_file(content_path, expected_name):
    """Pick best payload file from a torrent content path."""
    if not content_path:
        return None
    expected_name_l = expected_name.lower()
    expected_ext = os.path.splitext(expected_name_l)[1]

    if os.path.isfile(content_path):
        return content_path
    if not os.path.isdir(content_path):
        return None

    exact_match = None
    ext_match = None
    largest = None
    largest_size = -1
    for root, _dirs, files in os.walk(content_path):
        for fn in files:
            fp = os.path.join(root, fn)
            fn_l = fn.lower()
            if fn_l == expected_name_l:
                exact_match = fp
                break
            if expected_ext and fn_l.endswith(expected_ext) and ext_match is None:
                ext_match = fp
            try:
                sz = os.path.getsize(fp)
            except OSError:
                sz = -1
            if sz > largest_size:
                largest_size = sz
                largest = fp
        if exact_match:
            break

    return exact_match or ext_match or largest


def _download_via_qbittorrent(
    rom_name, dest_dir, final_path, cancel_event, progress_cb=None, log_cb=None, config=None
):
    """
    Use Torznab search + qBittorrent WebUI to fetch a ROM.
    Returns (success, local_path).
    """
    def log(msg):
        if log_cb:
            try:
                log_cb(msg)
            except Exception:
                pass

    config = config or {}
    qb_url = str(config.get('qbittorrent_url', '')).strip()
    qb_user = str(config.get('qbittorrent_user', '')).strip()
    qb_pass = str(config.get('qbittorrent_pass', '')).strip()
    remove_on_complete = bool(config.get('qbittorrent_remove_on_complete', True))
    if not qb_url or not qb_user or not qb_pass:
        log('qBittorrent fallback skipped: qbittorrent_url/user/pass not fully configured')
        return False, final_path

    if not qb_url.startswith(('http://', 'https://')):
        qb_url = 'http://' + qb_url
    qb_url = qb_url.rstrip('/')
    if qb_url.endswith('/api/v2'):
        qb_url = qb_url[:-7]

    search_session = requests.Session()
    candidates = _torznab_search_candidates(
        search_session, rom_name, config, log_cb=log
    )
    if not candidates:
        log('qBittorrent fallback skipped: Torznab yielded no candidates')
        return False, final_path

    qb = requests.Session()
    try:
        login = qb.post(
            f'{qb_url}/api/v2/auth/login',
            data={'username': qb_user, 'password': qb_pass},
            timeout=15
        )
        if login.status_code != 200 or 'ok' not in login.text.lower():
            log(f'qBittorrent login failed (status={login.status_code})')
            return False, final_path
    except Exception as e:
        log(f'qBittorrent login failed ({type(e).__name__}: {e})')
        return False, final_path

    def torrents_info(hash_filter=None):
        params = {}
        if hash_filter:
            params['hashes'] = hash_filter
        r = qb.get(f'{qb_url}/api/v2/torrents/info', params=params, timeout=15)
        r.raise_for_status()
        return r.json()

    def delete_torrent(hash_value):
        try:
            qb.post(
                f'{qb_url}/api/v2/torrents/delete',
                data={'hashes': hash_value, 'deleteFiles': 'false'},
                timeout=10
            )
        except Exception:
            pass

    os.makedirs(dest_dir, exist_ok=True)
    before_hashes = set()
    try:
        before_hashes = {
            str(t.get('hash', '')).lower()
            for t in torrents_info()
            if t.get('hash')
        }
    except Exception:
        pass

    for idx, cand in enumerate(candidates[:5], 1):
        if cancel_event.is_set():
            return False, final_path
        cand_title = cand.get('title', '(untitled)')
        cand_url = cand.get('url', '')
        log(f'qBittorrent candidate {idx}/{min(5, len(candidates))}: {cand_title}')
        if not cand_url:
            continue

        known_hash = _parse_btih_from_magnet(cand_url) if cand_url.startswith('magnet:') else None
        try:
            add_resp = qb.post(
                f'{qb_url}/api/v2/torrents/add',
                data={
                    'urls': cand_url,
                    'savepath': dest_dir,
                    'paused': 'false',
                    'autoTMM': 'false',
                },
                timeout=20
            )
            if add_resp.status_code != 200:
                log(f'Add torrent failed (status={add_resp.status_code})')
                continue
        except Exception as e:
            log(f'Add torrent failed ({type(e).__name__}: {e})')
            continue

        target_hash = (known_hash or '').lower()
        deadline = time.time() + 90
        while time.time() < deadline and not target_hash and not cancel_event.is_set():
            try:
                current = torrents_info()
            except Exception:
                time.sleep(1.5)
                continue
            new_items = [
                t for t in current
                if str(t.get('hash', '')).lower() not in before_hashes
            ]
            if new_items:
                new_items.sort(key=lambda t: float(t.get('added_on', 0)), reverse=True)
                target_hash = str(new_items[0].get('hash', '')).lower()
                break
            # Fallback: try title match
            title_l = cand_title.lower()
            for t in current:
                name_l = str(t.get('name', '')).lower()
                if title_l and title_l[:40] in name_l:
                    target_hash = str(t.get('hash', '')).lower()
                    break
            if target_hash:
                break
            time.sleep(1.5)

        if not target_hash:
            log('Could not resolve torrent hash in qBittorrent; trying next candidate')
            continue

        before_hashes.add(target_hash)
        done_states = {'uploading', 'stalledup', 'pausedup', 'queuedup', 'forcedup', 'checkingup'}
        while not cancel_event.is_set():
            try:
                info_list = torrents_info(target_hash)
            except Exception:
                time.sleep(1.5)
                continue
            if not info_list:
                time.sleep(1.5)
                continue

            info = info_list[0]
            state = str(info.get('state', '')).lower()
            progress = float(info.get('progress', 0.0) or 0.0)
            total_size = int(info.get('total_size') or info.get('size') or 0)
            downloaded = int(progress * total_size) if total_size > 0 else 0
            speed = float(info.get('dlspeed', 0.0) or 0.0) / 1024 / 1024
            if progress_cb:
                progress_cb(min(max(progress, 0.0), 1.0), speed, downloaded, total_size)

            if state in ('error', 'missingfiles'):
                log(f'Torrent entered error state: {state}')
                break

            if progress >= 0.999 and state in done_states:
                content_path = info.get('content_path') or os.path.join(
                    str(info.get('save_path') or dest_dir),
                    str(info.get('name') or '')
                )
                src_path = _best_downloaded_file(content_path, rom_name)
                if not src_path or not os.path.exists(src_path):
                    log(f'Torrent completed but payload not found: {content_path!r}')
                    break

                try:
                    if os.path.normcase(os.path.abspath(src_path)) != os.path.normcase(os.path.abspath(final_path)):
                        if os.path.exists(final_path):
                            os.remove(final_path)
                        try:
                            shutil.move(src_path, final_path)
                        except Exception:
                            shutil.copy2(src_path, final_path)
                    if remove_on_complete:
                        delete_torrent(target_hash)
                    log(f'qBittorrent completed: {final_path}')
                    return True, final_path
                except Exception as e:
                    log(f'Failed to finalize torrent payload ({type(e).__name__}: {e})')
                    break

            time.sleep(1.5)

        if cancel_event.is_set():
            delete_torrent(target_hash)
            log('qBittorrent download cancelled by user')
            return False, final_path

    return False, final_path


# ---------------------------------------------------------------------------
# Helper: atomic config save
# ---------------------------------------------------------------------------

def _atomic_write_json(path: str, data: dict) -> None:
    """Write data as JSON to path atomically (write temp + rename)."""
    tmp_path = None
    try:
        fd, tmp = tempfile.mkstemp(dir=APP_DATA, suffix='.json.tmp', prefix='cfg_')
        tmp_path = tmp
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception as e:
        print(f'[Config] Atomic save failed: {e}')
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Helper: safe zip extraction
# ---------------------------------------------------------------------------

def _safe_extractall(zip_ref: zipfile.ZipFile, extract_dir: str) -> None:
    """Extract zip, skipping any members with path traversal."""
    real_target = os.path.realpath(extract_dir)
    safe_members = []
    for member in zip_ref.namelist():
        dest = os.path.realpath(os.path.join(real_target, member))
        if dest.startswith(real_target + os.sep) or dest == real_target:
            safe_members.append(member)
        else:
            print(f'[ZIP] Skipping unsafe path: {member}')
    zip_ref.extractall(real_target, members=safe_members)


# ---------------------------------------------------------------------------
# Helper: ownership cache
# ---------------------------------------------------------------------------

class _OwnershipCache:
    """
    One scandir pass per folder replaces N individual stat() calls.
    Cache keyed by (local_path, folder_mtime) — invalidated automatically
    when the folder changes.
    """
    def __init__(self):
        self._cache: dict = {}
        self._lock = threading.Lock()

    def get_owned_set(self, local_path: str) -> set:
        if not local_path or not os.path.exists(local_path):
            return set()
        try:
            mtime = os.stat(local_path).st_mtime
        except OSError:
            return set()
        key = (local_path, mtime)
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        # Build — outside lock for I/O
        owned = set()
        try:
            with os.scandir(local_path) as it:
                for entry in it:
                    if entry.is_file(follow_symlinks=False):
                        if not _is_myrifetch_stub(entry.path):
                            owned.add(entry.name.lower())
                    elif entry.is_dir(follow_symlinks=False):
                        try:
                            with os.scandir(entry.path) as sub:
                                for s in sub:
                                    if s.is_file(follow_symlinks=False):
                                        if not _is_myrifetch_stub(s.path):
                                            owned.add(s.name.lower())
                        except OSError:
                            pass
        except OSError:
            pass
        with self._lock:
            # Evict old entries for same path
            stale = [k for k in self._cache if k[0] == local_path]
            for k in stale:
                del self._cache[k]
            self._cache[key] = owned
        return owned

    def invalidate(self, local_path: str) -> None:
        with self._lock:
            stale = [k for k in self._cache if k[0] == local_path]
            for k in stale:
                del self._cache[k]


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

class RAManager:
    def __init__(self, username, api_key):
        self.username = username
        self.api_key = api_key
        self.base_url = "https://retroachievements.org/API/"

    def get_user_summary(self):
        if not self.username or not self.api_key:
            return "Missing Credentials", None
        params = {'z': self.username, 'y': self.api_key, 'u': self.username}
        try:
            r = requests.get(
                f"{self.base_url}API_GetUserSummary.php",
                params=params, timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if "error" in data:
                    return data["error"], None
                return None, data
            return f"Server Error ({r.status_code})", None
        except Exception as e:
            return str(e), None


class TwitchManager:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.expires_at = 0
        self._lock = threading.Lock()  # FIXED: thread-safe auth

    def authenticate(self):
        if not self.client_id or not self.client_secret:
            return False
        try:
            r = requests.post('https://id.twitch.tv/oauth2/token', params={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials'
            }, timeout=10)
            r.raise_for_status()
            data = r.json()
            with self._lock:
                self.access_token = data['access_token']
                self.expires_at = time.time() + data['expires_in']
            return True
        except Exception:
            return False

    def get_headers(self):
        with self._lock:
            needs_refresh = (
                not self.access_token or time.time() >= self.expires_at
            )
        if needs_refresh:
            if not self.authenticate():
                return None
        with self._lock:
            token = self.access_token
            cid = self.client_id
        return {
            'Client-ID': cid,
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }

    def search_game(self, query):
        headers = self.get_headers()
        if not headers:
            return None
        # FIXED: escape quotes/semicolons to avoid IGDB query injection
        safe_query = query.replace('"', '').replace(';', '').strip()
        try:
            r = requests.post(
                "https://api.igdb.com/v4/games",
                headers=headers,
                data=(
                    f'search "{safe_query}"; '
                    f'fields name, cover.url, summary, first_release_date, '
                    f'genres.name, involved_companies.company.name; limit 1;'
                ),
                timeout=10
            )
            r.raise_for_status()
            data = r.json()
            return data[0] if data else None
        except Exception:
            return None


# ---------------------------------------------------------------------------
# ScreenScraper integration
# ---------------------------------------------------------------------------

# ScreenScraper system IDs — maps MyriFetch console names to SS platform IDs
SCREENSCRAPER_SYSTEM_IDS = {
    # Sony
    'PlayStation 1':  57,
    'PlayStation 2':  58,
    'PlayStation 3':  59,
    'PSP':            61,
    # Nintendo
    'NES':                  3,
    'SNES':                 4,
    'N64':                  14,
    'N64DD':                122,
    'GameCube':             13,
    'Wii':                  16,
    'Wii U':                18,
    'GBA':                  12,
    'Game Boy':             9,
    'Game Boy Color':       10,
    'Nintendo DS':          15,
    'Nintendo 3DS':         17,
    'New Nintendo 3DS':     17,
    'Virtual Boy':          11,
    'Famicom Disk System':  106,
    # Sega
    'Mega Drive':    1,
    'Master System': 2,
    'Saturn':        22,
    'Dreamcast':     23,
    'Mega CD':       20,
    'Game Gear':     21,
    'Sega 32X':      19,
    'SG-1000':       6,
    # Microsoft
    'Xbox':     32,
    'Xbox 360': 33,
    # SNK
    'Neo Geo CD':           70,
    'Neo Geo Pocket':       25,
    'Neo Geo Pocket Color': 82,
    # Atari
    'Atari 2600':    26,
    'Atari 5200':    40,
    'Atari 7800':    41,
    'Atari Lynx':    28,
    'Atari Jaguar':  27,
    'Atari Jaguar CD': 171,
    # NEC
    'PC Engine':    31,
    'PC Engine SG': 105,
    'PC Engine CD': 114,
    'PC-FX':        72,
    # Bandai
    'WonderSwan':       45,
    'WonderSwan Color': 46,
    # Panasonic
    '3DO': 29,
    # Philips
    'CD-i': 62,
    # Commodore
    'Amiga CD32': 130,
    # Other
    'ColecoVision': 48,
    'Intellivision': 115,
    'Vectrex':       102,
    'MSX':           113,
    'MSX2':          116,
}

# Reverse lookup: console_name → SS system ID (used from UltimateApp)
CONSOLE_TO_SS_ID = SCREENSCRAPER_SYSTEM_IDS


class ScreenScraperManager:
    """
    Wraps the ScreenScraper API (screenscraper.fr) to fetch game metadata
    and download media assets matching your RetroBat ES configuration:

      ScrapperImageSrc  = sstitle   → images/<name>-image.png
      ScrapperThumbSrc  = box-3D    → <name>.jpg  (next to ROM, <thumbnail>)
      + marquee                     → images/<name>-marquee.png
      + video snap                  → videos/<name>-video.mp4
    """

    SS_API = 'https://www.screenscraper.fr/api2/jeuInfos.php'
    SOFTNAME = 'MyriFetch'

    # Priority region order for media selection
    _REGION_PRIO = ['wor', 'us', 'en', 'eu', 'ss', 'uk', 'fr', 'de', 'jp']

    def __init__(self, ss_user: str, ss_password: str):
        self.ss_user = ss_user
        self.ss_password = ss_password
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': f'MyriFetch/{APP_NAME}',
        })

    def _base_params(self):
        return {
            'devid':      self.ss_user,
            'devpassword': self.ss_password,
            'softname':   self.SOFTNAME,
            'output':     'json',
            'ssid':       self.ss_user,
            'sspassword': self.ss_password,
        }

    def lookup_game(self, rom_name: str, system_id: int, log_cb=None):
        """
        Query ScreenScraper for a game by filename and system.
        Returns the 'jeu' dict from the API or None.
        """
        def log(msg):
            if log_cb:
                try:
                    log_cb(msg)
                except Exception:
                    pass

        params = self._base_params()
        params['systemeid'] = str(system_id)
        params['romnom'] = rom_name

        # Sanitised URL for logging (no passwords or usernames)
        safe_params = {k: v for k, v in params.items()
                       if k not in ('devpassword', 'sspassword', 'devid', 'ssid')}
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

        header = data.get('header', {})
        if str(header.get('success', '')).lower() not in ('true', '1'):
            err = header.get('error', 'unknown error')
            log(f'ScreenScraper: {err}')
            return None

        jeu = (data.get('response') or {}).get('jeu')
        if not jeu:
            log(f'ScreenScraper: no game data returned for {rom_name!r}')
            return None

        log(f'ScreenScraper: matched "{_ss_pick_name(jeu)}"')
        return jeu

    def _find_media(self, jeu: dict, media_type: str) -> str | None:
        """
        Return the best download URL for a given media type, using
        region priority order.  Returns None if not found.
        """
        medias = jeu.get('medias') or []
        candidates = [m for m in medias if m.get('type') == media_type]
        if not candidates:
            return None
        # Score by region priority
        def _score(m):
            region = str(m.get('region') or m.get('pays') or 'wor'
                         ).lower().strip()
            try:
                return self._REGION_PRIO.index(region)
            except ValueError:
                return len(self._REGION_PRIO)
        candidates.sort(key=_score)
        return candidates[0].get('url')

    def download_media(
        self, url: str, dest_path: str, log_cb=None
    ) -> bool:
        """Download a media file to dest_path. Returns True on success."""
        def log(msg):
            if log_cb:
                try:
                    log_cb(msg)
                except Exception:
                    pass
        # Sanitise URL before logging — SS media URLs can embed sspassword in query string
        try:
            _p = urlparse(url)
            _qs = {k: v for k, v in parse_qs(_p.query, keep_blank_values=True).items()
                   if k not in ('sspassword', 'ssid', 'devpassword', 'devid')}
            _safe_url = urlunparse(_p._replace(query=urlencode(_qs, doseq=True)))
        except Exception:
            _safe_url = '<url>'
        log(f'ScreenScraper → downloading {_safe_url}')
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

    def scrape_game(
        self, game: dict, rom_dir: str, config: dict,
        log_cb=None, progress_cb=None
    ) -> dict:
        """
        Full scrape for one game entry.  Downloads all configured media types
        and returns a metadata dict with keys:
            image, thumbnail, marquee, video,
            desc, genre, developer, publisher, releasedate, players, rating

        Matches your es_settings.cfg:
            ScrapperImageSrc = sstitle   → -image.png
            ScrapperThumbSrc = box-3D    → .jpg next to ROM
        """
        def log(msg):
            if log_cb:
                try:
                    log_cb(msg)
                except Exception:
                    pass

        meta = {}
        console_name = game.get('console', '')
        system_id = CONSOLE_TO_SS_ID.get(console_name)
        if not system_id:
            log(f'ScreenScraper: no system ID for console {console_name!r}')
            return meta

        rom_name = os.path.basename(game.get('path', ''))
        if not rom_name:
            return meta

        jeu = self.lookup_game(rom_name, system_id, log_cb=log)
        if not jeu:
            return meta

        base_name = os.path.splitext(rom_name)[0]
        images_dir = os.path.join(rom_dir, 'images')
        videos_dir = os.path.join(rom_dir, 'videos')

        steps = [
            # (ss_media_type, dest_path, meta_key)
            ('sstitle', os.path.join(images_dir, f'{base_name}-image.png'), 'image'),
            ('box-3D',  os.path.join(rom_dir,    f'{base_name}.jpg'),       'thumbnail'),
            ('marquee', os.path.join(images_dir, f'{base_name}-marquee.png'), 'marquee'),
            ('video',   os.path.join(videos_dir, f'{base_name}-video.mp4'), 'video'),
        ]

        for idx, (media_type, dest, key) in enumerate(steps):
            if progress_cb:
                try:
                    progress_cb(idx / len(steps))
                except Exception:
                    pass
            url = self._find_media(jeu, media_type)
            if url:
                if self.download_media(url, dest, log_cb=log):
                    meta[key] = dest
            else:
                log(f'ScreenScraper: no {media_type!r} media found')

        if progress_cb:
            try:
                progress_cb(1.0)
            except Exception:
                pass

        # ---- Text metadata ----
        lang = str(config.get('language', 'en')).lower()[:2]
        meta['desc']        = _ss_pick_text(jeu.get('synopsis') or [], lang)
        meta['genre']       = _ss_pick_genres(jeu)
        meta['developer']   = _ss_pick_company(jeu, 'developpeur')
        meta['publisher']   = _ss_pick_company(jeu, 'editeur')
        meta['releasedate'] = _ss_pick_date(jeu)
        meta['players']     = str(jeu.get('joueurs') or '')
        meta['rating']      = _ss_pick_rating(jeu)

        return meta


# --- ScreenScraper helper functions ---

def _ss_pick_name(jeu: dict) -> str:
    noms = jeu.get('noms') or []
    for region in ('wor', 'us', 'eu', 'jp', 'ss'):
        for n in noms:
            if str(n.get('region') or '').lower() == region:
                return n.get('text', '')
    return (noms[0].get('text', '') if noms else
            jeu.get('romnom', 'Unknown'))


def _ss_pick_text(items: list, lang: str) -> str:
    """Pick best synopsis/text for the given language."""
    if not items:
        return ''
    # Prefer exact language match, fall back to 'en'
    for target in (lang, 'en', 'fr'):
        for item in items:
            if str(item.get('langue') or item.get('language') or '').lower() == target:
                return (item.get('text') or item.get('synop') or '').strip()
    # Any
    first = items[0]
    return (first.get('text') or first.get('synop') or '').strip()


def _ss_pick_genres(jeu: dict) -> str:
    genres = jeu.get('genres') or []
    names = []
    for g in genres[:3]:
        noms = g.get('noms') or []
        name = _ss_pick_text(noms, 'en')
        if name:
            names.append(name)
    return ', '.join(names)


def _ss_pick_company(jeu: dict, key: str) -> str:
    company = jeu.get(key) or {}
    noms = company.get('noms') or []
    if noms:
        return noms[0].get('text', '')
    return str(company.get('text') or company.get('nom') or '')


def _ss_pick_date(jeu: dict) -> str:
    """Return ES-format date string: YYYYMMDDTHHMMSS"""
    dates = jeu.get('dates') or {}
    for region in ('wor', 'us', 'eu', 'jp'):
        d = dates.get(region, '')
        if d:
            # SS format varies: YYYY-MM-DD or YYYY or YYYY-MM
            d = d.strip()
            d_clean = d.replace('-', '')
            if len(d_clean) == 8:
                return f'{d_clean}T000000'
            if len(d_clean) == 4:
                return f'{d_clean}0101T000000'
            if len(d_clean) == 6:
                return f'{d_clean}01T000000'
    return ''


def _ss_pick_rating(jeu: dict) -> str:
    """Return ES rating 0.0-1.0 as string."""
    note = jeu.get('note') or ''
    try:
        # SS note is typically 0-20
        v = float(str(note).replace(',', '.'))
        if v > 1:
            v = v / 20.0
        return f'{max(0.0, min(1.0, v)):.2f}'
    except (ValueError, TypeError):
        return ''


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

class GameTooltip(ctk.CTkToplevel):
    def __init__(self, parent, title, details, x, y):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.geometry(f"+{x+15}+{y+15}")
        self.frame = ctk.CTkFrame(
            self, fg_color=C['bg'], border_width=1, border_color=C['cyan']
        )
        self.frame.pack()
        ctk.CTkLabel(
            self.frame, text=title,
            font=('Arial', 14, 'bold'), text_color=C['cyan']
        ).pack(anchor='w', padx=10, pady=(10, 5))
        for label, value in details.items():
            row = ctk.CTkFrame(self.frame, fg_color='transparent')
            row.pack(fill='x', padx=10, pady=1)
            ctk.CTkLabel(
                row, text=f"{label}: ",
                font=('Arial', 12, 'bold'), text_color=C['dim']
            ).pack(side='left')
            ctk.CTkLabel(
                row, text=value,
                font=('Arial', 12), text_color='white',
                wraplength=300, justify='left'
            ).pack(side='left')
        ctk.CTkLabel(self.frame, text=" ", font=('Arial', 2)).pack()


class CustomPopup(ctk.CTkToplevel):
    def __init__(self, parent, title, message, buttons=('OK',)):
        super().__init__(parent)
        self.title(title)
        self.result = None
        w, h = 400, 200
        x = parent.winfo_x() + parent.winfo_width() // 2 - w // 2
        y = parent.winfo_y() + parent.winfo_height() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(False, False)
        self.configure(fg_color=C['bg'])
        ctk.CTkLabel(
            self, text=message, wraplength=350,
            font=('Arial', 14), text_color=C['text']
        ).pack(pady=(40, 20), padx=20, fill='both', expand=True)
        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(pady=(0, 20))
        for btn_text in buttons:
            ctk.CTkButton(
                btn_frame, text=btn_text,
                command=lambda b=btn_text: self.on_btn(b),
                fg_color=C['cyan'], text_color='black',
                hover_color=C['pink'], width=100
            ).pack(side='left', padx=10)
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def on_btn(self, text):
        self.result = text
        self.destroy()


class ThemedDirBrowser(ctk.CTkToplevel):
    def __init__(self, parent, title="Select Folder", initial_dir=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.parent = parent
        w, h = 550, 700
        x = parent.winfo_x() + parent.winfo_width() // 2 - w // 2
        y = parent.winfo_y() + parent.winfo_height() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.configure(fg_color=C['bg'])
        if initial_dir and os.path.exists(initial_dir):
            self.current_dir = os.path.abspath(initial_dir)
        else:
            self.current_dir = os.path.expanduser("~")

        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(
            header, text="⬆ Up", width=60,
            command=self.go_up, fg_color=C['card'], hover_color=C['dim']
        ).pack(side='left', padx=(0, 5))
        self.path_var = tk.StringVar(value=self.current_dir)
        self.entry = ctk.CTkEntry(
            header, textvariable=self.path_var,
            fg_color=C['card'], text_color='white', border_color=C['dim']
        )
        self.entry.pack(side='left', fill='x', expand=True, padx=5)
        self.entry.bind('<Return>', self.on_enter_path)
        ctk.CTkButton(
            header, text="Go", width=40,
            command=self.on_enter_path, fg_color=C['cyan'], text_color='black'
        ).pack(side='left', padx=5)

        if os.name == 'nt':
            self.drives = self.get_drives()
            current_drive = os.path.splitdrive(self.current_dir)[0] + '\\'
            self.drive_var = tk.StringVar(value=current_drive)
            if self.drives:
                ctk.CTkOptionMenu(
                    header, variable=self.drive_var,
                    values=self.drives, command=self.change_drive,
                    width=70, fg_color=C['card'], button_color=C['dim']
                ).pack(side='left', padx=5)

        toolbar = ctk.CTkFrame(self, fg_color='transparent', height=30)
        toolbar.pack(fill='x', padx=15, pady=(0, 5))
        ctk.CTkButton(
            toolbar, text="+ New Folder", width=100, height=24,
            font=('Arial', 11), fg_color=C['card'], hover_color=C['dim'],
            command=self.create_folder
        ).pack(side='left')

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=C['card'])
        self.scroll.pack(fill='both', expand=True, padx=10, pady=5)
        self.bind_scroll(self.scroll, self.scroll)

        footer = ctk.CTkFrame(self, fg_color='transparent')
        footer.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(
            footer, text="Cancel", fg_color=C['pink'],
            hover_color='#990033', width=100, command=self.destroy
        ).pack(side='right', padx=5)
        ctk.CTkButton(
            footer, text="Select This Folder",
            fg_color=C['success'], text_color='black',
            hover_color='#00b359', width=150, command=self.select_current
        ).pack(side='right', padx=5)
        self.refresh_list()
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def bind_scroll(self, widget, target_frame):
        widget.bind("<Button-4>", lambda e, t=target_frame: self._on_scroll(e, t, -1))
        widget.bind("<Button-5>", lambda e, t=target_frame: self._on_scroll(e, t, 1))
        widget.bind("<MouseWheel>", lambda e, t=target_frame: self._on_scroll(e, t, 0))

    def _on_scroll(self, event, widget, direction):
        if direction == 0:
            widget._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            widget._parent_canvas.yview_scroll(direction, "units")

    def get_drives(self):
        return [chr(x) + ":\\" for x in range(65, 91) if os.path.exists(chr(x) + ":\\")]

    def change_drive(self, drive):
        self.current_dir = drive
        self.path_var.set(self.current_dir)
        self.refresh_list()

    def go_up(self):
        parent = os.path.dirname(self.current_dir)
        if parent != self.current_dir:
            self.current_dir = parent
            self.path_var.set(self.current_dir)
            self.refresh_list()

    def on_enter_path(self, event=None):
        p = self.path_var.get()
        if os.path.isdir(p):
            self.current_dir = p
            self.refresh_list()
        else:
            self.entry.configure(border_color=C['pink'])

    def create_folder(self):
        dialog = ctk.CTkInputDialog(text="New Folder Name:", title="Create Folder")
        name = dialog.get_input()
        if not name:
            return
        try:
            os.makedirs(os.path.join(self.current_dir, name), exist_ok=True)
            self.refresh_list()
        except Exception as e:
            print(e)

    def enter_folder(self, folder_name):
        new_path = os.path.join(self.current_dir, folder_name)
        if os.path.isdir(new_path):
            try:
                os.listdir(new_path)
                self.current_dir = new_path
                self.path_var.set(self.current_dir)
                self.refresh_list()
            except Exception:
                pass

    def select_current(self):
        self.result = self.current_dir
        self.destroy()

    def refresh_list(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self.entry.configure(border_color=C['dim'])
        try:
            # FIXED: use context manager to avoid FD leak
            with os.scandir(self.current_dir) as it:
                dirs = sorted(
                    entry.name for entry in it
                    if entry.is_dir(follow_symlinks=False)
                )
            if not dirs:
                lbl = ctk.CTkLabel(
                    self.scroll, text="(Empty or No Subfolders)",
                    text_color=C['dim']
                )
                lbl.pack(pady=20)
                self.bind_scroll(lbl, self.scroll)
                return
            for d in dirs:
                btn = ctk.CTkButton(
                    self.scroll, text=f"📁 {d}", anchor="w",
                    fg_color="transparent", text_color=C['text'],
                    hover_color=C['dim'], height=28,
                    command=lambda f=d: self.enter_folder(f)
                )
                btn.pack(fill="x", padx=2, pady=1)
                self.bind_scroll(btn, self.scroll)
        except Exception as e:
            err = ctk.CTkLabel(
                self.scroll, text=f"Access Denied: {e}",
                text_color=C['pink']
            )
            err.pack(pady=20)
            self.bind_scroll(err, self.scroll)


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class UltimateApp(ctk.CTk):
    def __init__(self):
        # FIXED: super().__init__() FIRST — never call Tk methods before this
        self.load_config()
        self.apply_saved_theme()
        super().__init__()

        self.app_version = "1.4.1"
        self.github_url = "https://github.com/crabbiemike/MyriFetch"

        self.twitch = TwitchManager(
            self.folder_mappings.get('twitch_id', ''),
            self.folder_mappings.get('twitch_secret', '')
        )
        self.ra = RAManager(
            self.folder_mappings.get('ra_user', ''),
            self.folder_mappings.get('ra_key', '')
        )

        self.title(f"MYRIFETCH v{self.app_version} // ROM MANAGER")
        self.geometry("1100x850")
        self.configure(bg_color=C['bg'])

        # Session for all HTTP — single connection pool
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        self.current_path = ""
        self.file_cache = []
        self.filtered_cache = []   # pre-sorted by filter_list
        self.download_list = []
        self.pending_stage_queue = collections.deque()  # FIXED: deque for O(1) pops
        self._cancel_event = threading.Event()   # SET = cancelled
        self._pause_event = threading.Event()    # SET = running (not paused)
        self._pause_event.set()                  # start in running state
        self.console_icons = {}
        self.current_page = 0
        self.items_per_page = 100
        self.checkboxes = []  # FIXED: init here not just in render_page

        self.home_widgets = []
        self.browser_widgets = []
        self.queue_widgets = []
        self.settings_widgets = []
        self.library_widgets = []
        self._library_games = None   # cache – avoids rescan on tab switch
        self._logger = None          # set up by _setup_logging()
        self._setup_logging()

        self.tooltip_window = None
        self.tooltip_job = None
        self.game_metadata_cache = {}
        self._search_after_id = None  # for debounced live search

        # FIXED: ownership cache — replaces per-file stat calls
        self._ownership_cache = _OwnershipCache()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.setup_sidebar()
        self.setup_main()
        threading.Thread(target=self.icon_manager, daemon=True).start()
        self.show_home()
        self.status_txt.configure(text=f"v{self.app_version}")
        self.net_log("System Initialized")
        try:
            self.refresh_dir("")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.folder_mappings = json.load(f)
                # Validate — must be a dict
                if not isinstance(self.folder_mappings, dict):
                    raise ValueError("Config root is not a dict")
            except (json.JSONDecodeError, ValueError) as e:
                backup = CONFIG_FILE + '.corrupt'
                try:
                    shutil.copy2(CONFIG_FILE, backup)
                    print(f"[Config] Corrupt — backed up to {backup}. Error: {e}")
                except Exception:
                    pass
                self.folder_mappings = {}
        else:
            self.folder_mappings = {}

        # Auto-migrate ScreenScraper credentials from RetroBat's es_settings.cfg
        # if they haven't been saved to MyriFetch config yet.
        if not self.folder_mappings.get('ss_user'):
            self._try_import_ss_creds_from_retrobat()

    def _try_import_ss_creds_from_retrobat(self):
        """
        If the user hasn't set SS credentials yet, silently read them from
        RetroBat's es_settings.cfg (ScreenScraperUser / ScreenScraperPass).
        """
        try:
            rb_path = self.folder_mappings.get('retrobat_path', r'C:\retrobat')
            cfg_path = os.path.join(
                rb_path, 'emulationstation', '.emulationstation', 'es_settings.cfg'
            )
            if not os.path.isfile(cfg_path):
                return
            tree = ET.parse(cfg_path)
            root = tree.getroot()
            user = pass_ = ''
            for el in root.findall('string'):
                name = el.get('name', '')
                value = el.get('value', '')
                if name == 'ScreenScraperUser':
                    user = value.strip()
                elif name == 'ScreenScraperPass':
                    pass_ = value.strip()
            if user and pass_:
                self.folder_mappings['ss_user'] = user
                self.folder_mappings['ss_password'] = pass_
        except Exception:
            pass

    def save_config(self):
        # FIXED: atomic write — no data loss on crash
        _atomic_write_json(CONFIG_FILE, self.folder_mappings)

    def _setup_logging(self):
        """Configure (or tear down) the file logger based on the debug_mode setting."""
        enabled = bool(self.folder_mappings.get('debug_mode', False))
        logger = logging.getLogger('MyriFetch')
        # Remove all existing handlers first to avoid duplicates on toggle
        for h in list(logger.handlers):
            logger.removeHandler(h)
            h.close()
        logger.propagate = False  # prevent records leaking to root logger
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

    def _debug_log(self, msg: str):
        """Write a debug message to the log file if debug mode is on."""
        if self._logger:
            self._logger.debug(msg)

    def apply_saved_theme(self):
        saved = self.folder_mappings.get('app_theme', 'Cyber Dark')
        if saved in THEMES:
            C.update(THEMES[saved])

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def change_theme(self, new_theme):
        self.folder_mappings['app_theme'] = new_theme
        self.save_config()
        popup = CustomPopup(
            self, "Theme Changed",
            "The theme has been updated.\n\nA restart is required to apply fully.\n"
            "Would you like to restart now?",
            ['Restart Now', 'Later']
        )
        if popup.result == 'Restart Now':
            self.restart_app()

    def restart_app(self):
        self.destroy()
        try:
            if getattr(sys, 'frozen', False):
                os.execl(sys.executable, sys.executable, *sys.argv[1:])
            else:
                os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            print(f"Restart failed: {e}")

    def change_default_region(self, new_region):
        self.folder_mappings['default_region'] = new_region
        self.save_config()
        self.region_var.set(new_region)
        self.filter_list()

    def net_log(self, msg):
        self.after(0, lambda m=msg: self.net_status.configure(text=f"Net: {m}"))

    # ------------------------------------------------------------------
    # Icon manager
    # ------------------------------------------------------------------

    def icon_manager(self):
        # FIXED: simple makedirs — no nonsensical rmtree on non-existent dir
        os.makedirs(ICON_DIR, exist_ok=True)
        self.net_log("Connecting to LaunchBox DB...")
        lb_urls = {}
        try:
            icon_headers = HEADERS.copy()
            icon_headers['Referer'] = 'https://gamesdb.launchbox-app.com/'
            r = self.session.get(
                'https://gamesdb.launchbox-app.com/platforms/index',
                headers=icon_headers, timeout=15
            )
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                for card in soup.find_all('div', class_='white-card'):
                    title_tag = card.find('a', class_='list-item-title')
                    if title_tag:
                        lb_name = title_tag.text.strip()
                        img_tag = card.find('img')
                        if img_tag and 'src' in img_tag.attrs:
                            for my_name, target_lb_name in LB_NAMES.items():
                                if lb_name.lower() == target_lb_name.lower():
                                    lb_urls[my_name] = img_tag['src']

            for name in CONSOLES.keys():
                safe_name = "".join(x for x in name if x.isalnum()) + ".png"
                local_path = os.path.join(ICON_DIR, safe_name)

                # FIXED: correct cache check — download only if missing or too small
                already_cached = (
                    os.path.exists(local_path) and
                    os.path.getsize(local_path) >= 500
                )

                if name in lb_urls and not already_cached:
                    self.net_log(f"Downloading icon: {name}")
                    try:
                        r = self.session.get(
                            lb_urls[name], stream=True, timeout=10
                        )
                        if r.status_code == 200:
                            with open(local_path, 'wb') as f:
                                for chunk in r.iter_content(1024):
                                    f.write(chunk)
                    except Exception:
                        pass

                if os.path.exists(local_path) and os.path.getsize(local_path) >= 500:
                    try:
                        pil_img = Image.open(local_path)
                        # FIXED: CTkImage created, then dispatched to main thread
                        img = ctk.CTkImage(
                            light_image=pil_img, dark_image=pil_img,
                            size=(100, 100)
                        )
                        self.after(0, lambda n=name, i=img: self.console_icons.update({n: i}))
                    except Exception:
                        pass

            self.net_log("Icons Loaded")
            self.after(0, self.render_home_grid)
            self.after(3000, lambda: self.net_log("Idle"))
        except Exception as e:
            print(f"LaunchBox Scrape Error: {e}")

    # ------------------------------------------------------------------
    # Sidebar & Main setup (unchanged from original, except search bar)
    # ------------------------------------------------------------------

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=220, corner_radius=0, fg_color='#101014'
        )
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_rowconfigure(8, weight=1)
        ctk.CTkLabel(
            self.sidebar, text="👾 MYRIFETCH",
            font=('Arial', 22, 'bold'), text_color='white'
        ).grid(row=0, column=0, padx=20, pady=30)

        self.btn_home = self.nav_btn("Home", 1, self.show_home)
        self.btn_library = self.nav_btn("Library", 2, self.show_library)
        self.btn_browser = self.nav_btn("Browser", 3, lambda: self.show_browser())
        self.btn_bios = self.nav_btn("BIOS Files", 4, self.show_bios)
        self.btn_queue = self.nav_btn("Downloads", 5, self.show_queue)
        self.btn_ra = self.nav_btn("Achievements", 6, self.show_achievements)
        self.btn_settings = self.nav_btn("Settings", 7, self.show_settings)

        self.btn_update = ctk.CTkButton(
            self.sidebar, text="Check for Updates ↗", height=32,
            fg_color=C['card'], hover_color=C['pink'],
            font=('Arial', 11, 'bold'),
            command=self.check_for_updates
        )
        self.btn_update.grid(row=8, column=0, padx=20, pady=(10, 0), sticky='s')

        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color=C['card'])
        self.status_frame.grid(row=9, column=0, padx=20, pady=10, sticky='ew')
        self.status_dot = ctk.CTkLabel(
            self.status_frame, text="●",
            text_color=C['success'], font=('Arial', 16)
        )
        self.status_dot.pack(side='left', padx=(10, 5))
        self.status_txt = ctk.CTkLabel(
            self.status_frame, text=f"v{self.app_version}",
            text_color=C['dim']
        )
        self.status_txt.pack(side='left')

        self.net_status = ctk.CTkLabel(
            self.sidebar, text="Net: Idle",
            text_color=C['dim'], font=('Consolas', 10), anchor='w'
        )
        self.net_status.grid(row=10, column=0, padx=15, pady=(0, 10), sticky='ew')

    def nav_btn(self, text, row, cmd):
        btn = ctk.CTkButton(
            self.sidebar, text=text, height=40,
            fg_color='transparent', anchor='w',
            font=('Arial', 13, 'bold'), hover_color='#27272a',
            command=cmd
        )
        btn.grid(row=row, column=0, padx=5, pady=5, sticky='ew')
        return btn

    def check_for_updates(self):
        def _check():
            try:
                r = self.session.get(
                    'https://api.github.com/repos/crabbiemike/MyriFetch/releases/latest',
                    timeout=10
                )
                if r.status_code == 200:
                    data = r.json()
                    latest = data.get('tag_name', '').lstrip('vV')
                    if latest and latest != self.app_version:
                        self.after(0, lambda: self._show_update_available(latest, data.get('html_url', self.github_url)))
                    else:
                        self.after(0, lambda: CustomPopup(
                            self, "Up to Date",
                            f"You are running the latest version (v{self.app_version}).",
                            ["OK"]
                        ))
                else:
                    self.after(0, lambda: webbrowser.open(self.github_url + '/releases'))
            except Exception:
                self.after(0, lambda: webbrowser.open(self.github_url + '/releases'))
        threading.Thread(target=_check, daemon=True).start()

    def _show_update_available(self, latest, url):
        result = CustomPopup(
            self, "Update Available",
            f"A new version is available!\n\nCurrent: v{self.app_version}\nLatest: v{latest}\n\nOpen download page?",
            ["Open", "Later"]
        )
        if result.result == "Open":
            webbrowser.open(url)

    def setup_main(self):
        self.main_area = ctk.CTkFrame(self, fg_color='transparent')
        self.main_area.grid(row=0, column=1, sticky='nsew', padx=20, pady=20)
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        # FIXED: search container with two rows — no more overlapping widgets
        self.search_container = ctk.CTkFrame(
            self.main_area, fg_color='transparent'
        )
        self.search_container.grid_columnconfigure(0, weight=1)
        self.search_container.grid_columnconfigure(1, weight=0)

        self.search_var = tk.StringVar()
        self.entry_search = ctk.CTkEntry(
            self.search_container,
            placeholder_text="Search...",
            height=40, fg_color=C['card'],
            border_width=2, border_color=C['cyan'],
            corner_radius=20, text_color='white',
            textvariable=self.search_var
        )
        self.entry_search.grid(
            row=0, column=0, columnspan=2, sticky='ew', pady=(0, 6)
        )
        self.entry_search.bind('<Return>', self.filter_list)

        # FIXED: debounced live search
        def _on_key(event):
            if self._search_after_id:
                self.after_cancel(self._search_after_id)
            self._search_after_id = self.after(300, self.filter_list)
        self.entry_search.bind('<KeyRelease>', _on_key)

        default_region = self.folder_mappings.get('default_region', 'All Regions')
        self.region_var = ctk.StringVar(value=default_region)
        self.region_filter = ctk.CTkOptionMenu(
            self.search_container, variable=self.region_var,
            values=['All Regions', 'USA', 'Europe', 'Japan', 'World'],
            command=self.filter_list,
            fg_color=C['card'], button_color=C['cyan'],
            button_hover_color=C['pink'], text_color='white',
            width=140, height=36, corner_radius=18
        )
        self.region_filter.grid(row=1, column=0, sticky='w')  # FIXED: row=1, col=0

        self.status_var = ctk.StringVar(value='All Status')
        self.status_filter = ctk.CTkOptionMenu(
            self.search_container, variable=self.status_var,
            values=['All Status', 'Missing Only', 'Owned Only'],
            command=self.filter_list,
            fg_color=C['card'], button_color=C['cyan'],
            button_hover_color=C['pink'], text_color='white',
            width=140, height=36, corner_radius=18
        )
        self.status_filter.grid(row=1, column=1, sticky='e')  # FIXED: row=1, col=1

        # Frames
        self.frame_home = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_library = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_details = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_browser = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_queue = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_settings = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_bios = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_achievements = ctk.CTkFrame(self.main_area, fg_color='transparent')

        # Home
        ctk.CTkLabel(
            self.frame_home, text="QUICK JUMP",
            font=('Arial', 16, 'bold'), text_color=C['dim']
        ).pack(anchor='w', pady=10)
        self.grid_consoles = ctk.CTkScrollableFrame(
            self.frame_home, fg_color='transparent'
        )
        self.grid_consoles.pack(fill='both', expand=True)
        self.bind_scroll(self.grid_consoles, self.grid_consoles)
        self.render_home_grid()

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

        # Browser
        self.frame_browser.grid_rowconfigure(1, weight=1)
        self.frame_browser.grid_columnconfigure(0, weight=1)
        nav = ctk.CTkFrame(self.frame_browser, fg_color='transparent')
        nav.pack(fill='x', pady=5)
        ctk.CTkButton(
            nav, text="⬅ Back", width=60,
            fg_color=C['card'], command=self.go_up
        ).pack(side='left')
        self.lbl_path = ctk.CTkLabel(nav, text="/", text_color=C['dim'], padx=10)
        self.lbl_path.pack(side='left')
        self.btn_open = ctk.CTkButton(
            nav, text="↗ Open", width=60,
            fg_color=C['card'], hover_color=C['dim'],
            command=self.open_current_folder
        )
        self.btn_open.pack(side='right', padx=(5, 0))
        self.btn_map = ctk.CTkButton(
            nav, text="📂 Set Folder",
            fg_color='transparent', border_width=1,
            border_color=C['cyan'], text_color=C['cyan'],
            command=self.set_mapping
        )
        self.btn_map.pack(side='right')

        self.storage_frame = ctk.CTkFrame(
            self.frame_browser, fg_color='transparent', height=20
        )
        self.storage_frame.pack(fill='x', padx=10)
        self.storage_label = ctk.CTkLabel(
            self.storage_frame, text="Storage: Checking...",
            font=('Arial', 10), text_color=C['dim']
        )
        self.storage_label.pack(side='left')
        self.storage_bar = ctk.CTkProgressBar(
            self.storage_frame, height=8, progress_color=C['dim']
        )
        self.storage_bar.set(0)
        self.storage_bar.pack(side='left', fill='x', expand=True, padx=10)

        self.list_frame = ctk.CTkScrollableFrame(
            self.frame_browser, fg_color=C['card']
        )
        self.list_frame.pack(fill='both', expand=True, pady=10)
        self.bind_scroll(self.list_frame, self.list_frame)

        self.loading_frame = ctk.CTkFrame(self.frame_browser, fg_color='transparent')
        self.loading_label = ctk.CTkLabel(
            self.loading_frame, text="ACCESSING DATABANK...",
            font=('Arial', 18, 'bold'), text_color=C['cyan']
        )
        self.loading_label.place(relx=0.5, rely=0.4, anchor='center')
        self.loading_bar = ctk.CTkProgressBar(
            self.loading_frame, width=300, height=20,
            progress_color=C['pink'], mode='indeterminate'
        )
        self.loading_bar.place(relx=0.5, rely=0.5, anchor='center')

        self.page_controls = ctk.CTkFrame(
            self.frame_browser, fg_color='transparent', height=40
        )
        self.page_controls.pack(fill='x', pady=5)
        self.btn_prev = ctk.CTkButton(
            self.page_controls, text="< Previous", width=100,
            fg_color=C['card'], command=self.prev_page
        )
        self.btn_prev.pack(side='left')
        self.lbl_page = ctk.CTkLabel(
            self.page_controls, text="Page 1", text_color=C['dim']
        )
        self.lbl_page.pack(side='left', expand=True)
        self.btn_next = ctk.CTkButton(
            self.page_controls, text="Next >", width=100,
            fg_color=C['card'], command=self.next_page
        )
        self.btn_next.pack(side='right')

        dl_frame = ctk.CTkFrame(self.frame_browser, fg_color='transparent')
        dl_frame.pack(fill='x')
        self.btn_dl = ctk.CTkButton(
            dl_frame, text="DOWNLOAD SELECTED [0]", height=50,
            fg_color=C['cyan'], text_color='black',
            font=('Arial', 14, 'bold'), command=self.add_to_queue
        )
        self.btn_dl.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.btn_dl_all = ctk.CTkButton(
            dl_frame, text="⬇ Download All Listed", height=50,
            fg_color=C['card'], text_color='white',
            font=('Arial', 14, 'bold'), hover_color=C['pink'],
            command=self.add_all_to_queue
        )
        self.btn_dl_all.pack(side='right', fill='x', expand=True, padx=(5, 0))

        # Queue
        ctk.CTkLabel(
            self.frame_queue, text="ACTIVE DOWNLOAD",
            font=('Arial', 20, 'bold')
        ).pack(anchor='w', pady=10)
        self.queue_controls = ctk.CTkFrame(
            self.frame_queue, fg_color='transparent'
        )
        self.queue_controls.pack(fill='x', pady=5)
        self.lbl_speed = ctk.CTkLabel(
            self.queue_controls, text="IDLE",
            font=('Consolas', 14), text_color=C['cyan']
        )
        self.lbl_speed.pack(side='left')
        self.btn_pause = ctk.CTkButton(
            self.queue_controls, text="Pause Download",
            fg_color=C['card'], width=120, height=30,
            command=self.toggle_pause, state='disabled'
        )
        self.btn_pause.pack(side='right', padx=(5, 0))
        self.btn_stop = ctk.CTkButton(
            self.queue_controls, text="Stop Download",
            fg_color=C['pink'], width=120, height=30,
            command=self.cancel_current, state='disabled'
        )
        self.btn_stop.pack(side='right')
        self.lbl_batches_left = ctk.CTkLabel(
            self.queue_controls, text="Batches Left: 0",
            font=('Arial', 12, 'bold'), text_color=C['pink']
        )
        self.lbl_batches_left.pack(side='right', padx=10)
        self.lbl_total_left = ctk.CTkLabel(
            self.queue_controls, text="Total Left: 0",
            font=('Arial', 12, 'bold'), text_color=C['cyan']
        )
        self.lbl_total_left.pack(side='right', padx=10)

        self.progress_bar = ctk.CTkProgressBar(
            self.frame_queue, height=15, progress_color=C['cyan']
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill='x', pady=10)
        self.log_box = ctk.CTkTextbox(
            self.frame_queue, fg_color=C['card'],
            font=('Consolas', 12), height=100
        )
        self.log_box.pack(fill='x', pady=(0, 10))
        ctk.CTkLabel(
            self.frame_queue, text="PENDING QUEUE",
            font=('Arial', 20, 'bold'), text_color=C['dim']
        ).pack(anchor='w', pady=10)
        self.queue_list_frame = ctk.CTkScrollableFrame(
            self.frame_queue, fg_color=C['card']
        )
        self.queue_list_frame.pack(fill='both', expand=True)
        self.bind_scroll(self.queue_list_frame, self.queue_list_frame)

        # Settings
        ctk.CTkLabel(
            self.frame_settings, text="SETTINGS & PATHS",
            font=('Arial', 20, 'bold')
        ).pack(anchor='w', pady=10)
        self.settings_scroll = ctk.CTkScrollableFrame(
            self.frame_settings, fg_color='transparent'
        )
        self.settings_scroll.pack(fill='both', expand=True, pady=10)
        self.bind_scroll(self.settings_scroll, self.settings_scroll)
        self.setup_bios_ui()

    # ------------------------------------------------------------------
    # The rest of the methods from the original, with fixes applied inline
    # ------------------------------------------------------------------

    def setup_bios_ui(self):
        url = 'https://archive.org/download/retroarch_bios/system.7z'
        ctk.CTkLabel(
            self.frame_bios, text="RETROARCH BIOS PACKS",
            font=('Arial', 20, 'bold'), text_color=C['cyan']
        ).pack(anchor='w', pady=20, padx=20)
        ctk.CTkLabel(
            self.frame_bios,
            text="Download complete BIOS packs for RetroArch and other emulators.\n"
                 "These files are required for many systems to run.",
            font=('Arial', 14), text_color=C['dim'], justify='left'
        ).pack(anchor='w', padx=20, pady=(0, 30))
        dl_frame = ctk.CTkFrame(self.frame_bios, fg_color=C['card'])
        dl_frame.pack(fill='x', padx=20, pady=10)
        ctk.CTkLabel(
            dl_frame, text="RetroArch System BIOS Pack (Complete)",
            font=('Arial', 16, 'bold'), text_color='white'
        ).pack(side='left', padx=20, pady=20)
        ctk.CTkButton(
            dl_frame, text="Download",
            fg_color=C['cyan'], text_color='black',
            font=('Arial', 14, 'bold'),
            command=lambda: self.queue_direct_item(
                "RetroArch_BIOS_Pack", url, "system.7z"
            )
        ).pack(side='right', padx=20)

    def queue_direct_item(self, name, url, filename=None):
        browser = ThemedDirBrowser(self, title=f"Select Save Location for {name}")
        local_dir = browser.result
        if not local_dir:
            return
        if not os.access(local_dir, os.W_OK):
            CustomPopup(self, "Permission Error", f"Cannot write to:\n{local_dir}", ["OK"])
            return
        dest = os.path.join(local_dir, filename or f"{name}.zip")
        self.download_list.append({
            'url': url, 'path': dest, 'name': name,
            'size_mb': 0, 'folder': local_dir, 'console_type': None
        })
        self.log(f"QUEUED: {name}")
        self.show_queue()
        self.render_queue_list()
        if not self.is_downloading:
            threading.Thread(target=self.process_queue, daemon=True).start()

    def render_home_grid(self):
        for w in self.home_widgets:
            w.destroy()
        self.home_widgets = []
        MAX_COLS = 3
        self.grid_consoles.grid_columnconfigure((0, 1, 2), weight=1)
        GROUPS = [
            ('SONY',      ['PlayStation 1', 'PlayStation 2', 'PlayStation 3', 'PSP']),
            ('NINTENDO',  ['NES', 'SNES', 'N64', 'N64DD',
                           'Game Boy', 'Game Boy Color', 'GBA',
                           'GameCube', 'Wii', 'Wii U',
                           'Nintendo DS', 'Nintendo 3DS', 'New Nintendo 3DS',
                           'Virtual Boy', 'Famicom Disk System']),
            ('SEGA',      ['Mega Drive', 'Master System', 'Saturn', 'Dreamcast',
                           'Mega CD', 'Game Gear', 'Sega 32X', 'SG-1000']),
            ('MICROSOFT', ['Xbox', 'Xbox 360']),
            ('SNK',       ['Neo Geo CD', 'Neo Geo Pocket', 'Neo Geo Pocket Color']),
            ('NEC',       ['PC Engine', 'PC Engine SG', 'PC Engine CD', 'PC-FX']),
            ('ATARI',     ['Atari 2600', 'Atari 5200', 'Atari 7800',
                           'Atari Lynx', 'Atari Jaguar', 'Atari Jaguar CD']),
            ('OTHER',     ['3DO', 'CD-i', 'WonderSwan', 'WonderSwan Color',
                           'Amiga CD32', 'ColecoVision', 'Intellivision',
                           'Vectrex', 'MSX', 'MSX2']),
            ('ARCADE',    ['TeknoParrot']),
        ]
        current_row = 0
        for group_name, console_list in GROUPS:
            header = ctk.CTkLabel(
                self.grid_consoles, text=group_name,
                font=('Arial', 14, 'bold'), text_color=C['cyan'], anchor='w'
            )
            header.grid(
                row=current_row, column=0, columnspan=MAX_COLS,
                sticky='w', padx=20, pady=5
            )
            self.bind_scroll(header, self.grid_consoles)
            self.home_widgets.append(header)
            current_row += 1
            col = 0
            for name in console_list:
                if name not in CONSOLES:
                    continue
                btn = ctk.CTkButton(
                    self.grid_consoles, text=f"\n{name}",
                    image=self.console_icons.get(name),
                    compound='top', width=150, height=150,
                    fg_color=C['card'], font=('Arial', 14, 'bold'),
                    hover_color=C['pink'],
                    command=lambda p=CONSOLES[name]: self.jump_to(p)
                )
                btn.grid(row=current_row, column=col, padx=10, pady=10, sticky='nsew')
                self.bind_scroll(btn, self.grid_consoles)
                self.home_widgets.append(btn)
                col += 1
                if col >= MAX_COLS:
                    col = 0
                    current_row += 1
            if col > 0:
                current_row += 1

    def jump_to(self, p):
        self.refresh_dir(p)
        self.show_browser()

    def show_loader(self):
        self.list_frame.pack_forget()
        self.page_controls.pack_forget()
        self.btn_dl.pack_forget()
        self.btn_dl_all.pack_forget()
        self.loading_frame.pack(fill='both', expand=True, pady=10)
        self.loading_bar.start()

    def hide_loader(self):
        self.loading_bar.stop()
        self.loading_frame.pack_forget()
        self.list_frame.pack(fill='both', expand=True, pady=10)
        self.page_controls.pack(fill='x', pady=5)
        self.btn_dl.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.btn_dl_all.pack(side='right', fill='x', expand=True, padx=(5, 0))

    def hide_all(self):
        # Always dismiss any floating tooltip when navigating away
        if self.tooltip_job:
            self.after_cancel(self.tooltip_job)
            self.tooltip_job = None
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except Exception:
                pass
            self.tooltip_window = None

        for frame in [
            self.frame_home, self.frame_browser, self.frame_queue,
            self.frame_settings, self.frame_bios, self.frame_library,
            self.frame_details, self.frame_achievements
        ]:
            frame.grid_forget()
        self.search_container.grid_forget()
        for btn in [
            self.btn_home, self.btn_library, self.btn_browser,
            self.btn_queue, self.btn_settings, self.btn_bios, self.btn_ra
        ]:
            btn.configure(fg_color='transparent', text_color='white')

    def show_home(self):
        self.hide_all()
        self.frame_home.grid(row=1, column=0, sticky='nsew')
        self.btn_home.configure(fg_color=C['cyan'], text_color='black')

    def show_browser(self):
        self.hide_all()
        self.search_container.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        self.frame_browser.grid(row=1, column=0, sticky='nsew')
        self.btn_browser.configure(fg_color=C['cyan'], text_color='black')
        self.update_storage_stats()

    def show_queue(self):
        self.hide_all()
        self.frame_queue.grid(row=1, column=0, sticky='nsew')
        self.btn_queue.configure(fg_color=C['cyan'], text_color='black')
        self.render_queue_list()

    def show_settings(self):
        self.hide_all()
        self.frame_settings.grid(row=1, column=0, sticky='nsew')
        self.btn_settings.configure(fg_color=C['cyan'], text_color='black')
        self.render_settings()

    def show_bios(self):
        self.hide_all()
        self.frame_bios.grid(row=1, column=0, sticky='nsew')
        self.btn_bios.configure(fg_color=C['cyan'], text_color='black')

    def show_library(self):
        self.hide_all()
        self.frame_library.grid(row=1, column=0, sticky='nsew')
        self.btn_library.configure(fg_color=C['cyan'], text_color='black')
        self._library_games = None  # force fresh scan on each visit
        self._load_library_async()

    def _load_library_async(self):
        """Show spinner immediately, scan ROM folders in background, render when done."""
        # Clear old content and show loading indicator right away
        for w in self.library_widgets:
            w.destroy()
        self.library_widgets = []

        loading_lbl = ctk.CTkLabel(
            self.lib_scroll,
            text="Scanning library...",
            font=('Arial', 14, 'bold'), text_color=C['dim']
        )
        loading_lbl.pack(pady=(40, 8))
        loading_bar = ctk.CTkProgressBar(
            self.lib_scroll, width=300, height=10,
            progress_color=C['cyan'], mode='indeterminate'
        )
        loading_bar.pack(pady=(0, 40))
        loading_bar.start()
        self.library_widgets.extend([loading_lbl, loading_bar])

        def _scan():
            games = self.scan_library()
            self._library_games = games   # cache for tab switching
            self.after(0, lambda: self._render_library_with_games(games))

        threading.Thread(target=_scan, daemon=True).start()

    def show_achievements(self):
        self.hide_all()
        self.frame_achievements.grid(row=1, column=0, sticky='nsew')
        self.btn_ra.configure(fg_color=C['cyan'], text_color='black')
        self.render_achievements()

    def render_achievements(self):
        for w in self.frame_achievements.winfo_children():
            w.destroy()
        header_row = ctk.CTkFrame(self.frame_achievements, fg_color='transparent')
        header_row.pack(fill='x', pady=(10, 20))
        ctk.CTkLabel(
            header_row, text="RETROACHIEVEMENTS",
            font=('Arial', 20, 'bold'), text_color=C['cyan']
        ).pack(side='left', padx=5)
        ctk.CTkButton(
            header_row, text="Browse RA-Supported ROMs ↗",
            fg_color=C['card'], hover_color=C['pink'],
            command=lambda: self.jump_to("RetroAchievements/")
        ).pack(side='right', padx=5)
        if not self.ra.api_key:
            ctk.CTkLabel(
                self.frame_achievements,
                text="Please configure your RA API Key in Settings.",
                text_color=C['dim']
            ).pack(pady=20)
            return
        loading = ctk.CTkLabel(
            self.frame_achievements,
            text="FETCHING PROFILE DATA...", font=('Arial', 14)
        )
        loading.pack(pady=20)

        def _load():
            error_msg, data = self.ra.get_user_summary()
            self.after(0, lambda: loading.destroy())
            if data:
                self.after(0, lambda: self.draw_ra_profile(data))
            else:
                self.after(0, lambda e=error_msg: ctk.CTkLabel(
                    self.frame_achievements,
                    text=f"Error: {e}", text_color=C['pink']
                ).pack())
        threading.Thread(target=_load, daemon=True).start()

    def draw_ra_profile(self, data):
        profile_card = ctk.CTkFrame(self.frame_achievements, fg_color=C['card'])
        profile_card.pack(fill='x', padx=10, pady=10)
        user_info = ctk.CTkFrame(profile_card, fg_color='transparent')
        user_info.pack(fill='x', padx=20, pady=20)
        ctk.CTkLabel(
            user_info, text=data.get('User', 'Unknown'),
            font=('Arial', 24, 'bold'), text_color=C['cyan']
        ).pack(side='left')
        stats_frame = ctk.CTkFrame(profile_card, fg_color='transparent')
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        for label, val in [
            ("Points", data.get('TotalPoints', '0')),
            ("Ratio", data.get('RetroRatio', '0')),
            ("Rank", data.get('Rank', 'N/A')),
            ("Completed", data.get('TotalGamesCompleted', '0'))
        ]:
            s_box = ctk.CTkFrame(stats_frame, fg_color=C['bg'], corner_radius=10)
            s_box.pack(side='left', padx=5, fill='x', expand=True)
            ctk.CTkLabel(
                s_box, text=label, font=('Arial', 10), text_color=C['dim']
            ).pack(pady=(5, 0))
            ctk.CTkLabel(
                s_box, text=val, font=('Arial', 14, 'bold'), text_color='white'
            ).pack(pady=(0, 5))

    def show_game_details(self, game):
        self.hide_all()
        self.frame_details.grid(row=1, column=0, sticky='nsew')
        for w in self.frame_details.winfo_children():
            w.destroy()
        header = ctk.CTkFrame(self.frame_details, fg_color='transparent')
        header.pack(fill='x', pady=10)
        ctk.CTkButton(
            header, text="⬅ Back to Library", width=120,
            command=self.show_library, fg_color=C['card']
        ).pack(side='left')
        content = ctk.CTkFrame(self.frame_details, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=20)
        left_col = ctk.CTkFrame(content, fg_color='transparent')
        left_col.pack(side='left', fill='y', padx=(0, 20))
        if game['cover'] and os.path.exists(game['cover']):
            try:
                pil = Image.open(game['cover'])
                w, h = pil.size
                ratio = 350 / h
                img = ctk.CTkImage(
                    light_image=pil, dark_image=pil,
                    size=(int(w * ratio), 350)
                )
                lbl_img = ctk.CTkLabel(left_col, text="", image=img)
            except Exception:
                lbl_img = ctk.CTkLabel(
                    left_col, text="[No Image]",
                    width=200, height=300, fg_color=C['card']
                )
        else:
            icon = self.console_icons.get(game['console'])
            lbl_img = (
                ctk.CTkLabel(left_col, text="", image=icon)
                if icon else ctk.CTkLabel(left_col, text="No Art")
            )
        lbl_img.pack(pady=10)
        ctk.CTkButton(
            left_col, text="Open File Location",
            fg_color=C['cyan'], text_color='black',
            command=lambda: self.launch_game_folder(game['path'])
        ).pack(fill='x', pady=5)
        ctk.CTkButton(
            left_col, text="Delete Game",
            fg_color=C['pink'], hover_color='#990033',
            command=lambda: self.confirm_delete(game)
        ).pack(fill='x', pady=5)
        right_col = ctk.CTkScrollableFrame(content, fg_color='transparent')
        right_col.pack(side='left', fill='both', expand=True)
        ctk.CTkLabel(
            right_col, text=game['name'],
            font=('Arial', 28, 'bold'), text_color='white',
            wraplength=600, justify='left'
        ).pack(anchor='w', pady=(10, 5))
        ctk.CTkLabel(
            right_col, text=f"Console: {game['console']}",
            font=('Arial', 14, 'bold'), text_color=C['cyan']
        ).pack(anchor='w', pady=(0, 20))
        self.lbl_genre = ctk.CTkLabel(
            right_col, text="Genre: Loading...",
            font=('Arial', 14), text_color=C['dim']
        )
        self.lbl_genre.pack(anchor='w', pady=2)
        self.lbl_dev = ctk.CTkLabel(
            right_col, text="Developer: Loading...",
            font=('Arial', 14), text_color=C['dim']
        )
        self.lbl_dev.pack(anchor='w', pady=2)
        self.lbl_date = ctk.CTkLabel(
            right_col, text="Release Date: Loading...",
            font=('Arial', 14), text_color=C['dim']
        )
        self.lbl_date.pack(anchor='w', pady=2)
        ctk.CTkLabel(
            right_col, text="\nDescription:",
            font=('Arial', 16, 'bold'), text_color='white'
        ).pack(anchor='w', pady=(20, 5))
        self.lbl_desc = ctk.CTkLabel(
            right_col, text="Loading summary from IGDB...",
            font=('Arial', 14), text_color='white',
            wraplength=600, justify='left'
        )
        self.lbl_desc.pack(anchor='w')
        threading.Thread(
            target=lambda: self.fetch_details_for_page(game['name']),
            daemon=True
        ).start()

    def fetch_details_for_page(self, game_name):
        # FIXED: strip extension before IGDB query
        base_name = os.path.splitext(game_name)[0]
        clean_name = base_name.split('(')[0].split('[')[0].strip()
        data = self.game_metadata_cache.get(clean_name) or self.twitch.search_game(clean_name)
        if data:
            genre = ", ".join(g['name'] for g in data.get('genres', []))
            dev = "Unknown"
            for c in data.get('involved_companies', []):
                if c.get('company'):
                    dev = c['company']['name']
                    break
            date = "Unknown"
            if 'first_release_date' in data:
                date = datetime.fromtimestamp(data['first_release_date']).strftime('%Y-%m-%d')
            summary = data.get('summary', 'No description available.')
            self.after(0, lambda: self.update_details_ui(genre or "Unknown", dev, date, summary))
        else:
            self.after(0, lambda: self.update_details_ui(
                "Unknown", "Unknown", "Unknown", "Could not find details on IGDB."
            ))

    def update_details_ui(self, genre, dev, date, summary):
        try:
            self.lbl_genre.configure(text=f"Genre: {genre}")
            self.lbl_dev.configure(text=f"Developer: {dev}")
            self.lbl_date.configure(text=f"Release Date: {date}")
            self.lbl_desc.configure(text=summary)
        except Exception:
            pass

    def confirm_delete(self, game):
        ask = CustomPopup(
            self, "Delete Game",
            f"Are you sure you want to delete:\n{game['name']}?\n\nThis cannot be undone.",
            ["Delete", "Cancel"]
        )
        if ask.result == "Delete":
            try:
                folder_path = os.path.dirname(os.path.abspath(game['path']))
                if os.path.exists(game['path']):
                    os.remove(game['path'])
                if game['cover'] and os.path.exists(game['cover']):
                    os.remove(game['cover'])
                try:
                    if os.path.exists(folder_path) and not os.listdir(folder_path):
                        os.rmdir(folder_path)
                except Exception:
                    pass
                # Invalidate ownership cache for this folder
                self._ownership_cache.invalidate(os.path.dirname(folder_path))
                self.show_library()
                CustomPopup(self, "Deleted", "Game files deleted successfully.", ["OK"])
            except Exception as e:
                CustomPopup(self, "Error", f"Could not delete: {e}", ["OK"])

    def scan_library(self):
        games = []
        valid_exts = (
            '.iso', '.cso', '.rvz', '.zip', '.7z', '.chd',
            '.wbfs', '.bin', '.nds', '.cia', '.gba', '.sfc', '.smc',
            '.parrot',
        )
        found_consoles = set()

        # FIXED: only iterate known console paths, not all config keys
        for remote_path in CONSOLES.values():
            local_path = self.folder_mappings.get(remote_path)
            if not local_path or not isinstance(local_path, str):
                continue
            if not os.path.exists(local_path):
                continue

            console_name = "Unknown"
            for k, v in CONSOLES.items():
                if v == remote_path:
                    console_name = k
                    break

            files_to_check = []
            try:
                with os.scandir(local_path) as it:
                    for entry in it:
                        if entry.is_file(follow_symlinks=False):
                            files_to_check.append((entry.name, entry.path))
                        elif entry.is_dir(follow_symlinks=False):
                            try:
                                with os.scandir(entry.path) as sub:
                                    for s in sub:
                                        if s.is_file(follow_symlinks=False):
                                            files_to_check.append((s.name, s.path))
                            except OSError:
                                pass
            except OSError:
                continue

            for fname, fpath in files_to_check:
                if fname.lower().endswith(valid_exts):
                    if _is_myrifetch_stub(fpath):
                        continue
                    base_name = os.path.splitext(fname)[0]
                    folder = os.path.dirname(fpath)
                    img_path = None
                    for ext in ('.jpg', '.jpeg', '.png'):
                        candidate = os.path.join(folder, base_name + ext)
                        if os.path.exists(candidate):
                            img_path = candidate
                            break

                    # Pre-load cover image here in the background scan thread
                    # so the main thread never blocks on PIL I/O when rendering.
                    ctk_img = None
                    if img_path:
                        try:
                            pil = Image.open(img_path)
                            w_px, h_px = pil.size
                            ratio = 150 / h_px
                            ctk_img = ctk.CTkImage(
                                light_image=pil, dark_image=pil,
                                size=(max(1, int(w_px * ratio)), 150)
                            )
                        except Exception:
                            pass

                    found_consoles.add(console_name)
                    games.append({
                        'name': base_name, 'path': fpath,
                        'console': console_name, 'cover': img_path,
                        'ctk_img': ctk_img,
                    })

        current_sort = self.lib_sort_var.get()
        sorted_consoles = sorted(found_consoles)
        # Safe to call from background thread — schedule on main thread
        self.after(0, lambda sc=sorted_consoles, cs=current_sort:
            self._build_lib_tabs(sc, cs))
        return games

    def _build_lib_tabs(self, sorted_consoles, current_sort: str):
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

    def render_library_grid(self, _=None):
        """Re-render the grid. Uses cached games if available, else rescans."""
        if self._library_games is not None:
            self._render_library_with_games(self._library_games)
        else:
            self._load_library_async()

    def _render_library_with_games(self, games):
        """Called on the main thread with pre-scanned, pre-loaded game data."""
        for w in self.library_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self.library_widgets = []

        filter_console = self.lib_sort_var.get()
        filtered = [
            g for g in games
            if filter_console == "All" or g['console'] == filter_console
        ]
        if not filtered:
            lbl = ctk.CTkLabel(
                self.lib_scroll,
                text="No games found in your mapped folders.",
                font=('Arial', 14), text_color=C['dim']
            )
            lbl.pack(pady=40)
            self.library_widgets.append(lbl)
            return
        COLUMNS = 4
        self.lib_scroll.grid_columnconfigure(tuple(range(COLUMNS)), weight=1)
        for i, game in enumerate(filtered):
            row_idx = i // COLUMNS
            col = i % COLUMNS
            card = ctk.CTkFrame(self.lib_scroll, fg_color=C['bg'])
            card.grid(row=row_idx, column=col, padx=10, pady=10, sticky='nsew')
            self.library_widgets.append(card)
            # Use pre-loaded image from background thread; fall back to console icon
            ctk_img = game.get('ctk_img') or self.console_icons.get(game['console'])
            raw_name = game['name']
            if len(raw_name) > 36:
                mid = raw_name[:18].rfind(' ')
                if mid < 8:
                    mid = 18
                line1 = raw_name[:mid].rstrip()
                line2 = raw_name[mid:mid + 18].strip()
                if len(raw_name) > mid + 18:
                    line2 = line2.rstrip()[:15].rstrip() + '...'
                display_name = f"\n{line1}\n{line2}"
            elif len(raw_name) > 18:
                mid = raw_name[:18].rfind(' ')
                if mid < 8:
                    mid = 18
                line1 = raw_name[:mid].rstrip()
                line2 = raw_name[mid:].strip()
                display_name = f"\n{line1}\n{line2}"
            else:
                display_name = f"\n{raw_name}"
            btn = ctk.CTkButton(
                card, text=display_name,
                image=ctk_img, compound='top',
                fg_color='transparent', hover_color=C['card'],
                text_color='white', font=('Arial', 11),
                command=lambda g=game: self.show_game_details(g)
            )
            btn.pack(fill='both', expand=True, padx=5, pady=5)
            clean_name = game['name'].split('(')[0].split('[')[0].strip()
            btn.bind("<Enter>", lambda e, n=clean_name: self.on_hover_enter(e, n))
            btn.bind("<Leave>", self.on_hover_leave)

            if not game.get('cover'):
                scrape_btn = ctk.CTkButton(
                    card, text="🎨 Scrape Art",
                    height=22, fg_color=C['card'],
                    hover_color=C['cyan'], text_color=C['dim'],
                    font=('Arial', 10),
                    command=lambda g=game, c=card: self._scrape_single_and_refresh(g, c)
                )
                scrape_btn.pack(fill='x', padx=5, pady=(0, 5))
                self.library_widgets.append(scrape_btn)

    def scrape_missing_art(self):
        """Scrape ScreenScraper media for every library game that has no cover image."""
        ss = self._get_ss_manager()
        if not ss:
            CustomPopup(
                self, "No ScreenScraper Credentials",
                "ScreenScraper username and password are required.\n"
                "Add them in Settings → ScreenScraper.", ["OK"]
            )
            return

        confirm = CustomPopup(
            self, "Scrape Missing Art",
            "Scan library and fetch cover art for all games without art?\n\n"
            "This uses ScreenScraper and may take a while.",
            ["Scrape", "Cancel"]
        )
        if confirm.result != "Scrape":
            return

        if hasattr(self, 'btn_scrape_all'):
            self.btn_scrape_all.configure(text="Scanning...", state='disabled')

        def _start():
            games = self.scan_library()
            missing = [g for g in games if not g.get('cover')]
            self.after(0, lambda: self._do_scrape_missing(missing))

        threading.Thread(target=_start, daemon=True).start()

    def _do_scrape_missing(self, missing):
        if not missing:
            CustomPopup(self, "All Art Present",
                        "All games in your library already have cover art.", ["OK"])
            if hasattr(self, 'btn_scrape_all'):
                self.btn_scrape_all.configure(
                    text="🎨 Scrape Missing Art", state='normal')
            return

        if hasattr(self, 'btn_scrape_all'):
            self.btn_scrape_all.configure(
                text=f"Scraping 0/{len(missing)}...", state='disabled')

        completed = [0]
        found = [0]

        def _on_done(success):
            completed[0] += 1
            if success:
                found[0] += 1
            n = completed[0]
            total = len(missing)
            if hasattr(self, 'btn_scrape_all'):
                self.after(0, lambda: self.btn_scrape_all.configure(
                    text=f"Scraping {n}/{total}...", state='disabled'
                ))
            if n >= total:
                self.after(0, self._scrape_all_done)

        def _run():
            for game in missing:
                time.sleep(0.3)
                self.scrape_game_art(game, done_cb=_on_done)

        threading.Thread(target=_run, daemon=True).start()

    def _scrape_all_done(self):
        if hasattr(self, 'btn_scrape_all'):
            self.btn_scrape_all.configure(
                text="🎨 Scrape Missing Art", state='normal'
            )
        self.render_library_grid()

    def _get_ss_manager(self) -> ScreenScraperManager | None:
        """Return a configured ScreenScraperManager or None if not set up."""
        ss_user = str(self.folder_mappings.get('ss_user', '')).strip()
        ss_pass = str(self.folder_mappings.get('ss_password', '')).strip()
        if not ss_user or not ss_pass:
            return None
        return ScreenScraperManager(ss_user, ss_pass)

    def scrape_game_art(self, game, done_cb=None):
        """
        Fetch media and metadata from ScreenScraper for a single game.
        Saves:
          - sstitle  → images/<n>-image.png  (<image>)
          - box-3D   → <n>.jpg next to ROM   (<thumbnail>)
          - marquee  → images/<n>-marquee.png
          - video    → videos/<n>-video.mp4
        Updates gamelist.xml with all metadata tags.
        Calls done_cb(success: bool) on the main thread when finished.
        """
        ss = self._get_ss_manager()
        if not ss:
            CustomPopup(
                self, "No ScreenScraper Credentials",
                "ScreenScraper username and password are required.\n"
                "Add them in Settings → ScreenScraper.", ["OK"]
            )
            return

        rom_dir = os.path.dirname(game.get('path', ''))
        config = self.folder_mappings

        def _fetch():
            meta = ss.scrape_game(game, rom_dir, config, log_cb=self._debug_log)
            success = bool(
                meta.get('image') or meta.get('thumbnail') or meta.get('desc')
            )
            if success and meta.get('thumbnail'):
                game['cover'] = meta['thumbnail']
            if success:
                self._writeback_scraped_meta(game, rom_dir, meta)
            self.after(0, lambda: done_cb and done_cb(success))

        threading.Thread(target=_fetch, daemon=True).start()

    def _writeback_scraped_meta(
        self, game: dict, rom_dir: str, meta: dict
    ) -> bool:
        """
        Update gamelist.xml with full scraped metadata:
        <image>, <thumbnail>, <marquee>, <video>,
        <desc>, <genre>, <developer>, <publisher>,
        <releasedate>, <players>, <rating>.
        """
        gamelist_path = os.path.join(rom_dir, 'gamelist.xml')
        if not os.path.isfile(gamelist_path):
            return False
        try:
            tree = ET.parse(gamelist_path)
            root = tree.getroot()
        except Exception:
            return False

        rom_base = os.path.splitext(
            os.path.basename(game.get('path', ''))
        )[0].lower()

        updated = False
        for game_el in root.findall('game'):
            path_el = game_el.find('path')
            if path_el is None:
                continue
            entry_base = os.path.splitext(
                os.path.basename((path_el.text or '').lstrip('./\\'))
            )[0].lower()
            if entry_base != rom_base:
                continue

            tag_map = {
                'image':       meta.get('image'),
                'thumbnail':   meta.get('thumbnail'),
                'marquee':     meta.get('marquee'),
                'video':       meta.get('video'),
                'desc':        meta.get('desc'),
                'genre':       meta.get('genre'),
                'developer':   meta.get('developer'),
                'publisher':   meta.get('publisher'),
                'releasedate': meta.get('releasedate'),
                'players':     meta.get('players'),
                'rating':      meta.get('rating'),
            }
            for tag, value in tag_map.items():
                if not value:
                    continue
                if os.path.isabs(str(value)):
                    try:
                        rel = os.path.relpath(value, rom_dir)
                        value = './' + rel.replace('\\', '/')
                    except ValueError:
                        pass
                el = game_el.find(tag)
                if el is None:
                    el = ET.SubElement(game_el, tag)
                el.text = str(value)

            # Remove stub genre if a real genre was scraped
            if meta.get('genre'):
                for g_el in game_el.findall('genre'):
                    if (g_el.text or '').strip().lower() == 'available to download':
                        game_el.remove(g_el)
                        break

            updated = True
            break

        if not updated:
            return False

        tmp = gamelist_path + '.tmp'
        try:
            tree.write(tmp, encoding='utf-8', xml_declaration=True)
            os.replace(tmp, gamelist_path)
        except Exception:
            try:
                os.remove(tmp)
            except OSError:
                pass
            return False
        return True

    def _scrape_single_and_refresh(self, game, card):
        """Scrape art for one game card and refresh the library on completion."""
        for w in card.winfo_children():
            if isinstance(w, ctk.CTkButton) and 'Scrape' in (w.cget('text') or ''):
                w.configure(text="Scraping...", state='disabled')
                break

        def _done(success):
            if success:
                self.render_library_grid()
            else:
                for w in card.winfo_children():
                    if isinstance(w, ctk.CTkButton) and 'Scraping' in (w.cget('text') or ''):
                        w.configure(text="Not found", state='disabled',
                                    text_color=C['pink'])
                        self.after(2000, lambda btn=w: btn.configure(
                            text="🎨 Scrape Art", state='normal',
                            text_color=C['dim']
                        ))
                        break

        self.scrape_game_art(game, done_cb=_done)

    def on_hover_enter(self, event, game_name):
        if not self.twitch.client_id:
            return
        if self.tooltip_job:
            self.after_cancel(self.tooltip_job)
        self.tooltip_job = self.after(
            600, lambda: self.fetch_and_show_tooltip(game_name, event)
        )

    def on_hover_leave(self, event):
        if self.tooltip_job:
            self.after_cancel(self.tooltip_job)
        self.tooltip_job = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def fetch_and_show_tooltip(self, game_name, event):
        if game_name in self.game_metadata_cache:
            self.show_tooltip_window(game_name, self.game_metadata_cache[game_name])
            return

        def _fetch():
            data = self.twitch.search_game(game_name)
            if not data:
                self.game_metadata_cache[game_name] = None
                return
            details = {}
            if 'first_release_date' in data:
                details['Released'] = datetime.fromtimestamp(
                    data['first_release_date']
                ).strftime('%Y-%m-%d')
            if 'genres' in data:
                details['Genre'] = ", ".join(
                    g['name'] for g in data['genres'][:2]
                )
            for comp in data.get('involved_companies', []):
                if comp.get('company'):
                    details['Developer'] = comp['company']['name']
                    break
            self.game_metadata_cache[game_name] = details
            self.after(0, lambda: self.show_tooltip_window(game_name, details))
        threading.Thread(target=_fetch, daemon=True).start()

    def show_tooltip_window(self, title, details):
        if not details:
            return
        x, y = self.winfo_pointerx(), self.winfo_pointery()
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = GameTooltip(self, title, details, x, y)

    def toggle_pause(self):
        if self.is_downloading:
            if self._pause_event.is_set():
                self._pause_event.clear()  # paused
                self.btn_pause.configure(
                    text="Resume Download",
                    fg_color=C['success'], text_color='black'
                )
                self.log("⏸ DOWNLOAD PAUSED")
            else:
                self._pause_event.set()  # resumed
                self.btn_pause.configure(
                    text="Pause Download",
                    fg_color=C['card'], text_color='white'
                )
                self.log("▶ RESUMING...")

    def cancel_current(self):
        if self.is_downloading:
            self._cancel_event.set()
            self._pause_event.set()  # unblock any paused workers
            # FIXED: clear deque in-place (thread sees the empty deque)
            self.pending_stage_queue.clear()
            self.download_list.clear()
            self.btn_stop.configure(state='disabled', text='Stopping...')
            self.log("🛑 STOPPING DOWNLOAD & WIPING ALL QUEUES...")
            self.update_batch_labels()
            self.after(0, self.render_queue_list)

    def render_settings(self):
        for widget in self.settings_widgets:
            widget.destroy()
        self.settings_widgets = []

        def _row(label_text, cyan=True):
            row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
            row.pack(fill='x', pady=10)
            self.settings_widgets.append(row)
            ctk.CTkLabel(
                row, text=label_text, width=160, anchor='w',
                font=('Arial', 13, 'bold'),
                text_color=C['cyan'] if cyan else 'white'
            ).pack(side='left', padx=10)
            return row

        # Theme
        theme_row = _row("APP THEME")
        current_theme = self.folder_mappings.get('app_theme', 'Cyber Dark')
        self.theme_var = ctk.StringVar(value=current_theme)
        ctk.CTkOptionMenu(
            theme_row, variable=self.theme_var,
            values=list(THEMES.keys()), command=self.change_theme,
            fg_color=C['bg'], button_color=C['cyan'],
            button_hover_color=C['pink'], text_color='white', corner_radius=20
        ).pack(side='left', padx=10)
        ctk.CTkLabel(
            theme_row, text="(Restart Required)",
            text_color=C['dim'], font=('Arial', 10)
        ).pack(side='left', padx=5)

        # Default region (browser filter)
        region_row = _row("DEFAULT REGION")
        current_region = self.folder_mappings.get('default_region', 'All Regions')
        self.default_region_var = ctk.StringVar(value=current_region)
        ctk.CTkOptionMenu(
            region_row, variable=self.default_region_var,
            values=['All Regions', 'USA', 'Europe', 'Japan', 'World'],
            command=self.change_default_region,
            fg_color=C['bg'], button_color=C['cyan'],
            button_hover_color=C['pink'], text_color='white', corner_radius=20
        ).pack(side='left', padx=10)

        # Sync region preference (controls which region variants appear in gamelist)
        sync_reg_row = _row("SYNC REGION FILTER")
        ctk.CTkLabel(
            sync_reg_row,
            text="Controls which region variants are synced as stubs (Best = USA→World→Europe→Japan)",
            text_color=C['dim'], font=('Arial', 9)
        ).pack(side='left', padx=(0, 8))
        current_sync_reg = self.folder_mappings.get('sync_region_pref', 'Best')
        self.sync_region_var = ctk.StringVar(value=current_sync_reg)
        ctk.CTkOptionMenu(
            sync_reg_row, variable=self.sync_region_var,
            values=['Best', 'All', 'USA', 'Europe', 'Japan'],
            command=lambda v: (
                self.folder_mappings.update({'sync_region_pref': v}),
                self.save_config()
            ),
            fg_color=C['bg'], button_color=C['cyan'],
            button_hover_color=C['pink'], text_color='white', corner_radius=20
        ).pack(side='left', padx=10)

        # Font size
        font_row = _row("BROWSER TEXT SIZE")
        self.font_size_var = tk.IntVar(
            value=self.folder_mappings.get('font_size', 12)
        )
        self.font_slider = ctk.CTkSlider(
            font_row, from_=10, to=24, number_of_steps=14,
            variable=self.font_size_var, command=self.update_font_size
        )
        self.font_slider.pack(side='left', padx=10, fill='x', expand=True)
        self.lbl_font_val = ctk.CTkLabel(
            font_row, text=str(self.font_size_var.get()), width=30
        )
        self.lbl_font_val.pack(side='left', padx=5)

        # Toggles
        for label, key, default in [
            ("FINISH CHIME", 'notif_sound', True),
            ("FILTER DEMOS", 'filter_demos', False),
            ("FILTER REVISIONS", 'filter_revs', False),
            ("GAME SUBFOLDERS", 'subfolder_per_game', True),
            ("DEBUG LOGGING", 'debug_mode', False),
        ]:
            tr = _row(label)
            var = tk.BooleanVar(value=self.folder_mappings.get(key, default))
            setattr(self, f'_{key}_var', var)
            ctk.CTkSwitch(
                tr, text="", variable=var,
                command=lambda k=key, v=var: self._toggle_bool_setting(k, v),
                progress_color=C['cyan']
            ).pack(side='left', padx=10)

        # Open log file
        def _open_log():
            if os.path.exists(LOG_FILE):
                if os.name == 'nt':
                    os.startfile(LOG_FILE)
                else:
                    subprocess.Popen(['xdg-open', LOG_FILE])
        log_row = _row("DEBUG LOG FILE", cyan=False)
        ctk.CTkButton(
            log_row, text="📋 Open Log",
            fg_color=C['card'], hover_color=C['cyan'],
            font=('Arial', 12), width=120,
            command=_open_log
        ).pack(side='left', padx=10)
        ctk.CTkLabel(
            log_row,
            text=LOG_FILE, text_color=C['dim'], font=('Arial', 9)
        ).pack(side='left', padx=5)
        self.settings_widgets.append(log_row)

        sep = ctk.CTkFrame(self.settings_scroll, fg_color=C['dim'], height=1)
        sep.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(sep)

        # Console paths
        for name, path in CONSOLES.items():
            row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
            row.pack(fill='x', pady=5)
            self.settings_widgets.append(row)
            ctk.CTkLabel(
                row, text=name, width=150, anchor='w',
                font=('Arial', 13, 'bold')
            ).pack(side='left', padx=10)
            current = self.folder_mappings.get(path)
            ctk.CTkLabel(
                row, text=current or "Default (Ask)",
                text_color='white' if current else C['dim'], anchor='w'
            ).pack(side='left', fill='x', expand=True)
            ctk.CTkButton(
                row, text="Change", width=80,
                fg_color=C['bg'], border_width=1,
                border_color=C['cyan'], text_color=C['cyan'],
                command=lambda p=path: self.change_console_path(p)
            ).pack(side='right', padx=10)

        clear_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        clear_row.pack(fill='x', pady=20)
        self.settings_widgets.append(clear_row)
        ctk.CTkButton(
            clear_row, text="Clear All Saved Directories",
            fg_color=C['pink'], hover_color='#990033',
            command=self.clear_saved_folders
        ).pack()

        sep2 = ctk.CTkFrame(self.settings_scroll, fg_color=C['dim'], height=1)
        sep2.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(sep2)

        # CHDMAN section
        ctk.CTkLabel(
            self.settings_scroll, text="CHDMAN COMPRESSION",
            font=('Arial', 14, 'bold'), text_color=C['cyan']
        ).pack(fill='x', pady=(10, 5))
        ctk.CTkLabel(
            self.settings_scroll,
            text="Automatically compress ISO/BIN/CUE to CHD after download.",
            text_color=C['dim'], font=('Arial', 12)
        ).pack(pady=(0, 10))
        row_chd = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        row_chd.pack(fill='x', pady=2)
        self.settings_widgets.append(row_chd)
        ctk.CTkLabel(row_chd, text="CHDMAN Path:", width=100, anchor='w').pack(
            side='left', padx=10
        )
        self.entry_chdman = ctk.CTkEntry(
            row_chd, fg_color=C['bg'], border_color=C['dim']
        )
        current_chd = self.folder_mappings.get('chdman_path', '')
        if not current_chd:
            current_chd = shutil.which('chdman') or ''
        self.entry_chdman.insert(0, current_chd)
        self.entry_chdman.pack(side='left', fill='x', expand=True, padx=10)
        self.entry_chdman.bind('<FocusOut>', lambda e: self.save_chd_settings())
        self.entry_chdman.bind('<Return>', lambda e: self.save_chd_settings())
        ctk.CTkButton(
            row_chd, text="Browse", width=60,
            fg_color=C['card'], command=self.browse_chdman
        ).pack(side='right', padx=10)
        self.chd_vars = {}
        grid_frame = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        grid_frame.pack(fill='x', padx=10, pady=5)
        self.settings_widgets.append(grid_frame)
        for i, (name, key_suffix) in enumerate([
            ('PlayStation 1', 'ps1'), ('PlayStation 2', 'ps2'),
            ('PSP', 'psp'), ('Dreamcast', 'dreamcast')
        ]):
            key = f'use_chdman_{key_suffix}'
            var = tk.BooleanVar(value=self.folder_mappings.get(key, False))
            self.chd_vars[key] = var
            r, c = i // 2, i % 2
            f = ctk.CTkFrame(grid_frame, fg_color='transparent')
            f.grid(row=r, column=c, sticky='w', padx=10, pady=5)
            ctk.CTkLabel(f, text=name, width=100, anchor='w').pack(side='left')
            ctk.CTkSwitch(
                f, text="", variable=var,
                command=self.save_chd_settings,
                progress_color=C['cyan']
            ).pack(side='left')

        sep3 = ctk.CTkFrame(self.settings_scroll, fg_color=C['dim'], height=1)
        sep3.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(sep3)

        # Twitch/IGDB
        ctk.CTkLabel(
            self.settings_scroll, text="TWITCH / IGDB API",
            font=('Arial', 14, 'bold'), text_color=C['cyan']
        ).pack(fill='x', pady=(10, 5))
        for label, attr, key, show in [
            ("Client ID:", 'entry_twitch_id', 'twitch_id', ''),
            ("Client Secret:", 'entry_twitch_secret', 'twitch_secret', '*'),
        ]:
            r = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
            r.pack(fill='x', pady=2)
            self.settings_widgets.append(r)
            ctk.CTkLabel(r, text=label, width=100, anchor='w').pack(
                side='left', padx=10
            )
            entry = ctk.CTkEntry(
                r, fg_color=C['bg'], border_color=C['dim'],
                show=show
            )
            entry.insert(0, self.folder_mappings.get(key, ''))
            entry.pack(side='left', fill='x', expand=True, padx=10)
            setattr(self, attr, entry)
        btn = ctk.CTkButton(
            self.settings_scroll,
            text="Save Keys & Test Connection",
            fg_color=C['cyan'], text_color='black',
            command=self.save_twitch_creds
        )
        btn.pack(pady=10)
        self.settings_widgets.append(btn)

        # RA
        ctk.CTkLabel(
            self.settings_scroll, text="RETROACHIEVEMENTS API",
            font=('Arial', 14, 'bold'), text_color=C['cyan']
        ).pack(fill='x', pady=(20, 5))
        for label, attr, key, show in [
            ("Username:", 'entry_ra_user', 'ra_user', ''),
            ("API Key:", 'entry_ra_key', 'ra_key', '*'),
        ]:
            r = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
            r.pack(fill='x', pady=2)
            self.settings_widgets.append(r)
            ctk.CTkLabel(r, text=label, width=100, anchor='w').pack(
                side='left', padx=10
            )
            entry = ctk.CTkEntry(
                r, fg_color=C['bg'], border_color=C['dim'], show=show
            )
            entry.insert(0, self.folder_mappings.get(key, ''))
            entry.pack(side='left', fill='x', expand=True, padx=10)
            setattr(self, attr, entry)
        btn2 = ctk.CTkButton(
            self.settings_scroll,
            text="Save RetroAchievements Keys",
            fg_color=C['cyan'], text_color='black',
            command=self.save_ra_creds
        )
        btn2.pack(pady=10)
        self.settings_widgets.append(btn2)

        sep4 = ctk.CTkFrame(self.settings_scroll, fg_color=C['dim'], height=1)
        sep4.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(sep4)

        # --- ScreenScraper ---
        ctk.CTkLabel(
            self.settings_scroll, text="SCREENSCRAPER",
            font=('Arial', 14, 'bold'), text_color=C['cyan']
        ).pack(fill='x', pady=(10, 2))
        ctk.CTkLabel(
            self.settings_scroll,
            text="Used for scraping media (box art, screenshots, video, metadata).\n"
                 "Register free at screenscraper.fr — same account you use in RetroBat.",
            font=('Arial', 11), text_color=C['dim'], justify='left'
        ).pack(fill='x', padx=10, pady=(0, 6))
        for label, attr, key, show in [
            ("Username:", 'entry_ss_user',     'ss_user',     ''),
            ("Password:", 'entry_ss_password', 'ss_password', '*'),
        ]:
            r = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
            r.pack(fill='x', pady=2)
            self.settings_widgets.append(r)
            ctk.CTkLabel(r, text=label, width=100, anchor='w').pack(
                side='left', padx=10
            )
            entry = ctk.CTkEntry(
                r, fg_color=C['bg'], border_color=C['dim'], show=show
            )
            entry.insert(0, self.folder_mappings.get(key, ''))
            entry.pack(side='left', fill='x', expand=True, padx=10)
            setattr(self, attr, entry)

        btn_ss = ctk.CTkButton(
            self.settings_scroll,
            text="Save ScreenScraper Credentials",
            fg_color=C['cyan'], text_color='black',
            command=self.save_ss_creds
        )
        btn_ss.pack(pady=10)
        self.settings_widgets.append(btn_ss)

        sep5 = ctk.CTkFrame(self.settings_scroll, fg_color=C['dim'], height=1)
        sep5.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(sep5)

        ctk.CTkLabel(
            self.settings_scroll, text="RETROBAT INTEGRATION",
            font=('Arial', 14, 'bold'), text_color=C['cyan']
        ).pack(fill='x', pady=(10, 5))

        rb_path_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        rb_path_row.pack(fill='x', pady=2)
        self.settings_widgets.append(rb_path_row)
        ctk.CTkLabel(rb_path_row, text="Install Path:", width=100, anchor='w').pack(
            side='left', padx=10
        )
        self.entry_retrobat_path = ctk.CTkEntry(
            rb_path_row, fg_color=C['bg'], border_color=C['dim']
        )
        self.entry_retrobat_path.insert(
            0, self.folder_mappings.get('retrobat_path', r'C:\retrobat')
        )
        self.entry_retrobat_path.pack(side='left', fill='x', expand=True, padx=10)
        self.entry_retrobat_path.bind('<FocusOut>', lambda e: self._save_retrobat_path())
        self.entry_retrobat_path.bind('<Return>', lambda e: self._save_retrobat_path())

        rb_btn_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        rb_btn_row.pack(fill='x', pady=5)
        self.settings_widgets.append(rb_btn_row)
        ctk.CTkButton(
            rb_btn_row, text="Detect & Auto-Map Consoles",
            fg_color=C['cyan'], text_color='black',
            command=self.detect_retrobat
        ).pack(side='left', padx=10)
        ctk.CTkButton(
            rb_btn_row, text="Sync Gamelists + Create Stubs",
            fg_color=C['card'], text_color='white',
            command=self.sync_retrobat_gamelists
        ).pack(side='left', padx=5)
        ctk.CTkButton(
            rb_btn_row, text="Remove Stub Files",
            fg_color=C['bg'], text_color='white',
            hover_color=C['pink'],
            command=self.remove_retrobat_stubs
        ).pack(side='left', padx=5)

        self.lbl_retrobat_status = ctk.CTkLabel(
            self.settings_scroll, text="", text_color=C['dim'], font=('Arial', 11)
        )
        self.lbl_retrobat_status.pack(anchor='w', padx=10, pady=(0, 10))
        self.settings_widgets.append(self.lbl_retrobat_status)

        # --- On-demand launcher section ---
        sep_launcher = ctk.CTkFrame(self.settings_scroll, fg_color=C['dim'], height=1)
        sep_launcher.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(sep_launcher)
        lbl_lt = ctk.CTkLabel(self.settings_scroll, text="ON-DEMAND LAUNCHER",
                              font=('Arial', 14, 'bold'), text_color=C['cyan'])
        lbl_lt.pack(fill='x', pady=(10, 2))
        self.settings_widgets.append(lbl_lt)
        lbl_ld = ctk.CTkLabel(
            self.settings_scroll,
            text="Intercepts ES game launches for missing ROMs.\n"
                 "Can use Myrient, Archive.org fallback, and optional qBittorrent fallback.\n"
                 "Then compresses to CHD (if enabled) and auto-launches.",
            text_color=C['dim'], font=('Arial', 11), justify='left')
        lbl_ld.pack(fill='x', padx=10, pady=(0, 8))
        self.settings_widgets.append(lbl_ld)
        launcher_btn_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        launcher_btn_row.pack(fill='x', pady=5)
        self.settings_widgets.append(launcher_btn_row)
        is_patched = self.is_es_systems_patched()
        if is_patched:
            ctk.CTkButton(
                launcher_btn_row, text="Restore Original es_systems.cfg",
                fg_color=C['pink'], hover_color='#990033',
                command=lambda: (self.restore_es_systems_cfg(), self.render_settings())
            ).pack(side='left', padx=10)
        else:
            ctk.CTkButton(
                launcher_btn_row, text="Enable On-Demand Launcher",
                fg_color=C['cyan'], text_color='black',
                command=lambda: (self.patch_es_systems_cfg(), self.render_settings())
            ).pack(side='left', padx=10)
        st = "✔ On-demand launcher enabled" if is_patched else "Not configured"
        sc = C['success'] if is_patched else C['dim']
        self.lbl_launcher_status = ctk.CTkLabel(
            self.settings_scroll, text=st, text_color=sc, font=('Arial', 11))
        self.lbl_launcher_status.pack(anchor='w', padx=10, pady=(0, 5))
        self.settings_widgets.append(self.lbl_launcher_status)
        lbl_ln = ctk.CTkLabel(self.settings_scroll,
                              text="Requires RetroBat restart after enabling/disabling.",
                              text_color=C['dim'], font=('Arial', 10))
        lbl_ln.pack(anchor='w', padx=10, pady=(0, 10))
        self.settings_widgets.append(lbl_ln)

        sep_sources = ctk.CTkFrame(self.settings_scroll, fg_color=C['dim'], height=1)
        sep_sources.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(sep_sources)

        ctk.CTkLabel(
            self.settings_scroll, text="ON-DEMAND SOURCE FALLBACK",
            font=('Arial', 14, 'bold'), text_color=C['cyan']
        ).pack(fill='x', pady=(10, 5))
        ctk.CTkLabel(
            self.settings_scroll,
            text="Fallback order for missing-stub launches. "
                 "qBittorrent requires Torznab + WebUI credentials.",
            text_color=C['dim'], font=('Arial', 11), justify='left'
        ).pack(fill='x', padx=10, pady=(0, 8))

        row_prompt = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        row_prompt.pack(fill='x', pady=2)
        self.settings_widgets.append(row_prompt)
        ctk.CTkLabel(
            row_prompt, text="Launcher Prompt:", width=120, anchor='w'
        ).pack(side='left', padx=10)
        self.launcher_prompt_source_var = tk.BooleanVar(
            value=self.folder_mappings.get('launcher_prompt_source_choice', True)
        )
        ctk.CTkSwitch(
            row_prompt,
            text="Ask source each on-demand launch",
            variable=self.launcher_prompt_source_var,
            progress_color=C['cyan'],
            command=self.save_download_source_settings
        ).pack(side='left', padx=10)

        row_mode = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        row_mode.pack(fill='x', pady=2)
        self.settings_widgets.append(row_mode)
        ctk.CTkLabel(row_mode, text="Source Mode:", width=120, anchor='w').pack(
            side='left', padx=10
        )
        mode_key = _get_download_source_mode(self.folder_mappings)
        mode_label = DOWNLOAD_SOURCE_MODE_LABELS.get(
            mode_key, DOWNLOAD_SOURCE_MODE_LABELS[DEFAULT_DOWNLOAD_SOURCE_MODE]
        )
        self.download_source_mode_var = ctk.StringVar(value=mode_label)
        ctk.CTkOptionMenu(
            row_mode,
            variable=self.download_source_mode_var,
            values=list(DOWNLOAD_SOURCE_MODE_LABELS.values()),
            fg_color=C['bg'],
            button_color=C['cyan'],
            button_hover_color=C['pink'],
            text_color='white',
            command=lambda _v: self.save_download_source_settings()
        ).pack(side='left', padx=10)

        for lbl, attr, key, show in [
            ("qB URL:", 'entry_qb_url', 'qbittorrent_url', ''),
            ("qB User:", 'entry_qb_user', 'qbittorrent_user', ''),
            ("qB Pass:", 'entry_qb_pass', 'qbittorrent_pass', '*'),
            ("Torznab URL:", 'entry_torznab_url', 'torznab_url', ''),
            ("Torznab API Key:", 'entry_torznab_key', 'torznab_api_key', '*'),
            ("Torznab Cat:", 'entry_torznab_cat', 'torznab_category', ''),
        ]:
            row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
            row.pack(fill='x', pady=2)
            self.settings_widgets.append(row)
            ctk.CTkLabel(row, text=lbl, width=120, anchor='w').pack(
                side='left', padx=10
            )
            entry = ctk.CTkEntry(
                row, fg_color=C['bg'], border_color=C['dim'], show=show
            )
            entry.insert(0, self.folder_mappings.get(key, ''))
            entry.pack(side='left', fill='x', expand=True, padx=10)
            entry.bind('<FocusOut>', lambda _e: self.save_download_source_settings())
            entry.bind('<Return>', lambda _e: self.save_download_source_settings())
            setattr(self, attr, entry)

        row_qb_toggle = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        row_qb_toggle.pack(fill='x', pady=2)
        self.settings_widgets.append(row_qb_toggle)
        ctk.CTkLabel(
            row_qb_toggle, text="qB Cleanup:", width=120, anchor='w'
        ).pack(side='left', padx=10)
        self.qb_remove_on_complete_var = tk.BooleanVar(
            value=self.folder_mappings.get('qbittorrent_remove_on_complete', True)
        )
        ctk.CTkSwitch(
            row_qb_toggle,
            text="Remove Torrent From qB After Import",
            variable=self.qb_remove_on_complete_var,
            progress_color=C['cyan'],
            command=self.save_download_source_settings
        ).pack(side='left', padx=10)

        ctk.CTkButton(
            self.settings_scroll,
            text="Save Source Settings",
            fg_color=C['cyan'],
            text_color='black',
            command=self.save_download_source_settings
        ).pack(pady=(8, 12))

    def _toggle_bool_setting(self, key, var):
        self.folder_mappings[key] = var.get()
        self.save_config()
        if key in ('filter_demos', 'filter_revs'):
            self.filter_list()
        if key == 'debug_mode':
            self._setup_logging()

    def browse_chdman(self):
        path = filedialog.askopenfilename(
            title="Select chdman executable",
            filetypes=[("Executables", "*.exe"), ("All Files", "*.*")]
        )
        if path:
            self.entry_chdman.delete(0, 'end')
            self.entry_chdman.insert(0, path)
            self.save_chd_settings()

    def save_chd_settings(self):
        if hasattr(self, 'entry_chdman'):
            self.folder_mappings['chdman_path'] = self.entry_chdman.get().strip()
        if hasattr(self, 'chd_vars'):
            for key, var in self.chd_vars.items():
                self.folder_mappings[key] = var.get()
        self.save_config()

    def save_download_source_settings(self):
        if hasattr(self, 'download_source_mode_var'):
            mode_label = self.download_source_mode_var.get().strip()
            mode_key = DOWNLOAD_SOURCE_LABEL_TO_MODE.get(
                mode_label, DEFAULT_DOWNLOAD_SOURCE_MODE
            )
            self.folder_mappings['download_source_mode'] = mode_key

        for attr, key in [
            ('entry_qb_url', 'qbittorrent_url'),
            ('entry_qb_user', 'qbittorrent_user'),
            ('entry_qb_pass', 'qbittorrent_pass'),
            ('entry_torznab_url', 'torznab_url'),
            ('entry_torznab_key', 'torznab_api_key'),
            ('entry_torznab_cat', 'torznab_category'),
        ]:
            if hasattr(self, attr):
                self.folder_mappings[key] = getattr(self, attr).get().strip()

        if hasattr(self, 'qb_remove_on_complete_var'):
            self.folder_mappings['qbittorrent_remove_on_complete'] = bool(
                self.qb_remove_on_complete_var.get()
            )
        if hasattr(self, 'launcher_prompt_source_var'):
            self.folder_mappings['launcher_prompt_source_choice'] = bool(
                self.launcher_prompt_source_var.get()
            )

        self.save_config()

    def update_font_size(self, value):
        val = int(float(value))
        self.lbl_font_val.configure(text=str(val))
        self.folder_mappings['font_size'] = val
        self.save_config()
        if self.frame_browser.winfo_viewable():
            self.render_page()

    def clear_saved_folders(self):
        confirm = CustomPopup(
            self, "Confirm Reset",
            "Are you sure you want to clear all saved download locations?",
            ["Yes", "No"]
        )
        if confirm.result == "Yes":
            for path in CONSOLES.values():
                self.folder_mappings.pop(path, None)
            self.save_config()
            self.render_settings()
            CustomPopup(
                self, "Success",
                "All console folder mappings have been cleared.", ["OK"]
            )

    def apply_folder_structure(self, base_path, remote_path):
        for k, v in CONSOLES.items():
            if v == remote_path:
                short = SHORT_NAMES.get(k, k)
                final = os.path.join(base_path, short)
                try:
                    os.makedirs(final, exist_ok=True)
                except Exception:
                    return base_path
                return final
        return base_path

    def change_console_path(self, path):
        browser = ThemedDirBrowser(self, title=f"Select folder for {path}")
        d = browser.result
        if d:
            final_path = self.apply_folder_structure(d, path)
            self.folder_mappings[path] = final_path
            self.save_config()
            self.render_settings()

    def save_twitch_creds(self):
        new_id = self.entry_twitch_id.get().strip()
        new_secret = self.entry_twitch_secret.get().strip()
        self.folder_mappings['twitch_id'] = new_id
        self.folder_mappings['twitch_secret'] = new_secret
        self.save_config()
        self.twitch.client_id = new_id
        self.twitch.client_secret = new_secret
        if self.twitch.authenticate():
            CustomPopup(self, "Success", "Twitch Authentication Successful!", ["OK"])
        else:
            CustomPopup(
                self, "Failed",
                "Could not authenticate.\nCheck your Client ID and Secret.", ["OK"]
            )

    def save_ra_creds(self):
        self.folder_mappings['ra_user'] = self.entry_ra_user.get().strip()
        self.folder_mappings['ra_key'] = self.entry_ra_key.get().strip()
        self.save_config()
        self.ra.username = self.folder_mappings['ra_user']
        self.ra.api_key = self.folder_mappings['ra_key']
        CustomPopup(self, "Success", "RetroAchievements keys saved.", ["OK"])

    def save_ss_creds(self):
        ss_user = self.entry_ss_user.get().strip()
        ss_pass = self.entry_ss_password.get().strip()
        self.folder_mappings['ss_user'] = ss_user
        self.folder_mappings['ss_password'] = ss_pass
        self.save_config()
        if ss_user and ss_pass:
            # Quick connectivity test
            def _test():
                try:
                    ss = ScreenScraperManager(ss_user, ss_pass)
                    # Lightweight call — just check the user info endpoint
                    r = ss._session.get(
                        'https://www.screenscraper.fr/api2/ssuserInfos.php',
                        params=ss._base_params(), timeout=10
                    )
                    ok = r.status_code == 200
                    msg = "ScreenScraper credentials saved and verified ✔" if ok else \
                          "Credentials saved, but could not verify (check username/password)."
                    self.after(0, lambda: CustomPopup(
                        self, "ScreenScraper", msg, ["OK"]
                    ))
                except Exception as e:
                    self.after(0, lambda err=str(e): CustomPopup(
                        self, "ScreenScraper", f"Saved, but verification failed:\n{err}", ["OK"]
                    ))
            threading.Thread(target=_test, daemon=True).start()
        else:
            CustomPopup(self, "Saved", "ScreenScraper credentials cleared.", ["OK"])

    def _save_retrobat_path(self):
        if hasattr(self, 'entry_retrobat_path'):
            self.folder_mappings['retrobat_path'] = self.entry_retrobat_path.get().strip()
            self.save_config()

    def detect_retrobat(self):
        self._save_retrobat_path()
        base = self.folder_mappings.get('retrobat_path', r'C:\retrobat')
        roms_base = os.path.join(base, 'roms')
        if not os.path.isdir(roms_base):
            CustomPopup(self, "Not Found", f"No roms folder found at:\n{roms_base}", ["OK"])
            return
        mapped = 0
        for console_name, myrient_path in CONSOLES.items():
            rb_folder = RETROBAT_ROM_FOLDERS.get(console_name)
            if not rb_folder:
                continue
            rom_dir = os.path.join(roms_base, rb_folder)
            if os.path.isdir(rom_dir):
                self.folder_mappings[myrient_path] = rom_dir
                mapped += 1
        self.save_config()
        self.render_settings()
        CustomPopup(self, "RetroBat Detected", f"Auto-mapped {mapped} console folders.", ["OK"])

    def _get_retrobat_targets(self):
        base = self.folder_mappings.get('retrobat_path', r'C:\retrobat')
        roms_base = os.path.join(base, 'roms')
        targets = []
        for console_name, myrient_path in CONSOLES.items():
            rb_folder = RETROBAT_ROM_FOLDERS.get(console_name)
            if not rb_folder:
                continue
            rom_dir = self.folder_mappings.get(myrient_path) or (
                os.path.join(roms_base, rb_folder) if os.path.isdir(roms_base) else None
            )
            if rom_dir and os.path.isdir(rom_dir):
                targets.append((console_name, myrient_path, rom_dir))
        return targets

    def sync_retrobat_gamelists(self):
        targets = self._get_retrobat_targets()
        if not targets:
            CustomPopup(
                self, "Nothing to Sync",
                "No mapped RetroBat console folders found.\n"
                "Run 'Detect & Auto-Map Consoles' first.", ["OK"]
            )
            return

        def _run():
            total = len(targets)
            total_stubs = 0
            for i, (console_name, myrient_path, rom_dir) in enumerate(targets, 1):
                self.after(0, lambda n=console_name, idx=i: (
                    hasattr(self, 'lbl_retrobat_status') and
                    self.lbl_retrobat_status.configure(
                        text=f"Syncing {n}... ({idx}/{total})",
                        text_color=C['dim']
                    )
                ))
                try:
                    files = self._fetch_myrient_catalog(myrient_path)
                    sync_region = self.folder_mappings.get('sync_region_pref', 'Best')
                    files = _apply_region_filter(files, sync_region)
                    self._write_gamelist_xml(rom_dir, files, console_name=console_name)
                    total_stubs += self._create_stub_files(rom_dir, files, console_name=console_name)
                except Exception as e:
                    self.after(0, lambda err=str(e), n=console_name: (
                        hasattr(self, 'lbl_retrobat_status') and
                        self.lbl_retrobat_status.configure(
                            text=f"⚠ Error on {n}: {err[:60]}",
                            text_color=C['pink']
                        )
                    ))
                    continue
            # Generate the ES auto-collection file listing all stub paths.
            # This creates the "Available to Download" collection in ES main menu.
            self._generate_collection_cfg(targets)

            self.after(0, lambda: (
                hasattr(self, 'lbl_retrobat_status') and
                self.lbl_retrobat_status.configure(
                    text=f"✔ Synced {total} gamelists; created {total_stubs:,} stubs",
                    text_color=C['success']
                )
            ))

        threading.Thread(target=_run, daemon=True).start()

    def _create_stub_files(self, rom_dir, file_list, console_name=None):
        """
        Create marker files for missing ROMs so EmulationStation can list them.
        Existing real files are never overwritten.

        For TeknoParrot: stubs use the .parrot extension instead of .zip,
        since ES scans for .parrot files in the teknoparrot system folder.
        """
        is_tp = (console_name == 'TeknoParrot')

        existing = set()
        try:
            with os.scandir(rom_dir) as it:
                for entry in it:
                    if entry.is_file(follow_symlinks=False):
                        existing.add(entry.name.lower())
        except OSError:
            return 0

        created = 0
        for fname in file_list:
            if not fname:
                continue
            # Safety: ignore any traversal-like names
            if os.path.basename(fname) != fname or '/' in fname or '\\' in fname:
                continue

            # TeknoParrot: swap .zip extension to .parrot for the stub
            if is_tp:
                base = os.path.splitext(fname)[0]
                stub_fname = base + '.parrot'
            else:
                stub_fname = fname

            key = stub_fname.lower()
            if key in existing:
                continue
            dest = os.path.join(rom_dir, stub_fname)
            try:
                with open(dest, 'wb') as f:
                    f.write(MYRIFETCH_STUB_CONTENT)
                existing.add(key)
                created += 1
            except OSError:
                continue
        return created

    def _remove_stub_files(self, rom_dir):
        removed = 0
        errors = 0
        try:
            with os.scandir(rom_dir) as it:
                for entry in it:
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    if _is_myrifetch_stub(entry.path):
                        try:
                            os.remove(entry.path)
                            removed += 1
                        except OSError:
                            errors += 1
        except OSError:
            errors += 1
        return removed, errors

    def remove_retrobat_stubs(self):
        targets = self._get_retrobat_targets()
        if not targets:
            CustomPopup(
                self, "Nothing to Clean",
                "No mapped RetroBat console folders found.\n"
                "Run 'Detect & Auto-Map Consoles' first.", ["OK"]
            )
            return

        confirm = CustomPopup(
            self, "Remove Stub Files",
            "Remove MyriFetch placeholder ROM files from mapped RetroBat folders?\n\n"
            "This will hide not-yet-downloaded titles in EmulationStation until next sync.",
            ["Yes", "No"]
        )
        if confirm.result != "Yes":
            return

        def _run():
            total = len(targets)
            removed_total = 0
            error_total = 0
            for i, (console_name, _myrient_path, rom_dir) in enumerate(targets, 1):
                self.after(0, lambda n=console_name, idx=i: (
                    hasattr(self, 'lbl_retrobat_status') and
                    self.lbl_retrobat_status.configure(
                        text=f"Cleaning stubs in {n}... ({idx}/{total})",
                        text_color=C['dim']
                    )
                ))
                removed, errors = self._remove_stub_files(rom_dir)
                removed_total += removed
                error_total += errors
                self._ownership_cache.invalidate(rom_dir)

            final_text = f"✔ Removed {removed_total:,} stub files"
            if error_total:
                final_text += f" ({error_total} errors)"
            self.after(0, lambda txt=final_text: (
                hasattr(self, 'lbl_retrobat_status') and
                self.lbl_retrobat_status.configure(text=txt, text_color=C['success'])
            ))
            self.after(0, lambda: CustomPopup(
                self, "Stub Cleanup Complete", final_text, ["OK"]
            ))

        threading.Thread(target=_run, daemon=True).start()

    def _fetch_myrient_catalog(self, myrient_path):
        url = BASE_URL + myrient_path
        r = self.session.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        files = []
        for row in soup.find_all('tr'):
            links = row.find_all('a')
            if not links:
                continue
            href = links[0].get('href')
            if not href or href in ('../', '/') or '?' in href or href.endswith('/'):
                continue
            name = unquote(links[0].text.strip())
            if name and name != 'Parent Directory':
                files.append(name)
        return files

    def _generate_collection_cfg(self, targets):
        """
        Write an EmulationStation automatic custom collection listing all stub
        files across every mapped system.

        The collection appears in ES as a dedicated "Available to Download" system
        in the main menu, giving users a storefront-style browse view that is
        completely separate from their per-system libraries.

        File location:
            <retrobat>\\emulationstation\\.emulationstation\\collections\\
                autolist_MyriFetch-Available.cfg

        ES picks up files in that folder automatically; no extra configuration
        is needed.  Each line is an absolute path to a stub ROM file.  When a
        game is downloaded, gamelist_writeback() removes the <hidden> tag in the
        per-system gamelist; a subsequent sync will also regenerate this file
        with the downloaded title absent.
        """
        retrobat_path = self.folder_mappings.get('retrobat_path', r'C:\retrobat')
        collections_dir = os.path.join(
            retrobat_path, 'emulationstation', '.emulationstation', 'collections'
        )
        try:
            os.makedirs(collections_dir, exist_ok=True)
        except OSError:
            return

        cfg_path = os.path.join(collections_dir, 'autolist_MyriFetch-Available.cfg')
        stub_paths = []
        for _console_name, _myrient_path, rom_dir in targets:
            try:
                with os.scandir(rom_dir) as it:
                    for entry in it:
                        if entry.is_file(follow_symlinks=False) and _is_myrifetch_stub(entry.path):
                            stub_paths.append(entry.path)
            except OSError:
                continue

        tmp_path = cfg_path + '.tmp'
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(stub_paths))
                if stub_paths:
                    f.write('\n')
            os.replace(tmp_path, cfg_path)
        except OSError:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


    def _write_gamelist_xml(self, rom_dir, file_list, console_name=None):
        """
        Write gamelist.xml for a ROM directory.

        Ownership detection scans local files for alternate extensions (.chd, .rvz,
        .iso, etc.) so that post-conversion files are always recognised, eliminating
        CHD drift on subsequent launches.

        For TeknoParrot: paths use .parrot extension; ownership is determined by
        the presence of a non-stub .parrot file (empty = real game).

        Stubs are tagged with <hidden>true</hidden> so they are invisible by default
        in EmulationStation.  The user reveals them via UI Settings -> Show Hidden
        Games: a clean, persistent toggle with no name mangling or genre pollution.
        A genre tag ("Available to Download") is also written as a secondary filter.
        """
        is_tp = (console_name == 'TeknoParrot')

        def _esc(s):
            return (s.replace('&', '&amp;').replace('<', '&lt;')
                     .replace('>', '&gt;').replace('"', '&quot;'))

        # Generate (or reuse) the shared stub thumbnail once per sync.
        stub_thumb = _ensure_stub_thumbnail()

        # Build a lower-cased index of every real file already on disk.
        local_files = {}
        try:
            with os.scandir(rom_dir) as it:
                for entry in it:
                    if entry.is_file(follow_symlinks=False):
                        local_files[entry.name.lower()] = entry.name
        except OSError:
            pass

        # Candidate extensions in priority order.  Converted formats (.chd, .rvz)
        # come before .zip so a converted file is always preferred over a stub.
        if is_tp:
            # For TeknoParrot the ES-visible file is always .parrot
            _ALT_EXTS = ('.parrot',)
        else:
            _ALT_EXTS = ('.chd', '.rvz', '.iso', '.cso', '.cue', '.bin', '.gdi', '.zip')

        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<gameList>']
        for fname in file_list:
            base_name = os.path.splitext(fname)[0]

            owned = False
            is_stub = True

            if is_tp:
                # TeknoParrot: canonical file is <base>.parrot
                real_fname = base_name + '.parrot'
                parrot_key = real_fname.lower()
                if parrot_key in local_files:
                    actual_path = os.path.join(rom_dir, local_files[parrot_key])
                    if not _is_myrifetch_stub(actual_path):
                        owned = True
                        is_stub = False
            else:
                real_fname = fname
                # Ownership check: alternate extensions first.
                for ext in _ALT_EXTS:
                    cand = (base_name + ext).lower()
                    if cand in local_files:
                        actual_path = os.path.join(rom_dir, local_files[cand])
                        if not _is_myrifetch_stub(actual_path):
                            owned = True
                            real_fname = local_files[cand]
                            is_stub = False
                            break

                # Fallback: exact filename match.
                if not owned and fname.lower() in local_files:
                    actual_path = os.path.join(rom_dir, local_files[fname.lower()])
                    if not _is_myrifetch_stub(actual_path):
                        owned = True
                        real_fname = local_files[fname.lower()]
                        is_stub = False

            # Owned games: clean name, no extra tags.
            # Stubs: hidden by default; revealed by "Show Hidden Games" toggle.
            lines.append('  <game>')
            lines.append(f'    <path>./{_esc(real_fname)}</path>')
            lines.append(f'    <n>{_esc(base_name)}</n>')
            if is_stub:
                lines.append('    <hidden>true</hidden>')
                lines.append('    <genre>Available to Download</genre>')
                if stub_thumb:
                    lines.append(f'    <thumbnail>{_esc(stub_thumb)}</thumbnail>')
            lines.append('  </game>')

        lines.append('</gameList>')

        out_path = os.path.join(rom_dir, 'gamelist.xml')
        tmp_path = out_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        os.replace(tmp_path, out_path)

    # ------------------------------------------------------------------
    # On-demand launcher: es_systems.cfg patching
    # ------------------------------------------------------------------

    def _get_es_systems_path(self):
        base = self.folder_mappings.get('retrobat_path', r'C:\retrobat')
        return os.path.join(base, 'emulationstation', '.emulationstation', 'es_systems.cfg')

    def is_es_systems_patched(self):
        cfg = self._get_es_systems_path()
        if not os.path.exists(cfg):
            return False
        try:
            with open(cfg, 'r', encoding='utf-8') as f:
                return 'myrient_launcher.py' in f.read()
        except Exception:
            return False

    def patch_es_systems_cfg(self):
        import xml.etree.ElementTree as ET
        cfg = self._get_es_systems_path()
        if not os.path.exists(cfg):
            CustomPopup(self, "Not Found", f"es_systems.cfg not found at:\n{cfg}", ["OK"])
            return

        # Backup
        bak = cfg + '.myrient.bak'
        if not os.path.exists(bak):
            shutil.copy2(cfg, bak)

        try:
            tree = ET.parse(cfg)
            root = tree.getroot()
        except Exception as e:
            CustomPopup(self, "Parse Error", f"Failed to parse es_systems.cfg:\n{e}", ["OK"])
            return

        # Determine launcher script path
        launcher_py = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'myrient_launcher.py'
        )
        if not os.path.exists(launcher_py):
            CustomPopup(self, "Not Found",
                        f"myrient_launcher.py not found at:\n{launcher_py}", ["OK"])
            return

        # Determine python executable — prefer pythonw for no console flash
        python_exe = sys.executable
        if os.name == 'nt':
            pythonw = python_exe.replace('python.exe', 'pythonw.exe')
            if os.path.exists(pythonw):
                python_exe = pythonw

        rb_systems = set(RETROBAT_ROM_FOLDERS.values())
        patched_count = 0

        for system_el in root.findall('system'):
            name_el = system_el.find('name')
            cmd_el = system_el.find('command')
            if name_el is None or cmd_el is None:
                continue
            sys_name = (name_el.text or '').strip()
            if sys_name not in rb_systems:
                continue
            if 'myrient_launcher.py' in (cmd_el.text or ''):
                continue  # already patched

            # Save original command
            orig_el = system_el.find('myrient_original_command')
            if orig_el is None:
                orig_el = ET.SubElement(system_el, 'myrient_original_command')
                orig_el.text = cmd_el.text

            cmd_el.text = (
                f'"{python_exe}" "{launcher_py}"'
                f' -gameinfo %GAMEINFOXML% %CONTROLLERSCONFIG%'
                f' -system %SYSTEM% -emulator %EMULATOR% -core %CORE% -rom %ROM%'
            )
            patched_count += 1

        if patched_count == 0:
            CustomPopup(self, "Already Patched",
                        "All supported systems are already patched.", ["OK"])
            return

        tree.write(cfg, encoding='unicode', xml_declaration=True)
        CustomPopup(
            self, "Launcher Enabled",
            f"Patched {patched_count} systems in es_systems.cfg.\n"
            f"Backup saved to: {os.path.basename(bak)}\n\n"
            f"Restart RetroBat for changes to take effect.",
            ["OK"]
        )
        if hasattr(self, 'lbl_launcher_status'):
            self.lbl_launcher_status.configure(
                text="✔ On-demand launcher enabled",
                text_color=C['success']
            )

    def restore_es_systems_cfg(self):
        cfg = self._get_es_systems_path()
        bak = cfg + '.myrient.bak'
        if not os.path.exists(bak):
            CustomPopup(self, "No Backup", "No backup file found to restore.", ["OK"])
            return
        try:
            shutil.copy2(bak, cfg)
            CustomPopup(
                self, "Restored",
                "Original es_systems.cfg restored.\n\n"
                "Restart RetroBat for changes to take effect.",
                ["OK"]
            )
            if hasattr(self, 'lbl_launcher_status'):
                self.lbl_launcher_status.configure(
                    text="Not configured",
                    text_color=C['dim']
                )
        except Exception as e:
            CustomPopup(self, "Error", f"Failed to restore:\n{e}", ["OK"])

    def bind_scroll(self, widget, target_frame):
        widget.bind("<Button-4>", lambda e, t=target_frame: self._on_scroll(e, t, -1))
        widget.bind("<Button-5>", lambda e, t=target_frame: self._on_scroll(e, t, 1))
        widget.bind("<MouseWheel>", lambda e, t=target_frame: self._on_scroll(e, t, 0))

    def _on_scroll(self, event, widget, direction):
        if direction == 0:
            widget._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else:
            widget._parent_canvas.yview_scroll(direction, "units")

    def refresh_dir(self, path=None):
        self.show_loader()
        target = path if path is not None else self.current_path

        def _work():
            try:
                req_headers = HEADERS.copy()
                if 'myrient.erista.me' not in target:
                    req_headers.pop('Referer', None)
                    req_headers.pop('Origin', None)
                self.net_log(f"Listing: {target[:20]}...")
                # Keep path encoded for the URL; decode only for display
                url = BASE_URL + target
                r = self.session.get(url, headers=req_headers, timeout=15)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, 'html.parser')
                parsed = []
                for row in soup.find_all('tr'):
                    links = row.find_all('a')
                    if not links:
                        continue
                    href = links[0].get('href')
                    if not href:       # FIXED: guard against None href
                        continue
                    name = links[0].text.strip()
                    if href in ('../', '/') or name == 'Parent Directory' or '?' in href:
                        continue
                    is_dir = href.endswith('/')
                    size_text = ""
                    if not is_dir:
                        for col in row.find_all('td'):
                            txt = col.text.strip()
                            if (
                                any(x in txt for x in ('M', 'G', 'K', 'B'))
                                and len(txt) < 10 and txt != name
                            ):
                                size_text = txt
                                break
                    parsed.append({
                        'name': unquote(name).strip('/'),
                        'href': href,
                        'type': 'dir' if is_dir else 'file',
                        'size': size_text
                    })
                self.current_path = target
                self.file_cache = parsed
                self.after(0, self.filter_list)
                self.after(0, self.update_map_btn)
                self.after(0, self.update_storage_stats)
                self.net_log("Idle")
            except Exception as e:
                self.after(0, self.hide_loader)
                self.after(0, lambda err=str(e): CustomPopup(
                    self, "Error", f"Failed to load: {err}", ["OK"]
                ))
                self.net_log("Network Error")
        threading.Thread(target=_work, daemon=True).start()

    def filter_list(self, event=None):
        search = self.search_var.get().lower()
        region = self.region_var.get().lower()
        ownership = self.status_var.get().lower()
        filter_demos = self.folder_mappings.get('filter_demos', False)
        filter_revs = self.folder_mappings.get('filter_revs', False)
        local_path = self.folder_mappings.get(self.current_path)

        # FIXED: one scandir pass for ownership, not N stat() calls
        owned_set = (
            self._ownership_cache.get_owned_set(local_path)
            if ownership != 'all status' and local_path
            else set()
        )

        filtered = []
        for i in self.file_cache:
            name_lower = i['name'].lower()
            if search and search not in name_lower:
                continue
            if i['type'] != 'dir':
                if region != 'all regions' and region not in name_lower:
                    continue
                if filter_demos and ('(demo)' in name_lower or ' demo' in name_lower):
                    continue
                if filter_revs and ('(rev ' in name_lower or ' rev ' in name_lower):
                    continue
                if ownership != 'all status':
                    is_owned = i['name'].lower() in owned_set
                    if ownership == 'missing only' and is_owned:
                        continue
                    if ownership == 'owned only' and not is_owned:
                        continue
            filtered.append(i)

        # FIXED: sort once here, not on every page render
        self.filtered_cache = sorted(
            filtered, key=lambda x: (x['type'] != 'dir', x['name'].lower())
        )
        self.current_page = 0
        self.render_page()
        item_count = sum(1 for x in self.filtered_cache if x['type'] != 'dir')
        self.btn_dl_all.configure(text=f"⬇ Download All Listed [{item_count}]")

    def render_page(self):
        self.hide_loader()
        # FIXED: no update_idletasks() here — avoids white flash
        for widget in self.browser_widgets:
            widget.destroy()
        self.browser_widgets = []

        self.lbl_path.configure(text="/" + self.current_path)
        self.checkboxes = []
        local_path = self.folder_mappings.get(self.current_path)

        # FIXED: pre-build ownership set once for the whole page
        owned_set = self._ownership_cache.get_owned_set(local_path) if local_path else set()

        # FIXED: no re-sort — filtered_cache already sorted by filter_list
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_items = self.filtered_cache[start:end]
        total_pages = max(
            1, (len(self.filtered_cache) + self.items_per_page - 1) // self.items_per_page
        )
        self.lbl_page.configure(text=f"Page {self.current_page + 1} / {total_pages}")
        self.btn_prev.configure(
            state='normal' if self.current_page > 0 else 'disabled'
        )
        self.btn_next.configure(
            state='normal' if end < len(self.filtered_cache) else 'disabled'
        )

        current_font_size = self.folder_mappings.get('font_size', 12)

        for item in page_items:
            row = ctk.CTkFrame(self.list_frame, fg_color='transparent')
            row.pack(fill='x', pady=2)
            self.browser_widgets.append(row)
            self.bind_scroll(row, self.list_frame)
            if item['type'] == 'dir':
                btn = ctk.CTkButton(
                    row, text=f"📁 {item['name']}",
                    font=('Arial', current_font_size),
                    fg_color='transparent', anchor='w',
                    hover_color=C['pink'],
                    command=lambda href=item['href']: self.refresh_dir(
                        self.current_path + href
                    )
                )
                btn.pack(fill='x')
                self.bind_scroll(btn, self.list_frame)
            else:
                is_owned = item['name'].lower() in owned_set
                var = ctk.IntVar()
                text_col = C['success'] if is_owned else 'white'
                display_text = f"✔ {item['name']}" if is_owned else item['name']
                chk = ctk.CTkCheckBox(
                    row, text=display_text, variable=var,
                    font=('Arial', current_font_size),
                    text_color=text_col,
                    fg_color=C['cyan'], hover_color=C['pink'],
                    command=self.update_selection_counter
                )
                chk.pack(side='left')
                self.bind_scroll(chk, self.list_frame)
                self.checkboxes.append((var, item['name'], item['href']))
                lbl = ctk.CTkLabel(
                    row, text=item['size'],
                    font=('Arial', current_font_size),
                    text_color=C['dim']
                )
                lbl.pack(side='right', padx=10)
                self.bind_scroll(lbl, self.list_frame)
                clean_name = item['name'].split('(')[0].split('[')[0].strip()
                clean_name = os.path.splitext(clean_name)[0].strip()
                for w in [row, chk, lbl]:
                    w.bind("<Enter>", lambda e, n=clean_name: self.on_hover_enter(e, n))
                    w.bind("<Leave>", self.on_hover_leave)

    def update_selection_counter(self):
        count = sum(1 for v, n, h in self.checkboxes if v.get() == 1)
        self.btn_dl.configure(text=f"DOWNLOAD SELECTED [{count}]")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        if (self.current_page + 1) * self.items_per_page < len(self.filtered_cache):
            self.current_page += 1
            self.render_page()

    def go_up(self):
        if self.current_path:
            parts = self.current_path.rstrip('/').split('/')
            if len(parts) <= 1:
                self.refresh_dir('')
            else:
                self.refresh_dir('/'.join(parts[:-1]) + '/')

    def get_local_folder(self):
        return self.folder_mappings.get(self.current_path)

    def update_map_btn(self):
        path = self.get_local_folder()
        if path:
            self.btn_map.configure(
                text=f"📂 {os.path.basename(path)}",
                fg_color=C['cyan'], text_color='black'
            )
        else:
            self.btn_map.configure(
                text="📂 Set Save Folder",
                fg_color='transparent', text_color=C['cyan']
            )

    def set_mapping(self):
        browser = ThemedDirBrowser(self, title="Select Download Folder", initial_dir=self.get_local_folder())
        d = browser.result
        if d:
            final_path = self.apply_folder_structure(d, self.current_path)
            self.folder_mappings[self.current_path] = final_path
            self.save_config()
            self.update_map_btn()
            self.update_storage_stats()
            self._ownership_cache.invalidate(final_path)

    def open_current_folder(self):
        path = self.get_local_folder()
        if not path or not os.path.exists(path):
            CustomPopup(self, "Error", "No valid local folder set.", ["OK"])
            return
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def launch_game_folder(self, game_path):
        if not game_path or not os.path.exists(game_path):
            CustomPopup(self, "Error", "File no longer exists.", ["OK"])
            return
        folder_path = os.path.dirname(os.path.abspath(game_path))
        try:
            if platform.system() == "Windows":
                subprocess.run(['explorer', '/select,', os.path.normpath(game_path)])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", game_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            CustomPopup(self, "Error", f"Could not open folder: {e}", ["OK"])

    def update_storage_stats(self):
        path = self.get_local_folder()
        if not path or not os.path.exists(path):
            self.storage_label.configure(text="Storage: No Folder Set")
            self.storage_bar.set(0)
            return
        try:
            total, used, free = shutil.disk_usage(path)
            free_gb = free / (2**30)
            self.storage_label.configure(text=f"Storage: {free_gb:.1f} GB Free")
            self.storage_bar.set(used / total)
            if free_gb < 10:
                self.storage_bar.configure(progress_color='pink')
            elif free_gb < 50:
                self.storage_bar.configure(progress_color='orange')
            else:
                self.storage_bar.configure(progress_color=C['success'])
        except Exception:
            self.storage_label.configure(text="Storage: Unknown")
            self.storage_bar.set(0)

    def add_to_queue(self):
        targets = [(n, h) for v, n, h in self.checkboxes if v.get() == 1]
        if targets:
            self._queue_items(targets)

    def add_all_to_queue(self):
        targets = [
            (item['name'], item['href'])
            for item in self.filtered_cache
            if item['type'] != 'dir'
        ]
        if targets:
            total_mb = 0
            cache_map = {item['name']: item for item in self.file_cache}
            for name, _ in targets:
                if name in cache_map:
                    raw = cache_map[name].get('size', '')
                    try:
                        clean_str = ''.join(c for c in raw if c.isdigit() or c == '.')
                        if clean_str:
                            val = float(clean_str)
                            if 'G' in raw:
                                total_mb += val * 1024
                            elif 'M' in raw:
                                total_mb += val
                            elif 'K' in raw:
                                total_mb += val / 1024
                    except Exception:
                        pass
            if total_mb >= 1024:
                size_str = f"~{total_mb / 1024:.1f} GB"
            elif total_mb > 0:
                size_str = f"~{total_mb:.0f} MB"
            else:
                size_str = "unknown size"
            confirm = CustomPopup(
                self, "Confirm Bulk Download",
                f"Queue {len(targets)} files ({size_str})?", ["Yes", "No"]
            )
            if confirm.result == "Yes":
                self._queue_items(targets)

    def _queue_items(self, targets):
        local_dir = self.get_local_folder()
        if not local_dir:
            browser = ThemedDirBrowser(self, title="Select Download Folder")
            local_dir = browser.result
            if not local_dir:
                return
            final_path = self.apply_folder_structure(local_dir, self.current_path)
            local_dir = final_path
            if self.current_path:
                ask = CustomPopup(
                    self, "Save Location?",
                    f"Save this as the default folder?\n\n{final_path}",
                    ["Yes", "No"]
                )
                if ask.result == "Yes":
                    self.folder_mappings[self.current_path] = final_path
                    self.save_config()
                    self.update_map_btn()
                    self.update_storage_stats()

        if not os.path.exists(local_dir):
            try:
                os.makedirs(local_dir, exist_ok=True)
            except Exception as e:
                CustomPopup(self, "Error", f"Could not create folder:\n{e}", ["OK"])
                return

        if not os.access(local_dir, os.W_OK):
            CustomPopup(self, "Permission Error", f"Cannot write to:\n{local_dir}", ["OK"])
            return

        cache_map = {item['name']: item for item in self.file_cache}

        console_type = None
        for c_name, c_path in CONSOLES.items():
            if self.current_path.startswith(c_path):
                console_type = _resolve_chd_console_key(c_name)
                break

        use_subfolders = self.folder_mappings.get('subfolder_per_game', True)
        for name, href in targets:
            url = BASE_URL + self.current_path + href
            game_clean = os.path.splitext(name)[0]
            game_folder = os.path.join(local_dir, game_clean) if use_subfolders else local_dir
            size_mb = 0
            if name in cache_map:
                try:
                    raw = cache_map[name]['size']
                    clean_str = ''.join(
                        c for c in raw if c.isdigit() or c == '.'
                    )
                    if clean_str:
                        val = float(clean_str)
                        if 'G' in raw:
                            size_mb = val * 1024
                        elif 'M' in raw:
                            size_mb = val
                        elif 'K' in raw:
                            size_mb = val / 1024
                except Exception:
                    pass
            self.pending_stage_queue.append({
                'url': url,
                'path': os.path.join(game_folder, name),
                'name': name,
                'size_mb': size_mb,
                'folder': game_folder,
                'console_type': console_type
            })

        self.show_queue()
        self.update_batch_labels()
        if not self.is_downloading:
            threading.Thread(target=self.process_queue, daemon=True).start()

    def update_batch_labels(self):
        total = len(self.pending_stage_queue) + len(self.download_list)
        batches = (len(self.pending_stage_queue) + 99) // 100
        self.after(0, lambda t=total: self.lbl_total_left.configure(
            text=f"Total Left: {t}"
        ))
        self.after(0, lambda b=batches: self.lbl_batches_left.configure(
            text=f"Batches Left: {b}"
        ))

    def remove_from_queue(self, index):
        if 0 <= index < len(self.download_list):
            item = self.download_list.pop(index)
            self.log(f"REMOVED: {item['name']}")
            self.render_queue_list()
            self.update_batch_labels()

    def render_queue_list(self):
        for w in self.queue_widgets:
            w.destroy()
        self.queue_widgets = []
        if not self.download_list and not self.pending_stage_queue:
            lbl = ctk.CTkLabel(
                self.queue_list_frame, text="Queue is empty",
                text_color=C['dim']
            )
            lbl.pack(pady=10)
            self.queue_widgets.append(lbl)
            return
        for i, item in enumerate(self.download_list):
            row = ctk.CTkFrame(self.queue_list_frame, fg_color='transparent')
            row.pack(fill='x', pady=2)
            self.queue_widgets.append(row)
            self.bind_scroll(row, self.queue_list_frame)
            ctk.CTkLabel(
                row, text=f"{i+1}. {item['name']}",
                anchor='w', text_color='white'
            ).pack(side='left', padx=5, fill='x', expand=True)
            ctk.CTkButton(
                row, text="❌", width=30,
                fg_color=C['bg'], hover_color=C['pink'],
                command=lambda idx=i: self.remove_from_queue(idx)
            ).pack(side='right', padx=5)

    def log(self, msg):
        self.log_box.insert('end', msg + "\n")
        self.log_box.see('end')

    def play_notification(self):
        if not self.folder_mappings.get('notif_sound', True):
            return
        if os.name == 'nt' and winsound:
            winsound.MessageBeep()
        else:
            print('\a')

    def dl_part(self, url, start, end, fname, headers, results, index):
        """Download byte range [start, end] into fname. Reports into results[index]."""
        expected = end - start + 1
        h = headers.copy()
        h['Range'] = f'bytes={start}-{end}'
        written = 0
        try:
            with self.session.get(url, headers=h, stream=True, timeout=30) as r:
                if r.status_code == 403:
                    raise IOError('403 Forbidden')
                r.raise_for_status()
                with open(fname, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        self._pause_event.wait()  # blocks cleanly when paused
                        if self._cancel_event.is_set():
                            break
                        f.write(chunk)
                        written += len(chunk)
            actual = os.path.getsize(fname) if os.path.exists(fname) else 0
            results[index] = (actual == expected, actual, expected)
        except Exception as e:
            self.log(f'  Part {index} error: {e}')
            results[index] = (False, written, expected)

    def download_cover(self, game_name, save_folder):
        # FIXED: strip extension before building IGDB query
        base_name = os.path.splitext(game_name)[0]
        clean_name = base_name.split('(')[0].split('[')[0].strip()
        clean_name = clean_name.replace('"', '').replace(';', '').strip()
        if not clean_name:
            return
        self.log(f"🎨 Searching art: {clean_name}...")
        game_data = self.twitch.search_game(clean_name)
        if game_data and 'cover' in game_data and 'url' in game_data['cover']:
            raw_url = game_data['cover']['url']
            if raw_url.startswith("//"):
                raw_url = "https:" + raw_url
            hq_url = raw_url.replace("t_thumb", "t_cover_big")
            try:
                r = self.session.get(hq_url, timeout=10)
                if r.status_code == 200:
                    save_path = os.path.join(
                        save_folder, os.path.splitext(game_name)[0] + ".jpg"
                    )
                    with open(save_path, 'wb') as f:
                        f.write(r.content)
                    self.log("✔ Art Downloaded")
                    self._ownership_cache.invalidate(save_folder)
                else:
                    self.log("⚠ Art download failed")
            except Exception as e:
                self.log(f"⚠ Art Error: {e}")
        else:
            self.log("⚠ No art found on ScreenScraper")

    def process_chd_compression(self, task, final_path):
        c_type = task.get('console_type')
        use_chd, _ = _use_chdman_for_console(self.folder_mappings, c_type)
        chd_exe = self.folder_mappings.get('chdman_path') or shutil.which('chdman')
        if not (use_chd and chd_exe and c_type):
            return final_path

        self.log("📦 Extracting for CHD compression...")
        try:
            extract_dir = task['folder']
            if zipfile.is_zipfile(final_path):
                with zipfile.ZipFile(final_path, 'r') as z:
                    # FIXED: zip slip prevention
                    _safe_extractall(z, extract_dir)

            src_file = None
            src_ext = None
            for ext in ['.gdi', '.cue', '.iso']:
                for f in os.listdir(extract_dir):
                    if f.lower().endswith(ext):
                        src_file = os.path.join(extract_dir, f)
                        src_ext = ext
                        break
                if src_file:
                    break

            if not src_file:
                self.log("⚠ No disc image found to compress.")
                return final_path

            chd_out = os.path.splitext(src_file)[0] + ".chd"
            modes = ['createdvd', 'createcd'] if src_ext == '.iso' else ['createcd']
            success = False
            last_err = ""

            si = None
            if os.name == 'nt':
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            self.after(0, lambda: self.lbl_speed.configure(text="Creating CHD..."))
            self.after(0, lambda: self.progress_bar.set(0))

            for mode in modes:
                self.log(f"💿 Running CHDMAN ({mode})...")
                cmd = [chd_exe, mode, '-i', src_file, '-o', chd_out, '-f']
                full_log = []
                try:
                    p = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        startupinfo=si, text=True, bufsize=1
                    )
                    # FIXED: line-buffered iteration — no char-by-char read()
                    for line in p.stdout:
                        line = line.rstrip()
                        if line:
                            full_log.append(line)
                            m = re.search(r'(\d+(?:\.\d+)?)%', line)
                            if m:
                                try:
                                    val = float(m.group(1))
                                    self.after(0, lambda v=val: self.progress_bar.set(v/100))
                                    self.after(0, lambda v=val: self.lbl_speed.configure(
                                        text=f'Creating CHD: {v:.1f}%'
                                    ))
                                except ValueError:
                                    pass
                    p.wait()
                    if p.returncode == 0 and os.path.exists(chd_out):
                        success = True
                        break
                    last_err = '\n'.join(full_log[-3:]) if full_log else 'Unknown Error'
                except Exception as e:
                    last_err = str(e)

            if success:
                self.log("✔ Compression Successful")
                if os.path.exists(final_path):
                    os.remove(final_path)
                for f in os.listdir(extract_dir):
                    p_item = os.path.join(extract_dir, f)
                    if p_item == chd_out:
                        continue
                    try:
                        if os.path.isfile(p_item):
                            os.remove(p_item)
                        else:
                            shutil.rmtree(p_item)
                    except Exception:
                        pass
                parent_dir = os.path.dirname(extract_dir)
                flat_path = os.path.join(parent_dir, os.path.basename(chd_out))
                if os.path.exists(flat_path):
                    os.remove(flat_path)
                shutil.move(chd_out, flat_path)
                if not os.listdir(extract_dir):
                    os.rmdir(extract_dir)
                return flat_path
            else:
                self.log(f"❌ CHDMAN Failed: {last_err}")
                if os.path.exists(chd_out):
                    os.remove(chd_out)
                return final_path

        except Exception as e:
            self.log(f"❌ Compression Error: {e}")
            return final_path

    def process_queue(self):
        self.is_downloading = True
        self._cancel_event.clear()
        self._pause_event.set()  # start running (not paused)

        # FIXED: all widget updates dispatched to main thread via after()
        self.after(0, lambda: self.btn_pause.configure(
            state='normal', text='Pause Download',
            fg_color=C['card'], text_color='white'
        ))
        self.after(0, lambda: self.btn_stop.configure(
            state='normal', text='Stop Download'
        ))

        while (self.download_list or self.pending_stage_queue) and not self._cancel_event.is_set():
            if not self.download_list and self.pending_stage_queue:
                self.log("📦 LOADING NEXT BATCH (100 items)...")
                BATCH_SIZE = 100
                # FIXED: deque popleft() is O(1)
                batch = [
                    self.pending_stage_queue.popleft()
                    for _ in range(min(BATCH_SIZE, len(self.pending_stage_queue)))
                ]
                self.download_list.extend(batch)
                self.after(0, self.render_queue_list)
                self.update_batch_labels()

            if not self.download_list:
                break

            try:
                task = self.download_list.pop(0)
                self.update_batch_labels()
                self.after(0, self.render_queue_list)
                self.log(f"▶ STARTING: {task['name']}")
                self.net_log(f"DL: {task['name'][:15]}...")

                req_headers = HEADERS.copy()
                if 'myrient.erista.me' not in task['url']:
                    req_headers.pop('Referer', None)
                    req_headers.pop('Origin', None)

                total_length = 0
                try:
                    head = self.session.head(
                        task['url'], headers=req_headers,
                        timeout=15, allow_redirects=True
                    )
                    total_length = int(head.headers.get('content-length', 0))
                except Exception:
                    pass
                if total_length == 0 and task['size_mb'] > 0:
                    total_length = int(task['size_mb'] * 1024 * 1024)

                save_folder = task['folder']
                os.makedirs(save_folder, exist_ok=True)

                final_path = task['path']
                if os.name == 'nt' and len(os.path.abspath(final_path)) > 255:
                    final_path = "\\\\?\\" + os.path.abspath(final_path)

                try:
                    _, _, free = shutil.disk_usage(save_folder)
                    if total_length > 0 and free < total_length:
                        self.log("❌ ERROR: Insufficient disk space")
                        continue
                except Exception:
                    pass

                start_t = time.time()
                parts = []
                threads = []

                if total_length == 0:
                    self.log("⚠ Unknown size — single-thread stream")
                    try:
                        with self.session.get(
                            task['url'], headers=req_headers,
                            stream=True, timeout=60
                        ) as r:
                            r.raise_for_status()
                            downloaded = 0
                            with open(final_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                                    self._pause_event.wait()  # blocks cleanly when paused
                                    if self._cancel_event.is_set():
                                        break
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    elapsed = time.time() - start_t
                                    if elapsed > 0.1:
                                        # FIXED: capture value in default arg
                                        self.after(0, lambda mb=downloaded / 1024 / 1024: self.lbl_speed.configure(
                                            text=f'DL: {mb:.1f} MB'
                                        ))
                                        self.after(0, lambda: self.progress_bar.set(0.5))
                    except Exception as e:
                        self.log(f"❌ Stream error: {e}")
                        continue
                else:
                    part_size = total_length // NUM_THREADS
                    # FIXED: results list for part integrity verification
                    results = [None] * NUM_THREADS
                    for i in range(NUM_THREADS):
                        s = i * part_size
                        e = (s + part_size - 1) if i < NUM_THREADS - 1 else (total_length - 1)
                        fname = f'{final_path}.part{i}'
                        parts.append(fname)
                        t = threading.Thread(
                            target=self.dl_part,
                            args=(task['url'], s, e, fname, req_headers, results, i),
                            daemon=True
                        )
                        threads.append(t)
                        t.start()

                    # Speed tracking for smooth display
                    last_bytes = 0
                    last_time = start_t

                    while any(t.is_alive() for t in threads) and not self._cancel_event.is_set():
                        time.sleep(0.4)
                        now = time.time()
                        current_size = sum(
                            os.path.getsize(p) for p in parts if os.path.exists(p)
                        )
                        elapsed = now - last_time
                        if elapsed >= 0.4:
                            speed = (current_size - last_bytes) / elapsed / 1024 / 1024
                            last_bytes = current_size
                            last_time = now
                        else:
                            speed = 0
                        pct = current_size / total_length if total_length > 0 else 0
                        # FIXED: capture in default args
                        self.after(0, lambda s=speed: self.lbl_speed.configure(
                            text=f'DL: {s:.2f} MB/s'
                        ))
                        self.after(0, lambda p=pct: self.progress_bar.set(p))

                    for t in threads:
                        t.join()

                    if self._cancel_event.is_set():
                        self.log("🛑 CANCELLED BY USER")
                        for p in parts:
                            if os.path.exists(p):
                                os.remove(p)
                        if os.path.exists(final_path):
                            os.remove(final_path)
                        break

                    # FIXED: verify all parts before stitching
                    failures = []
                    for i, result in enumerate(results):
                        if result is None:
                            failures.append(f'Part {i}: no result reported')
                            continue
                        ok, actual, expected = result
                        if not ok:
                            failures.append(f'Part {i}: download failed')
                        elif actual != expected:
                            failures.append(
                                f'Part {i}: size mismatch '
                                f'(got {actual:,} B, expected {expected:,} B)'
                            )

                    if failures:
                        for msg in failures:
                            self.log(f'❌ {msg}')
                        for p in parts:
                            if os.path.exists(p):
                                os.remove(p)
                        continue

                    self.log("🔗 Stitching...")
                    with open(final_path, 'wb') as f_out:
                        for p in parts:
                            with open(p, 'rb') as f_in:
                                shutil.copyfileobj(f_in, f_out, length=1024*1024)
                    # FIXED: delete parts AFTER successful stitch only
                    for p in parts:
                        try:
                            os.remove(p)
                        except Exception:
                            pass

                if self._cancel_event.is_set():
                    self.log("🛑 CANCELLED BY USER")
                    break

                if os.path.exists(final_path):
                    if os.path.getsize(final_path) < MIN_VALID_BYTES:
                        self.log("❌ FAILED: File too small (likely server error)")
                        try:
                            os.remove(final_path)
                        except Exception:
                            pass
                    else:
                        final_path = self.process_chd_compression(task, final_path)
                        # Invalidate ownership cache for this folder
                        self._ownership_cache.invalidate(task['folder'])
                        self.log("✔ COMPLETED")
                        if self.twitch.client_id:
                            save_dir = os.path.dirname(final_path)
                            self.download_cover(task['name'], save_dir)
                        self.play_notification()
                else:
                    self.log("❌ FAILED: File missing after download")

            except Exception as e:
                self.log(f"CRITICAL ERROR: {e}")
                traceback.print_exc()

        self.is_downloading = False
        self._cancel_event.clear()
        self._pause_event.set()

        # FIXED: all UI updates through after()
        self.after(0, lambda: self.btn_pause.configure(
            state='disabled', text='Pause Download',
            fg_color=C['card'], text_color='white'
        ))
        self.after(0, lambda: self.btn_stop.configure(
            state='disabled', text='Stop Download'
        ))
        self.after(0, lambda: self.progress_bar.set(0))
        self.after(0, lambda: self.lbl_speed.configure(text="IDLE"))
        self.update_batch_labels()
        self.net_log("Idle")


# ---------------------------------------------------------------------------
# Headless download engine (for on-demand launcher)
# ---------------------------------------------------------------------------

def _headless_dl_part(session, url, start, end, fname, headers, results, idx,
                      cancel_event, pause_event, event_cb=None, total_parts=None):
    """Download byte range [start, end] into fname. Reports into results[idx]."""
    expected = end - start + 1
    h = headers.copy()
    h['Range'] = f'bytes={start}-{end}'
    written = 0
    part_total = total_parts if total_parts is not None else NUM_THREADS
    if event_cb:
        event_cb(
            f'Part {idx + 1}/{part_total} started '
            f'({start:,}-{end:,}, {expected:,} bytes)'
        )
    try:
        with session.get(url, headers=h, stream=True, timeout=30) as r:
            status_code = r.status_code
            retry_after = _parse_retry_after_seconds(r.headers.get('Retry-After'))
            if r.status_code == 403:
                err = '403 Forbidden'
                results[idx] = (False, written, expected, err, status_code, retry_after)
                if event_cb:
                    event_cb(f'ERROR: Part {idx + 1} failed: {err}')
                return
            if r.status_code >= 400:
                err = f'HTTP{r.status_code}: {r.reason or "HTTP error"}'
                if retry_after is not None:
                    err += f' (Retry-After={retry_after}s)'
                results[idx] = (False, written, expected, err, status_code, retry_after)
                if event_cb:
                    event_cb(f'ERROR: Part {idx + 1} failed: {err}')
                return
            with open(fname, 'wb') as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    pause_event.wait()
                    if cancel_event.is_set():
                        break
                    f.write(chunk)
                    written += len(chunk)
        actual = os.path.getsize(fname) if os.path.exists(fname) else 0
        if actual == expected:
            results[idx] = (True, actual, expected, '', None, None)
        else:
            err = f'Part {idx + 1}: size mismatch (got {actual:,} B, expected {expected:,} B)'
            results[idx] = (False, actual, expected, err, None, None)
            if event_cb:
                event_cb(f'ERROR: {err}')
    except Exception as e:
        err = f'{type(e).__name__}: {e}'
        status_code = None
        retry_after = None
        if hasattr(e, 'response') and e.response is not None:
            try:
                status_code = e.response.status_code
                retry_after = _parse_retry_after_seconds(
                    e.response.headers.get('Retry-After')
                )
            except Exception:
                status_code = None
                retry_after = None
        results[idx] = (False, written, expected, err, status_code, retry_after)
        if event_cb:
            event_cb(f'ERROR: Part {idx + 1} failed: {err}')


def _is_teknoparrot_path(myrient_path: str) -> bool:
    """Return True if the myrient path is the TeknoParrot collection."""
    return str(myrient_path or '').startswith('TeknoParrot/')


def teknoparrot_post_process(zip_path: str, dest_dir: str, log_cb=None):
    """
    Post-download processing for TeknoParrot games:
      1. Extract zip to dest_dir/<game_base_name>/  (the game files folder)
      2. Create an empty real .parrot file at dest_dir/<game_base_name>.parrot
         (empty = owned/real; MYRIFETCH_STUB_CONTENT = stub/not-yet-downloaded)
      3. Delete the zip

    EmulationStation discovers the .parrot file and launches via emulatorLauncher,
    which hands off to TeknoParrot with the game folder path.

    Returns (success: bool, parrot_path: str).
    """
    def log(msg):
        _append_on_demand_log('teknoparrot', msg)
        if log_cb:
            try:
                log_cb(msg)
            except Exception:
                pass

    zip_name = os.path.basename(zip_path)
    game_base = os.path.splitext(zip_name)[0]
    extract_dir = os.path.join(dest_dir, game_base)
    parrot_path = os.path.join(dest_dir, game_base + '.parrot')

    log(f'Extracting {zip_name} to {extract_dir}')
    try:
        os.makedirs(extract_dir, exist_ok=True)
        real_extract_dir = os.path.realpath(extract_dir)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                member_dest = os.path.realpath(
                    os.path.join(extract_dir, member.filename)
                )
                # Zip-slip guard
                if not member_dest.startswith(real_extract_dir + os.sep) and \
                        member_dest != real_extract_dir:
                    log(f'WARN: Skipping unsafe zip path: {member.filename!r}')
                    continue
            zf.extractall(extract_dir)
        log(f'Extraction complete: {extract_dir}')
    except Exception as e:
        log(f'ERROR: Extraction failed: {type(e).__name__}: {e}')
        return False, parrot_path

    # Write the real (non-stub) .parrot marker — empty file signals ownership
    try:
        with open(parrot_path, 'w', encoding='utf-8') as f:
            f.write('')
        log(f'Created .parrot marker: {parrot_path}')
    except Exception as e:
        log(f'ERROR: Could not create .parrot file: {type(e).__name__}: {e}')
        return False, parrot_path

    # Remove the source zip (non-fatal if it fails)
    try:
        os.remove(zip_path)
        log(f'Deleted source zip: {zip_path}')
    except Exception as e:
        log(f'WARN: Could not delete zip after extraction: {type(e).__name__}: {e}')

    return True, parrot_path


def headless_download(rom_name, myrient_path, dest_dir, cancel_event, pause_event,
                      progress_cb=None, event_cb=None, download_config=None):
    """
    Download a single ROM from Myrient. Returns (success, local_path).
    progress_cb(pct, speed_mbps, downloaded_bytes, total_bytes) called periodically.
    """
    def emit(msg):
        _append_on_demand_log('download', f'{rom_name}: {msg}')
        if event_cb:
            try:
                event_cb(msg)
            except Exception:
                pass

    def cleanup_files(paths):
        for p in paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except OSError:
                pass

    def sleep_with_cancel(seconds):
        end_t = time.time() + seconds
        while time.time() < end_t:
            if cancel_event.is_set():
                return False
            time.sleep(0.1)
        return True

    def single_stream_download(max_attempts=1, reason='single-thread stream'):
        for attempt in range(max_attempts):
            if cancel_event.is_set():
                cleanup_files([stream_tmp_path])
                emit(f'{reason}: cancelled before attempt start')
                return False

            cooldown_left = _remaining_host_cooldown(download_host)
            if cooldown_left > 0:
                emit(
                    f'{reason}: waiting {cooldown_left}s for host cooldown '
                    f'({download_host})'
                )
                if not sleep_with_cancel(cooldown_left):
                    cleanup_files([stream_tmp_path])
                    emit(f'{reason}: cancelled during host cooldown wait')
                    return False

            if attempt > 0:
                delay = min(20, 3 * (2 ** (attempt - 1)))
                delay = max(delay, _remaining_host_cooldown(download_host))
                emit(
                    f'{reason}: retry {attempt + 1}/{max_attempts} '
                    f'after {delay}s backoff'
                )
                if not sleep_with_cancel(delay):
                    cleanup_files([stream_tmp_path])
                    emit(f'{reason}: cancelled during backoff')
                    return False

            downloaded = 0
            req_headers = _headers_for_url(url)
            mode = 'wb'
            resume_from = 0
            if total_length > 0 and os.path.exists(stream_tmp_path):
                try:
                    partial_size = os.path.getsize(stream_tmp_path)
                except OSError:
                    partial_size = 0
                if 0 < partial_size < total_length:
                    resume_from = partial_size
                    req_headers['Range'] = f'bytes={resume_from}-'
                    mode = 'ab'
                    emit(
                        f'{reason}: resuming at {resume_from:,}/{total_length:,} bytes '
                        f'(attempt {attempt + 1}/{max_attempts})'
                    )
                elif partial_size >= total_length:
                    cleanup_files([stream_tmp_path])
            try:
                with session.get(url, headers=req_headers, stream=True, timeout=60) as r:
                    retry_after = _parse_retry_after_seconds(r.headers.get('Retry-After'))
                    emit(
                        f'{reason}: GET status={r.status_code} '
                        f'(attempt {attempt + 1}/{max_attempts})'
                    )
                    if r.status_code == 429:
                        cooldown, count_429 = _mark_host_rate_limited(
                            download_host, retry_after
                        )
                        emit(
                            f'ERROR: {reason} got HTTP429 from {download_host}; '
                            f'Retry-After={retry_after if retry_after is not None else "n/a"}, '
                            f'cooldown={cooldown}s, host429count={count_429}'
                        )
                        continue
                    if resume_from > 0 and r.status_code == 200:
                        # Server ignored Range; restart from zero this attempt.
                        emit(
                            f'{reason}: server ignored Range resume, restarting stream '
                            f'from byte 0'
                        )
                        cleanup_files([stream_tmp_path])
                        resume_from = 0
                        mode = 'wb'
                    r.raise_for_status()
                    start_t = time.time()
                    downloaded = resume_from
                    with open(stream_tmp_path, mode) as f:
                        for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                            pause_event.wait()
                            if cancel_event.is_set():
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_cb and time.time() - start_t > 0.3:
                                elapsed = time.time() - start_t
                                speed = downloaded / elapsed / 1024 / 1024
                                pct = (downloaded / total_length) if total_length > 0 else 0.5
                                progress_cb(min(pct, 1.0), speed, downloaded, total_length)
            except Exception as e:
                emit(
                    f'ERROR: {reason} attempt {attempt + 1}/{max_attempts} failed '
                    f'after {downloaded:,} bytes ({type(e).__name__}: {e})'
                )
                continue

            if cancel_event.is_set():
                cleanup_files([stream_tmp_path])
                emit(f'{reason}: cancelled by user')
                return False

            if os.path.exists(stream_tmp_path):
                size = os.path.getsize(stream_tmp_path)
                if size >= MIN_VALID_BYTES or (total_length > 0 and size == total_length):
                    try:
                        os.replace(stream_tmp_path, final_path)
                        emit(f'{reason}: completed ({size:,} bytes)')
                        return True
                    except Exception as e:
                        emit(
                            f'ERROR: {reason} could not finalize output file '
                            f'({type(e).__name__}: {e})'
                        )
                        cleanup_files([stream_tmp_path])
                        continue
                emit(
                    f'ERROR: {reason} output too small '
                    f'({size:,} bytes, minimum {MIN_VALID_BYTES:,})'
                )
            else:
                emit(f'ERROR: {reason} ended but output file is missing')
        cleanup_files([stream_tmp_path])
        return False

    session = requests.Session()

    if isinstance(myrient_path, str) and myrient_path.lower().startswith(('http://', 'https://')):
        url = myrient_path
    else:
        url = BASE_URL + myrient_path + quote(rom_name)
    download_host = (urlparse(url).hostname or '').lower()
    req_headers = _headers_for_url(url)
    session.headers.clear()
    session.headers.update(req_headers)
    final_path = os.path.join(dest_dir, rom_name)
    os.makedirs(dest_dir, exist_ok=True)
    emit(f'Starting download from {url}')
    emit(f'Download host: {download_host or "unknown"}')
    emit(f'Destination: {final_path}')

    if os.name == 'nt' and len(os.path.abspath(final_path)) > 255:
        final_path = "\\\\?\\" + os.path.abspath(final_path)
        emit(f'Long path mode enabled: {final_path}')
    stream_tmp_path = final_path + '.streamdl'

    # Get file size
    total_length = 0
    try:
        head = session.head(url, headers=req_headers, timeout=15, allow_redirects=True)
        total_length = int(head.headers.get('content-length', 0))
        emit(f'HEAD status={head.status_code}, content-length={total_length:,} bytes')
    except Exception as e:
        emit(f'WARN: HEAD request failed ({type(e).__name__}: {e})')

    if total_length == 0:
        # Single-thread stream fallback
        emit('Using single-thread stream mode (server did not provide content-length)')
        return single_stream_download(max_attempts=4), final_path

    # Check disk space
    try:
        _, _, free = shutil.disk_usage(dest_dir)
        if free < total_length:
            emit(
                f'ERROR: Insufficient disk space '
                f'(need {total_length:,} B, free {free:,} B)'
            )
            return False, final_path
        emit(f'Disk free: {free:,} B')
    except Exception as e:
        emit(f'WARN: Disk space check failed ({type(e).__name__}: {e})')

    # Thread policy: prefer single-stream for smaller files and hosts that 429.
    thread_count, thread_reasons, _ = _choose_headless_threads(download_host, total_length)
    if thread_count <= 1:
        reason_text = '; '.join(thread_reasons) if thread_reasons else 'policy selected'
        emit(f'Using single-thread stream mode ({reason_text})')
        ok = single_stream_download(max_attempts=4, reason='single-thread policy stream')
        return ok, final_path

    # Multi-threaded ranged download
    part_size = total_length // thread_count
    results = [None] * thread_count
    parts = []
    threads = []
    start_t = time.time()
    emit(f'Using {thread_count} ranged threads for {total_length:,} bytes')
    if thread_reasons:
        emit(f'Thread policy notes: {"; ".join(thread_reasons)}')
    start_stagger = float(HOST_RANGE_THREAD_STAGGER_SEC.get(download_host, 0.0))
    if start_stagger > 0 and thread_count > 1:
        emit(
            f'Applying {start_stagger:.2f}s stagger between ranged thread starts '
            f'for {download_host}'
        )

    for i in range(thread_count):
        if i > 0 and start_stagger > 0:
            if not sleep_with_cancel(start_stagger):
                cleanup_files(parts + [stream_tmp_path])
                emit('Cancelled while staggering ranged thread startup')
                return False, final_path
        s = i * part_size
        e = (s + part_size - 1) if i < thread_count - 1 else (total_length - 1)
        fname = f'{final_path}.part{i}'
        parts.append(fname)
        t = threading.Thread(
            target=_headless_dl_part,
            args=(session, url, s, e, fname, req_headers, results, i,
                  cancel_event, pause_event, emit, thread_count),
            daemon=True
        )
        threads.append(t)
        t.start()

    last_bytes = 0
    last_time = start_t
    while any(t.is_alive() for t in threads) and not cancel_event.is_set():
        time.sleep(0.4)
        now = time.time()
        current_size = sum(os.path.getsize(p) for p in parts if os.path.exists(p))
        elapsed = now - last_time
        if elapsed >= 0.4:
            speed = (current_size - last_bytes) / elapsed / 1024 / 1024
            last_bytes = current_size
            last_time = now
        else:
            speed = 0
        pct = current_size / total_length if total_length > 0 else 0
        if progress_cb:
            progress_cb(pct, speed, current_size, total_length)

    for t in threads:
        t.join()

    if cancel_event.is_set():
        cleanup_files(parts + [stream_tmp_path])
        emit('Cancelled by user during multi-thread download')
        return False, final_path

    # Verify parts
    failures = []
    retry_after_values = []
    rate_limited = False
    for i, result in enumerate(results):
        if result is None:
            failures.append(f'Part {i + 1}: no result reported')
            continue
        status_code = None
        retry_after = None
        if len(result) >= 6:
            ok, actual, expected, err, status_code, retry_after = result
        else:
            ok, actual, expected, err = result
        if not ok:
            failures.append(err or f'Part {i + 1}: download failed')
            if (
                status_code == 429 or
                ('429' in str(err)) or
                ('Too Many Requests' in str(err))
            ):
                rate_limited = True
            if retry_after is not None:
                retry_after_values.append(retry_after)
            continue
        if actual != expected:
            failures.append(
                f'Part {i + 1}: size mismatch (got {actual:,} B, expected {expected:,} B)'
            )
    if failures:
        for msg in failures:
            emit(f'ERROR: {msg}')
        cleanup_files(parts + [stream_tmp_path])
        if rate_limited:
            retry_after = max(retry_after_values) if retry_after_values else None
            cooldown, count_429 = _mark_host_rate_limited(download_host, retry_after)
            emit(
                f'Rate limiting detected on ranged requests from {download_host}; '
                f'Retry-After={retry_after if retry_after is not None else "n/a"}, '
                f'cooldown={cooldown}s, host429count={count_429}'
            )
            if cooldown > 0:
                emit(f'Waiting {cooldown}s before fallback stream attempt')
                if not sleep_with_cancel(cooldown):
                    emit('Cancelled during rate-limit cooldown wait')
                    return False, final_path
            ok = single_stream_download(
                max_attempts=4,
                reason='rate-limit fallback stream'
            )
            return ok, final_path
        return False, final_path

    # Stitch
    emit('Stitching part files')
    try:
        with open(final_path, 'wb') as f_out:
            for p in parts:
                with open(p, 'rb') as f_in:
                    shutil.copyfileobj(f_in, f_out, length=1024*1024)
    except Exception as e:
        emit(f'ERROR: Failed while stitching parts ({type(e).__name__}: {e})')
        cleanup_files(parts + [final_path])
        return False, final_path

    cleanup_files(parts)

    if os.path.exists(final_path) and os.path.getsize(final_path) >= MIN_VALID_BYTES:
        emit(f'Completed successfully ({os.path.getsize(final_path):,} bytes)')
        return True, final_path
    emit('ERROR: Final file is missing or too small after stitching')
    return False, final_path


def headless_chd_compress(file_path, chdman_path, progress_cb=None):
    """
    Compress a disc image to CHD. Returns (success, output_path).
    progress_cb(pct_float) called periodically.
    """
    if not chdman_path or not os.path.exists(chdman_path):
        return False, file_path

    extract_dir = os.path.dirname(file_path)
    # Track files we create so we only clean up our own work
    extracted_files = set()

    # If it's a zip, extract first
    if zipfile.is_zipfile(file_path):
        with zipfile.ZipFile(file_path, 'r') as z:
            for member in z.namelist():
                extracted_files.add(
                    os.path.normcase(os.path.join(extract_dir, member))
                )
            _safe_extractall(z, extract_dir)

    src_file = None
    src_ext = None
    for ext in ['.gdi', '.cue', '.iso']:
        for f in os.listdir(extract_dir):
            if f.lower().endswith(ext):
                candidate = os.path.join(extract_dir, f)
                # Prefer files we just extracted; fall back to any match
                if not extracted_files or os.path.normcase(candidate) in extracted_files:
                    src_file = candidate
                    src_ext = ext
                    break
        if src_file:
            break

    if not src_file:
        return False, file_path

    chd_out = os.path.splitext(src_file)[0] + ".chd"
    modes = ['createdvd', 'createcd'] if src_ext == '.iso' else ['createcd']
    si = None
    if os.name == 'nt':
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    for mode in modes:
        cmd = [chdman_path, mode, '-i', src_file, '-o', chd_out, '-f']
        try:
            p = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                startupinfo=si, text=True, bufsize=1
            )
            for line in p.stdout:
                line = line.rstrip()
                if line and progress_cb:
                    m = re.search(r'(\d+(?:\.\d+)?)%', line)
                    if m:
                        try:
                            progress_cb(float(m.group(1)))
                        except ValueError:
                            pass
            p.wait()
            if p.returncode == 0 and os.path.exists(chd_out):
                # Cleanup: only remove the original download + extracted files
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception:
                    pass
                for ef in extracted_files:
                    try:
                        if os.path.exists(ef) and os.path.normcase(ef) != os.path.normcase(chd_out):
                            os.remove(ef)
                    except Exception:
                        pass
                return True, chd_out
        except Exception:
            pass

    if os.path.exists(chd_out):
        os.remove(chd_out)
    return False, file_path


# ---------------------------------------------------------------------------
# On-demand download popup (minimal GUI for launcher integration)
# ---------------------------------------------------------------------------

class DownloadPopup(ctk.CTk):
    """Minimal progress window for on-demand ROM downloads from RetroBat."""

    def __init__(self, rom_name, system_name, myrient_path, dest_dir,
                 console_type=None, config=None):
        super().__init__()
        self.title("MyriFetch — Downloading...")
        self._win_w = 760
        self._win_h = 520
        self.geometry(f"{self._win_w}x{self._win_h}")
        self.resizable(False, False)
        self.configure(fg_color=C['bg'])
        self.attributes('-topmost', True)
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self._win_w // 2)
        y = (self.winfo_screenheight() // 2) - (self._win_h // 2)
        self.geometry(f"{self._win_w}x{self._win_h}+{x}+{y}")

        self.rom_name = rom_name
        self.system_name = system_name
        self.myrient_path = myrient_path
        self.dest_dir = dest_dir
        self.console_type = console_type
        self.config = config or {}
        self.result_path = None
        self.success = False
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # start running
        self._last_error_detail = ''

        # UI
        ctk.CTkLabel(
            self, text=f"📥  {system_name}",
            font=('Arial', 18, 'bold'), text_color=C['cyan']
        ).pack(pady=(15, 2))

        display_name = rom_name if len(rom_name) < 55 else rom_name[:52] + '...'
        ctk.CTkLabel(
            self, text=display_name,
            font=('Arial', 14), text_color='white', wraplength=self._win_w - 40
        ).pack(pady=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(
            self, width=self._win_w - 60, height=18,
            progress_color=C['cyan'], fg_color=C['card']
        )
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        info_frame = ctk.CTkFrame(self, fg_color='transparent')
        info_frame.pack(fill='x', padx=24)
        self.lbl_speed = ctk.CTkLabel(
            info_frame, text="Connecting...",
            font=('Consolas', 13, 'bold'), text_color=C['dim']
        )
        self.lbl_speed.pack(side='left')
        self.lbl_eta = ctk.CTkLabel(
            info_frame, text="",
            font=('Consolas', 13, 'bold'), text_color=C['dim']
        )
        self.lbl_eta.pack(side='right')

        self.lbl_status = ctk.CTkLabel(
            self, text="", font=('Arial', 12), text_color=C['dim'],
            wraplength=self._win_w - 50
        )
        self.lbl_status.pack(pady=(5, 0))

        self.log_box = ctk.CTkTextbox(
            self, height=250, fg_color=C['card'], font=('Consolas', 13)
        )
        self.log_box.pack(fill='both', expand=True, padx=15, pady=(8, 8))
        self.log_box.configure(state='disabled')

        self.btn_cancel = ctk.CTkButton(
            self, text="Cancel", width=130, height=36,
            font=('Arial', 14, 'bold'),
            fg_color=C['pink'], hover_color='#990033',
            command=self._on_cancel
        )
        self.btn_cancel.pack(pady=(0, 10))

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._log_popup_event(
            f'Session started for {self.system_name} / {self.rom_name}'
        )
        self._log_popup_event(f'Destination folder: {self.dest_dir}')
        self._log_popup_event(f'Log file: {ON_DEMAND_LOG_FILE}')

        # Start download in background
        self._start_time = time.time()
        threading.Thread(target=self._run_download, daemon=True).start()

    def _append_ui_log(self, msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        line = f'[{timestamp}] {msg}\n'

        def _do():
            try:
                self.log_box.configure(state='normal')
                self.log_box.insert('end', line)
                self.log_box.see('end')
                self.log_box.configure(state='disabled')
            except Exception:
                pass

        self.after(0, _do)

    def _log_popup_event(self, msg):
        _append_on_demand_log('popup', f'{self.system_name}/{self.rom_name}: {msg}')
        self._append_ui_log(msg)

    def _on_download_event(self, msg):
        self._append_ui_log(msg)
        if msg.startswith('ERROR:') or 'failed' in msg.lower():
            self._last_error_detail = msg

    def _on_cancel(self):
        self._cancel_event.set()
        self.btn_cancel.configure(state='disabled', text='Cancelling...')
        self._log_popup_event('Cancel requested by user')

    def _update_progress(self, pct, speed, downloaded, total):
        def _do():
            self.progress_bar.set(min(pct, 1.0))
            self.lbl_speed.configure(text=f"{speed:.1f} MB/s")
            if total > 0 and speed > 0:
                remaining = (total - downloaded) / (speed * 1024 * 1024)
                mins, secs = divmod(int(remaining), 60)
                self.lbl_eta.configure(text=f"~{mins}:{secs:02d} remaining")
            dl_mb = downloaded / 1024 / 1024
            if total > 0:
                total_mb = total / 1024 / 1024
                self.lbl_status.configure(
                    text=f"{dl_mb:.0f} / {total_mb:.0f} MB ({pct*100:.0f}%)"
                )
            else:
                self.lbl_status.configure(text=f"{dl_mb:.1f} MB downloaded")
        self.after(0, _do)

    def _update_chd_progress(self, pct):
        def _do():
            self.progress_bar.set(pct / 100)
            self.lbl_speed.configure(text="Compressing...")
            self.lbl_eta.configure(text=f"{pct:.0f}%")
            self.lbl_status.configure(text="Creating CHD file...")
        self.after(0, _do)

    def _download_cover_art(self, downloaded_path):
        """
        Fetch artwork via ScreenScraper right after a game is downloaded.
        Saves box-3D thumbnail next to the ROM and writes gamelist.xml tags.
        """
        ss_user = str(self.config.get('ss_user', '')).strip()
        ss_pass = str(self.config.get('ss_password', '')).strip()
        if not ss_user or not ss_pass:
            self._log_popup_event('Artwork skipped: no ScreenScraper credentials')
            return

        console_name = self.console_type or ''
        system_id = CONSOLE_TO_SS_ID.get(console_name)
        if not system_id:
            self._log_popup_event(
                f'Artwork skipped: no ScreenScraper system ID for {console_name!r}'
            )
            return

        target_path = downloaded_path or os.path.join(
            self.dest_dir, self.rom_name or ''
        )
        rom_basename = os.path.basename(target_path)
        base_name    = os.path.splitext(rom_basename)[0]
        rom_dir      = os.path.dirname(target_path) or self.dest_dir

        self._log_popup_event(f'Artwork lookup (ScreenScraper): {rom_basename}')
        try:
            ss  = ScreenScraperManager(ss_user, ss_pass)
            jeu = ss.lookup_game(rom_basename, system_id,
                                 log_cb=self._log_popup_event)
            if not jeu:
                self._log_popup_event('Artwork: game not found on ScreenScraper')
                return

            # box-3D → thumbnail next to ROM (matches your es_settings.cfg)
            images_dir = os.path.join(rom_dir, 'images')
            videos_dir = os.path.join(rom_dir, 'videos')
            steps = [
                ('box-3D',  os.path.join(rom_dir,    f'{base_name}.jpg')),
                ('sstitle', os.path.join(images_dir, f'{base_name}-image.png')),
                ('marquee', os.path.join(images_dir, f'{base_name}-marquee.png')),
                ('video',   os.path.join(videos_dir, f'{base_name}-video.mp4')),
            ]
            meta = {}
            for media_type, dest in steps:
                url = ss._find_media(jeu, media_type)
                if url and ss.download_media(url, dest,
                                             log_cb=self._log_popup_event):
                    meta[{
                        'box-3D':  'thumbnail',
                        'sstitle': 'image',
                        'marquee': 'marquee',
                        'video':   'video',
                    }[media_type]] = dest

            # Text metadata
            lang = str(self.config.get('language', 'en')).lower()[:2]
            meta.update({
                'desc':        _ss_pick_text(jeu.get('synopsis') or [], lang),
                'genre':       _ss_pick_genres(jeu),
                'developer':   _ss_pick_company(jeu, 'developpeur'),
                'publisher':   _ss_pick_company(jeu, 'editeur'),
                'releasedate': _ss_pick_date(jeu),
                'players':     str(jeu.get('joueurs') or ''),
                'rating':      _ss_pick_rating(jeu),
            })

            # Write to gamelist.xml
            game_stub = {'path': target_path, 'name': base_name,
                         'console': console_name}
            self._writeback_scraped_meta_popup(game_stub, rom_dir, meta)

        except Exception as e:
            self._log_popup_event(
                f'Artwork error: {type(e).__name__}: {e}'
            )

    def _writeback_scraped_meta_popup(
        self, game: dict, rom_dir: str, meta: dict
    ) -> None:
        """Write ScreenScraper metadata to gamelist.xml from DownloadPopup context."""
        gamelist_path = os.path.join(rom_dir, 'gamelist.xml')
        if not os.path.isfile(gamelist_path):
            return
        try:
            tree = ET.parse(gamelist_path)
            root = tree.getroot()
        except Exception:
            return

        rom_base = os.path.splitext(
            os.path.basename(game.get('path', ''))
        )[0].lower()

        for game_el in root.findall('game'):
            path_el = game_el.find('path')
            if path_el is None:
                continue
            entry_base = os.path.splitext(
                os.path.basename((path_el.text or '').lstrip('./\\'))
            )[0].lower()
            if entry_base != rom_base:
                continue

            tag_map = {
                'image':       meta.get('image'),
                'thumbnail':   meta.get('thumbnail'),
                'marquee':     meta.get('marquee'),
                'video':       meta.get('video'),
                'desc':        meta.get('desc'),
                'genre':       meta.get('genre'),
                'developer':   meta.get('developer'),
                'publisher':   meta.get('publisher'),
                'releasedate': meta.get('releasedate'),
                'players':     meta.get('players'),
                'rating':      meta.get('rating'),
            }
            for tag, value in tag_map.items():
                if not value:
                    continue
                if os.path.isabs(str(value)):
                    try:
                        rel = os.path.relpath(value, rom_dir)
                        value = './' + rel.replace('\\', '/')
                    except ValueError:
                        pass
                el = game_el.find(tag)
                if el is None:
                    el = ET.SubElement(game_el, tag)
                el.text = str(value)
            if meta.get('genre'):
                for g_el in game_el.findall('genre'):
                    if (g_el.text or '').strip().lower() == 'available to download':
                        game_el.remove(g_el)
                        break
            break

        tmp = gamelist_path + '.tmp'
        try:
            tree.write(tmp, encoding='utf-8', xml_declaration=True)
            os.replace(tmp, gamelist_path)
        except Exception:
            try:
                os.remove(tmp)
            except OSError:
                pass

    def _run_download(self):
        success = False
        path = None
        source_mode = _get_download_source_mode(self.config)
        source_order = _source_mode_order(source_mode)
        mode_label = DOWNLOAD_SOURCE_MODE_LABELS.get(source_mode, source_mode)
        self._log_popup_event(f'Download source mode: {mode_label}')

        for idx, source in enumerate(source_order, 1):
            if self._cancel_event.is_set():
                break
            self.after(0, lambda: (
                self.progress_bar.set(0),
                self.lbl_eta.configure(text=""),
                self.lbl_status.configure(text="")
            ))

            if source == 'myrient':
                self._log_popup_event(
                    f'Source {idx}/{len(source_order)}: Myrient'
                )
                success, path = headless_download(
                    self.rom_name, self.myrient_path, self.dest_dir,
                    self._cancel_event, self._pause_event,
                    progress_cb=self._update_progress,
                    event_cb=self._on_download_event,
                    download_config=self.config
                )
            elif source == 'archive':
                self._log_popup_event(
                    f'Source {idx}/{len(source_order)}: Archive.org lookup'
                )
                archive_session = requests.Session()
                archive_url = _archive_find_direct_url(
                    archive_session, self.rom_name, log_cb=self._on_download_event
                )
                if not archive_url:
                    self._log_popup_event('Archive.org: no exact filename match found')
                    success = False
                    continue
                self._log_popup_event(f'Archive.org match: {archive_url}')
                success, path = headless_download(
                    self.rom_name, archive_url, self.dest_dir,
                    self._cancel_event, self._pause_event,
                    progress_cb=self._update_progress,
                    event_cb=self._on_download_event,
                    download_config=self.config
                )
            elif source == 'qbittorrent':
                self._log_popup_event(
                    f'Source {idx}/{len(source_order)}: qBittorrent + Torznab'
                )
                final_path = os.path.join(self.dest_dir, self.rom_name)
                success, path = _download_via_qbittorrent(
                    self.rom_name,
                    self.dest_dir,
                    final_path,
                    self._cancel_event,
                    progress_cb=self._update_progress,
                    log_cb=self._on_download_event,
                    config=self.config
                )
            else:
                self._log_popup_event(f'Unknown source {source!r}; skipping')
                success = False

            if success or self._cancel_event.is_set():
                break
            self._log_popup_event(f'Source {source} failed, trying next source')

        if not success or self._cancel_event.is_set():
            if not self._cancel_event.is_set():
                detail = self._last_error_detail or 'No detailed error captured.'
                self._log_popup_event(f'Final failure: {detail}')
                self.after(0, lambda: (
                    self.lbl_speed.configure(text="Download failed"),
                    self.lbl_eta.configure(text=""),
                    self.lbl_status.configure(
                        text=f"Could not download file. {detail[:180]}"
                    ),
                    self.progress_bar.set(0),
                    self.btn_cancel.configure(text="Close", state='normal')
                ))
            else:
                self._log_popup_event('Popup closing due to cancellation')
                self.after(0, self.destroy)
            return

        # CHD compression if enabled
        c_type = self.console_type
        use_chd, setting_key = _use_chdman_for_console(self.config, c_type)
        chd_exe = self.config.get('chdman_path') or shutil.which('chdman')
        if setting_key:
            self._log_popup_event(f'CHD setting {setting_key}={use_chd}')
        elif c_type:
            self._log_popup_event(
                f'CHD skipped: unsupported console type for CHD setting ({c_type})'
            )

        if use_chd and chd_exe and c_type:
            self._log_popup_event(f'CHD compression enabled with {chd_exe}')
            self.after(0, lambda: self.lbl_speed.configure(text="Compressing..."))
            self.after(0, lambda: self.progress_bar.set(0))
            self.after(0, lambda: self.btn_cancel.configure(state='disabled'))

            ok, chd_path = headless_chd_compress(
                path, chd_exe, progress_cb=self._update_chd_progress
            )
            if ok:
                self._log_popup_event(f'CHD compression succeeded: {chd_path}')
                path = chd_path
            else:
                self._log_popup_event('CHD compression failed; using original download')

        self._download_cover_art(path)

        # TeknoParrot post-processing: extract zip to subfolder, create .parrot
        if self.console_type == 'TeknoParrot' or _is_teknoparrot_path(self.myrient_path):
            self._log_popup_event('TeknoParrot: extracting zip and creating .parrot file...')
            self.after(0, lambda: (
                self.lbl_speed.configure(text="Extracting..."),
                self.progress_bar.configure(mode='indeterminate'),
                self.progress_bar.start()
            ))
            tp_ok, tp_path = teknoparrot_post_process(
                path, self.dest_dir,
                log_cb=self._log_popup_event
            )
            self.after(0, lambda: (
                self.progress_bar.stop(),
                self.progress_bar.configure(mode='determinate'),
                self.progress_bar.set(1.0)
            ))
            if tp_ok:
                path = tp_path
                self._log_popup_event(f'TeknoParrot ready: {tp_path}')
            else:
                self._log_popup_event('TeknoParrot extraction failed; keeping zip')

        self.success = True
        self.result_path = path
        self._log_popup_event(f'Download complete: {path}')

        # Auto-writeback: update gamelist.xml immediately so ES reflects the
        # real file on next reload — covers both GUI and on-demand downloads.
        # dest_dir is the ROM folder; rom_name is the original stub filename.
        if self.dest_dir and self.rom_name:
            wb_ok = gamelist_writeback(self.dest_dir, self.rom_name, path)
            self._log_popup_event(
                f'gamelist_writeback: {"OK" if wb_ok else "no-op / not found (non-fatal)"}'
            )

        self.after(0, self.destroy)


# ---------------------------------------------------------------------------
# CLI entry point for on-demand downloads
# ---------------------------------------------------------------------------

def run_cli_download(args):
    """Run a headless download with a minimal popup. Returns exit code."""
    system = args.system
    rom_name = args.download
    dest = args.dest
    myrient_path = args.myrient_path
    source_mode_override = (args.source_mode or '').strip()
    _append_on_demand_log(
        'cli',
        f'Invoked with system={system!r}, rom={rom_name!r}, '
        f'myrient_path={myrient_path!r}, dest={dest!r}, '
        f'source_mode_override={source_mode_override!r}'
    )

    # If myrient_path not given, resolve from system name
    if not myrient_path:
        myrient_path = SYSTEM_TO_MYRIENT.get(system)
        if not myrient_path:
            _append_on_demand_log('cli', f'ERROR: Unknown system {system!r}')
            print(f"[MyriFetch] Unknown system: {system}", file=sys.stderr)
            return 1

    if not dest:
        _append_on_demand_log('cli', 'ERROR: Missing --dest argument')
        print("[MyriFetch] --dest is required", file=sys.stderr)
        return 1

    # Load config for CHD settings
    config = {}
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if not isinstance(config, dict):
                config = {}
    except Exception:
        _append_on_demand_log('cli', 'WARN: Failed to load config for CHD settings')

    if source_mode_override:
        if source_mode_override in DOWNLOAD_SOURCE_MODE_LABELS:
            config['download_source_mode'] = source_mode_override
            _append_on_demand_log(
                'cli',
                f'Using launcher source mode override: {source_mode_override}'
            )
        else:
            _append_on_demand_log(
                'cli',
                f'WARN: Invalid --source-mode {source_mode_override!r}; '
                f'falling back to config/default'
            )

    console_type = SYSTEM_TO_CONSOLE.get(system)
    _append_on_demand_log(
        'cli',
        f'Opening popup for console_type={console_type!r}, log={ON_DEMAND_LOG_FILE}'
    )

    popup = DownloadPopup(
        rom_name=rom_name,
        system_name=console_type or system,
        myrient_path=myrient_path,
        dest_dir=dest,
        console_type=console_type,
        config=config
    )
    popup.mainloop()

    if popup.success:
        _append_on_demand_log('cli', f'Success, output={popup.result_path!r}')
        # Write back to gamelist.xml: update path, remove <hidden>, fix CHD drift.
        if popup.result_path and dest:
            wb_ok = gamelist_writeback(dest, rom_name, popup.result_path)
            _append_on_demand_log(
                'cli',
                f'gamelist_writeback {"succeeded" if wb_ok else "failed (non-fatal)"}'
            )
        return 0
    _append_on_demand_log(
        'cli',
        f'Failed or cancelled, last_result={popup.result_path!r}'
    )
    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MyriFetch ROM Manager')
    parser.add_argument('--download', type=str, default=None,
                        help='ROM filename to download (headless mode)')
    parser.add_argument('--system', type=str, default=None,
                        help='RetroBat system name (e.g. psx, ps2, gamecube)')
    parser.add_argument('--myrient-path', type=str, default=None,
                        help='Myrient catalog path (auto-resolved from --system if omitted)')
    parser.add_argument('--dest', type=str, default=None,
                        help='Destination directory for download')
    parser.add_argument('--source-mode', type=str, default=None,
                        help='Override source mode for this launch only')
    cli_args, remaining = parser.parse_known_args()

    if cli_args.download:
        sys.exit(run_cli_download(cli_args))
    else:
        try:
            app = UltimateApp()
            app.mainloop()
        except Exception:
            # FIXED: single except block; don't create new Tk() root (crashes macOS)
            error_msg = traceback.format_exc()
            print(error_msg, file=sys.stderr)
            try:
                messagebox.showerror(
                    "Critical Error",
                    f"MyriFetch crashed.\n\nSee terminal/stderr for full details.\n\n"
                    f"{error_msg[:600]}"
                )
            except Exception:
                pass
