# -*- coding: utf-8 -*-
"""
Mise à jour des données du jeu directement depuis le .pak, sans FModel.
Updating the game data straight from the .pak, without FModel.

Les palettes (PS_/PE_) sont de petits Blueprints dont la seule propriété
est une table « nom de slot -> couleur ». Le .uasset donne la liste des
noms, le .uexp la table : on en tire un .json identique à celui de FModel,
puis on réutilise files_importer comme si FModel venait d'exporter.
Les portraits (_CSP) sont décodés en PNG et leurs en-têtes enregistrés.

Palettes (PS_/PE_) are small Blueprints whose only property is a
"slot name -> colour" map. The .uasset holds the name list and the .uexp
the map: from them we build a .json identical to FModel's, then reuse
files_importer as if FModel had just exported. Portraits (_CSP) are
decoded to PNG and their headers recorded.
"""
import base64
import copy
import datetime
import hashlib
import json
import logging
import math
import os
import re
import shutil
import struct
import tempfile

from PIL import Image, ImageChops, ImageStat

import portraits

log = logging.getLogger("colorswap")

# Dossiers du pak qui contiennent des palettes | Pak folders that hold palettes
PALETTE_ROOTS = ("Rivals2/Content/Characters/", "Rivals2/Content/Platforms/")
PALETTE_RE = re.compile(r"^P[ES]_.+$")

# Empreinte de la version du jeu dont viennent les données livrées | Fingerprint of the game version the shipped data comes from
STAMP_NAME = "game_version.json"

# Écart moyen (0-255) en dessous duquel deux portraits sont la même image : | Mean difference (0-255) below which two portraits are the same image:
# les PNG exportés par FModel diffèrent un peu du décodage DXT5 sur les contours. | FModel's PNGs differ slightly from our DXT5 decode along outlines.
PORTRAIT_SAME_MEAN = 3.0


# --------------------------------------------------------------------------
# Lecture des palettes | Reading palettes
# --------------------------------------------------------------------------

def read_name_map(uasset):
    """
    Liste des noms (FName) d'un .uasset, ou None. Plutôt que de décoder tout
    l'en-tête, dont le format change avec le moteur, on cherche la paire
    (nombre, position) qui décrit une table de noms lisible jusqu'au bout.

    The FName list of a .uasset, or None. Rather than decoding the whole
    summary, whose layout changes with the engine, we look for the
    (count, offset) pair that describes a name table readable to the end.
    """
    for p in range(8, min(0x200, len(uasset) - 8)):
        count, offset = struct.unpack_from("<ii", uasset, p)
        if not (0 < count < 5000 and 0x20 < offset < len(uasset)):
            continue
        names, q = [], offset
        try:
            for _ in range(count):
                n = struct.unpack_from("<i", uasset, q)[0]
                if not 0 < n < 1024:
                    raise ValueError
                raw = uasset[q + 4:q + 4 + n]
                if len(raw) != n or raw[-1] != 0 or not all(32 <= b < 127 for b in raw[:-1]):
                    raise ValueError
                names.append(raw[:-1].decode("ascii"))
                q += 4 + n + 4        # chaîne + deux empreintes uint16 | string + two uint16 hashes
        except (ValueError, struct.error):
            continue
        return names
    return None


def read_color_slots(uexp, names):
    """
    Table des couleurs d'une palette : [(nom du slot, (R, G, B, A)), ...],
    ou None. Elle termine l'objet par défaut, juste avant les 8 derniers
    octets du fichier : [0][nombre] puis, par entrée, l'index du nom, son
    numéro (suffixe _N + 1) et quatre flottants.

    A palette's colour map: [(slot name, (R, G, B, A)), ...], or None. It
    ends the default object, right before the file's last 8 bytes:
    [0][count] then, per entry, the name index, its number (suffix _N + 1)
    and four floats.
    """
    end = len(uexp) - 8
    for n in range(1, 200):
        start = end - n * 24 - 8
        if start < 0:
            break
        removed, count = struct.unpack_from("<ii", uexp, start)
        if removed != 0 or count != n:
            continue
        slots = []
        for i in range(n):
            q = start + 8 + i * 24
            index, number = struct.unpack_from("<ii", uexp, q)
            if not (0 <= index < len(names) and 0 <= number < 1000):
                break
            rgba = struct.unpack_from("<4f", uexp, q + 8)
            if not all(math.isfinite(v) for v in rgba):
                break
            slots.append((names[index] + ("_%d" % (number - 1) if number else ""), rgba))
        else:
            return slots
    return None


def _srgb_byte(v):
    # Même conversion que FLinearColor::ToFColor(true) | Same conversion as FLinearColor::ToFColor(true)
    v = min(max(v, 0.0), 1.0)
    v = v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
    return int(math.floor(min(max(v, 0.0), 1.0) * 255.999))


