# Objective
Make RetroBat gamelists ownership-aware to visually distinguish local games from cloud stubs, and fix the "CHD drift" issue where RetroBat keeps trying to launch an outdated `.zip` stub path after a game is downloaded and compressed.

# Background & Motivation
Currently, when a user syncs gamelists via MyriFetch, the `_write_gamelist_xml` function writes the exact Myrient catalog filename (usually a `.zip`) for every single game. This approach causes two major UX issues:
1. **Visibility:** The user cannot tell which games in EmulationStation are locally owned and which are stubs waiting to be downloaded.
2. **CHD Drift:** If a user downloads a `.zip` game and MyriFetch successfully compresses it to a `.chd` file, the `gamelist.xml` is not updated. RetroBat continues to pass the old `.zip` path to the launcher, causing it to fall back into the slow "on-demand download" path instead of instantly launching the owned `.chd`.

# Proposed Solution
We will update `_write_gamelist_xml` in `MyriFetch.py` to be **ownership-aware**:
1. **Local Scan:** Before writing the XML for a console, the function will scan the local ROM directory to build a map of existing files.
2. **Extension Check:** For each Myrient catalog entry, we will check if the user already owns the game. We will check the exact filename and common alternative extensions (e.g., `.chd`, `.rvz`, `.iso`, `.cue`, `.gdi`, etc.).
3. **Owned Game Handling:** If the game is owned, the gamelist `<path>` will point to the actual local file extension (e.g., the `.chd`), ensuring the "fast path" launch works correctly. The `<name>` will be kept clean without prefixes.
4. **Stub Game Handling:** If the game is missing (a stub), the gamelist `<name>` will be prefixed with `[Download] ` so the user can visually identify it.
5. **RetroBat Toggle Support:** For stub games, we will also inject a `<genre>Available to Download</genre>` tag. This allows the user to easily hide or show the entire Myrient catalog using EmulationStation's built-in UI genre filters.

# Implementation Steps
1. Modify `_write_gamelist_xml` in `MyriFetch.py`:
   - Use `os.scandir` to collect all local files in `rom_dir`.
   - Iterate over `file_list` from the catalog.
   - Extract the `base_name` (filename without extension).
   - Check against `local_files` for `.zip`, `.chd`, `.rvz`, `.iso`, `.cso`, `.cue`, `.gdi`. Ensure the matching file is *not* a MyriFetch stub using the existing `_is_myrifetch_stub` function.
   - Build the `lines` list:
     - `path`: `./{_esc(real_fname)}`
     - `name`: `[Download] {_esc(base_name)}` (if stub) or `{_esc(base_name)}` (if owned)
     - `genre`: `Available to Download` (if stub)

# Verification
1. Run MyriFetch and click "Sync All Gamelists".
2. Open EmulationStation/RetroBat.
3. Verify that games not downloaded yet show up with the `[Download]` prefix.
4. Verify that games already downloaded and converted to `.chd` do not have the prefix.
5. Launch a previously downloaded `.chd` game and verify it boots immediately via the fast path without prompting the MyriFetch download window.
6. Verify that filtering by the "Available to Download" genre works in the EmulationStation UI.