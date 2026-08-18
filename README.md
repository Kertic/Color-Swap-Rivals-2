# Color-Swap-Rivals-2
A continuation of https://github.com/Keryan-666/Color-Swap-ROA-2 which enables you to change colors of different skin palettes 

## Installation

Clone the repo (or download it with the green **Code** button), then run the setup script once:

```
git clone https://github.com/Kertic/Color-Swap-Rivals-2
cd Color-Swap-Rivals-2
setup.bat
```

`setup.bat` installs anything missing: **Python 3** + the **Pillow** library, the **.NET 8 Desktop Runtime**, and the latest **FModel** release (downloaded into the tool's `FModel/` subfolder, used by the Update Game Data button). Anything already present is detected and skipped, so it's safe to re-run. Python and .NET are installed with winget (built into Windows 10/11); the .NET step may show a UAC prompt.

If winget's package source is broken, setup repairs it with `winget source reset` and retries; failing that it downloads the official installer from python.org instead. You should not need to fix winget yourself.

Setup also records the Python interpreter it found in `python_path.txt`, which `Start.vbs` and `run_importer.bat` use directly. This sidesteps a common Windows problem: the Microsoft Store's placeholder `python.exe` in `WindowsApps` often shadows a real install on `PATH` and fails with *"Python was not found; run without arguments to install from the Microsoft Store"*. If you ever see that, run `setup.bat` again.

## Getting Started

1. Run **`Start.vbs`**.
2. Click the yellow **Configure Mods Folder** button. The tool locates your Steam install and Rivals 2 automatically (across every Steam library), creates the `Mods` folder if it's missing, and opens the picker there - just confirm. Subfolders inside `Mods` are fine for organizing.
3. Pick a **Character**, **Skin**, **Color** (palette), and **File Type**:
   - **Skin** - the character's body/clothing colors
   - **Element/Energy** - effect colors (fire, smoke, energy) as an `Element0 → Element6` gradient
4. Edit colors by typing a hex value (e.g. `#FF00F0`) or clicking a color square to open a picker.
5. Click **Replace Colors** to build the mod. The `.pak` is placed in your Mods folder automatically. Make sure the game is closed when exporting.

## How to Use the New Features

### Preview

The purple **Preview** button shows an approximation of your edit before you export:

- **Skin file type** - displays the in-game character portrait recolored with the colors you've entered. Shading, outlines, and gradients are preserved; slots you haven't edited keep their original color.
- **Element/Energy file type** - displays a procedural flame/aura behind the portrait, colored by your `Element0 → Element6` gradient, plus a gradient bar showing the exact ramp. This is an approximation of how the game tints particles with those colors.

The preview refreshes each time you click the button, so edit → preview → tweak as much as you like before exporting.

### Editing a Mod You Already Installed

When you select a character/skin/palette that one of your installed `.pak` files already overrides, a teal **Load Installed Mod Colors** button appears next to Replace Colors. Clicking it reads the colors out of the installed pak and fills every field with them.

That gives you the mod's current state as your starting point, so tweaking an existing mod is just: select it, load, adjust, **Replace Colors**. No need to have saved a preset beforehand.

The button only shows up when a matching override actually exists, and it respects the File Type selector - viewing the Skin file of a modded palette loads the skin colors, while Element/Energy loads the effect gradient.

### Replacing the Character Select Portrait

Next to **Replace Colors** there is a **Replace character select portrait with skin preview** checkbox. With it ticked, exporting also rewrites the character-select portrait for that palette, so the CSS art matches your mod instead of showing the stock colors.

What gets written is exactly the image the **Preview** button shows - what you see is what ships.

Both work at the game's own resolution. The original portrait is read straight out of the game's `.pak` at full 1024×1024 (about a tenth of a second), recolored, re-encoded to DXT5 and spliced back into a texture of byte-identical size. Nothing is downscaled and nothing is stored: the portrait is fetched fresh each time.

One detail worth knowing: before matching pixels to palette slots, the source colors are grouped together in memory. The game's texture carries DXT compression noise, so without that step two neighbouring pixels of the same flat area can land on different palette slots and the result comes out visibly speckled. The image itself stays at full resolution - only the matching decision is stabilized.

This needs the Oodle decompression library, which **FModel downloads** - so it works once `setup.bat` has run. If the game install or that library can't be found, the checkbox greys out and explains which piece is missing.

> Portrait art is stored one-per-palette, so the replacement applies to the palette you are editing. A handful of portraits use texture layouts the tool doesn't handle (mip chains); those are skipped without affecting the rest of the export.

### Cross-Character Presets

**Save Preset** / **Load Preset** store your color choices as small `.json` files (a couple of starter presets are included in the `Preset` folder).

You can now load a preset made for a **different character or skin**. The tool will tell you it doesn't match and offer to adapt it:

- Slots with **matching names** transfer directly (`Body → Body`, `Hair → Hair`, element ramps line up by number).
- Remaining slots are filled by **brightness rank** - the preset's darkest colors go to the skin's darkest slots, brightest to brightest - so the design's overall structure carries over.

The result is a starting point, not a finished swap: fine-tune from there and use Preview to check it.

### Installed Mods

The **Installed Mods** button opens a list of every `.pak` in your Mods folder and shows exactly what each one overrides - character, skin, palette, and whether it's a Skin or Element/Energy replacement. It reads this straight out of each pak's file index, so it works for paks built by any version of the tool (including subfolders you've organized).

From that window you can:

- **Refresh** - re-scan the folder.
- **Open Folder** - jump to the Mods folder in Explorer.
- **Preview Before/After** - see the selected override rendered both ways: the original game colors next to the colors your installed mod actually applies, read straight out of the pak. It also reports how many color slots really changed. Works for both Skin and Element/Energy overrides.
- **Remove Selected** - removes **only the highlighted overrides**, not the whole file. If a pak covers several palettes (say Blue and Neutral), removing Blue rebuilds the pak with Neutral intact. When the last override in a pak is removed, the pak itself is deleted.
- **Remove All** - clear every mod and start fresh.

Deleted paks go to the **Recycle Bin**, not a permanent delete, so you can restore a mod if you remove it by mistake.

> **The game must be closed to add or remove mods.** Rivals 2 mounts pak files at startup and holds them locked while running, so a mod can't be installed, replaced, or removed mid-session, and changes only take effect on the next launch. The window warns you in red when it detects the game running, and removals are blocked until you close it.

### Update Game Data

The **Update Game Data** button lets you refresh the tool's game files yourself after a game patch (new characters, new skins) - no need to wait for a tool update.

Requirements: [FModel](https://fmodel.app) (free) and the `.usmap` mappings file (one ships in this folder; a game engine update may require a fresh one from the [Rivals 2 Modding Discord](https://discord.com/invite/tFdrmRQP8F)).

1. Click **Update Game Data**. The first time, you'll be asked to locate `FModel.exe` (remembered afterwards). The tool pre-configures FModel's game/output paths and launches it.
2. First FModel launch only: `Directory > Selector > "Add Undetected Game"` - name it `Rivals2`, point it at the game's `Paks` folder, click `+`, and set the UE version to `GAME_UE5_4`. Then in Settings, enable **Local Mapping File** and drag in the `.usmap` from this folder.
3. In FModel's file tree, right-click `Rivals2/Content/Characters`:
   - **Save Folder's Packages Properties (.json)**
   - **Save Folder's Packages Raw Data (.uexp)**
   - **Save Folder's Packages Textures (.png)** - only needed for the `_CSP` skin preview portraits; skip it and the palettes/skins themselves still import fine, but `Replace portrait` and the Preview thumbnails won't have anything to work with for skins you haven't exported textures for before.
   Repeat for `Rivals2/Content/Platforms`.
4. Close FModel and click **OK** in the tool. Everything imports automatically (palettes, platforms, shared skins, preview portraits) and a summary is shown. Restart the tool to see new characters.

`run_importer.bat` does the same import from the command line if you prefer (pass `--verbose` to see exactly why any given file was skipped, e.g. `run_importer.bat --verbose`).

> If a character or skin you expect isn't showing up after an import, it usually means those files simply weren't in the FModel export - re-check that you exported `Rivals2/Content/Characters` **after** loading a `.pak` that actually contains it (a very recently added skin may not be in your installed game version yet), and that you didn't miss the Properties/Raw Data steps above for that folder.

## Notes & Known Limitations

- Some skins share body or element colors with the default skin of the same palette. This is just how the game stores them.
- Editing the green (or purple) color for Retro crashes the game no matter what, so it can't be edited.
- Loxodont's rock color can't be changed - it lives in a different file type, and most of his skins share the same rock color anyway.
- Platform skins sometimes have inconsistent file/folder names; report any that misbehave.
- If a character crashes the game after modding, first delete any `[character]_P` folders in `Upack` and re-export.
- `Upack/[character]_P` is a staging folder that accumulates every palette you export for that character, which is how a single `.pak` can cover several palettes at once. Removing an override through **Installed Mods** prunes this folder too, so the removal sticks across future exports.

## Changelog

### 2026-08-17 - Importer fixes

- **Shared skins are now discovered instead of hardcoded.** `files_importer.py` only ever imported `Retro` and `Champion` out of `Characters/Shared/`, so the **Goo** skin (shown in game as *Mired*) never got its skin colors imported: like Retro/Champion it has no per-character `PS_` file, and its one shared `PS_Cha_Goo_*` set lives in `Characters/Shared/Goo/`. The result was a skin that offered *Element/Energy* but no *Skin* option. Any folder under `Characters/Shared/` holding `PE_`/`PS_` palettes is now picked up automatically, and the filename pattern no longer hardcodes the `Cha` character token or the skin name.
- Fixed `files_importer.py`'s FModel-output auto-detection: it built the default `Documents\FModel\Output` path from `%USERPROFILE%` alone, which misses OneDrive's "Known Folder Move" (Documents redirected to `OneDrive\Documents` while the old physical folder is left behind, often empty). The importer now checks both locations and picks whichever actually has the export.
- `files_importer.py` / `run_importer.bat` now accept a `--verbose` flag, and always print a per-reason summary count of skipped files (extension, segment count, prefix, character token, skin/palette mismatch, unmatched folder shape) so a skin or character that fails to import is self-diagnosing instead of silently vanishing.
- Documented the **Save Folder's Packages Textures (.png)** export step, needed for `_CSP` skin preview portraits - previously only Properties/Raw Data were mentioned, so a properties-only export would silently leave portraits stale.

### 2026-08-12 - New features

- **Load Installed Mod Colors button**: appears when the selected character/skin/palette is already covered by an installed mod, and fills the fields with that mod's colors so it can be edited directly - no preset round trip needed.
- **Character select portrait replacement**: a *Replace character select portrait with skin preview* checkbox next to Replace Colors. The image the Preview button shows is written into the portrait, so the preview matches the result. The original texture is read on demand from the game's own `.pak` (UE5 pak index reader + Oodle) for its header and exact size, then re-encoded to DXT5 and spliced back - no portrait data is stored on disk.
- **Installed Mods button**: lists every `.pak` in your Mods folder with the character/skin/palette it overrides (read from the pak index). Individual overrides can be removed without touching the rest of the pak (it is unpacked, pruned and rebuilt), or you can clear everything at once. Includes a before/after preview of what an installed override actually changes. Deleted paks go to the Recycle Bin, and the window warns when the game is running.
- Code comments are now bilingual (French original + English translation).
- **Preview button**: shows the in-game portrait recolored with your edited colors. For the Element/Energy file type it shows an approximate energy/flame effect built from the `Element0 → Element6` gradient, plus a gradient bar.
- **Cross-character presets**: loading a preset made for another character/skin now offers to adapt it to your current selection (matching slot names first, then spreading the remaining colors by brightness) as a starting point.
- **"Update Game Data" button**: guides you through a FModel export (the app pre-configures and launches FModel, you do two right-click exports) and then imports everything automatically. Lets you keep up with game patches yourself.
- A couple of starter presets are included in the `Preset` folder.

### 2026-08-11 - Game patch 1.7.0

- Game data refreshed from Rivals 2 patch 1.7.0: adds **Gouie** (all skins, palettes and icon) and updated palettes for existing characters.
- Fixed a startup error in `couleur.py` (harmless `NameError` in the console).
- `files_importer.py` reworked so anyone can refresh the data after future game patches: export `Rivals2/Content/Characters` and `/Platforms` from FModel (both "Properties .json" **and** "Raw Data .uexp"), then double-click `run_importer.bat`. It auto-detects FModel's output folder from FModel's own settings. The matching mappings file (`5.4.2-0+UE5-Rivals2.usmap`) is included for FModel.

## Credits

- Color Swap Tool created by **Keryan666** - https://gamebanana.com/tools/18380
- Original character updates by **Pixel956** - https://gamebanana.com/tools/18562
- Platforms support and prior updates by **HJ$** - https://gamebanana.com/tools/19682
- This continuation by **Kertic** - game patch 1.7.0 data (Gouie), the Preview button (skin recoloring and energy-effect previews), cross-character preset adaptation, the Update Game Data flow, and the prerequisite setup script
