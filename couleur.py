import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk
import re
import ctypes
from ctypes import wintypes
import struct
import json
import os
import shutil
import subprocess
import time
import pickle
import threading
from PIL import Image, ImageTk
import sys
from pathlib import Path

try:
    import portraits as portraits_module
except ImportError:      # portraits.py absent : l'option est simplement désactivée | portraits.py missing: the option is just disabled
    portraits_module = None

CONFIG_FILE = 'config.pkl'

BASE_DIR = r"Base_pas_edit\Rivals2\Content\Characters"

# Initialisation des variables globales | Global variable initialization
unrealpak_script_path = None
mods_folder_path = None
fmodel_path = None
output_folder_path = None
json_data = None
uexp_file_path = None
color_entries = {}
color_displays = {}
character_icons = {}
file_type_codes = {'Element/Energy': 'PE', 'Skin': 'PS'}
Primal_platform = False

# Dictionnaire des traductions | Translation dictionary
translations = {
    'fr': {
        'title': "ROA 2 Colorswap",
        'configure_mods': "Configurer le dossier Mods",
        'configure_fmodel_output': "Configurer l'output FModel",
        'save_preset': "Sauvegarder Preset",
        'load_preset': "Charger Preset",
        'replace_colors': "Remplacer les couleurs",
        'character': "Personnage:",
        'skin': "Skin:",
        'color': "Couleur:",
        'file_type': "Type de fichier:",
        'success_title': "Succès",
        'preset_loaded': "Preset chargé avec succès.",
        'preset_saved': "Preset sauvegardé avec succès.",
        'error_title': "Erreur",
        'json_decode_error': "Erreur de décodage JSON.",
        'no_json_loaded': "Aucun fichier JSON chargé.",
        'json_load_error': "Erreur de chargement du preset.",
        'uexp_not_found': "Fichier UEXP introuvable : {}",
        'json_not_found': "Fichier JSON introuvable : {}",
        'unexpected_json_format': "Format JSON inattendu.",
        'mods_configured': "Dossier mods configuré.",
        'FModel_output_configured': "Output FModel configuré",
        'pak_not_found': "Le fichier .pak n'a pas été trouvé.",
        'mods_not_configured': ("Dossier Mods introuvable. Cliquez d'abord sur le bouton jaune "
                                "« Configurer le dossier Mods » et sélectionnez le dossier Mods de Rivals 2."),
        'script_execution_failed': "Échec de l'exécution du script : {}",
        'pak_creation_failed': "Échec de la création du .pak : {}",
        'game_not_closed': "Vérifiez que le jeu est bien fermé",
        'load_error': "Une erreur s'est produite lors du chargement du preset : {}",
        'pak_creation_success': "Fichier .pak créé et déplacé vers le dossier mods",
        'preset_mismatch': "Le preset ne correspond pas au personnage ou au skin sélectionné.",
        'preview': "Aperçu",
        'preview_title': "Aperçu : {} - {} - {}",
        'preview_unavailable': "Aucune image d'aperçu disponible pour cette sélection.",
        'preview_note': "Aperçu approximatif généré à partir du portrait du jeu.",
        'preview_energy_note': "Aperçu approximatif de l'effet énergie (dégradé Element0 → Element6).",
        'preview_shared_note': "Aperçu du skin partagé sur chaque personnage qui le possède.",
        'preview_shared_none': ("Aucun portrait de personnage trouvé pour ce skin partagé.\n"
                                "Utilisez « Mettre à jour les données du jeu » pour les importer."),
        'preset_adapt_prompt': ("Ce preset est pour {} / {} mais la sélection actuelle est {} / {}.\n\n"
                                "Voulez-vous l'adapter à la sélection actuelle ?\n"
                                "Les couleurs seront réparties automatiquement (même nom d'abord, "
                                "puis par luminosité) pour donner un point de départ."),
        'preset_adapted': "Preset adapté et appliqué. Ajustez les couleurs si besoin.",
        'update_data': "Mettre à jour les données du jeu",
        'update_locate_fmodel': ("FModel est nécessaire pour extraire les fichiers du jeu.\n\n"
                                 "Cliquez sur OK pour sélectionner FModel.exe, "
                                 "ou téléchargez-le d'abord sur https://fmodel.app"),
        'update_instructions': ("FModel va s'ouvrir. Faites ceci dans FModel :\n\n"
                                "1. Au premier lancement : Directory > Selector > \"Add Undetected Game\",\n"
                                "    nom \"Rivals2\", dossier Paks du jeu, bouton +, puis version UE5_4.\n"
                                "    Activez ensuite \"Local Mapping File\" dans Settings et glissez-y\n"
                                "    le fichier .usmap fourni dans le dossier de cet outil.\n\n"
                                "2. Dans l'arborescence, clic droit sur Rivals2/Content/Characters :\n"
                                "    - Export Folder > Properties (.json)\n"
                                "    - Export Folder > Raw Data (.uasset) — inclut les .uexp\n"
                                "    - Export Folder > Textures (.png) — requis pour les aperçus\n"
                                "    Idem pour Rivals2/Content/Platforms.\n\n"
                                "3. Fermez FModel puis cliquez sur OK ci-dessous pour importer."),
        'update_no_exports': "Aucun export FModel trouvé. Refaites l'export puis réessayez.",
        'update_done': ("Import terminé :\n{} fichiers personnages, {} plateformes, "
                        "{} partagés, {} portraits.\n\nRedémarrez l'outil pour voir les nouveaux personnages."),
        'update_importer_missing': "files_importer.py introuvable à côté de l'application.",
        'file_type_skin': "Skin",
        'file_type_energy': "Élément/Énergie",
        'file_type_portrait': "Portrait",
        'manage_overrides': "Mods installés",
        'overrides_title': "Mods installés (fichiers .pak)",
        'overrides_no_folder': "Configurez d'abord le dossier Mods.",
        'overrides_col_pak': "Fichier .pak",
        'overrides_col_character': "Personnage",
        'overrides_col_skin': "Skin",
        'overrides_col_palette': "Palette",
        'overrides_col_type': "Type",
        'overrides_status': "{} fichier(s) .pak installé(s), {} remplacement(s).",
        'overrides_game_running': "Le jeu est en cours d'exécution : fermez-le pour ajouter ou supprimer des mods.",
        'overrides_refresh': "Actualiser",
        'overrides_open_folder': "Ouvrir le dossier",
        'overrides_remove_selected': "Supprimer la sélection",
        'overrides_remove_all': "Tout supprimer",
        'load_mod_values': "Reprendre les couleurs du mod",
        'mod_values_loaded': "{} couleur(s) chargée(s) depuis {}. Modifiez-les puis relancez le remplacement.",
        'mod_values_none': "Aucun mod installé ne correspond à cette sélection.",
        'mod_values_failed': "Impossible de lire les couleurs du mod installé.",
        'replace_portrait': "Remplacer le portrait de sélection par l'aperçu du skin",
        'portrait_no_module': "Portrait indisponible : portraits.py est introuvable.",
        'portrait_no_game': "Portrait indisponible : installation du jeu introuvable.",
        'portrait_no_oodle': "Portrait indisponible : lancez setup.bat (FModel fournit la DLL Oodle).",
        'portrait_no_data': "Portrait indisponible : données manquantes, utilisez « Mettre à jour les données du jeu ».",
        'choose_mods_folder': "Choisir le dossier Mods du jeu",
        'choose_FModel_output_folder': "Choisir le dossier d'output FModel",
        'overrides_preview': "Aperçu avant/après",
        'overrides_partial_removed': "{} remplacement(s) retiré(s). {} pak(s) reconstruit(s), {} supprimé(s).",
        'override_before': "Avant (jeu d'origine)",
        'override_after': "Après (mod installé)",
        'override_changed': "{} couleur(s) modifiée(s) sur {}.",
        'overrides_confirm': "Retirer {} remplacement(s) ?\n\n{}\n\nLe reste du pak est conservé.",
        'overrides_confirm_all': ("Envoyer les {} fichier(s) .pak à la corbeille ?\n\n"
                                  "Tous vos mods de couleurs seront désactivés. "
                                  "Ils restent récupérables depuis la corbeille."),
        'overrides_close_game': "Fermez le jeu avant de supprimer des mods (les fichiers sont verrouillés).",
        'overrides_removed': "{} fichier(s) .pak envoyé(s) à la corbeille.",
        'overrides_remove_failed': "Suppression impossible. Vérifiez que le jeu est fermé.",
    },
    'en': {
        'title': "ROA 2 Colorswap",
        'configure_mods': "Configure Mods Folder",
        'configure_fmodel_output': "Configure FModel output",
        'save_preset': "Save Preset",
        'load_preset': "Load Preset",
        'replace_colors': "Replace Colors",
        'character': "Character:",
        'skin': "Skin:",
        'color': "Color:",
        'file_type': "File Type:",
        'success_title': "Success",
        'preset_loaded': "Preset loaded successfully.",
        'preset_saved': "Preset saved successfully.",
        'error_title': "Error",
        'json_decode_error': "JSON decoding error.",
        'no_json_loaded': "No JSON file loaded.",
        'json_load_error': "Error loading preset.",
        'uexp_not_found': "UEXP file not found: {}",
        'json_not_found': "JSON file not found: {}",
        'unexpected_json_format': "Unexpected JSON format.",
        'mods_configured': "Mods folder configured.",
        'FModel_output_configured': "FModel output configured",
        'pak_not_found': "The .pak file was not found.",
        'mods_not_configured': ("Mods folder not set. Click the yellow \"Configure Mods Folder\" "
                                "button first and pick your Rivals 2 Mods folder."),
        'script_execution_failed': "Script execution failed: {}",
        'pak_creation_failed': "Failed to create .pak: {}",
        'game_not_closed': "Make sure the game is closed",
        'load_error': "An error occurred while loading the preset: {}",
        'pak_creation_success': "Pak file created and moved to mods folder",
        'preset_mismatch': "The preset does not match the selected character or skin.",
        'preview': "Preview",
        'preview_title': "Preview: {} - {} - {}",
        'preview_unavailable': "No preview image available for this selection.",
        'preview_note': "Approximate preview generated from the in-game portrait.",
        'preview_energy_note': "Approximate energy effect preview (Element0 → Element6 gradient).",
        'preview_shared_note': "Shared skin previewed on every character that has it.",
        'preview_shared_none': ("No character portraits found for this shared skin.\n"
                                "Use \"Update Game Data\" to import them."),
        'preset_adapt_prompt': ("This preset is for {} / {} but the current selection is {} / {}.\n\n"
                                "Apply it adapted to the current selection?\n"
                                "Colors will be assigned automatically (matching names first, "
                                "then by brightness) to give you a starting point."),
        'preset_adapted': "Preset adapted and applied. Fine-tune the colors as needed.",
        'update_data': "Update Game Data",
        'update_locate_fmodel': ("FModel is required to extract the game files.\n\n"
                                 "Click OK to locate FModel.exe, "
                                 "or download it first from https://fmodel.app"),
        'update_instructions': ("FModel will open. Do the following in FModel:\n\n"
                                "1. First launch only: Directory > Selector > \"Add Undetected Game\",\n"
                                "    name \"Rivals2\", the game's Paks folder, + button, then UE version UE5_4.\n"
                                "    Then enable \"Local Mapping File\" in Settings and drag in the\n"
                                "    .usmap file shipped in this tool's folder.\n\n"
                                "2. In the file tree, right-click Rivals2/Content/Characters:\n"
                                "    - Export Folder > Properties (.json)\n"
                                "    - Export Folder > Raw Data (.uasset) — includes the .uexp\n"
                                "    - Export Folder > Textures (.png) — needed for skin previews\n"
                                "    Do the same for Rivals2/Content/Platforms.\n\n"
                                "3. Close FModel, then click OK below to import."),
        'update_no_exports': "No FModel exports found. Redo the export and try again.",
        'update_done': ("Import finished:\n{} character files, {} platforms, "
                        "{} shared, {} portraits.\n\nRestart the tool to see new characters."),
        'update_importer_missing': "files_importer.py not found next to the application.",
        'file_type_skin': "Skin",
        'file_type_energy': "Element/Energy",
        'file_type_portrait': "Portrait",
        'manage_overrides': "Installed Mods",
        'overrides_title': "Installed Mods (.pak files)",
        'overrides_no_folder': "Configure the Mods folder first.",
        'overrides_col_pak': ".pak file",
        'overrides_col_character': "Character",
        'overrides_col_skin': "Skin",
        'overrides_col_palette': "Palette",
        'overrides_col_type': "Type",
        'overrides_status': "{} .pak file(s) installed, {} override(s).",
        'overrides_game_running': "The game is running: close it before adding or removing mods.",
        'overrides_refresh': "Refresh",
        'overrides_open_folder': "Open Folder",
        'overrides_remove_selected': "Remove Selected",
        'overrides_remove_all': "Remove All",
        'load_mod_values': "Load Installed Mod Colors",
        'mod_values_loaded': "Loaded {} color(s) from {}. Edit them and run Replace Colors again.",
        'mod_values_none': "No installed mod matches this selection.",
        'mod_values_failed': "Could not read the colors from the installed mod.",
        'replace_portrait': "Replace character select portrait with skin preview",
        'portrait_no_module': "Portrait unavailable: portraits.py is missing.",
        'portrait_no_game': "Portrait unavailable: game installation not found.",
        'portrait_no_oodle': "Portrait unavailable: run setup.bat (FModel provides the Oodle DLL).",
        'portrait_no_data': "Portrait unavailable: data missing, use \"Update Game Data\" to restore it.",
        'choose_mods_folder': "Choose the game's Mods folder",
        'choose_FModel_output_folder': "Select the FModel output folder",
        'overrides_preview': "Preview Before/After",
        'overrides_partial_removed': "{} override(s) removed. {} pak(s) rebuilt, {} deleted.",
        'override_before': "Before (original game)",
        'override_after': "After (installed mod)",
        'override_changed': "{} of {} colors changed.",
        'overrides_confirm': "Remove {} override(s)?\n\n{}\n\nThe rest of the pak is kept.",
        'overrides_confirm_all': ("Send all {} .pak file(s) to the Recycle Bin?\n\n"
                                  "This disables every color mod you have installed. "
                                  "They stay recoverable from the Recycle Bin."),
        'overrides_close_game': "Close the game before removing mods (the files are locked).",
        'overrides_removed': "{} .pak file(s) sent to the Recycle Bin.",
        'overrides_remove_failed': "Removal failed. Make sure the game is closed.",
    }
}

# Langue actuelle
current_language = 'fr'  # Valeur par défaut, sera chargée depuis la config | Default value, will be loaded from the config


def update_texts():
    # Mettre à jour le titre de la fenêtre | Update the window title
    root.title(translations[current_language]['title'])

    # Mettre à jour les textes des widgets | Update the widget texts
    config_button.config(text=translations[current_language]['configure_mods'])
    config_button2.config(text=translations[current_language]['configure_fmodel_output'])
    save_preset_button.config(
        text=translations[current_language]['save_preset'])
    load_preset_button.config(
        text=translations[current_language]['load_preset'])
    replace_button.config(
        text=translations[current_language]['replace_colors'])
    preview_button.config(
        text=translations[current_language]['preview'])
    load_mod_button.config(
        text=translations[current_language]['load_mod_values'])
    portrait_check.config(
        text=translations[current_language]['replace_portrait'])
    update_data_button.config(
        text=translations[current_language]['update_data'])
    overrides_button.config(
        text=translations[current_language]['manage_overrides'])

    # Mettre à jour les labels | Update the labels
    character_label.config(
        text=translations[current_language]['character'])
    skin_label.config(text=translations[current_language]['skin'])
    color_label.config(text=translations[current_language]['color'])
    file_type_label.config(
        text=translations[current_language]['file_type'])

    # Mettre à jour le menu des langues | Update the language menu
    language_menu['text'] = selected_language.get()

    # Le message d'indisponibilité du portrait doit suivre la langue | The portrait unavailable message must follow the language
    try:
        refresh_portrait_option()
    except NameError:
        pass      # appelé avant la création des widgets | called before the widgets exist


def change_language(*args):
    global current_language
    current_language = language_options[selected_language.get()]
    update_texts()


