import os
import re
import json
import shutil
import sys
from pathlib import Path

# -------- CONFIG --------
# Détection automatique du dossier de sortie de FModel. | Automatic detection of FModel's output folder.
# On teste plusieurs emplacements et on garde celui qui contient réellement | Several locations are tested and we keep the one that actually holds
# les exports Rivals2 (peu importe où FModel a été configuré). | the Rivals2 exports (wherever FModel was configured).
_CANDIDATE_OUTPUTS = [
    Path(os.environ.get("USERPROFILE", "")) / "Documents" / "FModel" / "Output",
]


def _appsettings_output():
    # Lit OutputDirectory depuis la config de FModel si disponible | Reads OutputDirectory from FModel's own config if available
    cfg = Path(os.environ.get("APPDATA", "")) / "FModel" / "AppSettings.json"
    try:
        out = json.loads(cfg.read_text(encoding="utf-8")).get("OutputDirectory")
        return Path(out) if out else None
    except Exception:
        return None


def _resolve_fmodel_output():
    candidates = []
    cfg_out = _appsettings_output()
    if cfg_out:
        candidates.append(cfg_out)
    candidates += _CANDIDATE_OUTPUTS
    # 1) Priorité à un dossier qui contient déjà des personnages exportés | 1) Prefer a folder that already contains exported characters
    for c in candidates:
        if (c / "Exports" / "Rivals2" / "Content" / "Characters").exists():
            return c
    # 2) Sinon, le premier qui a au moins un dossier Exports | 2) Otherwise, the first one with at least an Exports folder
    for c in candidates:
        if (c / "Exports").exists():
            return c
    # 3) Sinon, le premier candidat (pour le message d'erreur) | 3) Otherwise, the first candidate (for the error message)
    return candidates[0]


def refresh_paths():
    # Re-résout les chemins FModel (utile quand l'export vient d'être fait) | Re-resolves the FModel paths (useful right after an export)
    global FMODEL_OUTPUT, SOURCE_ROOT, PLATFORM_ROOT
    FMODEL_OUTPUT = _resolve_fmodel_output()
    SOURCE_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Characters"
    PLATFORM_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Platforms"


FMODEL_OUTPUT = _resolve_fmodel_output()
SOURCE_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Characters"

# Dossier Base_pas_edit de cet outil (relatif au script, déplaçable) | This tool's Base_pas_edit folder (relative to the script, movable)
DEST_ROOT = Path(__file__).resolve().parent / "Base_pas_edit" / "Rivals2" / "Content" / "Characters"

ALLOWED_PREFIXES = {"PE", "PS", "T"}
ALLOWED_EXTENSIONS = {".json", ".uexp"}

PLATFORM_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Platforms"


def run_import():
    # Point d'entrée utilisé par l'application : lance tout l'import | Entry point used by the application: runs the whole import
    # et retourne le nombre de fichiers copiés par catégorie. | and returns the number of files copied per category.
    refresh_paths()
    if not SOURCE_ROOT.exists():
        return None
    return {
        'platforms': platProcess(),
        'characters': characters(),
        'shared': shared(),
        'portraits': csp_portraits(),
    }


def platProcess():
    copied = 0
    for root, dirs, files in os.walk(PLATFORM_ROOT):
        root_path = Path(root)

        # Skip root folder itself
        if root_path == PLATFORM_ROOT:
            continue

        platform_skin = root_path.name  # folder name = skin

        for file in files:
            file_path = root_path / file
            name, ext = file_path.stem, file_path.suffix

            if ext not in {".json", ".uexp"}:
                continue

            parts = name.split("_")

            # Expected: PS_Pla_Skinname_Palette
            if len(parts) != 4:
                continue

            prefix, pla, skinname, palette = parts

            if prefix != "PS":
                continue

            # Build destination path
            dest_path = (
                DEST_ROOT
                / "Platforms"
                / "Skins"
                / platform_skin
                / "Data"
                / "Palettes"
                / palette
                / file
            )

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, dest_path)
            copied += 1

            print(f"Copied platform file: {file_path} → {dest_path}")
    return copied


