# 👾 MyriFetch - personal experimental fork

A fork of MyriFetch with the goal of making it much better, more user-friendly, and deeply integrated into RetroBat (and eventually other emulators and frontends).

MyriFetch is a modern, high-performance ROM manager and downloader designed specifically for the Myrient (Erista) repository. It replaces manual browser downloads with a sleek, dark-mode GUI capable of browsing, queuing, and accelerating downloads via multi-threading.

## ✨ Features

* 🚀 **"Hydra" Download Engine**: Splits files into 4 parallel chunks (threads) to maximize bandwidth. Per-part integrity verification ensures no silent corruption.
* 📦 **Bulk Queue System**: Select multiple games, add them to a 100-item batch queue, and let it run in the background.
* 🏆 **RetroAchievements Integration**: Connect your RA account to view your profile stats, points, and rank directly within the app.
* 🎨 **IGDB Metadata & Box Art**: Integrated with Twitch/IGDB API to automatically fetch high-quality box art, descriptions, genres, and release dates for your library.
* 💾 **Smart Resume & Integrity**: Atomic config saves prevent data loss on crash. Per-part size verification catches corrupt downloads before stitching. Includes "Pause," "Resume," and "Stop" features for safe download management.
* 📂 **Library Manager**: Scan your local folders to view your collection, see what you're missing, and open file locations directly from the app. Ownership detection uses a fast single-pass directory scan instead of per-file lookups.
* 🛠️ **BIOS Downloader**: One-click downloads for essential RetroArch and emulator BIOS packs.
* 🐧 **Cross-Platform**: Runs natively on Windows, Linux, and macOS.
* 🔍 **Live Search**: Debounced real-time filtering as you type — no need to press Enter.
* 🎮 **RetroBat Integration**: Auto-detect your RetroBat install, one-click console folder mapping, and gamelist sync with lightweight placeholder files so all Myrient titles appear in EmulationStation — downloaded or not.
* 🚀 **On-Demand Launcher**: Select any game in EmulationStation — if the ROM is missing, MyriFetch automatically downloads it with a progress popup, optionally compresses to CHD, then launches the game. No manual downloading needed.

## 🎮 Supported Platforms

* Sony PlayStation 1, 2, 3 & PSP
* Nintendo GameCube, Wii, 3DS, DS, GBA, SNES
* Sega Dreamcast
* Microsoft Xbox
* And more via the custom folder browser...

<img width="1102" height="882" alt="Screenshot 2026-02-14 163818" src="https://github.com/user-attachments/assets/7dfea677-7204-4ffe-bdfb-9f9e58d4e487" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 163849" src="https://github.com/user-attachments/assets/cc7948ba-8a59-4765-9c18-576fe383f4b2" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164026" src="https://github.com/user-attachments/assets/9f3029d6-f60d-4804-a5cc-b354d0aa7b1e" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164130" src="https://github.com/user-attachments/assets/944dfa55-5d21-43cb-b7b6-e2f69548f068" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164141" src="https://github.com/user-attachments/assets/e1d6be2b-4417-4d70-851b-ab6554f05199" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164207" src="https://github.com/user-attachments/assets/f7ab9403-26c5-490c-9b6e-44087a6d0363" />
<img width="1102" height="882" alt="Screenshot 2026-02-14 164214" src="https://github.com/user-attachments/assets/13a07311-a4d2-4652-bf7c-9353fe42ec32" />

## 🛠️ Installation & Usage

### Windows

1. Download the latest `MyriFetch-Windows.exe` from the [Releases] page.
2. Run the executable.
3. **Setup**: Go to **Settings** to map your console folders and enter your Twitch/RA API keys for the full experience.

### Linux

1. Download `MyriFetch-Linux-Appimage.AppImage`.
2. Make it executable: `chmod +x MyriFetch-Linux-Appimage.AppImage`.
3. Run `MyriFetch-Linux-Appimage.AppImage`.
4. **Setup**: Go to **Settings** to map your console folders and enter your Twitch/RA API keys for the full experience.

### macOS

1. Download `MyriFetch-macOS`.
2. Open your terminal and navigate to the download location.
3. Make the script executable: `chmod +x MyriFetch-macOS`.
4. Run the script: `./MyriFetch-macOS`.
5. **Setup**: Go to **Settings** to map your console folders and enter your Twitch/RA API keys for the full experience.

## 💿 CHDman Usage

### Windows

For safety and security reasons, this repository does not include the chdman.exe executable. Since you cannot always trust third-party binaries and repositories, it is best to download it yourself directly from the official source. This also ensures you get the most recent and compatible version.