def save_config():
    # Sauvegarde de la configuration dans un fichier pickle | Save the configuration to a pickle file
    config = {
        'unrealpak_script_path': unrealpak_script_path,
        'mods_folder_path': mods_folder_path,
        'selected_language': current_language,
        'fmodel_path': fmodel_path,
        'fmodel_output_path': fmodel_output_path,
    }
    with open(CONFIG_FILE, 'wb') as f:
        pickle.dump(config, f)


def load_config():
    # Chargement de la configuration depuis le fichier pickle | Load the configuration from the pickle file
    global unrealpak_script_path, mods_folder_path, preset_dir, current_language, fmodel_path, fmodel_output_path
    project_root = os.path.dirname(
        os.path.abspath(__file__))  # Chemin du projet racine | Project root path

    # Chemin de UnrealPak-With-Compression.bat dans Upack | Path to UnrealPak-With-Compression.bat in Upack
    unrealpak_script_path = os.path.join(
        project_root, "Upack", "UnrealPak-With-Compression.bat")

    # Chemin du dossier Preset à la racine du projet | Path to the Preset folder at the project root
    preset_dir = os.path.join(project_root, "Preset")

    # Valeur par défaut de la langue | Default language value
    current_language = 'fr'

    # Charger le dossier mods et la langue depuis le fichier de configuration si disponible | Load the mods folder and language from the config file if available
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'rb') as f:
            config = pickle.load(f)
            mods_folder_path = config.get('mods_folder_path')
            current_language = config.get('selected_language', 'fr')
            fmodel_path = config.get('fmodel_path')
            fmodel_output_path = config.get('fmodel_output_path')


def get_output_and_unrealpak_dirs():
    # Obtient les chemins des dossiers de sortie pour UnrealPak | Gets the output folder paths for UnrealPak
    character = selected_character.get()
    skin = selected_skin.get()
    color = selected_color.get()
    file_type = selected_file_type.get()

    # Dossier à utiliser pour UnrealPak | Folder to use for UnrealPak
    unrealpak_folder_path = os.path.join(
        os.path.dirname(unrealpak_script_path), f"{character}_P")

    if character == 'Ranno' and skin == 'DartFrog':
        # Chemin de sortie pour DartFrog | Output path for DartFrog
        output_folder_path = os.path.join(
            unrealpak_folder_path,
            "Rivals2", "Content", "Characters", character, "Skins", skin, "Data"
        )
    elif character == 'Fleet' and skin == 'Pajama':
        #Même problème, on a besoin d'un dossier Pyjama et un fichier Pajama | Same problem, we need a Pyjama folder and a Pajama file
        output_folder_path = os.path.join(
            unrealpak_folder_path,
            "Rivals2", "Content", "Characters", character, "Skins", 'Pyjama', "Data", "Palettes", color
        )
    elif character == 'Shared':
        output_folder_path = os.path.join(
            unrealpak_folder_path,
            "Rivals2", "Content", "Characters", character, skin
        )
    elif character == 'Platforms': 
        # Les plateformes sont stockées à un endroit différent, pas dans Characters | Platforms are stored elsewhere, not under Characters
        match skin:
            case 'RanDefault':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "RannoDefault"
                )
            case 'EtaDefault':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "EtalusDefault"
                )
            case 'OlyDefault':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "OlympiaDefault"
                )
            case 'Ranger':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "RangerPlat"
                )
            case 'OrcDefault':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "OrcaneDefault"
                )
            case 'Zetterburn':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "ZetterburnDefault"
                )
            case 'AbsDefault':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "AbsaDefault"
                )
            case 'FoodFight':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "Foodfight"
                )
            case 'GalDefault':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "GalvanDefault"
                )
            case 'LarDefault':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "LaReinaDefault"
                )
            case 'Retro':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "RetroBacker"
                )
            case 'GouDefault':
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "GouieDefault"
                )
            case 'Default' if color=='Red' and Primal_platform==True:
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", "Primal"
                )
            case _:
                output_folder_path = os.path.join(
                    unrealpak_folder_path,
                    "Rivals2", "Content", "Platforms", skin
                )

    else:
        # Chemin de sortie général | General output path
        output_folder_path = os.path.join(
            unrealpak_folder_path,
            "Rivals2", "Content", "Characters", character, "Skins", skin, "Data", "Palettes", color
        )

    # Création du dossier de sortie si nécessaire | Create the output folder if needed
    os.makedirs(output_folder_path, exist_ok=True)
    return output_folder_path, unrealpak_folder_path


def save_preset():
    # Vérifier que les données JSON sont chargées | Check that the JSON data is loaded
    if json_data is None:
        messagebox.showerror(
            translations[current_language]['error_title'], translations[current_language]['no_json_loaded'])
        return
    preset_file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[
                                               ("JSON files", "*.json")], initialdir=preset_dir)
    if preset_file:
        preset_data = {
            "Character": selected_character.get(),
            "Skin": selected_skin.get(),
            "Colors": []
        }
        for entry in json_data:
            if "Properties" in entry and "CustomColorSlotDefinitions" in entry["Properties"]:
                for color in entry["Properties"]["CustomColorSlotDefinitions"]:
                    key = color["Key"]
                    if key == "Element0":
                        continue  # Ignorer "Element0"
                    if key in color_entries:
                        hex_color = color_entries[key].get().lstrip('#')
                        if len(hex_color) == 6:
                            r = int(hex_color[0:2], 16) / 255.0
                            g = int(hex_color[2:4], 16) / 255.0
                            b = int(hex_color[4:6], 16) / 255.0
                            new_color = {
                                "Key": key,
                                "Value": {"R": r, "G": g, "B": b}
                            }
                            preset_data["Colors"].append(new_color)
        # Sauvegarder les données du preset | Save the preset data
        with open(preset_file, 'w', encoding='utf-8') as f:
            json.dump(preset_data, f, indent=4)
        messagebox.showinfo(translations[current_language]['success_title'],
                            translations[current_language]['preset_saved'])


def _luminance(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def adapt_preset_to_selection(preset_data):
    """
    Adapte un preset d'un autre personnage/skin à la sélection actuelle :
    correspondance par nom de slot d'abord, puis répartition des couleurs
    restantes par rang de luminosité (les zones sombres du skin reçoivent
    les couleurs sombres du preset, etc.).

    Adapts a preset from another character/skin to the current selection:
    slots are matched by name first, then the remaining colors are spread
    by brightness rank (the skin's dark areas receive the preset's dark
    colors, and so on).
    """
    sources = []
    for color in preset_data.get("Colors", []):
        if color.get("Key") == "Element0":
            continue
        v = color.get("Value", {})
        try:
            rgb = (max(0, min(255, round(float(v["R"]) * 255))),
                   max(0, min(255, round(float(v["G"]) * 255))),
                   max(0, min(255, round(float(v["B"]) * 255))))
        except (KeyError, TypeError, ValueError):
            continue
        sources.append((str(color.get("Key", "")).lower(), rgb))
    if not sources:
        return {}

    targets = []  # (key, couleur d'origine du slot) | (key, the slot's original color)
    for entry in json_data:
        if "Properties" in entry and "CustomColorSlotDefinitions" in entry["Properties"]:
            for color in entry["Properties"]["CustomColorSlotDefinitions"]:
                key = color["Key"]
                if key == "Element0" or key not in color_entries:
                    continue
                orig_hex = rgb_hex_from_json(color["Value"].get("Hex", ""))
                orig = tuple(int(orig_hex[i:i+2], 16)
                             for i in (0, 2, 4)) if orig_hex else (128, 128, 128)
                targets.append((key, orig))

    assignment = {}
    source_by_key = dict(sources)
    used_sources = set()
    remaining = []
    for key, orig in targets:
        src = source_by_key.get(key.lower())
        if src is not None:
            assignment[key] = src
            used_sources.add(key.lower())
        else:
            remaining.append((key, orig))

    if remaining:
        pool = [rgb for k, rgb in sources if k not in used_sources]
        if not pool:
            pool = [rgb for _, rgb in sources]
        pool.sort(key=_luminance)
        remaining.sort(key=lambda t: _luminance(t[1]))
        n = len(remaining)
        for i, (key, _orig) in enumerate(remaining):
            j = round(i * (len(pool) - 1) / max(1, n - 1))
            assignment[key] = pool[j]
    return assignment


def apply_color_assignment(assignment):
    # Écrit les couleurs calculées dans les champs de saisie | Writes the computed colors into the entry fields
    for key, (r, g, b) in assignment.items():
        if key in color_entries:
            hex_color = f"#{r:02X}{g:02X}{b:02X}"
            color_entries[key].delete(0, tk.END)
            color_entries[key].insert(0, hex_color)
            update_color_display(key)


def load_preset():
    # Charge un preset et l'applique aux couleurs actuelles | Loads a preset and applies it to the current colors
    preset_file = filedialog.askopenfilename(
        filetypes=[("JSON files", "*.json")], initialdir=preset_dir)
    if preset_file:
        with open(preset_file, 'r', encoding='utf-8') as f:
            try:
                preset_data = json.load(f)
                # Si le preset vient d'un autre personnage/skin, proposer de l'adapter | If the preset is from another character/skin, offer to adapt it
                if preset_data.get("Character") != selected_character.get() or preset_data.get("Skin") != selected_skin.get():
                    if json_data is None:
                        messagebox.showerror(
                            translations[current_language]['error_title'], translations[current_language]['no_json_loaded'])
                        return
                    accept = messagebox.askyesno(
                        translations[current_language]['load_preset'],
                        translations[current_language]['preset_adapt_prompt'].format(
                            preset_data.get("Character", "?"), preset_data.get("Skin", "?"),
                            selected_character.get(), selected_skin.get()))
                    if not accept:
                        return
                    apply_color_assignment(
                        adapt_preset_to_selection(preset_data))
                    messagebox.showinfo(translations[current_language]['success_title'],
                                        translations[current_language]['preset_adapted'])
                    return
                if json_data is None:
                    messagebox.showerror(
                        translations[current_language]['error_title'], translations[current_language]['no_json_loaded'])
                    return
                # Appliquer les données du preset à json_data | Apply the preset data to json_data
                preset_colors = {color["Key"]: color["Value"]
                                 for color in preset_data.get("Colors", []) if color["Key"] != "Element0"}
                for entry in json_data:
                    if "Properties" in entry and "CustomColorSlotDefinitions" in entry["Properties"]:
                        for color in entry["Properties"]["CustomColorSlotDefinitions"]:
                            key = color["Key"]
                            if key == "Element0":
                                continue  # Ignorer "Element0"
                            if key in preset_colors:
                                value = preset_colors[key]
                                hex_color = f"#{int(value['R'] * 255):02X}{int(value['G'] * 255):02X}{int(value['B'] * 255):02X}"
                                if key in color_entries:
                                    color_entries[key].delete(0, tk.END)
                                    color_entries[key].insert(0, hex_color)
                                    update_color_display(key)
                messagebox.showinfo(translations[current_language]['success_title'],
                                    translations[current_language]['preset_loaded'])
            except json.JSONDecodeError:
                messagebox.showerror(
                    translations[current_language]['error_title'], translations[current_language]['json_load_error'])
            except Exception as e:
                messagebox.showerror(
                    translations[current_language]['error_title'], translations[current_language]['load_error'].format(e))


def precise_float_to_hex(value):
    # Convertit un float en représentation hexadécimale précise | Converts a float to its exact hexadecimal representation
    binary = struct.unpack('>I', struct.pack('>f', value))[0]
    hex_value = f'{binary:08X}'
    return hex_value


def invert_hex(hex_value):
    # Inverse les octets dans une chaîne hexadécimale | Reverses the bytes in a hexadecimal string
    return ''.join([hex_value[i:i+2] for i in range(0, len(hex_value), 2)][::-1])


def hex_to_linear_rgb(color_hex):
    # Convertit une couleur hexadécimale en valeurs RGB linéaires | Converts a hexadecimal color to linear RGB values
    color_hex = color_hex.lstrip('#')
    r = int(color_hex[0:2], 16) / 255.0
    g = int(color_hex[2:4], 16) / 255.0
    b = int(color_hex[4:6], 16) / 255.0

    def linearize(value):
        # Applique la correction gamma pour obtenir une valeur linéaire | Applies gamma correction to get a linear value
        if value <= 0.04045:
            return value / 12.92
        else:
            return ((value + 0.055) / 1.055) ** 2.4

    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)

    return r_lin, g_lin, b_lin


def load_json():
    # Charge le fichier JSON associé au fichier UEXP et met à jour l'interface | Loads the JSON file paired with the UEXP file and updates the UI
    global json_data
    json_file_path = uexp_file_path.replace(".uexp", ".json")

    # Vérifier si le fichier JSON existe | Check whether the JSON file exists
    if not os.path.exists(json_file_path):
        messagebox.showerror(
            translations[current_language]['error_title'], translations[current_language]['json_not_found'].format(json_file_path))
        return False

    # Charger le fichier JSON | Load the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            # Vérifier que le JSON est une liste avec au moins deux éléments | Check that the JSON is a list with at least two entries
            if isinstance(data, list) and len(data) > 1:
                json_data = filter_colors_in_uexp(
                    data)  # Appliquer le filtrage | Apply the filtering
                # Afficher les couleurs filtrées | Display the filtered colors
                populate_color_selectors(json_data)
                # Définir les couleurs de base à partir du JSON | Set the base colors from the JSON
                set_initial_colors(json_data)
                print(f"Fichier JSON chargé et filtré : {json_file_path}")
                return True
            else:
                messagebox.showerror(
                    translations[current_language]['error_title'], translations[current_language]['unexpected_json_format'])
                return False
        except json.JSONDecodeError:
            messagebox.showerror(
                translations[current_language]['error_title'], translations[current_language]['json_decode_error'])
            return False


def rgb_hex_from_json(hex_value):
    # Le JSON stocke AARRGGBB quand la couleur a une transparence (alpha < 1), | The JSON stores AARRGGBB when the color has transparency (alpha < 1),
    # et RRGGBB sinon. Tkinter n'accepte que #RRGGBB : on retire l'alpha. | and RRGGBB otherwise. Tkinter only accepts #RRGGBB, so strip the alpha.
    hex_value = str(hex_value).lstrip('#')
    if len(hex_value) == 8:
        hex_value = hex_value[2:]
    return hex_value if len(hex_value) == 6 else None


def set_initial_colors(data):
    # Initialise les couleurs affichées dans l'interface à partir des données JSON | Initializes the colors shown in the UI from the JSON data
    for entry in data:
        if "Properties" in entry and "CustomColorSlotDefinitions" in entry["Properties"]:
            for color in entry["Properties"]["CustomColorSlotDefinitions"]:
                key = color["Key"]
                if "Hex" in color["Value"]:
                    rgb_hex = rgb_hex_from_json(color["Value"]["Hex"])
                    if key in color_displays and rgb_hex:
                        # Mettre à jour le fond avec la couleur initiale | Update the background with the initial color
                        color_displays[key].config(bg=f'#{rgb_hex}')
                    # Laisser l'entrée vide (ne rien insérer dans color_entries) | Leave the entry blank (insert nothing into color_entries)
                    if key in color_entries:
                        # S'assurer que le champ est vide | Make sure the field is empty
                        color_entries[key].delete(0, tk.END)


def get_preview_recolor_map():
    # Construit la liste (couleur d'origine -> nouvelle couleur) en sRGB | Builds the (original color -> new color) list in sRGB
    # à partir des champs saisis par l'utilisateur | from the fields filled in by the user
    mapping = []
    if json_data is None:
        return mapping
    for entry in json_data:
        if "Properties" in entry and "CustomColorSlotDefinitions" in entry["Properties"]:
            for color in entry["Properties"]["CustomColorSlotDefinitions"]:
                key = color["Key"]
                if key == "Element0":
                    continue
                orig_hex = rgb_hex_from_json(color["Value"].get("Hex", ""))
                if not orig_hex:
                    continue
                orig = tuple(int(orig_hex[i:i+2], 16) for i in (0, 2, 4))
                new = orig
                if key in color_entries:
                    user_hex = color_entries[key].get().lstrip('#')
                    if len(user_hex) == 6:
                        try:
                            new = tuple(int(user_hex[i:i+2], 16)
                                        for i in (0, 2, 4))
                        except ValueError:
                            pass
                mapping.append((orig, new))
    return mapping


