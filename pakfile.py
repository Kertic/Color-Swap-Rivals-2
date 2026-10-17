# -*- coding: utf-8 -*-
"""
Lecture et écriture de .pak Unreal, sans UnrealPak.
Reading and writing Unreal .pak files, without UnrealPak.

Lecture : anciens paks (index « legacy », versions 3 à 9, comme ceux de
l'UnrealPak 4.17 livré dans Upack) et paks UE5 (versions 10 à 12, index
encodé), non compressés, zlib ou Oodle.

Écriture : pak version 12 (celle du jeu depuis UE5.8), avec le même
agencement que le pak du jeu : index principal, index par empreinte de
chemin (FNV-64, vérifié sur le pak du jeu) et index complet des dossiers.
Non utilisée pour l'instant : le jeu monte ces paks de mods mais n'y lit
aucun fichier (ni à la racine, ni au dossier commun, ni compressés), alors
que les paks version 4 d'UnrealPak fonctionnent.

Reading: old paks ("legacy" index, versions 3 to 9, like those made by the
UnrealPak 4.17 bundled in Upack) and UE5 paks (versions 10 to 12, encoded
index), uncompressed, zlib or Oodle.

Writing: version 12 paks (the game's since UE5.8), with the same layout
as the game's pak: primary index, path-hash index (FNV-64, checked against
the game's pak) and full directory index. Unused for now: the game mounts
these as mod paks but reads no file from them (mounted at the root, at the
common folder, or compressed), whereas UnrealPak's version 4 paks work.
"""
import hashlib
import os
import struct
import zlib

MAGIC = 0x5A6F12E1
WRITE_VERSION = 12            # Utf8PakDirectory : le format du pak du jeu | the game pak's format
MOUNT_POINT = "../../../"     # comme le pak du jeu | like the game's pak
_COMPRESSION_SLOTS = 5        # noms de méthodes de compression dans le pied de page | compression method names in the footer
_ZLIB_FLAG = 0x01             # ancienne énumération (version < 8) | old enum (version < 8)
BLOCK_SIZE = 65536            # taille de bloc de compression, comme le pak du jeu | compression block size, like the game's pak


class PakError(ValueError):
    pass


# --------------------------------------------------------------------------
# Lecture | Reading
# --------------------------------------------------------------------------

class _Cursor:
    def __init__(self, buf, pos=0):
        self.b, self.p = buf, pos

    def _take(self, fmt):
        v = struct.unpack_from(fmt, self.b, self.p)
        self.p += struct.calcsize(fmt)
        return v[0]

    def i32(self): return self._take("<i")
    def u32(self): return self._take("<I")
    def i64(self): return self._take("<q")
    def u64(self): return self._take("<Q")
    def u8(self): return self._take("<B")

    def raw(self, n):
        v = self.b[self.p:self.p + n]
        self.p += n
        return v

    def fstring(self):
        n = self.i32()
        if n == 0:
            return ""
        if n < 0:
            return self.raw(-n * 2).decode("utf-16-le", "replace").rstrip("\x00")
        raw = self.raw(n)
        try:
            return raw.decode("utf-8").rstrip("\x00")
        except UnicodeDecodeError:
            return raw.decode("latin-1").rstrip("\x00")


def _read_entry(c, version):
    """
    FPakEntry tel qu'écrit dans l'index legacy et devant chaque fichier.
    FPakEntry as written in the legacy index and in front of each file.
    """
    entry = {"offset": c.i64(), "size": c.i64(), "usize": c.i64()}
    if version < 8:
        flags = c.i32()
        entry["method"] = "Zlib" if flags & _ZLIB_FLAG else (None if flags == 0 else "flags:%d" % flags)
    else:
        entry["method_index"] = c.u32()
    if version <= 1:
        c.i64()                       # horodatage | timestamp
    c.raw(20)                         # SHA-1
    entry["blocks"] = []
    if version >= 3:
        compressed = (entry.get("method") is not None) if version < 8 else entry["method_index"] != 0
        if compressed:
            for _ in range(c.i32()):
                entry["blocks"].append((c.i64(), c.i64()))
        entry["flags"] = c.u8()
        entry["block_size"] = c.u32()
    return entry