def fmodel_hex(r, g, b, a):
    # "RRGGBB", ou "AARRGGBB" quand l'alpha n'est ni 0 ni 1, comme FModel | "RRGGBB", or "AARRGGBB" when alpha is neither 0 nor 1, like FModel
    alpha = int(math.floor(min(max(a, 0.0), 1.0) * 255.999))
    rgb = "%02X%02X%02X" % (_srgb_byte(r), _srgb_byte(g), _srgb_byte(b))
    return rgb if alpha in (0, 255) else "%02X%s" % (alpha, rgb)


def slot_definitions(slots):
    return [{"Key": key, "Value": {"R": round(r, 6), "G": round(g, 6), "B": round(b, 6),
                                   "A": round(a, 6), "Hex": fmodel_hex(r, g, b, a)}}
            for key, (r, g, b, a) in slots]


def default_palette_json(package, name):
    # Ce qu'écrit FModel pour une palette ; seule la table de couleurs sert à l'outil | What FModel writes for a palette; only the colour map is used by the tool
    return [
        {
            "Type": "BlueprintGeneratedClass",
            "Name": f"{name}_C",
            "Flags": "RF_Public | RF_Transactional | RF_WasLoaded | RF_LoadCompleted",
            "Class": "UScriptClass'BlueprintGeneratedClass'",
            "Package": package,
            "SuperStruct": {"ObjectName": "Class'RivalsColorPalette'", "ObjectPath": "/Script/Rivals2"},
            "ClassFlags": "CLASS_CompiledFromBlueprint",
            "ClassWithin": {"ObjectName": "Class'Object'", "ObjectPath": "/Script/CoreUObject"},
            "ClassConfigName": "Engine",
            "bCooked": True,
            "ClassDefaultObject": {"ObjectName": f"{name}_C'Default__{name}_C'",
                                   "ObjectPath": f"{package}.1"},
            "EditorTags": {"BlueprintType": "BPTYPE_Normal"},
        },
        {
            "Type": f"{name}_C",
            "Name": f"Default__{name}_C",
            "Flags": "RF_Public | RF_ClassDefaultObject | RF_ArchetypeObject | RF_WasLoaded | RF_LoadCompleted",
            "Class": f"BlueprintGeneratedClass'{package}.{name}_C'",
            "Package": package,
            "Properties": {"CustomColorSlotDefinitions": []},
        },
    ]


def palette_json(package, name, slots, template=None):
    """
    Texte .json d'une palette, au format exact de FModel. Si l'outil a déjà
    un .json pour ce package, il sert de modèle : seule la table de couleurs
    est remplacée, le reste (drapeaux, héritage) est conservé tel quel.

    A palette's .json text, in FModel's exact format. When the tool already
    has a .json for this package it is used as the template: only the colour
    map is replaced, the rest (flags, inheritance) is kept as it is.
    """
    data = copy.deepcopy(template) if template else default_palette_json(package, name)
    target = next((e for e in data if isinstance(e.get("Properties"), dict)
                   and "CustomColorSlotDefinitions" in e["Properties"]), data[-1])
    target.setdefault("Properties", {})["CustomColorSlotDefinitions"] = slot_definitions(slots)
    text = json.dumps(data, indent=2, ensure_ascii=False)
    # Newtonsoft (FModel) écrit les exposants en majuscule : 5E-05 | Newtonsoft (FModel) writes exponents in capitals: 5E-05
    text = re.sub(r'(?<=[0-9])e(?=[-+][0-9])', 'E', text)
    return text.replace("\n", "\r\n")


# --------------------------------------------------------------------------
# Version des données | Data version
# --------------------------------------------------------------------------