def recolor_preview_image(im, mapping):
    # Recolore le portrait : chaque pixel est attribué au slot de palette | Recolors the portrait: each pixel is matched to the palette slot
    # dont il est le plus proche (à un facteur d'ombrage près), puis ce | it is closest to (allowing for a shading factor), then that
    # facteur est réappliqué à la nouvelle couleur pour garder l'ombrage. | factor is reapplied to the new color to preserve shading.
    if not any(o != n for o, n in mapping):
        return im
    im = im.convert("RGBA")
    pixels = list(im.getdata())
    cache = {}
    threshold_sq = 60 * 60 * 3  # tolérance de correspondance (par pixel) | match tolerance (per pixel)
    out = []
    for p in pixels:
        r, g, b, a = p
        if a == 0:
            out.append(p)
            continue
        key = (r >> 3, g >> 3, b >> 3)
        cached = cache.get(key)
        if cached is None:
            best_dist = None
            best_new = None
            best_scale = 1.0
            for orig, new in mapping:
                orr, og, ob = orig
                denom = orr * orr + og * og + ob * ob
                if denom == 0:
                    scale = 0.0
                else:
                    scale = (r * orr + g * og + b * ob) / denom
                    if scale < 0.0:
                        scale = 0.0
                    elif scale > 2.5:
                        scale = 2.5
                dr = r - orr * scale
                dg = g - og * scale
                db = b - ob * scale
                dist = dr * dr + dg * dg + db * db
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best_new = new
                    best_scale = scale
            if best_dist is not None and best_dist <= threshold_sq:
                nr, ng, nb = best_new
                cached = (min(255, int(nr * best_scale)),
                          min(255, int(ng * best_scale)),
                          min(255, int(nb * best_scale)))
            else:
                cached = False  # pixel hors palette : inchangé | pixel outside the palette: left unchanged
            cache[key] = cached
        if cached is False:
            out.append(p)
        else:
            out.append((cached[0], cached[1], cached[2], a))
    result = Image.new("RGBA", im.size)
    result.putdata(out)
    return result


def get_element_ramp():
    # Construit le dégradé Element0 -> ElementN (couleurs éditées incluses) | Builds the Element0 -> ElementN gradient (including edited colors)
    stops = []
    if json_data is None:
        return stops
    for entry in json_data:
        if "Properties" in entry and "CustomColorSlotDefinitions" in entry["Properties"]:
            for color in entry["Properties"]["CustomColorSlotDefinitions"]:
                key = color["Key"]
                if not key.startswith("Element"):
                    continue
                try:
                    index = int(key[len("Element"):])
                except ValueError:
                    continue
                orig_hex = rgb_hex_from_json(color["Value"].get("Hex", ""))
                if not orig_hex:
                    continue
                rgb = tuple(int(orig_hex[i:i+2], 16) for i in (0, 2, 4))
                if key in color_entries:
                    user_hex = color_entries[key].get().lstrip('#')
                    if len(user_hex) == 6:
                        try:
                            rgb = tuple(int(user_hex[i:i+2], 16)
                                        for i in (0, 2, 4))
                        except ValueError:
                            pass
                stops.append((index, rgb))
    stops.sort()
    return [rgb for _, rgb in stops]


def sample_ramp(stops, t):
    # Interpole linéairement dans le dégradé (t entre 0 et 1) | Linearly interpolates within the gradient (t between 0 and 1)
    if not stops:
        return (0, 0, 0)
    if len(stops) == 1 or t <= 0:
        return stops[0]
    if t >= 1:
        return stops[-1]
    pos = t * (len(stops) - 1)
    i = int(pos)
    frac = pos - i
    a, b = stops[i], stops[i + 1]
    return (int(a[0] + (b[0] - a[0]) * frac),
            int(a[1] + (b[1] - a[1]) * frac),
            int(a[2] + (b[2] - a[2]) * frac))


def render_energy_preview(portrait, stops):
    # Dessine une flamme/aura procédurale colorée par le dégradé d'éléments, | Draws a procedural flame/aura colored by the element gradient,
    # avec le portrait par-dessus si disponible, et une barre de dégradé. | with the portrait on top if available, plus a gradient bar.
    import math
    w, h = 400, 400
    bar_h = 26
    aura = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = aura.load()
    cx, cy = w / 2.0, h * 0.62
    for y in range(h):
        for x in range(0, w, 2):  # pas de 2 puis duplication : 2x plus rapide | step of 2 then duplicate: 2x faster
            dx = (x - cx) / (w * 0.42)
            dy = (y - cy) / (h * 0.55)
            if dy < 0:
                # Forme de flamme : haute au centre, courte sur les côtés, | Flame shape: tall at the center, short at the sides,
                # avec un léger vacillement du contour | with a slight flicker along the outline
                taper = 0.42 + 1.1 * abs(dx)
                taper *= 1.0 + 0.07 * math.sin(y * 0.06) + 0.05 * math.sin(y * 0.13 + 1.7)
                dy *= taper
            d = math.sqrt(dx * dx + dy * dy)
            intensity = 1.0 - d
            if intensity <= 0:
                continue
            intensity = intensity ** 1.35
            r, g, b = sample_ramp(stops, intensity)
            alpha = int(255 * min(1.0, intensity * 2.2))
            px[x, y] = (r, g, b, alpha)
            if x + 1 < w:
                px[x + 1, y] = (r, g, b, alpha)
    canvas = Image.new("RGBA", (w, h + bar_h + 8), (242, 242, 242, 255))
    canvas.alpha_composite(aura, (0, 0))
    if portrait is not None:
        p = portrait.copy()
        p.thumbnail((int(w * 0.72), int(h * 0.72)), Image.LANCZOS)
        canvas.alpha_composite(
            p, ((w - p.width) // 2, int(h * 0.94) - p.height))
    # Barre de dégradé en bas | Gradient bar at the bottom
    for x in range(w):
        r, g, b = sample_ramp(stops, x / (w - 1))
        for y in range(h + 8, h + 8 + bar_h):
            canvas.putpixel((x, y), (r, g, b, 255))
    return canvas


preview_window = None


def find_preview_source():
    # Portrait importé à côté de la palette (repli hors ligne) | Imported portrait next to the palette (offline fallback)
    import glob as _glob
    if not uexp_file_path:
        return None
    matches = _glob.glob(os.path.join(
        os.path.dirname(uexp_file_path), "*_CSP.png"))
    return matches[0] if matches else None


def load_portrait_source():
    """
    Portrait d'origine en pleine résolution. Le fichier livré à côté de la
    palette est utilisé en priorité : il évite toute dépendance au jeu, à
    Oodle et à FModel. Le .pak du jeu ne sert que de secours.

    Original portrait at full resolution. The file shipped next to the
    palette is preferred: it avoids any dependency on the game, on Oodle
    and on FModel. The game .pak is only a fallback.
    """
    source = find_preview_source()
    if source:
        try:
            return Image.open(source).convert("RGBA")
        except OSError as e:
            print(f"Portrait illisible ({source}) : {e}")
    name = portrait_file_name()
    if name and portraits_module is not None:
        try:
            pak = get_game_pak()
            if pak is not None:
                image = portraits_module.decode_csp(pak.read_file(name))
                if image is not None:
                    return image
        except (FileNotFoundError, RuntimeError, OSError, ValueError) as e:
            print(f"Portrait non lu depuis le pak ({name}) : {e}")
    return None


_portrait_manifest = None


def load_portrait_manifest():
    """
    En-têtes de textures livrés avec l'outil (145 octets par portrait).
    Ils permettent de reconstruire un .uexp sans lire le jeu.

    Texture headers shipped with the tool (145 bytes per portrait). They
    allow rebuilding a .uexp without reading the game.
    """
    global _portrait_manifest
    if _portrait_manifest is None:
        path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "portrait_headers.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                _portrait_manifest = json.load(f)
        except (OSError, ValueError):
            _portrait_manifest = {}
    return _portrait_manifest


def flatten_source_colors(image, colors=256):
    """
    Regroupe les couleurs de la source avant recoloration.

    La texture du jeu contient du bruit de compression : sans ce
    regroupement, deux pixels voisins d'un même aplat tombent sur des
    slots de palette différents et le résultat est moucheté. L'image
    reste en pleine résolution ; seule la décision d'appariement est
    stabilisée.

    Groups the source colors before recoloring.

    The game texture carries compression noise: without this grouping,
    two neighbouring pixels of the same flat area land on different
    palette slots and the result comes out speckled. The image stays at
    full resolution; only the matching decision is stabilized.
    """
    rgb = image.convert("RGB").quantize(
        colors=colors, method=Image.FASTOCTREE).convert("RGB")
    flattened = rgb.convert("RGBA")
    flattened.putalpha(image.getchannel("A"))
    return flattened


def build_skin_preview_image():
    """
    Construit l'image d'aperçu du skin, en pleine résolution du jeu.
    C'est aussi l'image écrite dans le portrait de sélection, afin que
    l'aperçu corresponde exactement au résultat.

    Builds the skin preview image at the game's full resolution. This is
    also the image written into the character-select portrait, so the
    preview matches the result exactly.
    """
    image = load_portrait_source()
    if image is None:
        return None
    return recolor_preview_image(flatten_source_colors(image),
                                 get_preview_recolor_map())


def shared_skin_portraits(skin, color):
    # Portraits par personnage d'un skin partagé. Un skin comme Goo/Retro n'a | Per-character portraits of a shared skin. A skin like Goo/Retro has no
    # pas de portrait propre, mais chaque personnage qui le possède a son | portrait of its own, but every character that has it owns its imported
    # T_<Cha>_<Skin>_<Color>_CSP.png importé sous son dossier. On les rassemble | T_<Cha>_<Skin>_<Color>_CSP.png under its own folder. We gather them so the
    # pour prévisualiser le skin partagé sur tout le roster concerné. | shared skin can be previewed across the whole affected roster.
    import glob as _glob
    chars_root = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), BASE_DIR)
    pattern = os.path.join(chars_root, "*", "Skins", skin, "Data",
                           "Palettes", color, f"T_*_{skin}_{color}_CSP.png")
    found = []
    for path in _glob.glob(pattern):
        parts = os.path.normpath(path).split(os.sep)
        try:
            character = parts[parts.index("Skins") - 1]
        except ValueError:
            character = os.path.basename(os.path.dirname(path))
        found.append((character, path))
    found.sort(key=lambda cp: cp[0].lower())
    return found


def build_shared_preview_images(max_side=256):
    # Recolore le portrait de chaque personnage avec la palette partagée éditée. | Recolors each character's portrait with the edited shared palette.
    # On réduit d'abord la vignette : la recoloration est en Python pur et une | The thumbnail is downscaled first: recoloring is pure Python and a full-res
    # image pleine résolution par personnage serait lente sans gain visible ici. | image per character would be slow with no visible gain for a gallery cell.
    mapping = get_preview_recolor_map()
    results = []
    for character, path in shared_skin_portraits(selected_skin.get(),
                                                 selected_color.get()):
        try:
            im = Image.open(path).convert("RGBA")
        except OSError as e:
            print(f"Portrait illisible ({path}) : {e}")
            continue
        if max(im.size) > max_side:
            im.thumbnail((max_side, max_side), Image.LANCZOS)
        results.append((character,
                        recolor_preview_image(flatten_source_colors(im), mapping)))
    return results


def show_shared_preview():
    # Galerie défilante : le skin partagé recoloré sur chaque personnage. | Scrollable gallery: the shared skin recolored on every character.
    global preview_window
    images = build_shared_preview_images()
    if not images:
        messagebox.showinfo(translations[current_language]['preview'],
                            translations[current_language]['preview_shared_none'])
        return
    if preview_window is not None and preview_window.winfo_exists():
        preview_window.destroy()
    preview_window = tk.Toplevel(root)
    preview_window.title(translations[current_language]['preview_title'].format(
        selected_character.get(), selected_skin.get(), selected_color.get()))
    preview_window.configure(bg="#f2f2f2")

    note = tk.Label(preview_window, text=translations[current_language]['preview_shared_note'],
                    font=("Arial", 8), bg="#f2f2f2", fg="#666666")
    note.pack(side="bottom", pady=(2, 8))

    canvas = tk.Canvas(preview_window, bg="#f2f2f2", highlightthickness=0)
    scrollbar = tk.Scrollbar(preview_window, orient="vertical",
                             command=canvas.yview)
    grid_frame = tk.Frame(canvas, bg="#f2f2f2")
    grid_frame.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=grid_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    photos = []
    columns = 4
    for i, (character, im) in enumerate(images):
        photo = ImageTk.PhotoImage(im)
        photos.append(photo)
        cell = tk.Frame(grid_frame, bg="#f2f2f2")
        cell.grid(row=i // columns, column=i % columns, padx=8, pady=8)
        tk.Label(cell, image=photo, bg="#f2f2f2").pack()
        tk.Label(cell, text=character, font=("Arial", 9),
                 bg="#f2f2f2", fg="#333333").pack(pady=(4, 0))
    preview_window.photos = photos  # référence anti-GC | anti-GC reference

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    # Fenêtre de taille raisonnable (au plus 3 rangées visibles) + molette. | Reasonably sized window (at most 3 rows visible) + mouse wheel.
    cell_w = images[0][1].width + 32
    cell_h = images[0][1].height + 44
    rows = (len(images) + columns - 1) // columns
    width = min(columns, len(images)) * cell_w + 44
    height = min(3, rows) * cell_h + 60
    preview_window.geometry(f"{int(width)}x{int(height)}")

    def _on_wheel(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_wheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))


def show_preview():
    # Affiche le portrait du jeu recoloré avec les couleurs saisies | Shows the in-game portrait recolored with the entered colors
    global preview_window
    if not uexp_file_path:
        return
    is_energy = file_type_codes.get(selected_file_type.get()) == 'PE'
    # Skin partagé (couleurs) : le prévisualiser sur tout le roster concerné, | Shared skin (colors): preview it across the whole affected roster, since
    # puisqu'une seule palette repeint chaque personnage qui a ce skin. | a single palette repaints every character that has this skin.
    if selected_character.get() == 'Shared' and not is_energy:
        try:
            root.config(cursor="wait")
            root.update()
            show_shared_preview()
        except Exception as e:
            messagebox.showerror(
                translations[current_language]['error_title'], str(e))
        finally:
            root.config(cursor="")
        return
    try:
        root.config(cursor="wait")
        root.update()
        if is_energy:
            im = render_energy_preview(
                load_portrait_source(), get_element_ramp())
        else:
            im = build_skin_preview_image()
        if im is None:
            messagebox.showinfo(translations[current_language]['preview'],
                                translations[current_language]['preview_unavailable'])
            return
        if preview_window is not None and preview_window.winfo_exists():
            preview_window.destroy()
        preview_window = tk.Toplevel(root)
        preview_window.title(translations[current_language]['preview_title'].format(
            selected_character.get(), selected_skin.get(), selected_color.get()))
        preview_window.configure(bg="#f2f2f2")
        photo = ImageTk.PhotoImage(im)
        label = tk.Label(preview_window, image=photo, bg="#f2f2f2")
        label.image = photo  # référence pour éviter le garbage collection | keep a reference to prevent garbage collection
        label.pack(padx=10, pady=(10, 0))
        note_key = 'preview_energy_note' if is_energy else 'preview_note'
        note = tk.Label(preview_window, text=translations[current_language][note_key],
                        font=("Arial", 8), bg="#f2f2f2", fg="#666666")
        note.pack(pady=(2, 8))
    except Exception as e:
        messagebox.showerror(
            translations[current_language]['error_title'], str(e))
    finally:
        root.config(cursor="")