class PakReader:
    """
    Un .pak ouvert : point de montage, fichiers (chemins relatifs au point
    de montage) et lecture de leur contenu.

    An opened .pak: mount point, files (paths relative to the mount point)
    and reading their contents.
    """

    def __init__(self, path, oodle=None):
        self.path = path
        self.oodle = oodle
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            f.seek(max(0, size - 300))
            tail = f.read()
        pos = tail.rfind(struct.pack("<I", MAGIC))
        if pos < 0:
            raise PakError("pak non reconnu | not a pak file: %s" % path)
        self.version = struct.unpack_from("<I", tail, pos + 4)[0]
        index_offset, index_size = struct.unpack_from("<QQ", tail, pos + 8)
        if pos > 0 and tail[pos - 1] != 0 and self.version >= 4:
            raise PakError("index chiffré non pris en charge | encrypted index not supported")
        names = []
        if self.version >= 8:
            start = pos + 44
            for i in range((len(tail) - start) // 32):
                names.append(tail[start + i * 32:start + (i + 1) * 32].rstrip(b"\0").decode("ascii", "replace"))
        self.compression_names = names
        with open(path, "rb") as f:
            f.seek(index_offset)
            index = f.read(index_size)
        if self.version >= 10:
            self._load_encoded_index(index)
        else:
            self._load_legacy_index(index)

    def _load_legacy_index(self, index):
        c = _Cursor(index)
        self.mount = c.fstring()
        self.files = {}
        for _ in range(c.i32()):
            name = c.fstring()
            entry = _read_entry(c, self.version)
            self.files[name.replace("\\", "/")] = entry["offset"]

    def _load_encoded_index(self, index):
        c = _Cursor(index)
        self.mount = c.fstring()
        c.i32()                                   # nombre d'entrées | entry count
        c.u64()                                   # graine du hachage | hash seed
        if c.u32():                               # index par empreinte | path-hash index
            c.i64(); c.i64(); c.raw(20)
        if not c.u32():
            raise PakError("pak sans index des dossiers | pak without a directory index")
        fdi_offset, fdi_size = c.i64(), c.i64()
        c.raw(20)
        encoded = c.raw(c.i32())
        with open(self.path, "rb") as f:
            f.seek(fdi_offset)
            fdi = _Cursor(f.read(fdi_size))
        self.files = {}
        for _ in range(fdi.i32()):
            directory = fdi.fstring()
            for _ in range(fdi.i32()):
                name = fdi.fstring()
                at = fdi.i32()
                rel = (directory.lstrip("/") + name) if directory != "/" else name
                self.files[rel] = self._decode_offset(encoded, at)

    @staticmethod
    def _decode_offset(encoded, at):
        flags = struct.unpack_from("<I", encoded, at)[0]
        p = at + 4
        if flags & 0x3f == 0x3f:
            p += 4                                # taille de bloc explicite | explicit block size
        if flags >> 31:
            return struct.unpack_from("<I", encoded, p)[0]
        return struct.unpack_from("<Q", encoded, p)[0]

    def read(self, rel):
        """Contenu décompressé d'un fichier. | Decompressed contents of one file."""
        offset = self.files[rel]
        with open(self.path, "rb") as f:
            f.seek(offset)
            head = f.read(4096)
            c = _Cursor(head)
            entry = _read_entry(c, self.version)
            header_len = c.p
            if self.version >= 8:
                index = entry["method_index"]
                method = None if index == 0 else self.compression_names[index - 1]
            else:
                method = entry["method"]
            if method is None:
                f.seek(offset + header_len)
                return f.read(entry["usize"])
            out = bytearray()
            for start, end in entry["blocks"]:
                # Depuis la version 5, les blocs sont relatifs à l'entrée | Since version 5, blocks are relative to the entry
                f.seek((offset + start) if self.version >= 5 else start)
                chunk = f.read(end - start)
                remaining = entry["usize"] - len(out)
                if method.lower() == "zlib":
                    out += zlib.decompress(chunk)
                elif method.lower() == "oodle" and self.oodle is not None:
                    out += self.oodle.decompress(chunk, min(entry["block_size"] or remaining, remaining))
                else:
                    raise PakError("compression non prise en charge | unsupported compression: %s" % method)
            return bytes(out)

    def extract_all(self, dest_dir):
        """Écrit chaque fichier sous dest_dir (chemins relatifs au point de montage). | Writes every file under dest_dir (paths relative to the mount point)."""
        for rel in self.files:
            target = os.path.join(dest_dir, *rel.split("/"))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(self.read(rel))
        return len(self.files)


# --------------------------------------------------------------------------
# Écriture | Writing
# --------------------------------------------------------------------------

def _fstring(text):
    data = text.encode("utf-8") + b"\0"
    return struct.pack("<i", len(data)) + data


def path_hash(rel, seed):
    """
    Empreinte FNV-64 d'un chemin (FPakFile::HashPath, version >= 11) :
    chemin en minuscules, en UTF-16, avec la graine ajoutée à la base.

    FNV-64 fingerprint of a path (FPakFile::HashPath, version >= 11):
    lowercased path, as UTF-16, with the seed added to the offset basis.
    """
    h = (0xcbf29ce484222325 + seed) & 0xFFFFFFFFFFFFFFFF
    for b in rel.lower().encode("utf-16-le"):
        h ^= b
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return h


def _directory_index(directories):
    out = bytearray(struct.pack("<i", len(directories)))
    for directory in sorted(directories):
        files = directories[directory]
        out += _fstring(directory) + struct.pack("<i", len(files))
        for name, at in files:
            out += _fstring(name) + struct.pack("<i", at)
    return bytes(out)


def common_mount(paths):
    """
    Point de montage au dossier commun le plus profond, comme UnrealPak
    (ex. ../../../Rivals2/Content/Characters/Fleet/Skins/).

    Mount point at the deepest common folder, like UnrealPak (e.g.
    ../../../Rivals2/Content/Characters/Fleet/Skins/).
    """
    folders = [p.replace("\\", "/").lstrip("/").split("/")[:-1] for p in paths]
    common = []
    for parts in zip(*folders) if folders else ():
        if any(part != parts[0] for part in parts):
            break
        common.append(parts[0])
    return MOUNT_POINT + "".join(part + "/" for part in common)


def _entry(offset_in_blob, data, compress):
    """
    En-tête + données d'une entrée, et sa forme encodée pour l'index, selon
    les conventions du pak du jeu : un seul bloc de la taille du fichier pour
    les petits fichiers, sinon des blocs de 64 Ko dont les tailles
    compressées sont listées dans l'index ; offsets des blocs relatifs à
    l'en-tête.

    Header + data of one entry, and its encoded form for the index, using
    the game pak's conventions: a single block the size of the file for
    small files, otherwise 64 KB blocks whose compressed sizes are listed in
    the index; block offsets relative to the header.
    """
    usize = len(data)
    if not compress or usize == 0:
        header = struct.pack("<qqqI", 0, usize, usize, 0) + hashlib.sha1(data).digest() + struct.pack("<BI", 0, 0)
        flags = ((offset_in_blob < 2 ** 32) << 31) | ((usize < 2 ** 32) << 30) | ((usize < 2 ** 32) << 29)
        encoded = struct.pack("<I", flags) + _u32_or_u64(offset_in_blob) + _u32_or_u64(usize)
        return header + data, encoded
    chunks = [zlib.compress(data[i:i + BLOCK_SIZE], 9) for i in range(0, usize, BLOCK_SIZE)]
    compressed = b"".join(chunks)
    size = len(compressed)
    header_len = 8 * 3 + 4 + 20 + 4 + 16 * len(chunks) + 1 + 4
    blocks, cursor = b"", header_len
    for chunk in chunks:
        blocks += struct.pack("<qq", cursor, cursor + len(chunk))
        cursor += len(chunk)
    block_size = usize if len(chunks) == 1 else BLOCK_SIZE
    header = (struct.pack("<qqqI", 0, size, usize, 1) + hashlib.sha1(compressed).digest()
              + struct.pack("<i", len(chunks)) + blocks + struct.pack("<BI", 0, block_size))
    packed = 0 if len(chunks) == 1 else (BLOCK_SIZE >> 11)
    flags = (packed | (len(chunks) << 6) | (1 << 23) | ((offset_in_blob < 2 ** 32) << 31)
             | ((usize < 2 ** 32) << 30) | ((size < 2 ** 32) << 29))
    encoded = (struct.pack("<I", flags) + _u32_or_u64(offset_in_blob) + _u32_or_u64(usize)
               + _u32_or_u64(size))
    if len(chunks) > 1:
        encoded += b"".join(struct.pack("<I", len(chunk)) for chunk in chunks)
    return header + compressed, encoded


def _u32_or_u64(value):
    return struct.pack("<I", value) if value < 2 ** 32 else struct.pack("<Q", value)


def write_pak(out_path, files, mount=None, compress=True):
    """
    Écrit un pak version 12 non compressé. `files` : [(chemin sous la racine
    du jeu avec des « / », ex. Rivals2/Content/..., contenu), ...]. Sans
    `mount`, le point de montage est le dossier commun (voir common_mount).

    Writes a version 12 pak. `files`: [(path under the game root with "/"
    separators, e.g. Rivals2/Content/..., contents), ...]. Without `mount`,
    the mount point is the common folder (see common_mount). Files are
    zlib-compressed unless `compress` is False.
    """
    if mount is None:
        mount = common_mount([rel for rel, _data in files])
    prefix = mount[len(MOUNT_POINT):] if mount.startswith(MOUNT_POINT) else ""
    files = [(rel.replace("\\", "/").lstrip("/")[len(prefix):], data) for rel, data in files]
    files = sorted(files, key=lambda item: item[0].lower())
    seed = zlib.crc32(os.path.basename(out_path).lower().encode("utf-16-le"))
    blob = bytearray()
    encoded = bytearray()
    path_hashes = []
    directories = {}
    for rel, data in files:
        rel = rel.replace("\\", "/").lstrip("/")
        # En-tête devant les données : offset 0, comme dans le pak du jeu | Header in front of the data: offset 0, like in the game's pak
        stored, entry = _entry(len(blob), data, compress)
        blob += stored
        at = len(encoded)
        encoded += entry
        path_hashes.append((path_hash(rel, seed), at))
        directory, _, name = rel.rpartition("/")
        directory = directory + "/" if directory else "/"
        directories.setdefault(directory, []).append((name, at))
        # Les dossiers parents figurent aussi dans l'index, vides | Parent folders appear in the index too, empty
        parent = directory.rstrip("/")
        while "/" in parent:
            parent = parent.rsplit("/", 1)[0]
            directories.setdefault(parent + "/", [])

    full_index = _directory_index(directories)
    hash_index = bytearray(struct.pack("<i", len(path_hashes)))
    for h, at in path_hashes:
        hash_index += struct.pack("<Qi", h, at)
    hash_index += full_index                  # index des dossiers « élagué » : ici complet | "pruned" directory index: complete here

    def primary(index_offset):
        p = bytearray(_fstring(mount))
        p += struct.pack("<iQ", len(files), seed)
        phi_offset = index_offset + primary_len
        p += struct.pack("<Iqq", 1, phi_offset, len(hash_index)) + hashlib.sha1(hash_index).digest()
        p += struct.pack("<Iqq", 1, phi_offset + len(hash_index), len(full_index)) + hashlib.sha1(full_index).digest()
        p += struct.pack("<i", len(encoded)) + encoded
        p += struct.pack("<i", 0)             # entrées non encodables | non-encodable entries
        return bytes(p)

    primary_len = 0
    primary_len = len(primary(0))             # la taille ne dépend pas des offsets | the size doesn't depend on the offsets
    index_offset = len(blob)
    primary_index = primary(index_offset)
    footer = bytes(16) + b"\0" + struct.pack("<IIQQ", MAGIC, WRITE_VERSION, index_offset, len(primary_index))
    names = (b"Zlib".ljust(32, b"\0") if compress else bytes(32)) + bytes(32 * (_COMPRESSION_SLOTS - 1))
    footer += hashlib.sha1(primary_index).digest() + names

    tmp = out_path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(blob)
        f.write(primary_index)
        f.write(hash_index)
        f.write(full_index)
        f.write(footer)
    os.replace(tmp, out_path)
    return len(files)