1. Go to the [official MAME tools download page](https://www.mamedev.org/release.html), download and install MAME.
2. Go to the CHDman section in settings and select the path to CHDman (where you installed the tools to).
3. Turn on compression per system (PS1, PS2, PSP and Dreamcast).

### Linux

On most distributions, `chdman` is bundled with the `mame-tools` package.

**Method 1: Native Package Manager**

1. Open your terminal.
2. Run the command for your distribution:

**Debian / Ubuntu / Linux Mint:**
```bash
sudo apt install mame-tools
```

**Arch Linux / Manjaro:**
```bash
sudo pacman -S mame-tools
```

**Fedora:**
```bash
sudo dnf install mame-tools
```

**Method 2: Homebrew (Alternative)**

Alternatively, if you use Homebrew on Linux:

1. Open Terminal.
2. Run the following command:
```bash
brew install rom-tools
```

3. Once installed, the program should recognise where the executable is located.

### MacOS

On macOS, `chdman` is available through Homebrew in the `rom-tools` package.

1. Open Terminal.
2. Install Homebrew if you haven't already (https://brew.sh).
3. Run the following command:
```bash
brew install rom-tools
```

## 🏗️ Building from Source

**Requirements**: Python 3.10+, pip

```bash
# Clone the repo
git clone https://github.com/CrabbieMike/MyriFetch.git
cd MyriFetch

# Install dependencies
pip install -r requirements.txt

# Run
python MyriFetch.py

```

## 🎮 RetroBat Integration

MyriFetch can integrate directly with your [RetroBat](https://www.retrobat.org/) installation:

1. **Auto-Map Console Folders**: Go to Settings → RetroBat Integration, set your RetroBat install path (default `C:\retrobat`), and click **"Detect & Auto-Map Consoles"**. MyriFetch will scan `roms\` and auto-fill all 12 console folder mappings.
2. **Sync Gamelists**: Click **"Sync All Gamelists"** to fetch the full Myrient catalog for each mapped system, write `gamelist.xml`, and create lightweight placeholder ROM stubs for missing files. EmulationStation will then show all available titles — downloaded or not.
3. **Per-Console Mapping Display**: After auto-detection, the Settings panel shows each mapped console and its corresponding RetroBat `roms\` subfolder so you can verify the mappings at a glance.
4. **Cleanup Option**: Use **"Remove Stub Files"** if you want to hide not-yet-downloaded titles again.

### Supported RetroBat System Mappings

| MyriFetch Console | RetroBat Folder |
|---|---|
| PlayStation 1 | `psx` |
| PlayStation 2 | `ps2` |
| PlayStation 3 | `ps3` |
| PSP | `psp` |
| GameCube | `gamecube` |
| Wii | `wii` |
| Dreamcast | `dreamcast` |
| Xbox | `xbox` |
| SNES | `snes` |
| GBA | `gba` |
| Nintendo DS | `nds` |
| Nintendo 3DS | `3ds` |

### 🚀 On-Demand Download from EmulationStation

When RetroBat shows all available games (via synced gamelists) and you launch a game you don't own, MyriFetch intercepts the launch, downloads the ROM from Myrient with a progress popup, optionally compresses it to CHD, and then auto-launches the game — all seamlessly.

**Setup:**

1. Go to **Settings → On-Demand Launcher** and click **"Enable On-Demand Launcher"**.
2. MyriFetch patches `es_systems.cfg` to route game launches through its wrapper script for all 12 supported systems. A `.myrient.bak` backup is created automatically.
3. **Restart RetroBat** for the changes to take effect.
4. Launch any game — if the ROM exists, it plays instantly with zero overhead. If missing, a download popup appears.

**Features:**
- Minimal progress popup with speed, ETA, progress bar, and cancel button
- Automatic retry (up to 2 retries) on network failure
- CHD compression after download (if enabled for that system in Settings)
- Clean cancellation — no orphan files left behind
- Fast pass-through for owned games (~50ms overhead)

**To disable:** Go to Settings → On-Demand Launcher → **"Restore Original es_systems.cfg"**.

## ⚙️ Advanced Customization

The **Settings** menu allows you to:

* **Theme Switching**: Choose between Cyber Dark, Nord, Gruvbox, and Matrix themes.
* **Browser Text Size**: Adjust the UI font size for better readability on high-resolution displays.
* **Content Filters**: Toggle filters for Demos and Revision files to keep your search results clean.
* **Storage Monitoring**: Real-time tracking of free space on your mapped drives.
* **Game Subfolders**: Toggle per-game subfolder organization for downloads.
* **CHDman Compression**: Automatically compress ISO/BIN/CUE to CHD format after download for supported systems (PS1, PS2, PSP, Dreamcast).

## 🔄 What's New in v1.4.2

* **Atomic config saves** — no more data loss on crash or power failure
* **Per-part download integrity** — each chunk is size-verified before stitching; corrupt downloads are caught and reported
* **Zip slip prevention** — safe extraction guards against path traversal attacks
* **Ownership cache** — library and browser ownership detection is now a fast single-pass scan instead of per-file stat calls
* **Live search** — debounced filtering as you type (300ms delay)
* **Connection pooling** — all HTTP requests go through a shared session, eliminating redundant TLS handshakes
* **Fixed PS1 icons** — LaunchBox mapping corrected (was "Sony Federation")
* **Fixed filter overlap** — region and status filters now both visible on separate rows
* **Fixed IGDB queries** — file extensions stripped before search; special characters escaped
* **Fixed lambda closures** — download speed and progress displays now show current values, not stale ones
* **Thread-safe UI** — all widget updates from background threads dispatched through `after()`
* **RetroBat integration** — auto-map consoles, sync gamelists, per-console mapping display
* **On-demand launcher** — select a missing game in EmulationStation and MyriFetch downloads it automatically with a progress popup, optional CHD compression, and auto-launch
* **threading.Event download control** — pause/resume/cancel uses proper thread synchronization instead of busy-polling
* **Version check** — "Check for Updates" queries the GitHub Releases API and shows a dialog if a newer version exists
* **Download All size estimate** — bulk download confirmation now shows total estimated size (e.g. "Queue 4,231 files (~1.2 TB)?")
* **Improved CHD processing** — line-buffered progress reading instead of char-by-char

## ⚠️ Disclaimer

This software is for archival and preservation purposes only. The developer is not affiliated with Myrient/Erista or RetroAchievements. Please support the original hardware and developers when possible.