def load_files():
    # Charge le fichier UEXP et le JSON associé | Loads the UEXP file and its paired JSON
    try:
        # Afficher le curseur d'attente | Show the wait cursor
        root.config(cursor="wait")
        root.update()
        # Désactiver les menus déroulants | Disable the dropdown menus
        disable_selection_menus()
        # Désactiver le bouton "Remplacer les couleurs" | Disable the "Replace Colors" button
        replace_button.config(state='disabled')
        preview_button.config(state='disabled')
        load_mod_button.grid_remove()
        # Cacher les clés et les couleurs | Hide the keys and colors
        clear_color_selectors()
        if load_uexp():
            if load_json():
                # Si le chargement est réussi, réactiver le bouton "Remplacer les couleurs" | If loading succeeded, re-enable the "Replace Colors" button
                replace_button.config(state='normal')
                preview_button.config(state='normal')
                # Proposer de reprendre les couleurs du mod déjà installé | Offer to pull in the colors of the already-installed mod
                update_mod_button_state()
    except Exception as e:
        messagebox.showerror(
            translations[current_language]['error_title'], str(e))
    finally:
        # Réactiver les menus après le chargement | Re-enable the menus after loading
        enable_selection_menus()
        # Réinitialiser le curseur | Reset the cursor
        root.config(cursor="")


def clear_color_selectors():
    # Efface les widgets des clés et des couleurs | Clears the key and color widgets
    for widget in color_frame.winfo_children():
        widget.destroy()
    global color_entries, color_displays
    color_entries = {}
    color_displays = {}


def filter_colors_in_uexp(data):
    """
    Filtre les clés du JSON qui correspondent aux couleurs présentes dans le fichier UEXP,
    en respectant l'ordre des valeurs et en ne prenant qu'une occurrence par couleur.

    Filters the JSON keys matching colors present in the UEXP file, keeping
    the order of the values and taking only one occurrence per color.
    """
    with open(uexp_file_path, 'rb') as f:
        uexp_data = f.read().hex().upper()

    filtered_data = []
    current_position = 0  # Position actuelle dans uexp_data pour l'analyse séquentielle | Current position in uexp_data for the sequential scan

    for entry in data:
        if "Properties" in entry and "CustomColorSlotDefinitions" in entry["Properties"]:
            filtered_colors = []
            for color in entry["Properties"]["CustomColorSlotDefinitions"]:
                key = color["Key"]
                value = color["Value"]

                # Convertir chaque composante RGB en hexadécimale | Convert each RGB component to hexadecimal
                hex_r = invert_hex(precise_float_to_hex(value["R"]))
                hex_g = invert_hex(precise_float_to_hex(value["G"]))
                hex_b = invert_hex(precise_float_to_hex(value["B"]))
                color_hex = hex_r + hex_g + hex_b

                # Rechercher séquentiellement la première occurrence de color_hex après current_position | Sequentially find the first occurrence of color_hex after current_position
                position = uexp_data.find(color_hex, current_position)
                if position != -1:
                    # Si trouvé, enregistrer la couleur avec la position actuelle | If found, record the color with its current position
                    color["UEXP_Hex"] = color_hex
                    # Conserver les couleurs trouvées | Keep the colors that were found
                    filtered_colors.append(color)
                    # Mettre à jour current_position pour poursuivre après cet emplacement | Update current_position to continue past this location
                    current_position = position + len(color_hex)

                    # Afficher les détails de la correspondance | Print the match details
                    print(f"Correspondance trouvée pour '{key}':")
                    print(f"  Valeur dans UEXP : {color_hex}")
                    print(f"  Position dans UEXP : {position}")
                else:
                    print(
                        f"Valeur {color_hex} non trouvée pour la couleur {key}, passage à la suivante.")

            if filtered_colors:
                # Si des couleurs filtrées ont été trouvées, conserver l'entrée | If filtered colors were found, keep the entry
                filtered_entry = entry.copy()
                filtered_entry["Properties"]["CustomColorSlotDefinitions"] = filtered_colors
                filtered_data.append(filtered_entry)
    return filtered_data


def populate_color_selectors(data):
    # Effacer les widgets précédents | Clear the previous widgets
    for widget in color_frame.winfo_children():
        widget.destroy()

    global color_entries, color_displays
    color_entries = {}
    color_displays = {}

    row = 0
    col = 0
    for entry in data:
        if "Properties" in entry and "CustomColorSlotDefinitions" in entry["Properties"]:
            for color in entry["Properties"]["CustomColorSlotDefinitions"]:
                key = color["Key"]

                # Ignorer "Element0"
                if key == "Element0":
                    continue  # Passe à la couleur suivante | Move on to the next color

                # Afficher les informations de la couleur qui va être ajoutée | Print info about the color about to be added
                print(
                    f"Affichage de la couleur '{key}' avec correspondance trouvée")

                # Créer les champs pour chaque clé filtrée | Create the fields for each filtered key
                label = tk.Label(color_frame, text=key,
                                 font=("Arial", 10, "bold"))
                label.grid(row=row, column=col*3, padx=5, pady=5, sticky="w")

                color_entry = tk.Entry(
                    color_frame, width=10, font=("Arial", 10))
                color_entry.grid(row=row, column=col*3 + 1, padx=5, pady=5)
                color_entries[key] = color_entry
                color_entry.bind("<KeyRelease>", lambda e,
                                 k=key: update_color_display(k))

                color_display = tk.Label(
                    color_frame, width=2, height=1, bg="#FFFFFF", relief="solid", borderwidth=1)
                color_display.grid(
                    row=row, column=col*3 + 2, padx=5, pady=5)
                color_displays[key] = color_display

                # Ajouter l'événement de clic sur le carré de couleur | Add the click event on the color square
                color_display.bind("<Button-1>", lambda e,
                                   k=key: choose_color(k))

                col += 1
                if col >= 2:
                    col = 0
                    row += 1


def choose_color(key):
    # Ouvre un sélecteur de couleurs pour choisir une couleur | Opens a color picker to choose a color
    current_color = color_entries[key].get()
    if not current_color:
        current_color = color_displays[key].cget("bg")
    if not current_color or current_color == 'SystemButtonFace':
        current_color = "#FFFFFF"
    color_code = colorchooser.askcolor(
        title="Choisir une couleur", initialcolor=current_color)[1]
    if color_code:
        color_entries[key].delete(0, tk.END)
        color_entries[key].insert(0, color_code)
        update_color_display(key)


def update_color_display(key):
    # Met à jour le carré de couleur en fonction de l'entrée utilisateur | Updates the color square based on the user's input
    hex_color = color_entries[key].get()
    if hex_color.startswith('#') and len(hex_color) == 7:
        color_displays[key].config(bg=hex_color)


def load_uexp():
    # Charge le fichier UEXP basé sur la sélection de l'utilisateur | Loads the UEXP file based on the user's selection
    global uexp_file_path
    character = selected_character.get()
    skin = selected_skin.get()
    color = selected_color.get()
    file_type_code = file_type_codes.get(selected_file_type.get())

    # Cas particulier pour Ranno - DartFrog | Special case for Ranno - DartFrog
    if character == 'Ranno' and skin == 'DartFrog':
        # Les fichiers sont dans Data, pas dans Data/Palettes/Color | The files live in Data, not in Data/Palettes/Color
        uexp_directory = os.path.join(
            BASE_DIR, character, "Skins", skin, "Data")

        # Le nom du fichier est au format : PS_Ran_Dart_Color.uexp | The file name follows the format: PS_Ran_Dart_Color.uexp
        character_prefix = character[:3].capitalize()
        uexp_filename = f"{file_type_code}_{character_prefix}_Dart_{color}.uexp"
    elif character == 'Fleet' and skin == 'Pyjama' :
        #Les fichiers utilisent l'orthographe Pajama mais le dossier est Pyjama... DAN | The files are spelled Pajama but the folder is Pyjama... DAN
        uexp_directory = os.path.join(
            BASE_DIR, character, "Skins", skin, "Data", "Palettes", color)

        character_prefix = character[:3].capitalize()
        uexp_filename = f"{file_type_code}_{character_prefix}_Pajama_{color}.uexp"
    elif character == 'Platforms':
        uexp_directory = os.path.join(
            BASE_DIR, character, "Skins", skin, "Data", "Palettes", color)
        if skin == 'EtalusDefault':
            uexp_filename = f"{file_type_code}_Pla_EtaDefault_{color}.uexp"
        elif skin == 'OlympiaDefault':
            uexp_filename = f"{file_type_code}_Pla_OlyDefault_{color}.uexp"
        elif skin == 'OrcaneDefault':
            uexp_filename = f"{file_type_code}_Pla_OrcDefault_{color}.uexp"
        elif skin == 'RangerPlat':
            uexp_filename = f"{file_type_code}_Pla_Ranger_{color}.uexp"
        elif skin == 'RannoDefault' and color == 'Green':
            uexp_filename = f"{file_type_code}_Pla_RanDefault_{color}.uexp"
        elif skin == 'ZetterburnDefault':
            uexp_filename = f"{file_type_code}_Pla_Zetterburn_{color}.uexp"
        elif skin == 'AbsaDefault':
            uexp_filename = f"{file_type_code}_Pla_AbsDefault_{color}.uexp"
        elif skin == 'Foodfight':
            uexp_filename = f"{file_type_code}_Pla_FoodFight_{color}.uexp"
        elif skin == 'LaReinaDefault':
            uexp_filename = f"{file_type_code}_Pla_LarDefault_{color}.uexp"
        elif skin == 'GouieDefault':
            uexp_filename = f"{file_type_code}_Pla_GouDefault_{color}.uexp"
        elif skin == 'RetroBacker':
            uexp_filename = f"{file_type_code}_Pla_Retro_{color}.uexp"
        elif skin == 'Primal' and color == 'Red':
            uexp_filename = f"{file_type_code}_Pla_Default_{color}.uexp"
            Primal_platform = True #DAN FIX YOUR GAME, there are 2 files named the same in different folders
        elif skin == 'Default':
            uexp_filename = f"{file_type_code}_Pla_{skin}_{color}.uexp"
            Primal_platform = False 
        else:
            uexp_filename = f"{file_type_code}_Pla_{skin}_{color}.uexp"

    else:
        # Cas général | General case
        # Construction du nom de fichier selon le format | Build the file name according to the format
        character_prefix = character[:3].capitalize()
        if character == 'Shared':
            character_prefix = 'Cha'
        uexp_filename = f"{file_type_code}_{character_prefix}_{skin}_{color}.uexp"
        # Chemin du dossier UEXP | Path to the UEXP folder
        uexp_directory = os.path.join(
            BASE_DIR, character, "Skins", skin, "Data", "Palettes", color)

    # Construction du chemin complet du fichier UEXP | Build the full path to the UEXP file
    uexp_file_path = os.path.join(uexp_directory, uexp_filename)

    # Vérification de l'existence du fichier | Check that the file exists
    if not os.path.exists(uexp_file_path):
        messagebox.showerror(
            translations[current_language]['error_title'], translations[current_language]['uexp_not_found'].format(uexp_file_path))
        return False
    print(f"Fichier UEXP chargé : {uexp_file_path}")
    return True


def replace_colors_in_uexp():
    # Remplace les couleurs dans le fichier UEXP en fonction des entrées utilisateur | Replaces the colors in the UEXP file based on the user's entries
    if json_data is None:
        messagebox.showerror(
            translations[current_language]['error_title'], translations[current_language]['no_json_loaded'])
        return

    try:
        # Obtenir les chemins de sortie et de UnrealPak | Get the output and UnrealPak paths
        output_folder_path, unrealpak_folder_path = get_output_and_unrealpak_dirs()

        # Copier le fichier UEXP dans le dossier de sortie avec la hiérarchie complète | Copy the UEXP file into the output folder with the full hierarchy
        modified_uexp_path = os.path.join(
            output_folder_path, os.path.basename(uexp_file_path))
        shutil.copy(uexp_file_path, modified_uexp_path)
        print(
            f"Fichier UEXP copié dans le dossier de sortie : {modified_uexp_path}")

        # Charger les données de la copie du fichier UEXP en hexadécimale pour modification | Load the copied UEXP file's data as hex for editing
        with open(modified_uexp_path, 'rb') as f:
            uexp_data = f.read().hex().upper()

        modified_data = uexp_data
        current_position = 0  # Position de départ pour les remplacements séquentiels | Starting position for the sequential replacements

        for key, entry in color_entries.items():
            hex_color_input = entry.get()
            if not hex_color_input:
                continue  # Ignorer les champs vides | Skip empty fields

            # Conversion de la couleur hex en valeurs linéaires RGB pour remplacement | Convert the hex color to linear RGB values for replacement
            r, g, b = hex_to_linear_rgb(hex_color_input)
            hex_r = invert_hex(precise_float_to_hex(r))
            hex_g = invert_hex(precise_float_to_hex(g))
            hex_b = invert_hex(precise_float_to_hex(b))
            new_hex = hex_r + hex_g + hex_b

            # Rechercher la couleur d'origine à partir du JSON filtré | Look up the original color from the filtered JSON
            selected_color_entry = None
            for item in json_data:
                if "Properties" in item and "CustomColorSlotDefinitions" in item["Properties"]:
                    for color in item["Properties"]["CustomColorSlotDefinitions"]:
                        if color["Key"] == key and "UEXP_Hex" in color:
                            selected_color_entry = color
                            break

            # Si la couleur d'origine existe, procéder au remplacement séquentiel | If the original color exists, perform the sequential replacement
            if selected_color_entry:
                original_hex = selected_color_entry["UEXP_Hex"]
                # Rechercher la première occurrence après la position courante | Find the first occurrence after the current position
                position = modified_data.find(
                    original_hex, current_position)
                if position != -1:
                    # Remplacer cette occurrence uniquement et afficher les informations de modification | Replace only this occurrence and print the change details
                    modified_data = (
                        modified_data[:position] + new_hex +
                        modified_data[position + len(original_hex):]
                    )
                    # Afficher les détails de la modification | Print the change details
                    print(f"Modification pour la clé '{key}':")
                    print(f"  Couleur d'origine : {original_hex}")
                    print(f"  Nouvelle couleur  : {new_hex}")
                    print(f"  Position de remplacement : {position}")

                    # Mettre à jour la position courante pour continuer après cet emplacement | Update the current position to continue past this location
                    current_position = position + len(new_hex)
                else:
                    print(
                        f"Couleur '{key}' non trouvée dans le fichier UEXP.")
            else:
                print(
                    f"Aucune correspondance trouvée pour la clé '{key}' dans le JSON.")

        # Convertir les données modifiées en bytes et les écrire dans le fichier UEXP modifié | Convert the modified data back to bytes and write the modified UEXP file
        uexp_bytes = bytes.fromhex(modified_data)
        with open(modified_uexp_path, 'wb') as f:
            f.write(uexp_bytes)

        # Portrait de sélection : recoloré et ajouté au même dossier de staging | Character-select portrait: recolored and added to the same staging folder
        if replace_portrait_var.get():
            build_recolored_portrait(output_folder_path)

        ask_for_pak_directory_and_create(unrealpak_folder_path)
    except Exception as e:
        messagebox.showerror(
            translations[current_language]['error_title'], str(e))


def portrait_file_name():
    """
    Nom du fichier portrait correspondant à la sélection, déduit du .uexp
    de palette : PS_For_Ranger_Neutral.uexp -> T_For_Ranger_Neutral_CSP.uexp

    Portrait file name for the current selection, derived from the palette
    .uexp: PS_For_Ranger_Neutral.uexp -> T_For_Ranger_Neutral_CSP.uexp
    """
    if not uexp_file_path:
        return None
    stem = os.path.splitext(os.path.basename(uexp_file_path))[0]
    parts = stem.split('_')
    if len(parts) != 4:
        return None
    return 'T_' + '_'.join(parts[1:]) + '_CSP.uexp'


def find_game_pak_file():
    # Le .pak principal du jeu, qui contient les portraits | The game's main .pak, which holds the portraits
    paks = find_game_paks_dir()
    if not paks:
        return None
    for name in os.listdir(paks):
        if name.lower().endswith('.pak') and 'windows' in name.lower():
            return os.path.join(paks, name)
    return None


def fmodel_search_dirs():
    # Emplacements où chercher la DLL Oodle installée par FModel | Places to look for the Oodle DLL installed by FModel
    dirs = []
    if fmodel_path:
        exe_dir = os.path.dirname(fmodel_path)
        dirs += [os.path.join(exe_dir, "Output"), exe_dir]
    app_dir = os.path.dirname(os.path.abspath(__file__))
    dirs.append(os.path.join(app_dir, "FModel", "Output"))
    dirs.append(os.path.join(app_dir, "FModel"))
    appdata = os.environ.get('APPDATA')
    if appdata:
        cfg = os.path.join(appdata, "FModel", "AppSettings.json")
        try:
            with open(cfg, 'r', encoding='utf-8') as f:
                output = json.load(f).get("OutputDirectory")
            if output:
                dirs.append(output)
        except (OSError, ValueError):
            pass
    return [d for d in dirs if d and os.path.isdir(d)]


