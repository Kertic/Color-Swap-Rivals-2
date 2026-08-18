import base64
import os
import re
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

# La console Windows est souvent en cp1252 : les flèches "→" et autres caractères | The Windows console is often cp1252: the "→" arrows and other non-cp1252
# non-cp1252 des messages feraient planter print() (UnicodeEncodeError) dès qu'un | characters in messages would crash print() (UnicodeEncodeError) as soon as a
# fichier est copié. On bascule les flux en UTF-8 tolérant. | file is copied. Switch the streams to tolerant UTF-8.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# Mis à True par --verbose : affiche une ligne [SKIP] par fichier rejeté avec | Set to True by --verbose: prints one [SKIP] line per rejected file with
# la raison précise. Sans ça, seul un résumé des motifs de rejet est affiché. | the exact reason. Without it, only a summary of rejection reasons is shown.
VERBOSE = False

# Langue des messages de log. L'appli la règle via files_importer.LANG avant | Log message language. The app sets it via files_importer.LANG before calling
# run_import ; un lancement autonome la lit dans config.pkl. Défaut : anglais. | run_import; a standalone run reads it from config.pkl. Default: English.
LANG = "en"

_MESSAGES = {
    "outputs_found":    {"en": "FModel output(s) found: {}",
                         "fr": "Sorties FModel détectées : {}"},
    "shared_found":     {"en": "Shared skins found: {}",
                         "fr": "Skins partagés trouvés : {}"},
    "src_not_found":    {"en": "Source folder not found, skipping: {}",
                         "fr": "Dossier source introuvable, ignoré : {}"},
    "up_to_date":       {"en": "Up to date: {}",
                         "fr": "Déjà à jour : {}"},
    "done":             {"en": "Done. {} file(s) copied/updated, {} already up to date.",
                         "fr": "Terminé. {} fichier(s) copié(s)/mis à jour, {} déjà à jour."},
    "portraits_copied": {"en": "Portraits copied (full resolution): {}",
                         "fr": "Portraits copiés (pleine résolution) : {}"},
    "headers_saved":    {"en": "Portrait headers saved: {}",
                         "fr": "En-têtes de portraits enregistrés : {}"},
    "skipped_summary":  {"en": "[{}] {} file(s) skipped by filter -> {}",
                         "fr": "[{}] {} fichier(s) ignoré(s) par filtre -> {}"},
    "no_export":        {"en": "[ERROR] No FModel export found. Locations checked:",
                         "fr": "[ERREUR] Aucun export FModel trouvé. Emplacements testés :"},
    "detected_outputs": {"en": "FModel output(s) detected ({}):",
                         "fr": "Sorties FModel détectées ({}) :"},
    "export_hint":      {"en": "Export the files from FModel first:",
                         "fr": "Exportez d'abord les fichiers depuis FModel :"},
}

# Étapes d'export affichées quand aucun export n'est trouvé. | Export steps shown when no export is found.
_EXPORT_STEPS = {
    "en": [
        "  1. Load the Rivals2 .pak (UE5_4, .usmap mappings loaded)",
        "  2. Right-click the Rivals2/Content/Characters folder",
        "     -> Export Folder > Properties (.json)",
        "     -> Export Folder > Raw Data (.uasset)  [includes the .uexp]",
        "     -> Export Folder > Textures (.png)  [needed for the _CSP portraits]",
        "  3. Do the same for Rivals2/Content/Platforms",
        "  4. Re-run this script (run_importer.bat); add --verbose for per-file skip detail",
    ],
    "fr": [
        "  1. Chargez le .pak Rivals2 (UE5_4, mappings .usmap charges)",
        "  2. Clic droit sur le dossier Rivals2/Content/Characters",
        "     -> Export Folder > Properties (.json)",
        "     -> Export Folder > Raw Data (.uasset)  [inclut les .uexp]",
        "     -> Export Folder > Textures (.png)  [necessaire pour les portraits _CSP]",
        "  3. Faites de meme pour Rivals2/Content/Platforms",
        "  4. Relancez ce script (run_importer.bat), ajoutez --verbose pour le detail des fichiers ignores",
    ],
}


def _t(key, *args):
    # Message localisé selon LANG, repli sur l'anglais puis sur la clé. | Message localized by LANG, falling back to English then to the key.
    entry = _MESSAGES.get(key, {})
    text = entry.get(LANG) or entry.get("en") or key
    return text.format(*args) if args else text