def characters():
    copied = 0
    for root, dirs, files in os.walk(SOURCE_ROOT):
        root_path = Path(root)

        parts = root_path.parts

        # We only care about folders matching:
        # Characters/{Character}/Skins/{Skin}/Data/Palettes/{Palette}
        try:
            idx = parts.index("Characters")
        except ValueError:
            continue

        if len(parts) < idx + 7:
            continue

        if (
            parts[idx + 2] != "Skins"
            or parts[idx + 4] != "Data"
            or parts[idx + 5] != "Palettes"
        ):
            continue

        character = parts[idx + 1]
        skin = parts[idx + 3]
        palette = parts[idx + 6]

        char_prefix = 'Lar' if character == 'LaReina' else character[:3] 

        for file in files:
            file_path = root_path / file
            name, ext = file_path.stem, file_path.suffix

            if ext not in ALLOWED_EXTENSIONS:
                continue

            segments = name.split("_")
            if len(segments) != 4:
                continue

            prefix, cha, skin_name, palette_name = segments

            if (
                prefix in ALLOWED_PREFIXES
                and cha == char_prefix
                and skin_name == skin
                and palette_name == palette
            ):
                # Build destination path
                relative_path = file_path.relative_to(SOURCE_ROOT)
                dest_path = DEST_ROOT / relative_path

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)
                copied += 1

                print(f"Copied: {file_path} → {dest_path}")
    return copied


FOLDERS = ["Retro", "Champion"]
 
# Matches: PE_Cha_Retro_Red.uasset  /  PS_Cha_Champion_Blue.uasset  etc.
PATTERN = re.compile(r"^(PE|PS)_Cha_(?P<folder>Retro|Champion)_(?P<color>.+)\.(uexp|json)$")
 
 
def shared():
    copied = 0
    skipped = 0
 
    for folder in FOLDERS:
        src_folder = SOURCE_ROOT / "Shared" / folder
 
        if not src_folder.exists():
            print(f"[WARN]  Source folder not found, skipping: {src_folder}")
            continue
 
        for file in src_folder.iterdir():
            if not file.is_file():
                continue
 
            match = PATTERN.match(file.name)
            if not match:
                continue
 
            color = match.group("color")
 
            dest_dir = DEST_ROOT / "Shared" / "Skins" / folder / "Data" / "Palettes" / color
            dest_dir.mkdir(parents=True, exist_ok=True)
 
            dest_file = dest_dir / file.name
 
            if dest_file.exists():
                if file.stat().st_mtime <= dest_file.stat().st_mtime:
                    print(f"[SKIP]  Up to date: {dest_file.relative_to(DEST_ROOT)}")
                    skipped += 1
                    continue
                print(f"[UPDATE] {file.name}  →  .../{folder}/Data/Palettes/{color}/")
            else:
                print(f"[NEW]    {file.name}  →  .../{folder}/Data/Palettes/{color}/")
 
            shutil.copy2(file, dest_file)
            copied += 1
 
    print(f"\nDone. {copied} file(s) copied/updated, {skipped} already up to date.")
    return copied


def csp_portraits():
    # Copie les portraits (T_*_CSP.png) utilisés par le bouton Aperçu, | Copies the portraits (T_*_CSP.png) used by the Preview button,
    # réduits et quantifiés pour limiter la taille du dossier. | downscaled and quantized to keep the folder size down.
    try:
        from PIL import Image
    except ImportError:
        print("[WARN] PIL indisponible, portraits d'aperçu non copiés")
        return 0
    copied = 0
    for root, dirs, files in os.walk(SOURCE_ROOT):
        for file in files:
            if not file.endswith("_CSP.png"):
                continue
            src = Path(root) / file
            dest = DEST_ROOT / src.relative_to(SOURCE_ROOT)
            # ne copier que là où l'outil a déjà des données de palette | only copy where the tool already has palette data
            if not dest.parent.is_dir():
                continue
            im = Image.open(src).convert("RGBA")
            if max(im.size) > 400:
                im.thumbnail((400, 400), Image.LANCZOS)
            im = im.quantize(colors=256, method=Image.FASTOCTREE)
            im.save(dest, optimize=True)
            copied += 1
    print(f"Portraits d'aperçu copiés : {copied}")
    return copied


if __name__ == "__main__":
    print(f"Dossier de sortie FModel detecte : {FMODEL_OUTPUT}")
    if not SOURCE_ROOT.exists():
        print(f"[ERREUR] Aucun export trouve ici : {SOURCE_ROOT}")
        print("Exportez d'abord les fichiers depuis FModel :")
        print("  1. Chargez le .pak Rivals2 (UE5_4, mappings .usmap charges)")
        print("  2. Clic droit sur le dossier Rivals2/Content/Characters")
        print("     -> Save Folder's Packages Properties (.json)")
        print("     -> Save Folder's Packages Textures / Raw Data (.uexp)")
        print("  3. Faites de meme pour Rivals2/Content/Platforms")
        print("  4. Relancez ce script (run_importer.bat)")
        sys.exit(1)
    platProcess()
    characters()
    shared()
    csp_portraits()