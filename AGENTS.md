# Repository Guidelines

## Project Structure & Module Organization
`MyriFetch.py` is the main application entry point and contains the GUI, download engine, API integrations, and settings logic. Root-level assets include `icon.png`, `icon.ico`, and `MyriFetch.desktop`. Build helpers live at the root (`Build_Windows.bat`, `build_appimage.sh`).
`retrobat/` contains RetroBat integration assets, templates, and installer resources; treat it as data/config content unless you are intentionally changing RetroBat packaging behavior.
CI definitions are under `.github/workflows/`.

## Build, Test, and Development Commands
- `python -m venv .venv && .venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/macOS): create and activate a local environment.
- `pip install -r requirements.txt`: install runtime dependencies.
- `python MyriFetch.py`: run the app locally.
- `python -m py_compile MyriFetch.py`: quick syntax validation before commit.
- `Build_Windows.bat`: clean Windows PyInstaller build to `dist/MyriFetch.exe`.
- `bash build_appimage.sh`: Linux AppImage build flow.

## Coding Style & Naming Conventions
Use Python with 4-space indentation and PEP 8 spacing. Follow existing naming patterns:
- `snake_case` for functions/variables (`refresh_dir`, `download_list`)
- `CamelCase` for classes (`UltimateApp`, `TwitchManager`)
- `UPPER_CASE` for module constants (`APP_NAME`, `NUM_THREADS`)
Keep platform-specific logic explicit (`os.name`, `platform.system()`), and route UI updates from worker threads through Tk/CTk-safe callbacks (for example `after()`).

## Testing Guidelines
There is no dedicated automated test suite in this repo yet. For changes, include:
- syntax check (`python -m py_compile MyriFetch.py`)
- manual smoke test of affected flows (browse, queue, download, pause/resume, settings save/load)
- platform-specific verification when touching build scripts
If you add testable logic, introduce focused `pytest` tests in a new `tests/` directory.

## Commit & Pull Request Guidelines
Recent history uses short, imperative commit messages (for example: `Update README.md`, `Added CHD support using chdman`). Keep commits small and single-purpose.
PRs should include:
- what changed and why
- platforms tested (Windows/Linux/macOS)
- screenshots for UI changes
- linked issue(s) when applicable

## Security & Configuration Tips
Do not commit API keys, personal tokens, or local machine-specific paths from settings. Treat generated output (`build/`, `dist/`, `build_venv/`) as temporary artifacts, not source.
