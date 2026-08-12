# Color-Swap-Rivals-2
A continuation of https://github.com/Keryan-666/Color-Swap-ROA-2 which enables you to change colors of different skin palettes 

## Installation

Clone the repo (or download it with the green **Code** button), then run the setup script once:

```
git clone https://github.com/Kertic/Color-Swap-Rivals-2
cd Color-Swap-Rivals-2
setup.bat
```

`setup.bat` uses winget (built into Windows 10/11) to install anything missing: **Python 3.12** + the **Pillow** library, the **.NET 8 Desktop Runtime**, and it downloads the latest **FModel** release into the tool's `FModel/` subfolder (used by the Update Game Data button). Everything already installed is detected and skipped. The .NET runtime install may show a UAC prompt.

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
   Repeat for `Rivals2/Content/Platforms`.
4. Close FModel and click **OK** in the tool. Everything imports automatically (palettes, platforms, shared skins, preview portraits) and a summary is shown. Restart the tool to see new characters.

`run_importer.bat` does the same import from the command line if you prefer.

## Notes & Known Limitations

- Some skins share body or element colors with the default skin of the same palette. This is just how the game stores them.
- Editing the green (or purple) color for Retro crashes the game no matter what, so it can't be edited.
- Loxodont's rock color can't be changed - it lives in a different file type, and most of his skins share the same rock color anyway.
- Platform skins sometimes have inconsistent file/folder names; report any that misbehave.
- If a character crashes the game after modding, first delete any `[character]_P` folders in `Upack` and re-export.

## Changelog

### 2026-08-12 - New features

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