def read_stamp(repo_dir):
    try:
        with open(os.path.join(repo_dir, "Base_pas_edit", STAMP_NAME), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_stamp(repo_dir, pak):
    stamp = {"pak_index_sha1": pak.index_hash(),
             "updated": datetime.date.today().isoformat()}
    with open(os.path.join(repo_dir, "Base_pas_edit", STAMP_NAME), "w", encoding="utf-8") as f:
        json.dump(stamp, f, indent=2)
    return stamp


def is_up_to_date(repo_dir, pak):
    # Les données livrées viennent-elles de cette version du jeu ? | Does the shipped data come from this game version?
    return read_stamp(repo_dir).get("pak_index_sha1") == pak.index_hash()


# --------------------------------------------------------------------------
# Mise à jour | Update
# --------------------------------------------------------------------------

def _palette_templates(base_root):
    # .json existants, par package (« Rivals2/Content/.../PS_x ») -> (contenu, chemin) | Existing .json files, by package ("Rivals2/Content/.../PS_x") -> (contents, path)
    templates = {}
    for dirpath, _dirs, files in os.walk(base_root):
        for name in files:
            if not name.endswith(".json") or not PALETTE_RE.match(name):
                continue
            try:
                with open(os.path.join(dirpath, name), "r", encoding="utf-8") as f:
                    data = json.load(f)
                package = next(e["Package"] for e in data if e.get("Package"))
            except (OSError, ValueError, StopIteration, AttributeError, TypeError):
                continue
            templates[package] = (data, os.path.join(dirpath, name))
    return templates


def _same_as_existing(json_path, text, uexp):
    # Vrai si l'outil a déjà exactement ces deux fichiers | True when the tool already has exactly these two files
    try:
        with open(json_path, "rb") as f:
            if f.read() != text.encode("utf-8"):
                return False
        with open(json_path[:-len(".json")] + ".uexp", "rb") as f:
            return f.read() == uexp
    except OSError:
        return False


def _snapshot(base_root):
    # Empreinte des .json/.uexp de l'outil, pour lister ce qui a changé | Fingerprint of the tool's .json/.uexp files, to list what changed
    snap = {}
    for dirpath, _dirs, files in os.walk(base_root):
        for name in files:
            if name.endswith((".json", ".uexp")):
                full = os.path.join(dirpath, name)
                with open(full, "rb") as f:
                    snap[os.path.relpath(full, base_root)] = hashlib.sha1(f.read()).hexdigest()
    return snap


def export_palettes(pak, out_root, templates, progress):
    """
    Écrit les palettes du jeu sous out_root/Exports/..., comme un export
    FModel (Properties .json + Raw Data .uexp). Renvoie (écrites, échecs).

    Writes the game's palettes under out_root/Exports/..., like a FModel
    export (Properties .json + Raw Data .uexp). Palettes the tool already
    has byte for byte are left out, so the import only touches what
    changed. Returns (palettes read, failures).
    """
    by_dir = {}
    for directory, name, offset in pak.listing():
        if directory.startswith(PALETTE_ROOTS) and PALETTE_RE.match(name):
            by_dir.setdefault(directory, {})[name] = offset
    candidates = [(d, n[:-len(".uexp")], files)
                  for d, files in by_dir.items() for n in files
                  if n.endswith(".uexp") and n[:-len(".uexp")] + ".uasset" in files]

    written, failures = 0, []
    for i, (directory, stem, files) in enumerate(candidates):
        if i % 100 == 0:
            progress(("palettes", i, len(candidates)))
        uasset = pak.read_at(files[stem + ".uasset"])
        names = read_name_map(uasset)
        # Les palettes sont des Blueprints ; les PS_ des effets visuels n'en sont pas | Palettes are Blueprints; visual-effect PS_ assets are not
        if names is None or "BlueprintGeneratedClass" not in names:
            continue
        uexp = pak.read_at(files[stem + ".uexp"])
        slots = read_color_slots(uexp, names)
        if slots is None:
            if "RivalsColorPalette" in names:
                failures.append(directory + stem)
                log.warning("Palette illisible | Unreadable palette: %s%s", directory, stem)
            continue
        package = directory.rstrip("/") + "/" + stem
        template, existing = templates.get(package, (None, None))
        text = palette_json(package, stem, slots, template)
        written += 1
        if existing and _same_as_existing(existing, text, uexp):
            continue
        folder = os.path.join(out_root, "Exports", *directory.strip("/").split("/"))
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, stem + ".uexp"), "wb") as f:
            f.write(uexp)
        with open(os.path.join(folder, stem + ".json"), "w", encoding="utf-8", newline="") as f:
            f.write(text)
    progress(("palettes", len(candidates), len(candidates)))
    return written, failures