def portrait_support_status():
    """
    Vérifie que le remplacement de portrait est possible.
    Renvoie (disponible, message d'explication).

    Checks whether portrait replacement is possible.
    Returns (available, explanation message).
    """
    if portraits_module is None:
        return False, translations[current_language]['portrait_no_module']
    name = portrait_file_name()
    # Cas normal : en-tête livré + portrait livré, aucun accès au jeu | Normal case: shipped header + shipped portrait, no game access
    if name and name in load_portrait_manifest() and find_preview_source():
        return True, ""
    # Secours : lire la texture directement dans le .pak (nécessite Oodle) | Fallback: read the texture straight from the .pak (needs Oodle)
    if find_game_pak_file() and portraits_module.find_oodle_dll(fmodel_search_dirs()):
        return True, ""
    return False, translations[current_language]['portrait_no_data']


_game_pak_cache = {}


def get_game_pak():
    # L'index du pak est coûteux à lire : on le garde en mémoire | The pak index is costly to read: keep it in memory
    pak_path = find_game_pak_file()
    if not pak_path:
        return None
    if pak_path not in _game_pak_cache:
        dll = portraits_module.find_oodle_dll(fmodel_search_dirs())
        _game_pak_cache[pak_path] = portraits_module.GamePak(
            pak_path, portraits_module.Oodle(dll) if dll else None)
    return _game_pak_cache[pak_path]


def build_recolored_portrait(output_folder_path):
    """
    Écrit l'image d'aperçu du skin dans le portrait de sélection.

    Le .uexp d'origine est lu dans le .pak du jeu pour en conserver
    l'en-tête et la taille exacte ; seuls les pixels viennent de l'aperçu.
    Recoloriser l'aperçu (déjà aplati en 256 couleurs) donne des aplats
    nets, là où la texture pleine résolution produit des taches.

    Writes the skin preview image into the character-select portrait.

    The original .uexp is read from the game .pak to keep its header and
    exact size; only the pixels come from the preview. Recoloring the
    preview (already flattened to 256 colours) gives clean flat areas,
    whereas the full-resolution texture comes out speckled.
    """
    name = portrait_file_name()
    if not name:
        return False

    recolored = build_skin_preview_image()
    if recolored is None:
        print("Aucune image d'aperçu disponible pour cette sélection.")
        return False

    entry = load_portrait_manifest().get(name)
    if entry:
        # Chemin normal : tout est livré avec l'outil | Normal path: everything ships with the tool
        import base64
        patched = portraits_module.build_csp_uexp(
            base64.b64decode(entry['wrapper']), recolored, entry['side'])
    else:
        # Secours : relire la texture d'origine dans le .pak du jeu | Fallback: re-read the original texture from the game .pak
        pak = get_game_pak()
        if pak is None:
            print(f"Aucun en-tête connu pour {name} et pak indisponible.")
            return False
        try:
            original_uexp = pak.read_file(name)
        except (FileNotFoundError, RuntimeError, OSError) as e:
            print(f"Portrait introuvable dans le pak : {name} ({e})")
            return False
        if portraits_module.csp_layout(original_uexp) is None:
            print(f"Disposition de texture non prise en charge : {name}")
            return False
        patched = portraits_module.encode_csp(original_uexp, recolored)

    os.makedirs(output_folder_path, exist_ok=True)
    destination = os.path.join(output_folder_path, name)
    with open(destination, 'wb') as f:
        f.write(patched)
    print(f"Portrait recoloré écrit : {destination}")
    return True


def default_mods_folder():
    # Dossier Mods du jeu, créé au besoin (rien n'est codé en dur) | The game's Mods folder, created if needed (nothing hardcoded)
    paks = find_game_paks_dir()
    if not paks:
        return None
    mods = os.path.join(paks, 'Mods')
    try:
        os.makedirs(mods, exist_ok=True)
    except OSError:
        return paks if os.path.isdir(paks) else None
    return mods


def configure_script_and_mods_folder():
    # Permet à l'utilisateur de sélectionner le dossier mods | Lets the user select the mods folder
    global mods_folder_path
    # Démarrer la sélection dans le dossier Mods détecté automatiquement | Start the picker in the auto-detected Mods folder
    initial = mods_folder_path if mods_folder_path and os.path.isdir(
        mods_folder_path) else default_mods_folder()
    # Demander uniquement le dossier mods | Ask only for the mods folder
    chosen = filedialog.askdirectory(
        title=translations[current_language]['choose_mods_folder'],
        initialdir=initial or os.path.expanduser("~"))
    if not chosen:
        return
    mods_folder_path = chosen
    save_config()
    messagebox.showinfo(translations[current_language]['success_title'],
                        translations[current_language]['mods_configured'])


def configure_FModel_export_folder():
    # Permet à l'utilisateur de sélectionner le dossier d'output FModel | Lets the user select the FModel output folder
    global fmodel_output_path
    # Démarrer la sélection dans le dossier output FModel détecté automatiquement | Start the picker in the auto-detected FModel output folder
    initial = fmodel_output_path if fmodel_output_path and os.path.isdir(
        fmodel_output_path) else default_mods_folder()
    # Demander uniquement le dossier mods | Ask only for the mods folder
    chosen = filedialog.askdirectory(
        title=translations[current_language]['choose_FModel_output_folder'],
        initialdir=initial or os.path.expanduser("~"))
    if not chosen:
        return
    fmodel_output_path = chosen
    save_config()
    messagebox.showinfo(translations[current_language]['success_title'],
                        translations[current_language]['FModel_output_configured'])


def ask_for_pak_directory_and_create(unrealpak_folder_path):
    # Exécute UnrealPak pour créer le fichier .pak et le déplace dans le dossier mods | Runs UnrealPak to create the .pak file and moves it to the mods folder
    global mods_folder_path
    # Sans dossier Mods, le déplacement final planterait sur un chemin None. On | Without a Mods folder the final move would crash on a None path. Auto-detect
    # le détecte automatiquement (dossier Mods du jeu) ; si le jeu est introuvable, | it (the game's Mods folder); if the game can't be found, tell the user to set
    # on demande à l'utilisateur de le configurer plutôt qu'une erreur obscure. | it via the button instead of showing a cryptic error.
    if not mods_folder_path or not os.path.isdir(mods_folder_path):
        auto = default_mods_folder()
        if auto:
            mods_folder_path = auto
            save_config()
        else:
            messagebox.showerror(translations[current_language]['error_title'],
                                 translations[current_language]['mods_not_configured'])
            return
    character = selected_character.get()
    # Construire le chemin du dossier de sortie pour UnrealPak basé sur le personnage sélectionné | Build the UnrealPak output folder path from the selected character
    unrealpak_folder_path = os.path.join(
        os.path.dirname(unrealpak_script_path), f"{character}_P")

    # Créer le dossier si nécessaire | Create the folder if needed
    os.makedirs(unrealpak_folder_path, exist_ok=True)

    try:
        # Exécuter UnrealPak-With-Compression.bat en utilisant le dossier unrealpak_folder_path | Run UnrealPak-With-Compression.bat using the unrealpak_folder_path folder
        subprocess.run(
            [unrealpak_script_path, unrealpak_folder_path], check=True)
        time.sleep(0.2)  # Pause pour s'assurer que le fichier est créé | Pause to make sure the file has been created

        # Rechercher le fichier .pak dans le répertoire UnrealPak | Look for the .pak file in the UnrealPak directory
        generated_pak = None
        for file in os.listdir(os.path.dirname(unrealpak_script_path)):
            if file.endswith(".pak"):
                generated_pak = os.path.join(
                    os.path.dirname(unrealpak_script_path), file)
                break

        if generated_pak and os.path.exists(generated_pak):
            destination = os.path.join(
                mods_folder_path, os.path.basename(generated_pak))
            shutil.move(generated_pak, destination)
            messagebox.showinfo(
                translations[current_language]['success_title'], f"{translations[current_language]['pak_creation_success']} : {mods_folder_path}")
        else:
            messagebox.showerror(
                translations[current_language]['error_title'], translations[current_language]['pak_not_found'])
    except subprocess.CalledProcessError as e:
        messagebox.showerror(
            translations[current_language]['error_title'], translations[current_language]['script_execution_failed'].format(e))
    except PermissionError as e:
        if e.errno == 13:
            messagebox.showerror(
                translations[current_language]['error_title'], translations[current_language]['game_not_closed'])
        else:
            messagebox.showerror(
                translations[current_language]['error_title'], translations[current_language]['pak_creation_failed'].format(e))
    except Exception as e:
        messagebox.showerror(
            translations[current_language]['error_title'], translations[current_language]['pak_creation_failed'].format(e))


def load_character_icons():
    # Charge les icônes des personnages depuis le dossier 'icons' | Loads the character icons from the 'icons' folder
    characters_path = os.path.join(BASE_DIR)
    characters = [name for name in os.listdir(
        characters_path) if os.path.isdir(os.path.join(characters_path, name))]
    for character in characters:
        image_path = f"icons/{character}.png"  # Chemin de chaque icône PNG | Path to each PNG icon
        if os.path.exists(image_path):  # Vérifie si l'image existe | Check whether the image exists
            try:
                # Ajustez la taille si nécessaire | Adjust the size if needed
                img = Image.open(image_path).resize((32, 32))
                character_icons[character] = ImageTk.PhotoImage(
                    img)  # Convertir en PhotoImage pour Tkinter | Convert to PhotoImage for Tkinter
            except Exception as e:
                print(
                    f"Erreur : Impossible de charger l'image {image_path}. {e}")
        else:
            print(f"Image non trouvée pour le personnage {character}")
    return characters


def update_selected_character_icon(*args):
    # Met à jour l'icône affichée du personnage sélectionné | Updates the displayed icon for the selected character
    selected_character_name = selected_character.get()
    # Mettre à jour l'icône dans le Label | Update the icon in the Label
    selected_character_icon_label.config(
        image=character_icons.get(selected_character_name))
    selected_character_icon_label.image = character_icons.get(
        selected_character_name)  # Référence pour éviter le garbage collection | Keep a reference to prevent garbage collection
    # Mettre à jour le menu des skins | Update the skin menu
    update_skin_menu()


def skin_has_editable_palette(character_name, skin_name):
    # Vrai si le skin a une vraie palette éditable (fichier PE_/PS_). Les skins | True if the skin has a real editable palette (a PE_/PS_ file). Shared skins
    # partagés importés uniquement comme portraits (T_*_CSP, sans palette par | imported only as portraits (T_*_CSP, with no per-character palette) have none:
    # personnage) n'en ont pas : ils s'éditent via le personnage « Shared » et ne | they are edited through the "Shared" character and must not show up as a
    # doivent pas apparaître comme un skin éditable ici (sinon menu vide + blocage). | selectable skin here (otherwise: empty menus and a stuck-looking UI).
    base = os.path.join(BASE_DIR, character_name, 'Skins', skin_name)
    palettes = os.path.join(base, 'Data', 'Palettes')
    if not os.path.isdir(palettes):
        # Forme spéciale (ex. Ranno/DartFrog range ses .uexp directement sous Data/). | Special shape (e.g. Ranno/DartFrog keeps its .uexp directly under Data/).
        data = os.path.join(base, 'Data')
        if os.path.isdir(data):
            return any(f.startswith(('PE_', 'PS_')) for f in os.listdir(data))
        return True  # structure inconnue : ne pas filtrer | unknown structure: don't filter
    for color in os.listdir(palettes):
        color_dir = os.path.join(palettes, color)
        if os.path.isdir(color_dir) and any(
                f.startswith(('PE_', 'PS_')) for f in os.listdir(color_dir)):
            return True
    return False


def update_skin_menu(*args):
    # Met à jour le menu des skins en fonction du personnage sélectionné | Updates the skin menu based on the selected character
    character_name = selected_character.get()
    skins_path = os.path.join(BASE_DIR, character_name, 'Skins')
    if os.path.exists(skins_path):
        skins = [name for name in os.listdir(
            skins_path) if os.path.isdir(os.path.join(skins_path, name))]
        # Masquer les skins partagés importés seulement comme portraits : sans | Hide shared skins imported only as portraits: with no editable palette they
        # palette éditable ils ouvrent un skin vide. Le personnage « Shared » les | open an empty skin. The "Shared" character keeps them for editing the shared
        # garde pour éditer la palette partagée. | palette.
        if character_name != 'Shared':
            skins = [s for s in skins
                     if skin_has_editable_palette(character_name, s)]
        # Trier les skins pour un affichage cohérent | Sort the skins for consistent display
        skins.sort()
        # Effacer les anciennes options du menu | Clear the menu's previous options
        skin_menu['menu'].delete(0, 'end')
        for skin in skins:
            skin_menu['menu'].add_command(
                label=skin, command=tk._setit(selected_skin, skin))
        # Sélectionner 'Default' si disponible, sinon le premier skin | Select 'Default' if available, otherwise the first skin
        if 'Default' in skins:
            selected_skin.set('Default')
        elif skins:
            selected_skin.set(skins[0])
        else:
            selected_skin.set('')
    else:
        selected_skin.set('')
        skin_menu['menu'].delete(0, 'end')
    # Mettre à jour le menu des couleurs | Update the color menu
    update_color_menu()


def update_color_menu(*args):
    # Met à jour le menu des couleurs en fonction du skin sélectionné | Updates the color menu based on the selected skin
    character_name = selected_character.get()
    skin_name = selected_skin.get()

    if character_name == 'Ranno' and skin_name == 'DartFrog':
        # Les couleurs sont déterminées par les fichiers dans le dossier Data | The colors are determined by the files in the Data folder
        data_path = os.path.join(
            BASE_DIR, character_name, 'Skins', skin_name, 'Data')
        if os.path.exists(data_path):
            colors = []
            for file in os.listdir(data_path):
                if file.endswith('.uexp'):
                    # Extraire la couleur du nom du fichier | Extract the color from the file name
                    # Format attendu : PS_Ran_Dart_Color.uexp
                    parts = file.replace('.uexp', '').split('_')
                    if len(parts) >= 4:
                        color = parts[3]
                        colors.append(color)
            # Supprimer les doublons et trier | Remove duplicates and sort
            colors = sorted(set(colors))
        else:
            colors = []
    else:
        # Cas général | General case
        palettes_path = os.path.join(
            BASE_DIR, character_name, 'Skins', skin_name, 'Data', 'Palettes')
        if os.path.exists(palettes_path):
            colors = [name for name in os.listdir(palettes_path) if os.path.isdir(
                os.path.join(palettes_path, name))]
            colors.sort()
        else:
            colors = []

    # Mettre à jour le menu des couleurs | Update the color menu
    color_menu['menu'].delete(0, 'end')
    for color in colors:
        color_menu['menu'].add_command(
            label=color, command=tk._setit(selected_color, color))
    if colors:
        selected_color.set(colors[0])
    else:
        selected_color.set('')
    # Mettre à jour le menu des types de fichiers | Update the file type menu
    update_file_type_menu()