def _detect_lang():
    # Lancement autonome : reprendre la langue choisie dans l'appli (config.pkl). | Standalone run: reuse the language chosen in the app (config.pkl).
    cfg = Path(__file__).resolve().parent / "config.pkl"
    try:
        import pickle
        with open(cfg, "rb") as f:
            lang = pickle.load(f).get("selected_language")
        if lang in ("en", "fr"):
            return lang
    except Exception:
        pass
    return "en"


def _skip(counter, reason, path, detail=""):
    # Comptabilise + (en mode verbose) affiche pourquoi un fichier n'a pas été importé. | Tallies + (in verbose mode) prints why a file wasn't imported.
    counter[reason] += 1
    if VERBOSE:
        suffix = f" ({detail})" if detail else ""
        print(f"[SKIP] {reason}{suffix}: {path}")


def _print_skip_summary(label, counter):
    if not counter:
        return
    total = sum(counter.values())
    detail = ", ".join(f"{reason}={n}" for reason, n in counter.most_common())
    print(_t("skipped_summary", label, total, detail))

# -------- CONFIG --------
# Détection automatique du dossier de sortie de FModel. | Automatic detection of FModel's output folder.
# On teste plusieurs emplacements et on garde celui qui contient réellement | Several locations are tested and we keep the one that actually holds
# les exports Rivals2 (peu importe où FModel a été configuré). | the Rivals2 exports (wherever FModel was configured).
def _documents_roots():
    # OneDrive "Known Folder Move" fait pointer le dossier spécial Documents vers | OneDrive "Known Folder Move" repoints the special Documents folder to
    # OneDrive\Documents, mais laisse l'ancien %USERPROFILE%\Documents en place | OneDrive\Documents, but leaves the old %USERPROFILE%\Documents folder in place
    # (souvent vide). Un chemin construit à la main depuis USERPROFILE seul rate | (often empty). A path built by hand from USERPROFILE alone misses that
    # donc ce déplacement : on liste les deux. | move, so both are listed here.
    profile = Path(os.environ.get("USERPROFILE", ""))
    roots = [profile / "Documents"]
    for var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        onedrive = os.environ.get(var)
        if onedrive:
            candidate = Path(onedrive) / "Documents"
            if candidate not in roots:
                roots.append(candidate)
    return roots


_CANDIDATE_OUTPUTS = [root / "FModel" / "Output" for root in _documents_roots()]


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


def canonical_output():
    # Chemin de sortie unique à imposer à FModel, pour que FModel écrive et que | The single output folder to pin FModel to, so that FModel writes and the
    # l'importeur lise au même endroit — Properties (.json) ET Raw Data (.uexp). | importer reads from one place — both Properties (.json) AND Raw Data (.uexp).
    resolved = _resolve_fmodel_output()
    # Si un dossier résolu contient déjà des exports, il fait référence. | If a resolved folder already holds exports, it is authoritative.
    if (resolved / "Exports").exists():
        return resolved
    # Sinon, viser le vrai dossier Documents de Windows, ce que FModel choisit | Otherwise target Windows' real Documents folder, which is what FModel picks
    # de lui-même. Avec OneDrive KFM, Documents est redirigé vers OneDrive\Documents ; | on its own. With OneDrive KFM, Documents is redirected to OneDrive\Documents;
    # sans OneDrive, c'est %USERPROFILE%\Documents. On ne prend la branche OneDrive | without OneDrive, it's %USERPROFILE%\Documents. The OneDrive branch is only
    # que si ce dossier Documents existe vraiment (OneDrive gère bien Documents). | taken when that Documents folder truly exists (OneDrive really owns Documents).
    for var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        onedrive = os.environ.get(var)
        if onedrive and (Path(onedrive) / "Documents").is_dir():
            return Path(onedrive) / "Documents" / "FModel" / "Output"
    profile = os.environ.get("USERPROFILE")
    if profile:
        return Path(profile) / "Documents" / "FModel" / "Output"
    return resolved