def refresh_portraits(pak, repo_dir, progress):
    """
    Met à jour les portraits de sélection (_CSP) : en-tête enregistré dans
    portrait_headers.json, et PNG d'aperçu réécrit seulement s'il manque ou
    si l'image du jeu a vraiment changé. L'empreinte des pixels est gardée
    pour sauter les portraits inchangés la fois suivante.

    Refreshes the character-select portraits (_CSP): header recorded in
    portrait_headers.json, and the preview PNG rewritten only when it is
    missing or the game's image really changed. A fingerprint of the
    pixels is kept to skip unchanged portraits next time.
    """
    base_root = os.path.join(repo_dir, "Base_pas_edit")
    manifest_path = os.path.join(repo_dir, "portrait_headers.json")
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        manifest = {}
    shared_dir = os.path.join(base_root, "Rivals2", "Content", "Characters", "Shared", "Skins")
    shared = {n.casefold() for n in os.listdir(shared_dir)} if os.path.isdir(shared_dir) else set()

    portraits_in_pak = [(d, n, o) for d, n, o in pak.listing()
                        if d.startswith("Rivals2/Content/Characters/")
                        and n.startswith("T_") and n.endswith("_CSP.uexp")]
    stats = {"added": 0, "updated": 0, "unchanged": 0, "skipped": 0}
    for i, (directory, name, offset) in enumerate(portraits_in_pak):
        if i % 50 == 0:
            progress(("portraits", i, len(portraits_in_pak)))
        parts = directory.strip("/").split("/")
        dest_dir = os.path.join(base_root, *parts)
        rel = parts[3:]          # sous Characters/ | under Characters/
        is_shared = len(rel) >= 3 and rel[1] == "Skins" and rel[2].casefold() in shared
        # Comme files_importer : seulement là où l'outil a des palettes | Like files_importer: only where the tool has palettes
        if not os.path.isdir(dest_dir) and not is_shared:
            stats["skipped"] += 1
            continue
        old = manifest.get(name) or {}
        png = os.path.join(dest_dir, name[:-len(".uexp")] + ".png")
        # Entrée du pak identique à la dernière fois : rien à relire | Pak entry identical to last time: nothing to read again
        entry_hash = pak.entry_hash(offset)
        if old.get("pak_sha1") == entry_hash and os.path.exists(png):
            stats["unchanged"] += 1
            continue
        data = pak.read_at(offset)
        wrapper = portraits.csp_wrapper(data)
        if wrapper is None:
            stats["skipped"] += 1          # mipmaps ou format inattendu | mip chain or unexpected layout
            continue
        side = portraits.csp_layout(data)[1]
        header_len = portraits.CSP_HEADER_LEN
        digest = hashlib.sha1(data[header_len:header_len + side * side]).hexdigest()

        if not os.path.exists(png):
            state = "added"
        elif old.get("sha1") == digest:
            state = "unchanged"
        else:
            image = portraits.decode_csp(data)
            try:
                current = Image.open(png).convert("RGBA")
                same = current.size == image.size and max(
                    ImageStat.Stat(ImageChops.difference(image, current)).mean) < PORTRAIT_SAME_MEAN
            except OSError:
                same = False
            state = "unchanged" if same else "updated"
        if state != "unchanged":
            os.makedirs(dest_dir, exist_ok=True)
            portraits.decode_csp(data).save(png)
            log.info("Portrait %s : %s", state, png)
        stats[state] += 1
        manifest[name] = {"side": side, "wrapper": base64.b64encode(wrapper).decode("ascii"),
                          "sha1": digest, "pak_sha1": entry_hash}

    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, indent=0, sort_keys=True))
    progress(("portraits", len(portraits_in_pak), len(portraits_in_pak)))
    return stats


def update_game_data(pak, repo_dir, importer, progress=lambda step: None):
    """
    Met à jour toutes les données de l'outil depuis le .pak du jeu.
    `importer` est le module files_importer, qui range les fichiers.
    Renvoie un résumé : palettes ajoutées / modifiées, portraits, échecs.

    Updates all of the tool's data from the game .pak. `importer` is the
    files_importer module, which files everything in place. Returns a
    summary: palettes added / changed, portraits, failures.
    """
    base_root = os.path.join(repo_dir, "Base_pas_edit")
    progress(("start", 0, 0))
    log.info("Mise à jour des données depuis | Updating game data from %s (index %s)",
             pak.path, pak.index_hash())
    before = _snapshot(base_root)
    templates = _palette_templates(base_root)

    work = tempfile.mkdtemp(prefix="colorswap_gamedata_")
    try:
        written, failures = export_palettes(pak, work, templates, progress)
        progress(("import", 0, 0))
        importer._use_output(work)
        importer.platProcess()
        importer.characters()
        importer.shared()
    finally:
        shutil.rmtree(work, ignore_errors=True)

    portrait_stats = refresh_portraits(pak, repo_dir, progress)
    after = _snapshot(base_root)
    added = sorted(p for p in after if p not in before and p.endswith(".json"))
    changed = sorted(p for p in after if p in before and after[p] != before[p] and p.endswith(".json"))
    # Une palette dont seul le .uexp a changé compte aussi | A palette whose .uexp alone changed counts too
    changed += sorted(p[:-len(".uexp")] + ".json" for p in after
                      if p.endswith(".uexp") and p in before and after[p] != before[p]
                      and p[:-len(".uexp")] + ".json" not in changed)
    stamp = write_stamp(repo_dir, pak)
    summary = {"palettes_read": written, "added": added, "changed": sorted(set(changed)),
               "failures": failures, "portraits": portrait_stats, "stamp": stamp}
    log.info("Données mises à jour | Game data updated: %s palettes read, %s added, %s changed, "
             "%s unreadable, portraits %s", written, len(added), len(summary["changed"]),
             len(failures), portrait_stats)
    for p in added:
        log.info("  + %s", p)
    for p in summary["changed"]:
        log.info("  ~ %s", p)
    return summary