def update_file_type_menu(*args):
    # Met à jour le menu des types de fichiers en fonction de la couleur sélectionnée | Updates the file type menu based on the selected color
    character_name = selected_character.get()
    skin_name = selected_skin.get()
    color_name = selected_color.get()

    if character_name == 'Ranno' and skin_name == 'DartFrog':
        # Les fichiers sont dans Data | The files live in Data
        data_path = os.path.join(
            BASE_DIR, character_name, 'Skins', skin_name, 'Data')
        file_types_found = []
        if os.path.exists(data_path):
            files = os.listdir(data_path)
            for file in files:
                if file.endswith('.uexp') and color_name in file:
                    if file.startswith('PE_'):
                        file_types_found.append('Element/Energy')
                    elif file.startswith('PS_'):
                        file_types_found.append('Skin')
            file_types_found = list(set(file_types_found))
            file_types_found.sort()
        else:
            file_types_found = []
    else:
        # Cas général | General case
        data_path = os.path.join(BASE_DIR, character_name,
                                 'Skins', skin_name, 'Data', 'Palettes', color_name)
        file_types_found = []
        if os.path.exists(data_path):
            files = os.listdir(data_path)
            for file in files:
                if file.startswith('PE_'):
                    file_types_found.append('Element/Energy')
                elif file.startswith('PS_'):
                    file_types_found.append('Skin')
            file_types_found = list(set(file_types_found))
            file_types_found.sort()
        else:
            print(f"Chemin non trouvé : {data_path}")

    # Mettre à jour le dictionnaire des codes de type de fichier | Update the file type code dictionary
    global file_type_codes
    file_type_codes = {'Element/Energy': 'PE', 'Skin': 'PS'}

    # Mettre à jour le menu des types de fichiers | Update the file type menu
    file_type_menu['menu'].delete(0, 'end')
    for file_type in file_types_found:
        file_type_menu['menu'].add_command(
            label=file_type, command=tk._setit(selected_file_type, file_type))
    # Sélectionner 'Skin' si disponible, sinon le premier type de fichier | Select 'Skin' if available, otherwise the first file type
    if 'Skin' in file_types_found:
        selected_file_type.set('Skin')
    elif file_types_found:
        selected_file_type.set(file_types_found[0])
    else:
        selected_file_type.set('')


def create_character_menu(characters):
    # Crée le menu déroulant des personnages avec icônes | Creates the character dropdown menu with icons
    character_menu = tk.Menubutton(
        header_frame, textvariable=selected_character, indicatoron=True, borderwidth=1, relief="raised")
    character_menu.grid(row=0, column=3, padx=2, pady=5, sticky="w")
    character_menu.menu = tk.Menu(character_menu, tearoff=False)
    character_menu["menu"] = character_menu.menu

    for character in characters:
        character_icon = character_icons.get(character)
        character_menu.menu.add_radiobutton(
            label=character,
            image=character_icon,
            compound='left',
            variable=selected_character,
            value=character,
            command=lambda c=character: selected_character.set(c)
        )
    return character_menu


def disable_selection_menus():
    # Désactiver les menus déroulants pendant le chargement | Disable the dropdown menus while loading
    character_menu.config(state='disabled')
    skin_menu.config(state='disabled')
    color_menu.config(state='disabled')
    file_type_menu.config(state='disabled')


def enable_selection_menus():
    # Réactiver les menus déroulants après le chargement | Re-enable the dropdown menus after loading
    character_menu.config(state='normal')
    skin_menu.config(state='normal')
    color_menu.config(state='normal')
    file_type_menu.config(state='normal')


def on_selection_change(*args):
    # Fonction appelée lorsque les sélections changent | Called whenever the selections change
    global last_change_time
    # Mettre à jour le moment du dernier changement | Update the timestamp of the last change
    last_change_time = time.time()
    # Démarrer un thread pour attendre et charger les fichiers | Start a thread to wait and then load the files
    threading.Thread(target=delayed_load).start()


def delayed_load():
    global last_change_time
    # Attendre 0.5 secondes
    time.sleep(0.5)
    # Vérifier si suffisamment de temps s'est écoulé depuis le dernier changement | Check whether enough time has passed since the last change
    if time.time() - last_change_time >= 0.5:
        # Vérifie que toutes les sélections sont faites | Check that every selection has been made
        if selected_character.get() and selected_skin.get() and selected_color.get() and selected_file_type.get():
            # Charger les fichiers sur le thread principal | Load the files on the main thread
            root.after(0, load_files)