def refresh_paths():
    # Re-résout les chemins FModel (utile quand l'export vient d'être fait) | Re-resolves the FModel paths (useful right after an export)
    global FMODEL_OUTPUT, SOURCE_ROOT, PLATFORM_ROOT
    FMODEL_OUTPUT = _resolve_fmodel_output()
    SOURCE_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Characters"
    PLATFORM_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Platforms"


def _use_output(out):
    # Rebranche les racines sur un dossier de sortie FModel précis. | Rebinds the roots onto one specific FModel output folder.
    global FMODEL_OUTPUT, SOURCE_ROOT, PLATFORM_ROOT
    FMODEL_OUTPUT = Path(out)
    SOURCE_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Characters"
    PLATFORM_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Platforms"


def _all_fmodel_outputs():
    # Rassemble TOUS les dossiers de sortie FModel qui contiennent vraiment un | Gathers EVERY FModel output folder that actually holds a Rivals2 export.
    # export Rivals2. Un export finit souvent éclaté : Properties/Raw Data d'un | An export often ends up split: Properties/Raw Data on one side, Textures on
    # côté, Textures de l'autre (instance FModel portable ayant posé son Output à | the other (a portable FModel instance that dropped its Output next to itself,
    # côté d'elle, ex. un zip extrait dans Downloads). On les réunit tous pour | e.g. a zip unpacked in Downloads). We union them all so a single import
    # qu'un seul import récupère tout, où que ça se trouve. | picks everything up, wherever it lives.
    roots = []
    seen = set()

    def add(base):
        if not base:
            return
        base = Path(base)
        key = os.path.normcase(str(base))
        if key in seen:
            return
        seen.add(key)
        if (base / "Exports" / "Rivals2" / "Content" / "Characters").exists():
            roots.append(base)

    add(_appsettings_output())
    for c in _CANDIDATE_OUTPUTS:
        add(c)
    # Instance FModel embarquée avec l'outil | FModel instance bundled with the tool
    add(Path(__file__).resolve().parent / "FModel" / "Output")
    # Instances FModel portables (zip extrait) : un Output posé sous un dossier | Portable FModel instances (unpacked zip): an Output sitting under a folder in
    # de Downloads / Desktop, ou directement à la racine de ces dossiers. | Downloads / Desktop, or directly at the root of those folders.
    profile = Path(os.environ.get("USERPROFILE", ""))
    for area in ("Downloads", "Desktop"):
        base = profile / area
        add(base / "Output")
        try:
            for entry in base.iterdir():
                if entry.is_dir():
                    add(entry / "Output")
        except OSError:
            pass
    return roots


def _copy_if_newer(src, dest):
    # Copie sans jamais écraser une destination plus récente. Indispensable quand | Copies without ever clobbering a newer destination. Essential when importing
    # on importe depuis plusieurs exports (certains plus anciens) : le fichier le | from several exports (some older than others): the freshest file wins no
    # plus frais gagne, quel que soit l'ordre de traitement. | matter the processing order.
    src = Path(src)
    dest = Path(dest)
    if dest.exists() and src.stat().st_mtime <= dest.stat().st_mtime:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True


FMODEL_OUTPUT = _resolve_fmodel_output()
SOURCE_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Characters"

# Dossier Base_pas_edit de cet outil (relatif au script, déplaçable) | This tool's Base_pas_edit folder (relative to the script, movable)
DEST_ROOT = Path(__file__).resolve().parent / "Base_pas_edit" / "Rivals2" / "Content" / "Characters"

ALLOWED_PREFIXES = {"PE", "PS", "T"}
ALLOWED_EXTENSIONS = {".json", ".uexp"}

PLATFORM_ROOT = FMODEL_OUTPUT / "Exports" / "Rivals2" / "Content" / "Platforms"


def run_import():
    # Point d'entrée de l'application : importe depuis TOUTES les sorties FModel | App entry point: imports from EVERY discovered FModel output (properties, raw
    # découvertes (properties, raw data, textures — même éclatées entre plusieurs | data, textures — even when split across several instances) and returns the
    # instances) et renvoie le total copié par catégorie. | total copied per category.
    roots = _all_fmodel_outputs()
    if not roots:
        return None
    print("[INFO] " + _t("outputs_found", len(roots)))
    for r in roots:
        print(f"        - {r}")
    totals = {'platforms': 0, 'characters': 0, 'shared': 0, 'portraits': 0}
    for out in roots:
        _use_output(out)
        totals['platforms'] += platProcess()
        totals['characters'] += characters()
        totals['shared'] += shared()
        totals['portraits'] += csp_portraits()
    return totals