def find_steam_root():
    # Emplacement d'installation de Steam, via le registre puis les chemins usuels | Steam's install location, via the registry then the usual paths
    try:
        import winreg
        for root_key, sub in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                              (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
            try:
                with winreg.OpenKey(root_key, sub) as key:
                    for value in ("SteamPath", "InstallPath"):
                        try:
                            path = winreg.QueryValueEx(key, value)[0]
                            if path and os.path.isdir(path):
                                # Le registre renvoie souvent des slashs et des minuscules | The registry often returns forward slashes and lowercase
                                return os.path.normpath(path)
                        except FileNotFoundError:
                            continue
            except OSError:
                continue
    except ImportError:
        pass
    for fallback in (os.path.join(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'), 'Steam'),
                     os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'), 'Steam')):
        if os.path.isdir(fallback):
            return fallback
    return None


def find_steam_libraries():
    # Toutes les bibliothèques Steam déclarées dans libraryfolders.vdf | Every Steam library declared in libraryfolders.vdf
    steam_root = find_steam_root()
    if not steam_root:
        return []
    libraries = []
    seen = set()

    def add(path):
        # Dédoublonnage insensible à la casse et au séparateur | Deduplicate ignoring case and separator style
        normalized = os.path.normpath(path)
        if os.path.isdir(normalized) and normalized.lower() not in seen:
            seen.add(normalized.lower())
            libraries.append(normalized)

    add(os.path.join(steam_root, 'steamapps'))
    vdf = os.path.join(steam_root, 'steamapps', 'libraryfolders.vdf')
    try:
        with open(vdf, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except OSError:
        return libraries
    # Les entrées "path" contiennent des chemins échappés façon C:\\Games\\Steam | The "path" entries hold escaped paths such as C:\\Games\\Steam
    for match in re.finditer(r'"path"\s*"([^"]+)"', content):
        add(os.path.join(match.group(1).replace('\\\\', '\\'), 'steamapps'))
    return libraries


def find_game_paks_dir():
    # Cherche le dossier Paks du jeu dans toutes les bibliothèques Steam | Looks for the game's Paks folder across every Steam library
    for steamapps in find_steam_libraries():
        paks = os.path.join(steamapps, 'common', 'Rivals 2',
                            'Rivals2', 'Content', 'Paks')
        if os.path.isdir(paks):
            return paks
    return None


def update_game_data():
    # Extrait les données du jeu via FModel (semi-automatique) puis les importe | Extracts the game data via FModel (semi-automatic) then imports it
    global fmodel_path
    app_dir = os.path.dirname(os.path.abspath(__file__))
    importer_path = os.path.join(app_dir, "files_importer.py")
    if not os.path.exists(importer_path):
        messagebox.showerror(translations[current_language]['error_title'],
                             translations[current_language]['update_importer_missing'])
        return

    # 1. Trouver FModel.exe (mémorisé dans la config après le premier choix) | 1. Find FModel.exe (remembered in the config after the first pick)
    if not fmodel_path or not os.path.exists(fmodel_path):
        # setup.ps1 installe FModel dans le sous-dossier FModel de l'outil | setup.ps1 installs FModel into the tool's FModel subfolder
        bundled_fmodel = os.path.join(app_dir, "FModel", "FModel.exe")
        if os.path.exists(bundled_fmodel):
            fmodel_path = bundled_fmodel
            save_config()
    if not fmodel_path or not os.path.exists(fmodel_path):
        messagebox.showinfo(translations[current_language]['update_data'],
                            translations[current_language]['update_locate_fmodel'])
        chosen = filedialog.askopenfilename(
            title="FModel.exe", filetypes=[("FModel", "FModel.exe"), ("Executables", "*.exe")])
        if not chosen:
            return
        fmodel_path = chosen
        save_config()

    # 2. Aligner la config FModel : forcer OutputDirectory sur le dossier que | 2. Align FModel's config: pin OutputDirectory to the folder the importer
    #    l'importeur va lire, pour que Properties (.json) ET Raw Data (.uexp) | will read, so Properties (.json) AND Raw Data (.uexp) land together. This
    #    atterrissent ensemble. Réécrit à chaque fois : une OutputDirectory | is rewritten every launch: a stale OutputDirectory (e.g. the empty, OneDrive-
    #    périmée (ex. dossier Documents local vide, ignoré par FModel qui utilise | blind local Documents path that FModel ignores in favour of OneDrive\Documents)
    #    OneDrive\Documents) ne serait sinon jamais corrigée. | would otherwise never be corrected.
    appdata = os.environ.get('APPDATA')
    if appdata:
        try:
            if app_dir not in sys.path:
                sys.path.insert(0, app_dir)
            import files_importer as _fi
            output_dir = str(_fi.canonical_output())
        except Exception:
            output_dir = os.path.join(os.path.expanduser(
                "~"), "Documents", "FModel", "Output")
        fmodel_cfg = os.path.join(appdata, "FModel", "AppSettings.json")
        paks = find_game_paks_dir()
        try:
            settings = {}
            if os.path.exists(fmodel_cfg):
                with open(fmodel_cfg, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            if not isinstance(settings, dict):
                settings = {}
            if paks:
                settings['GameDirectory'] = paks
            settings['OutputDirectory'] = output_dir
            os.makedirs(os.path.dirname(fmodel_cfg), exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)
            with open(fmodel_cfg, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
        except (OSError, ValueError):
            pass  # FModel se configurera manuellement | FModel will fall back to manual config

    # 3. Lancer FModel et afficher les instructions (l'utilisateur exporte puis valide) | 3. Launch FModel and show the instructions (the user exports, then confirms)
    try:
        subprocess.Popen([fmodel_path])
    except OSError as e:
        messagebox.showerror(
            translations[current_language]['error_title'], str(e))
        return
    messagebox.showinfo(translations[current_language]['update_data'],
                        translations[current_language]['update_instructions'])

    # 4. Importer les fichiers exportés | 4. Import the exported files
    try:
        root.config(cursor="wait")
        root.update()
        import importlib
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)
        import files_importer
        importlib.reload(files_importer)
        # Les logs de l'importeur suivent la langue de l'appli | The importer's logs follow the app's language
        files_importer.LANG = current_language
        counts = files_importer.run_import()
    except Exception as e:
        messagebox.showerror(
            translations[current_language]['error_title'], str(e))
        return
    finally:
        root.config(cursor="")
    if counts is None:
        messagebox.showerror(translations[current_language]['error_title'],
                             translations[current_language]['update_no_exports'])
        return
    messagebox.showinfo(translations[current_language]['update_data'],
                        translations[current_language]['update_done'].format(
                            counts['characters'], counts['platforms'],
                            counts['shared'], counts['portraits']))


PAK_PATH_RE = re.compile(rb"[0-9A-Za-z_./\-]{5,}")


def parse_pak_overrides(pak_path):
    """
    Lit l'index d'un .pak (non chiffré) et renvoie la liste des remplacements
    sous forme (personnage, skin, palette, type). L'index stocke les chemins
    en ASCII : on les extrait directement, ce qui reste valable quelle que
    soit la version de pak.

    Reads an (unencrypted) .pak index and returns its overrides as
    (character, skin, palette, type). The index stores paths as ASCII, so
    they are extracted directly, which stays valid across pak versions.
    """
    try:
        with open(pak_path, 'rb') as f:
            data = f.read()
    except OSError:
        return []

    mount = ""
    relatives = []
    for match in PAK_PATH_RE.finditer(data):
        text = match.group().decode('ascii', 'ignore')
        if text.startswith('../'):
            mount = text
        elif text.endswith(('.uexp', '.uasset', '.ubulk')):
            relatives.append(text)

    mount = mount.replace('../', '')
    results = []
    seen = set()
    for rel in relatives:
        full = (mount.rstrip('/') + '/' + rel) if mount else rel
        parts = [p for p in full.split('/') if p]
        name = parts[-1]
        if name.startswith('PE_'):
            kind = translations[current_language]['file_type_energy']
        elif name.startswith('PS_'):
            kind = translations[current_language]['file_type_skin']
        elif name.startswith('T_') and '_CSP' in name:
            kind = translations[current_language]['file_type_portrait']
        else:
            kind = name.split('_')[0]

        character = skin = palette = '?'
        if 'Characters' in parts:
            i = parts.index('Characters')
            if i + 1 < len(parts):
                character = parts[i + 1]
            if 'Skins' in parts:
                j = parts.index('Skins')
                if j + 1 < len(parts):
                    skin = parts[j + 1]
            elif i + 2 < len(parts) - 1:
                skin = parts[i + 2]
            if 'Palettes' in parts:
                k = parts.index('Palettes')
                if k + 1 < len(parts):
                    palette = parts[k + 1]
            else:
                palette = name.rsplit('_', 1)[-1].rsplit('.', 1)[0]
        elif 'Platforms' in parts:
            i = parts.index('Platforms')
            character = 'Platforms'
            if i + 1 < len(parts):
                skin = parts[i + 1]
            palette = name.rsplit('_', 1)[-1].rsplit('.', 1)[0]

        key = (character, skin, palette, kind)
        if key not in seen:
            seen.add(key)
            results.append(key)
    return results


def is_game_running():
    # Le jeu verrouille les .pak tant qu'il tourne | The game locks the .pak files while it is running
    try:
        output = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Rivals2-Win64-Shipping.exe'],
                                capture_output=True, text=True, timeout=10,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        return 'Rivals2-Win64-Shipping' in output.stdout
    except (OSError, subprocess.SubprocessError):
        return False


class _SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [("hwnd", wintypes.HWND),
                ("wFunc", wintypes.UINT),
                ("pFrom", wintypes.LPCWSTR),
                ("pTo", wintypes.LPCWSTR),
                ("fFlags", ctypes.c_uint16),
                ("fAnyOperationsAborted", wintypes.BOOL),
                ("hNameMappings", ctypes.c_void_p),
                ("lpszProgressTitle", wintypes.LPCWSTR)]


def send_to_recycle_bin(paths):
    # Supprime via la corbeille : l'utilisateur peut toujours restaurer | Deletes via the Recycle Bin so the user can always restore
    if not paths:
        return True
    buffer = '\0'.join(paths) + '\0\0'
    op = _SHFILEOPSTRUCTW(None, 3, buffer, None, 0x0040 | 0x0010 | 0x0004,
                          False, None, None)
    return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op)) == 0


def list_mod_paks():
    if not mods_folder_path or not os.path.isdir(mods_folder_path):
        return []
    paks = []
    for dirpath, dirnames, filenames in os.walk(mods_folder_path):
        for name in filenames:
            if name.lower().endswith('.pak'):
                paks.append(os.path.join(dirpath, name))
    return sorted(paks)


def pak_mount_point(pak_path):
    # Renvoie le point de montage brut du pak (ex: ../../../Rivals2/Content/...) | Returns the pak's raw mount point (e.g. ../../../Rivals2/Content/...)
    try:
        with open(pak_path, 'rb') as f:
            data = f.read()
    except OSError:
        return ""
    for match in PAK_PATH_RE.finditer(data):
        text = match.group().decode('ascii', 'ignore')
        if text.startswith('../'):
            return text
    return ""


def describe_pak_file(full_path):
    # (personnage, skin, palette, type) pour un chemin complet dans le pak | (character, skin, palette, type) for a full path inside the pak
    parts = [p for p in full_path.replace('\\', '/').split('/') if p]
    name = parts[-1]
    if name.startswith('PE_'):
        kind = translations[current_language]['file_type_energy']
    elif name.startswith('PS_'):
        kind = translations[current_language]['file_type_skin']
    elif name.startswith('T_') and '_CSP' in name:
        kind = translations[current_language]['file_type_portrait']
    else:
        kind = name.split('_')[0]
    character = skin = palette = '?'
    if 'Characters' in parts:
        i = parts.index('Characters')
        if i + 1 < len(parts):
            character = parts[i + 1]
        if 'Skins' in parts:
            j = parts.index('Skins')
            if j + 1 < len(parts):
                skin = parts[j + 1]
        elif i + 2 < len(parts) - 1:
            skin = parts[i + 2]
        if 'Palettes' in parts:
            k = parts.index('Palettes')
            if k + 1 < len(parts):
                palette = parts[k + 1]
        else:
            palette = name.rsplit('_', 1)[-1].rsplit('.', 1)[0]
    elif 'Platforms' in parts:
        character = 'Platforms'
        i = parts.index('Platforms')
        if i + 1 < len(parts):
            skin = parts[i + 1]
        palette = name.rsplit('_', 1)[-1].rsplit('.', 1)[0]
    return character, skin, palette, kind


def unrealpak_exe_path():
    return os.path.join(os.path.dirname(unrealpak_script_path), "UnrealPak.exe")


def extract_pak(pak_path, dest_dir):
    # Extrait un pak ; les chemins produits sont relatifs au point de montage | Extracts a pak; the resulting paths are relative to the mount point
    os.makedirs(dest_dir, exist_ok=True)
    subprocess.run([unrealpak_exe_path(), pak_path, "-extract", dest_dir],
                   check=True, capture_output=True, text=True,
                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def build_pak_from_staging(staging_dir, out_pak):
    # Reconstruit un pak à partir d'un dossier de staging complet | Rebuilds a pak from a complete staging folder
    upack_dir = os.path.dirname(unrealpak_script_path)
    filelist = os.path.join(upack_dir, "filelist.txt")
    with open(filelist, 'w') as f:
        f.write(f'"{staging_dir}\\*.*" "..\\..\\..\\*.*"\n')
    subprocess.run([unrealpak_exe_path(), out_pak, f"-create={filelist}", "-compress"],
                   check=True, capture_output=True, text=True, cwd=upack_dir,
                   creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))


def staging_dir_for_pak(pak_path):
    # Dossier Upack/<perso>_P correspondant à <perso>_P.pak | The Upack/<character>_P folder matching <character>_P.pak
    stem = os.path.splitext(os.path.basename(pak_path))[0]
    return os.path.join(os.path.dirname(unrealpak_script_path), stem)


def prune_staging_folder(pak_path, targets):
    """
    Retire aussi les fichiers correspondants du dossier de staging.
    Sans cela, "Remplacer les couleurs" reconstruit le pak à partir du
    staging (qui s'accumule) et ressuscite les remplacements supprimés.

    Also removes the matching files from the staging folder. Without this,
    "Replace Colors" rebuilds the pak from the staging folder (which
    accumulates) and resurrects overrides that were removed.
    """
    staging = staging_dir_for_pak(pak_path)
    if not os.path.isdir(staging):
        return 0
    removed = 0
    for dirpath, dirnames, filenames in os.walk(staging):
        for name in list(filenames):
            full = os.path.join(dirpath, name).replace('\\', '/')
            if describe_pak_file(full) in targets:
                try:
                    os.remove(os.path.join(dirpath, name))
                    removed += 1
                except OSError:
                    pass
    # Nettoyer les dossiers devenus vides | Clean up folders left empty
    for dirpath, dirnames, filenames in os.walk(staging, topdown=False):
        try:
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
        except OSError:
            pass
    return removed


def remove_overrides_from_pak(pak_path, targets):
    """
    Retire uniquement les remplacements listés dans `targets`
    (personnage, skin, palette, type) et reconstruit le pak.
    Le dossier de staging est nettoyé en même temps pour que la
    suppression survive au prochain export.
    Renvoie 'rebuilt', 'deleted' (plus rien dedans) ou lève une exception.

    Removes only the overrides listed in `targets` (character, skin,
    palette, type) and rebuilds the pak. The staging folder is pruned at
    the same time so the removal survives the next export.
    Returns 'rebuilt', 'deleted' (nothing left inside) or raises.
    """
    import tempfile
    mount = pak_mount_point(pak_path)
    prefix = mount.replace('../', '').strip('/')
    work = tempfile.mkdtemp(prefix="colorswap_pak_")
    try:
        extracted = os.path.join(work, "extracted")
        extract_pak(pak_path, extracted)

        # Reconstituer l'arborescence complète (le montage est retiré à l'extraction) | Rebuild the full tree (extraction strips the mount point)
        staging = os.path.join(
            work, os.path.splitext(os.path.basename(pak_path))[0])
        root = os.path.join(staging, *prefix.split('/')) if prefix else staging
        kept = 0
        for dirpath, dirnames, filenames in os.walk(extracted):
            for name in filenames:
                rel = os.path.relpath(os.path.join(dirpath, name), extracted)
                full = (prefix + '/' + rel.replace('\\', '/')).strip('/')
                if describe_pak_file(full) in targets:
                    continue  # celui-ci est retiré | this one is being removed
                dest = os.path.join(root, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(os.path.join(dirpath, name), dest)
                kept += 1

        if kept == 0:
            if not send_to_recycle_bin([pak_path]):
                raise OSError(pak_path)
            # Plus rien à exporter : jeter tout le dossier de staging | Nothing left to export: drop the whole staging folder
            shutil.rmtree(staging_dir_for_pak(pak_path), ignore_errors=True)
            return 'deleted'

        rebuilt = os.path.join(work, "rebuilt.pak")
        build_pak_from_staging(staging, rebuilt)
        if not os.path.exists(rebuilt):
            raise OSError(rebuilt)
        shutil.copy2(rebuilt, pak_path)
        # Garder le staging aligné, sinon le prochain export ramène ces couleurs | Keep staging aligned, otherwise the next export brings these colors back
        prune_staging_folder(pak_path, targets)
        return 'rebuilt'
    finally:
        shutil.rmtree(work, ignore_errors=True)


def linear_to_srgb_bytes(r, g, b):
    # Inverse de hex_to_linear_rgb : linéaire -> octets sRGB | Inverse of hex_to_linear_rgb: linear -> sRGB bytes
    def encode(value):
        value = max(0.0, min(1.0, value))
        if value <= 0.0031308:
            srgb = value * 12.92
        else:
            srgb = 1.055 * (value ** (1 / 2.4)) - 0.055
        return max(0, min(255, int(round(srgb * 255))))
    return encode(r), encode(g), encode(b)


def read_override_colors(base_json_path, base_uexp_path, modified_uexp_path):
    """
    Compare le uexp d'origine et celui installé dans le pak.
    Renvoie [(clé, rgb_avant, rgb_après), ...].

    Compares the original uexp with the one installed in the pak.
    Returns [(key, rgb_before, rgb_after), ...].
    """
    with open(base_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(base_uexp_path, 'rb') as f:
        base_hex = f.read().hex().upper()
    with open(modified_uexp_path, 'rb') as f:
        mod_hex = f.read().hex().upper()

    results = []
    position = 0
    for entry in data:
        if "Properties" not in entry or "CustomColorSlotDefinitions" not in entry["Properties"]:
            continue
        for color in entry["Properties"]["CustomColorSlotDefinitions"]:
            value = color["Value"]
            original = (invert_hex(precise_float_to_hex(value["R"]))
                        + invert_hex(precise_float_to_hex(value["G"]))
                        + invert_hex(precise_float_to_hex(value["B"])))
            found = base_hex.find(original, position)
            if found == -1:
                continue
            position = found + len(original)
            chunk = mod_hex[found:found + len(original)]
            if len(chunk) < len(original):
                continue
            floats = []
            for i in range(3):
                piece = chunk[i * 8:(i + 1) * 8]
                floats.append(struct.unpack(
                    '>f', bytes.fromhex(invert_hex(piece)))[0])
            before_hex = rgb_hex_from_json(value.get("Hex", ""))
            before = tuple(int(before_hex[j:j+2], 16) for j in (0, 2, 4)) \
                if before_hex else linear_to_srgb_bytes(value["R"], value["G"], value["B"])
            after = linear_to_srgb_bytes(*floats)
            results.append((color["Key"], before, after))
    return results


def find_base_files(character, skin, palette, prefix):
    # Retrouve le json/uexp d'origine correspondant à un remplacement | Finds the original json/uexp matching an override
    folder = os.path.join(BASE_DIR, character, 'Skins',
                          skin, 'Data', 'Palettes', palette)
    if not os.path.isdir(folder):
        alt = os.path.join(BASE_DIR, character, skin)  # Shared
        folder = alt if os.path.isdir(alt) else folder
    if not os.path.isdir(folder):
        return None, None
    for name in os.listdir(folder):
        if name.startswith(prefix) and name.endswith('.uexp'):
            uexp = os.path.join(folder, name)
            base_json = uexp[:-len('.uexp')] + '.json'
            if os.path.exists(base_json):
                return base_json, uexp
    return None, None


def pak_full_paths(pak_path):
    # Chemins complets (montage + entrées) contenus dans un pak | Full paths (mount + entries) held inside a pak
    try:
        with open(pak_path, 'rb') as f:
            data = f.read()
    except OSError:
        return []
    mount = ""
    relatives = []
    for match in PAK_PATH_RE.finditer(data):
        text = match.group().decode('ascii', 'ignore')
        if text.startswith('../'):
            mount = text
        elif text.endswith(('.uexp', '.uasset', '.ubulk')):
            relatives.append(text)
    mount = mount.replace('../', '').strip('/')
    if not mount:
        return relatives
    return [(mount + '/' + rel).replace('//', '/') for rel in relatives]


def current_file_prefix():
    # 'PE_' ou 'PS_' selon le type de fichier sélectionné | 'PE_' or 'PS_' depending on the selected file type
    return 'PE_' if file_type_codes.get(selected_file_type.get()) == 'PE' else 'PS_'


def find_installed_override(character, skin, palette, prefix):
    """
    Cherche un .pak installé qui remplace exactement cette combinaison.
    Renvoie (chemin_du_pak, nom_du_fichier) ou (None, None).

    Looks for an installed .pak overriding exactly this combination.
    Returns (pak_path, file_name) or (None, None).
    """
    if not mods_folder_path or not os.path.isdir(mods_folder_path):
        return None, None
    for pak in list_mod_paks():
        for full in pak_full_paths(pak):
            name = full.rsplit('/', 1)[-1]
            if not name.startswith(prefix) or not name.endswith('.uexp'):
                continue
            if describe_pak_file(full)[:3] == (character, skin, palette):
                return pak, name
    return None, None


def load_installed_mod_values():
    # Remplit les champs avec les couleurs du mod déjà installé | Fills the fields with the colors of the already-installed mod
    import tempfile
    if json_data is None or not uexp_file_path:
        return
    character = selected_character.get()
    skin = selected_skin.get()
    palette = selected_color.get()
    pak, name = find_installed_override(
        character, skin, palette, current_file_prefix())
    if not pak:
        messagebox.showinfo(translations[current_language]['load_mod_values'],
                            translations[current_language]['mod_values_none'])
        return

    base_json = uexp_file_path.replace('.uexp', '.json')
    work = tempfile.mkdtemp(prefix="colorswap_load_")
    try:
        root.config(cursor="wait")
        root.update()
        extract_pak(pak, work)
        modified = None
        for dirpath, dirnames, filenames in os.walk(work):
            if name in filenames:
                modified = os.path.join(dirpath, name)
                break
        if not modified:
            messagebox.showerror(translations[current_language]['error_title'],
                                 translations[current_language]['mod_values_failed'])
            return
        colors = read_override_colors(base_json, uexp_file_path, modified)
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        messagebox.showerror(
            translations[current_language]['error_title'], str(e))
        return
    finally:
        root.config(cursor="")
        shutil.rmtree(work, ignore_errors=True)

    assignment = {key: after for key, _before,
                  after in colors if key in color_entries}
    if not assignment:
        messagebox.showinfo(translations[current_language]['load_mod_values'],
                            translations[current_language]['mod_values_failed'])
        return
    apply_color_assignment(assignment)
    messagebox.showinfo(translations[current_language]['success_title'],
                        translations[current_language]['mod_values_loaded'].format(
                            len(assignment), os.path.basename(pak)))


def update_mod_button_state():
    # Affiche le bouton seulement si la sélection est déjà moddée | Show the button only when the current selection is already modded
    try:
        pak, _name = (None, None)
        if json_data is not None and selected_color.get():
            pak, _name = find_installed_override(selected_character.get(),
                                                 selected_skin.get(),
                                                 selected_color.get(),
                                                 current_file_prefix())
        if pak:
            load_mod_button.grid()
        else:
            load_mod_button.grid_remove()
    except tk.TclError:
        pass


def show_installed_portrait_preview(pak_path, character, skin, palette, parent):
    """
    Compare le portrait d'origine (lu dans le pak du jeu) avec celui
    installé par le mod.

    Compares the original portrait (read from the game pak) with the one
    installed by the mod.
    """
    import tempfile
    game_pak = get_game_pak()
    work = tempfile.mkdtemp(prefix="colorswap_csp_")
    try:
        extract_pak(pak_path, work)
        modified_path = None
        for dirpath, dirnames, filenames in os.walk(work):
            for name in filenames:
                if name.startswith('T_') and name.endswith('_CSP.uexp'):
                    modified_path = os.path.join(dirpath, name)
                    break
        if not modified_path:
            messagebox.showinfo(translations[current_language]['preview'],
                                translations[current_language]['preview_unavailable'],
                                parent=parent)
            return
        with open(modified_path, 'rb') as f:
            after_image = portraits_module.decode_csp(f.read())
        before_image = None
        if game_pak is not None:
            try:
                before_image = portraits_module.decode_csp(
                    game_pak.read_file(os.path.basename(modified_path)))
            except (FileNotFoundError, RuntimeError, OSError):
                before_image = None
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        messagebox.showerror(
            translations[current_language]['error_title'], str(e), parent=parent)
        return
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if after_image is None:
        messagebox.showinfo(translations[current_language]['preview'],
                            translations[current_language]['preview_unavailable'],
                            parent=parent)
        return

    window = tk.Toplevel(parent)
    window.title(translations[current_language]['preview_title'].format(
        character, skin, palette))
    window.configure(bg="#f2f2f2")
    tk.Label(window, text=translations[current_language]['file_type_portrait'],
             font=("Arial", 9), bg="#f2f2f2").pack(pady=(8, 2))
    row = tk.Frame(window, bg="#f2f2f2")
    row.pack(padx=10, pady=5)
    for title_key, img in (('override_before', before_image),
                           ('override_after', after_image)):
        if img is None:
            continue
        column = tk.Frame(row, bg="#f2f2f2")
        column.pack(side='left', padx=8)
        tk.Label(column, text=translations[current_language][title_key],
                 font=("Arial", 10, "bold"), bg="#f2f2f2").pack()
        shown = img.copy()
        shown.thumbnail((360, 360), Image.LANCZOS)
        photo = ImageTk.PhotoImage(shown)
        label = tk.Label(column, image=photo, bg="#f2f2f2")
        label.image = photo
        label.pack()


def show_override_preview(pak_path, character, skin, palette, kind, parent):
    # Aperçu avant/après d'un remplacement installé | Before/after preview of an installed override
    import tempfile
    if kind == translations[current_language]['file_type_portrait']:
        show_installed_portrait_preview(
            pak_path, character, skin, palette, parent)
        return
    is_energy = kind == translations[current_language]['file_type_energy']
    prefix = 'PE_' if is_energy else 'PS_'
    base_json, base_uexp = find_base_files(character, skin, palette, prefix)
    if not base_json:
        messagebox.showinfo(translations[current_language]['preview'],
                            translations[current_language]['preview_unavailable'],
                            parent=parent)
        return

    work = tempfile.mkdtemp(prefix="colorswap_prev_")
    try:
        extract_pak(pak_path, work)
        modified = None
        for dirpath, dirnames, filenames in os.walk(work):
            for name in filenames:
                if name == os.path.basename(base_uexp):
                    modified = os.path.join(dirpath, name)
                    break
        if not modified:
            messagebox.showinfo(translations[current_language]['preview'],
                                translations[current_language]['preview_unavailable'],
                                parent=parent)
            return
        colors = read_override_colors(base_json, base_uexp, modified)

        portrait = None
        folder = os.path.dirname(base_uexp)
        for name in os.listdir(folder):
            if name.endswith('_CSP.png'):
                portrait = Image.open(os.path.join(
                    folder, name)).convert('RGBA')
                break

        if is_energy:
            def ramp(index):
                stops = []
                for key, before, after in colors:
                    if key.startswith('Element'):
                        try:
                            stops.append(
                                (int(key[len('Element'):]), (before, after)[index]))
                        except ValueError:
                            pass
                stops.sort()
                return [rgb for _, rgb in stops]
            before_img = render_energy_preview(portrait, ramp(0))
            after_img = render_energy_preview(portrait, ramp(1))
        else:
            if portrait is None:
                messagebox.showinfo(translations[current_language]['preview'],
                                    translations[current_language]['preview_unavailable'],
                                    parent=parent)
                return
            before_img = portrait
            after_img = recolor_preview_image(
                portrait, [(b, a) for _key, b, a in colors])
    except (OSError, subprocess.SubprocessError, ValueError) as e:
        messagebox.showerror(
            translations[current_language]['error_title'], str(e), parent=parent)
        return
    finally:
        shutil.rmtree(work, ignore_errors=True)

    window = tk.Toplevel(parent)
    window.title(translations[current_language]['preview_title'].format(
        character, skin, palette))
    window.configure(bg="#f2f2f2")
    # Tolérance de 2 : la conversion sRGB -> linéaire -> sRGB peut décaler | Tolerance of 2: the sRGB -> linear -> sRGB round trip can shift
    # une composante de 1 sans que la couleur ait réellement été modifiée | a channel by 1 without the color actually having been edited
    changed = sum(1 for _k, b, a in colors
                  if max(abs(b[i] - a[i]) for i in range(3)) > 2)
    tk.Label(window, text=translations[current_language]['override_changed'].format(
        changed, len(colors)), font=("Arial", 9), bg="#f2f2f2").pack(pady=(8, 2))
    row = tk.Frame(window, bg="#f2f2f2")
    row.pack(padx=10, pady=5)
    for title_key, img in (('override_before', before_img), ('override_after', after_img)):
        column = tk.Frame(row, bg="#f2f2f2")
        column.pack(side='left', padx=8)
        tk.Label(column, text=translations[current_language][title_key],
                 font=("Arial", 10, "bold"), bg="#f2f2f2").pack()
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(column, image=photo, bg="#f2f2f2")
        label.image = photo
        label.pack()


overrides_window = None


def show_overrides():
    # Fenêtre listant les .pak installés et ce qu'ils remplacent | Window listing the installed .pak files and what they override
    global overrides_window
    if not mods_folder_path or not os.path.isdir(mods_folder_path):
        messagebox.showerror(translations[current_language]['error_title'],
                             translations[current_language]['overrides_no_folder'])
        return
    if overrides_window is not None and overrides_window.winfo_exists():
        overrides_window.destroy()
    overrides_window = tk.Toplevel(root)
    overrides_window.title(translations[current_language]['overrides_title'])
    overrides_window.geometry("720x420")
    overrides_window.configure(bg="#f2f2f2")

    status = tk.Label(overrides_window, font=("Arial", 9),
                      bg="#f2f2f2", fg="#444444", anchor="w", justify="left")
    status.pack(fill="x", padx=10, pady=(10, 4))

    columns = ('pak', 'character', 'skin', 'palette', 'type')
    tree = ttk.Treeview(overrides_window, columns=columns, show='headings')
    for col, width in zip(columns, (150, 110, 120, 110, 120)):
        tree.heading(col, text=translations[current_language]['overrides_col_' + col])
        tree.column(col, width=width, anchor='w')
    scroll = ttk.Scrollbar(overrides_window, orient='vertical',
                           command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side='top', fill='both', expand=True, padx=(10, 0), pady=4)
    scroll.place(relx=1.0, rely=0.0, anchor='ne')

    def refresh():
        tree.delete(*tree.get_children())
        paks = list_mod_paks()
        total = 0
        for pak in paks:
            label = os.path.relpath(pak, mods_folder_path)
            entries = parse_pak_overrides(pak)
            if not entries:
                tree.insert('', 'end', values=(
                    label, '?', '?', '?', ''), tags=(pak,))
                total += 1
                continue
            for character, skin, palette, kind in entries:
                tree.insert('', 'end', values=(
                    label, character, skin, palette, kind), tags=(pak,))
                total += 1
        running = is_game_running()
        msg = translations[current_language]['overrides_status'].format(
            len(paks), total)
        if running:
            msg += "\n" + translations[current_language]['overrides_game_running']
        status.config(text=msg, fg="#B00020" if running else "#444444")

    def preview_selected():
        selection = tree.selection()
        if not selection:
            return
        item = selection[0]
        pak = tree.item(item, 'tags')[0]
        values = tree.item(item, 'values')
        if values[1] == '?':
            messagebox.showinfo(translations[current_language]['preview'],
                                translations[current_language]['preview_unavailable'],
                                parent=overrides_window)
            return
        try:
            overrides_window.config(cursor="wait")
            overrides_window.update()
            show_override_preview(pak, values[1], values[2], values[3],
                                  values[4], overrides_window)
        finally:
            overrides_window.config(cursor="")

    def remove_selected():
        # Retire seulement les remplacements sélectionnés, pas tout le pak | Removes only the selected overrides, not the whole pak
        selection = tree.selection()
        if not selection:
            return
        by_pak = {}
        labels = []
        for item in selection:
            pak = tree.item(item, 'tags')[0]
            values = tree.item(item, 'values')
            by_pak.setdefault(pak, set()).add(
                (values[1], values[2], values[3], values[4]))
            labels.append(f"{values[1]} / {values[2]} / {values[3]}  [{values[4]}]")
        if not messagebox.askyesno(translations[current_language]['overrides_remove_selected'],
                                   translations[current_language]['overrides_confirm'].format(
                                       len(labels), "\n".join(labels)),
                                   parent=overrides_window):
            return
        if is_game_running():
            messagebox.showerror(translations[current_language]['error_title'],
                                 translations[current_language]['overrides_close_game'],
                                 parent=overrides_window)
            return
        rebuilt = deleted = 0
        try:
            overrides_window.config(cursor="wait")
            overrides_window.update()
            for pak, targets in by_pak.items():
                outcome = remove_overrides_from_pak(pak, targets)
                if outcome == 'deleted':
                    deleted += 1
                else:
                    rebuilt += 1
        except (OSError, subprocess.SubprocessError) as e:
            messagebox.showerror(translations[current_language]['error_title'],
                                 translations[current_language]['overrides_remove_failed']
                                 + f"\n\n{e}", parent=overrides_window)
            refresh()
            return
        finally:
            overrides_window.config(cursor="")
        messagebox.showinfo(translations[current_language]['success_title'],
                            translations[current_language]['overrides_partial_removed'].format(
                                len(labels), rebuilt, deleted),
                            parent=overrides_window)
        refresh()

    def remove_all():
        paks = list_mod_paks()
        if not paks:
            return
        if not messagebox.askyesno(translations[current_language]['overrides_remove_all'],
                                   translations[current_language]['overrides_confirm_all'].format(
                                       len(paks)),
                                   parent=overrides_window):
            return
        do_removal(paks)

    def do_removal(paks):
        if is_game_running():
            messagebox.showerror(translations[current_language]['error_title'],
                                 translations[current_language]['overrides_close_game'],
                                 parent=overrides_window)
            return
        if send_to_recycle_bin(paks):
            # Vider aussi le staging, sinon un export le ferait revenir | Also clear staging, otherwise an export would bring it back
            for pak in paks:
                shutil.rmtree(staging_dir_for_pak(pak), ignore_errors=True)
            messagebox.showinfo(translations[current_language]['success_title'],
                                translations[current_language]['overrides_removed'].format(
                                    len(paks)),
                                parent=overrides_window)
        else:
            messagebox.showerror(translations[current_language]['error_title'],
                                 translations[current_language]['overrides_remove_failed'],
                                 parent=overrides_window)
        refresh()

    button_bar = tk.Frame(overrides_window, bg="#f2f2f2")
    button_bar.pack(fill="x", padx=10, pady=8)
    tk.Button(button_bar, text=translations[current_language]['overrides_refresh'],
              command=refresh, font=("Arial", 9)).pack(side='left', padx=(0, 5))
    tk.Button(button_bar, text=translations[current_language]['overrides_open_folder'],
              command=lambda: os.startfile(mods_folder_path),
              font=("Arial", 9)).pack(side='left', padx=5)
    tk.Button(button_bar, text=translations[current_language]['overrides_preview'],
              command=preview_selected, font=("Arial", 9),
              bg="#9C27B0", fg="white").pack(side='left', padx=5)
    tk.Button(button_bar, text=translations[current_language]['overrides_remove_selected'],
              command=remove_selected, font=("Arial", 9),
              bg="#FF9800", fg="white").pack(side='right', padx=5)
    tk.Button(button_bar, text=translations[current_language]['overrides_remove_all'],
              command=remove_all, font=("Arial", 9),
              bg="#F44336", fg="white").pack(side='right', padx=5)

    refresh()


def on_closing():
    # Fonction appelée lors de la fermeture de l'application | Called when the application is closing
    save_config()
    root.destroy()


# Créer la fenêtre Tkinter | Create the Tkinter window
root = tk.Tk()
root.title(translations[current_language]['title'])
root.geometry("900x600")
root.configure(bg="#f2f2f2")

# Définir l'icône de la fenêtre | Set the window icon
# Chemin vers votre icône .png | Path to your .png icon
icon_path = os.path.join("icons", "app_icon.png")

if os.path.exists(icon_path):
    icon_image = tk.PhotoImage(file=icon_path)
    root.iconphoto(False, icon_image)
else:
    print("Icône de l'application non trouvée.")

# Variables pour les menus déroulants (après création de root) | Variables for the dropdown menus (after root is created)
selected_character = tk.StringVar()
selected_skin = tk.StringVar()
selected_color = tk.StringVar()
selected_file_type = tk.StringVar()

# Variable pour stocker le moment du dernier changement | Variable holding the timestamp of the last change
last_change_time = 0

# Charger la configuration au démarrage | Load the configuration at startup
load_config()

# Charger les icônes et les personnages | Load the icons and the characters
characters = load_character_icons()

# Frame d'en-tête pour les menus et la configuration | Header frame for the menus and configuration
header_frame = tk.Frame(root, bg="#f2f2f2")
header_frame.pack(pady=10)

# Sélecteur de langue | Language selector
selected_language = tk.StringVar()
language_options = {'Français': 'fr', 'English': 'en'}
selected_language.set(next(
    key for key, value in language_options.items() if value == current_language))
language_menu = tk.OptionMenu(
    header_frame, selected_language, *language_options.keys())
language_menu.grid(row=0, column=0, padx=5, pady=5, sticky="w")
selected_language.trace_add('write', change_language)

# Label pour afficher l'icône sélectionnée | Label showing the selected icon
selected_character_icon_label = tk.Label(header_frame, bg="#f2f2f2")
selected_character_icon_label.grid(row=0, column=1, padx=2, pady=5)

# Labels pour les menus déroulants | Labels for the dropdown menus
character_label = tk.Label(header_frame, font=("Arial", 10))
character_label.grid(row=0, column=2, padx=2, pady=5, sticky="e")

skin_label = tk.Label(header_frame, font=("Arial", 10))
skin_label.grid(row=0, column=4, padx=2, pady=5, sticky="e")

color_label = tk.Label(header_frame, font=("Arial", 10))
color_label.grid(row=0, column=6, padx=2, pady=5, sticky="e")

file_type_label = tk.Label(header_frame, font=("Arial", 10))
file_type_label.grid(row=0, column=8, padx=2, pady=5, sticky="e")

# Menu déroulant pour le personnage avec icônes | Dropdown menu for the character, with icons
character_menu = create_character_menu(characters)
selected_character.trace_add("write", update_selected_character_icon)

# Menu pour le skin | Menu for the skin
skin_menu = tk.OptionMenu(header_frame, selected_skin, '')
skin_menu.grid(row=0, column=5, padx=2, pady=5, sticky="w")
selected_skin.trace_add('write', update_color_menu)

# Menus déroulants pour la couleur et le type de fichier | Dropdown menus for the color and the file type
color_menu = tk.OptionMenu(header_frame, selected_color, '')
color_menu.grid(row=0, column=7, padx=2, pady=5, sticky="w")
selected_color.trace_add('write', update_file_type_menu)

file_type_menu = tk.OptionMenu(header_frame, selected_file_type, '')
file_type_menu.grid(row=0, column=9, padx=2, pady=5, sticky="w")

# Sélectionner le personnage initial (après création de tous les menus) | Select the initial character (after every menu has been created)
selected_character.set(characters[0])

# Lier les variables de sélection à la fonction de changement | Bind the selection variables to the change handler
selected_character.trace_add('write', on_selection_change)
selected_skin.trace_add('write', on_selection_change)
selected_color.trace_add('write', on_selection_change)
selected_file_type.trace_add('write', on_selection_change)

# Mettre à jour l'icône du personnage initial | Update the initial character's icon
update_selected_character_icon()

# Appeler la fonction une première fois pour initialiser le menu des skins | Call the function once to initialize the skin menu
update_skin_menu()

# Bouton unique de configuration pour UnrealPak et Mods | Single configuration button for UnrealPak and Mods
config_button = tk.Button(header_frame, command=configure_script_and_mods_folder,
                          font=("Arial", 10), bg="#FFC107", fg="black")
config_button2 = tk.Button(header_frame, command=configure_FModel_export_folder,
                          font=("Arial", 10), bg = "#BBBBBB", fg="black")
config_button.grid(row=1, column=0, columnspan=10, pady=7)
config_button2.grid(row=1, column=5, columnspan=10, pady=7)

# Boutons pour sauvegarder et charger des presets | Buttons to save and load presets
save_preset_button = tk.Button(header_frame, command=save_preset,
                               font=("Arial", 9), bg="#2196F3", fg="white")
save_preset_button.grid(row=2, column=0, padx=(5, 5), pady=5, sticky="w")

load_preset_button = tk.Button(header_frame, command=load_preset,
                               font=("Arial", 9), bg="#2196F3", fg="white")
load_preset_button.grid(row=2, column=1, padx=(5, 5), pady=5, sticky="w")

update_data_button = tk.Button(header_frame, command=update_game_data,
                               font=("Arial", 9), bg="#607D8B", fg="white")
update_data_button.grid(row=2, column=2, columnspan=3,
                        padx=(5, 5), pady=5, sticky="w")

overrides_button = tk.Button(header_frame, command=show_overrides,
                             font=("Arial", 9), bg="#795548", fg="white")
overrides_button.grid(row=2, column=5, columnspan=3,
                      padx=(5, 5), pady=5, sticky="w")

# Frame pour afficher les couleurs | Frame displaying the colors
color_frame = tk.Frame(root, bg="#ffffff", borderwidth=1, relief="solid")
color_frame.pack(fill="both", expand=True, padx=10, pady=5)

# Frame pour le bouton d'action | Frame for the action button
action_frame = tk.Frame(root, bg="#f2f2f2")
action_frame.pack(pady=5)

replace_button = tk.Button(action_frame, command=replace_colors_in_uexp,
                           font=("Arial", 10), bg="#4CAF50", fg="white", state='disabled')
replace_button.grid(row=0, column=0, padx=5, pady=2)

preview_button = tk.Button(action_frame, command=show_preview,
                           font=("Arial", 10), bg="#9C27B0", fg="white", state='disabled')
preview_button.grid(row=0, column=1, padx=5, pady=2)

# Visible uniquement quand la sélection est déjà moddée | Only visible when the current selection is already modded
load_mod_button = tk.Button(action_frame, command=load_installed_mod_values,
                            font=("Arial", 10), bg="#009688", fg="white")
load_mod_button.grid(row=0, column=2, padx=5, pady=2)
load_mod_button.grid_remove()

# Remplace aussi le portrait de sélection avec les mêmes couleurs | Also replaces the character-select portrait with the same colors
replace_portrait_var = tk.BooleanVar(value=False)
portrait_check = tk.Checkbutton(action_frame, variable=replace_portrait_var,
                                font=("Arial", 9), bg="#f2f2f2",
                                activebackground="#f2f2f2")
portrait_check.grid(row=0, column=3, padx=(12, 5), pady=2)

portrait_status_label = tk.Label(action_frame, font=("Arial", 8),
                                 bg="#f2f2f2", fg="#B00020")
portrait_status_label.grid(row=1, column=0, columnspan=4)
portrait_status_label.grid_remove()


def refresh_portrait_option():
    # Griser l'option et expliquer pourquoi si le portrait est inaccessible | Grey the option out and explain why when the portrait is unreachable
    available, reason = portrait_support_status()
    if available:
        portrait_check.config(state='normal')
        portrait_status_label.grid_remove()
    else:
        replace_portrait_var.set(False)
        portrait_check.config(state='disabled')
        portrait_status_label.config(text=reason)
        portrait_status_label.grid()


refresh_portrait_option()

# Mise à jour initiale des textes | Initial text update
update_texts()

# Gérer la fermeture de l'application | Handle application shutdown
root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