def platProcess():
    copied = 0
    skips = Counter()
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
                _skip(skips, "extension", file_path, ext or "no extension")
                continue

            parts = name.split("_")

            # Expected: PS_Pla_Skinname_Palette
            if len(parts) != 4:
                _skip(skips, "segment_count", file_path, f"{len(parts)} segments, expected 4")
                continue

            prefix, pla, skinname, palette = parts

            if prefix != "PS":
                _skip(skips, "prefix", file_path, f"got '{prefix}', expected 'PS'")
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

            if _copy_if_newer(file_path, dest_path):
                copied += 1
                print(f"Copied platform file: {file_path} → {dest_path}")
    _print_skip_summary("platforms", skips)
    return copied


def characters():
    copied = 0
    skips = Counter()
    dir_skips = Counter()
    for root, dirs, files in os.walk(SOURCE_ROOT):
        root_path = Path(root)

        parts = root_path.parts

        # We only care about folders matching:
        # Characters/{Character}/Skins/{Skin}/Data/Palettes/{Palette}
        try:
            idx = parts.index("Characters")
        except ValueError:
            continue

        # Ne signaler que les dossiers situés sous .../Skins/... : le reste | Only flag folders that sit under .../Skins/... : everything else
        # (Animation, Attacks, Taunts, UI, VFX, ...) est volontairement hors | (Animation, Attacks, Taunts, UI, VFX, ...) is intentionally out of
        # périmètre depuis toujours, le signaler serait du bruit. | scope and always has been — flagging it would just be noise.
        char_dir_parts = parts[idx + 1:]
        in_skins_tree = len(char_dir_parts) >= 2 and char_dir_parts[1] == "Skins"

        if len(parts) < idx + 7:
            # Dossier trop court pour être une palette (ex: .../Skins/Mired/ sans | Folder too shallow to be a palette folder (e.g. .../Skins/Mired/ with
            # sous-dossier Data/Palettes/... en dessous). | no Data/Palettes/... underneath it).
            if files and in_skins_tree:
                _skip(dir_skips, "not_a_palette_folder", root_path,
                      f"{len(parts) - idx - 1} segment(s) under Characters, expected 6")
            continue

        if (
            parts[idx + 2] != "Skins"
            or parts[idx + 4] != "Data"
            or parts[idx + 5] != "Palettes"
        ):
            if files and in_skins_tree:
                _skip(dir_skips, "folder_shape", root_path,
                      f"expected .../Skins/<skin>/Data/Palettes/<palette>, got '{'/'.join(parts[idx+1:idx+7])}'")
            continue

        character = parts[idx + 1]
        skin = parts[idx + 3]
        palette = parts[idx + 6]

        char_prefix = 'Lar' if character == 'LaReina' else character[:3]

        for file in files:
            file_path = root_path / file
            name, ext = file_path.stem, file_path.suffix

            if ext not in ALLOWED_EXTENSIONS:
                _skip(skips, "extension", file_path, ext or "no extension")
                continue

            segments = name.split("_")
            if len(segments) != 4:
                _skip(skips, "segment_count", file_path, f"{len(segments)} segments, expected 4")
                continue

            prefix, cha, skin_name, palette_name = segments

            if prefix not in ALLOWED_PREFIXES:
                _skip(skips, "prefix", file_path, f"got '{prefix}', expected one of {sorted(ALLOWED_PREFIXES)}")
                continue
            if cha != char_prefix:
                _skip(skips, "cha_token", file_path, f"got '{cha}', expected '{char_prefix}' for character '{character}'")
                continue
            if skin_name != skin:
                _skip(skips, "skin_mismatch", file_path, f"got '{skin_name}', folder is '{skin}'")
                continue
            if palette_name != palette:
                _skip(skips, "palette_mismatch", file_path, f"got '{palette_name}', folder is '{palette}'")
                continue

            # Build destination path
            relative_path = file_path.relative_to(SOURCE_ROOT)
            dest_path = DEST_ROOT / relative_path

            if _copy_if_newer(file_path, dest_path):
                copied += 1
                print(f"Copied: {file_path} → {dest_path}")
    _print_skip_summary("characters:files", skips)
    _print_skip_summary("characters:folders", dir_skips)
    return copied


# Skins partagés : certains skins (Retro, Champion, Goo, ...) n'ont pas de | Shared skins: some skins (Retro, Champion, Goo, ...) have no per-character
# fichier PS_ par personnage. Leurs couleurs de skin vivent une seule fois dans | PS_ file. Their skin colors live exactly once under
# Characters/Shared/<Skin>/ et servent à tous les personnages qui ont ce skin. | Characters/Shared/<Skin>/ and serve every character that has that skin.
#
# Matches: PE_Cha_Retro_Red.json / PS_Cha_Champion_Blue.uexp / PS_Cha_Goo_Neutral.json
# Le token personnage ("Cha") n'est plus figé, et le nom du skin n'est plus une | The character token ("Cha") is no longer fixed, and the skin name is no longer
# alternance codée en dur : il est vérifié contre le nom du dossier réel. | a hardcoded alternation: it is checked against the real folder name.
PATTERN = re.compile(
    r"^(?P<type>PE|PS)_(?P<cha>[A-Za-z0-9]+)_(?P<folder>[A-Za-z0-9]+)_(?P<color>.+)\.(uexp|json)$"
)

# Utilisé seulement si Characters/Shared/ est absent de l'export. | Only used when Characters/Shared/ is missing from the export.
FALLBACK_FOLDERS = ["Retro", "Champion"]


def _shared_folders():
    # Découvre les skins partagés au lieu de les coder en dur : tout dossier de | Discovers shared skins instead of hardcoding them: any folder under
    # Characters/Shared/ contenant vraiment des palettes PE_/PS_ compte. | Characters/Shared/ that actually holds PE_/PS_ palettes counts.
    root = SOURCE_ROOT / "Shared"
    if not root.exists():
        return list(FALLBACK_FOLDERS)
    found = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        if any(PATTERN.match(f.name) for f in entry.iterdir() if f.is_file()):
            found.append(entry.name)
    return found or list(FALLBACK_FOLDERS)


def shared():
    copied = 0
    skipped = 0
    skips = Counter()

    folders = _shared_folders()
    print("[INFO] " + _t("shared_found", ', '.join(folders) if folders else '(none)'))

    for folder in folders:
        src_folder = SOURCE_ROOT / "Shared" / folder

        if not src_folder.exists():
            print("[WARN]  " + _t("src_not_found", src_folder))
            continue

        for file in src_folder.iterdir():
            if not file.is_file():
                continue

            match = PATTERN.match(file.name)
            if not match:
                _skip(skips, "pattern_mismatch", file,
                      f"doesn't match PE|PS_<cha>_{folder}_<color>.(uexp|json)")
                continue

            # Le nom du skin dans le fichier doit correspondre au dossier. La | The skin name in the filename must match the folder. The comparison is
            # comparaison ignore la casse : un dossier "Goo" et un fichier | case-insensitive, so a "Goo" folder and a "...goo..." filename still
            # "...goo..." se retrouvent quand même. | find each other.
            if match.group("folder").casefold() != folder.casefold():
                _skip(skips, "skin_mismatch", file,
                      f"got '{match.group('folder')}', folder is '{folder}'")
                continue

            color = match.group("color")
 
            dest_dir = DEST_ROOT / "Shared" / "Skins" / folder / "Data" / "Palettes" / color
            dest_dir.mkdir(parents=True, exist_ok=True)
 
            dest_file = dest_dir / file.name
 
            if dest_file.exists():
                if file.stat().st_mtime <= dest_file.stat().st_mtime:
                    print("[SKIP]  " + _t("up_to_date", dest_file.relative_to(DEST_ROOT)))
                    skipped += 1
                    continue
                print(f"[UPDATE] {file.name}  →  .../{folder}/Data/Palettes/{color}/")
            else:
                print(f"[NEW]    {file.name}  →  .../{folder}/Data/Palettes/{color}/")
 
            shutil.copy2(file, dest_file)
            copied += 1
 
    print("\n" + _t("done", copied, skipped))
    _print_skip_summary("shared", skips)
    return copied


MANIFEST_PATH = Path(__file__).resolve().parent / "portrait_headers.json"


def csp_portraits():
    """
    Copie les portraits en pleine résolution et enregistre, pour chacun,
    les 145 octets d'en-tête/fin de sa texture.

    Ces 145 octets permettent de reconstruire le .uexp hors ligne : l'outil
    n'a alors besoin ni du .pak du jeu ni de FModel pour remplacer un
    portrait.

    Copies the portraits at full resolution and records, for each one, the
    145 header/trailer bytes of its texture.

    Those 145 bytes are what makes rebuilding the .uexp offline possible:
    the tool then needs neither the game .pak nor FModel to replace a
    portrait.
    """
    copied = 0
    manifest = {}
    if MANIFEST_PATH.exists():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except ValueError:
            manifest = {}

    # Skins partagés : leur palette éditable vit une seule fois dans Shared/, | Shared skins: their editable palette lives once under Shared/, never under
    # jamais sous le personnage. characters() ne crée donc aucun dossier de | the character. So characters() creates no palette folder for a character
    # palette pour un personnage qui n'a que ce skin partagé (fichier CS_ seul, | that only has this shared skin (a lone CS_ blueprint, which is not an
    # non éditable) — et son portrait par personnage était alors ignoré ci-dessous. | editable palette) — and its per-character portrait was then dropped below.
    shared_skins = {s.casefold() for s in _shared_folders()}

    for root, dirs, files in os.walk(SOURCE_ROOT):
        for file in files:
            if not file.endswith("_CSP.png"):
                continue
            src = Path(root) / file
            dest = DEST_ROOT / src.relative_to(SOURCE_ROOT)
            # ne copier que là où l'outil a déjà des données de palette | only copy where the tool already has palette data
            if not dest.parent.is_dir():
                # Exception pour les skins partagés : créer le dossier pour que le | Exception for shared skins: create the folder so the per-character
                # portrait par personnage serve l'aperçu roster (l'édition, elle, | portrait can feed the whole-roster preview (editing still happens on
                # se fait sur la palette unique de Shared/). Un skin normal sans | the single palette under Shared/). A normal skin with no editable
                # palette éditable reste ignoré, pour ne pas créer de faux dossiers. | palette stays skipped, to avoid creating phantom skin folders.
                rel_parts = src.relative_to(SOURCE_ROOT).parts
                is_shared_skin = (len(rel_parts) >= 3 and rel_parts[1] == "Skins"
                                  and rel_parts[2].casefold() in shared_skins)
                if not is_shared_skin:
                    continue
            if _copy_if_newer(src, dest):
                copied += 1

            # En-tête/fin de la texture correspondante | Header/trailer of the matching texture
            uexp = src.with_suffix(".uexp")
            if not uexp.exists():
                continue
            data = uexp.read_bytes()
            payload = len(data) - 145
            side = int(round(payload ** 0.5))
            if side * side != payload or side not in (256, 512, 1024, 2048):
                continue        # mipmaps ou format inattendu | mip chain or unexpected format
            manifest[uexp.name] = {
                "wrapper": base64.b64encode(data[:117] + data[-28:]).decode("ascii"),
                "side": side,
            }

    if manifest:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=0, sort_keys=True),
                                 encoding="utf-8")
    print(_t("portraits_copied", copied))
    print(_t("headers_saved", len(manifest)))
    return copied


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import FModel-exported game data into Base_pas_edit.")
    parser.add_argument("--verbose", action="store_true",
                         help="Print one [SKIP] line per file rejected by a filter, not just the summary counts.")
    parser.add_argument("--lang", choices=("en", "fr"),
                         help="Log language. Defaults to the app's saved language (config.pkl), else English.")
    args = parser.parse_args()
    VERBOSE = args.verbose
    LANG = args.lang or _detect_lang()

    outputs = _all_fmodel_outputs()
    if not outputs:
        print(_t("no_export"))
        for c in ([_appsettings_output()] + _CANDIDATE_OUTPUTS):
            if c:
                print(f"     - {c}")
        print(_t("export_hint"))
        for line in _EXPORT_STEPS.get(LANG, _EXPORT_STEPS["en"]):
            print(line)
        sys.exit(1)
    print(_t("detected_outputs", len(outputs)))
    for o in outputs:
        print(f"   - {o}")
    for out in outputs:
        _use_output(out)
        platProcess()
        characters()
        shared()
        csp_portraits()