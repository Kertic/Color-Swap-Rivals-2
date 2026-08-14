# -*- coding: utf-8 -*-
"""
Lecture et réécriture des portraits de sélection (textures CSP).
Reading and rewriting character-select portraits (CSP textures).

Les portraits ne sont pas livrés avec l'outil : ils sont lus à la demande
dans le .pak du jeu (index UE5 v11, blocs compressés en Oodle), recolorés,
puis ré-encodés en DXT5 et réinjectés dans un .uexp de taille identique.

Portraits are not shipped with the tool: they are read on demand from the
game's .pak (UE5 v11 index, Oodle-compressed blocks), recolored, then
re-encoded to DXT5 and spliced back into a .uexp of identical size.
"""
import ctypes
import glob
import io
import os
import struct

from PIL import Image

# Un .uexp de texture CSP est : en-tête + données DXT5 + fin de bloc
# A CSP texture .uexp is: header + DXT5 payload + trailer
CSP_HEADER_LEN = 117
CSP_TRAILER_LEN = 28
SUPPORTED_SIDES = (256, 512, 1024, 2048)


# --------------------------------------------------------------------------
# Oodle
# --------------------------------------------------------------------------

def find_oodle_dll(extra_dirs=()):
    """
    Cherche la DLL Oodle. FModel la télécharge dans son dossier .data ;
    d'autres jeux Unreal en installent une copie.

    Looks for the Oodle DLL. FModel downloads one into its .data folder;
    other Unreal games ship a copy of their own.
    """
    patterns = []
    for base in extra_dirs:
        if not base:
            continue
        patterns += [
            os.path.join(base, ".data", "oodle-data-shared.dll"),
            os.path.join(base, "oodle-data-shared.dll"),
            os.path.join(base, "**", "oo2core_*_win64.dll"),
        ]
    for pattern in patterns:
        for hit in glob.glob(pattern, recursive=True):
            if os.path.isfile(hit):
                return hit
    return None


class Oodle:
    """Enveloppe ctypes autour de OodleLZ_Decompress. | ctypes wrapper around OodleLZ_Decompress."""

    def __init__(self, dll_path):
        self.path = dll_path
        self._lib = ctypes.WinDLL(dll_path)
        self._fn = self._lib.OodleLZ_Decompress
        self._fn.restype = ctypes.c_longlong
        self._fn.argtypes = [
            ctypes.c_char_p, ctypes.c_longlong,     # compressed buffer + size
            ctypes.c_char_p, ctypes.c_longlong,     # raw buffer + size
            ctypes.c_int, ctypes.c_int, ctypes.c_int,   # fuzz, crc, verbosity
            ctypes.c_void_p, ctypes.c_longlong,     # decode buffer base/size
            ctypes.c_void_p, ctypes.c_void_p,       # callback + user data
            ctypes.c_void_p, ctypes.c_longlong,     # scratch memory
            ctypes.c_int,                           # thread phase
        ]

    def decompress(self, compressed, raw_size):
        out = ctypes.create_string_buffer(raw_size)
        written = self._fn(compressed, len(compressed), out, raw_size,
                           1, 0, 0, None, 0, None, None, None, 0, 3)
        if written != raw_size:
            raise RuntimeError(
                f"Oodle a renvoyé {written} au lieu de {raw_size} | Oodle returned {written}, expected {raw_size}")
        return out.raw[:raw_size]


# --------------------------------------------------------------------------
# Lecture du .pak du jeu (version 11, non chiffré) | Reading the game .pak (v11, unencrypted)
# --------------------------------------------------------------------------

class _Cursor:
    def __init__(self, buf):
        self.b = buf
        self.p = 0

    def i32(self):
        v = struct.unpack_from("<i", self.b, self.p)[0]
        self.p += 4
        return v

    def i64(self):
        v = struct.unpack_from("<q", self.b, self.p)[0]
        self.p += 8
        return v

    def u64(self):
        v = struct.unpack_from("<Q", self.b, self.p)[0]
        self.p += 8
        return v

    def skip(self, n):
        self.p += n

    def fstring(self):
        n = self.i32()
        if n == 0:
            return ""
        if n < 0:
            raw = self.b[self.p:self.p + (-n) * 2]
            self.p += (-n) * 2
            return raw.decode("utf-16-le", "ignore").rstrip("\x00")
        raw = self.b[self.p:self.p + n]
        self.p += n
        return raw.decode("ascii", "ignore").rstrip("\x00")


class GamePak:
    """
    Index d'un .pak Unreal 5. L'index est lu une seule fois puis mis en cache.
    Index of an Unreal 5 .pak. Read once, then cached.
    """

    FOOTER_LEN = 204
    MAGIC = 0x5A6F12E1

    def __init__(self, pak_path, oodle=None):
        self.path = pak_path
        self.oodle = oodle
        self._entries = None      # {nom de fichier -> (dossier, offset encodé)}
        self._encoded = None

    # -- index ------------------------------------------------------------
    def _load_index(self):
        if self._entries is not None:
            return
        size = os.path.getsize(self.path)
        with open(self.path, "rb") as f:
            f.seek(size - self.FOOTER_LEN)
            footer = f.read(self.FOOTER_LEN)
            magic, version = struct.unpack_from("<II", footer, 0)
            if magic != self.MAGIC:
                raise RuntimeError("pak non reconnu | unrecognized pak")
            index_off, index_size = struct.unpack_from("<QQ", footer, 8)
            f.seek(index_off)
            index = f.read(index_size)

        c = _Cursor(index)
        c.fstring()                    # mount point
        c.i32()                        # entry count
        c.u64()                        # path hash seed
        if c.i32():                    # path hash index
            c.i64(); c.i64(); c.skip(20)
        fdi_off = fdi_size = 0
        if c.i32():                    # full directory index
            fdi_off = c.i64(); fdi_size = c.i64(); c.skip(20)
        encoded_size = c.i32()
        self._encoded = index[c.p:c.p + encoded_size]

        entries = {}
        if fdi_off:
            with open(self.path, "rb") as f:
                f.seek(fdi_off)
                fdi = f.read(fdi_size)
            d = _Cursor(fdi)
            for _ in range(d.i32()):
                directory = d.fstring()
                for _ in range(d.i32()):
                    name = d.fstring()
                    entries.setdefault(name, (directory, d.i32()))
        self._entries = entries

    def has(self, filename):
        self._load_index()
        return filename in self._entries

    def directory_of(self, filename):
        self._load_index()
        found = self._entries.get(filename)
        return found[0] if found else None

    # -- lecture d'un fichier | reading one file --------------------------
    def read_file(self, filename):
        """
        Renvoie le contenu décompressé d'un fichier du pak.
        Returns the decompressed contents of one file in the pak.
        """
        self._load_index()
        found = self._entries.get(filename)
        if not found:
            raise FileNotFoundError(filename)
        _directory, encoded_offset = found
        entry_offset = self._decode_offset(encoded_offset)

        with open(self.path, "rb") as f:
            f.seek(entry_offset)
            head = f.read(4096)
            c = _Cursor(head)
            c.i64()                       # offset (répété | repeated)
            c.i64()                       # taille compressée | compressed size
            uncompressed = c.i64()
            method = c.i32()
            c.skip(20)                    # hash
            blocks = []
            if method != 0:
                for _ in range(c.i32()):
                    blocks.append((c.i64(), c.i64()))
            c.skip(1)                     # flags
            block_size = struct.unpack_from("<I", head, c.p)[0]
            c.p += 4
            header_len = c.p

            if method == 0:
                f.seek(entry_offset + header_len)
                return f.read(uncompressed)

            if self.oodle is None:
                raise RuntimeError("Oodle indisponible | Oodle unavailable")
            out = bytearray()
            for start, end in blocks:
                f.seek(entry_offset + start)
                chunk = f.read(end - start)
                remaining = uncompressed - len(out)
                out += self.oodle.decompress(chunk, min(block_size, remaining))
            return bytes(out)

    def _decode_offset(self, encoded_offset):
        # Seul l'offset de l'entrée nous intéresse ; l'en-tête complet est
        # relu depuis le pak. | Only the entry offset is needed here; the full
        # header is re-read from the pak itself.
        flags = struct.unpack_from("<I", self._encoded, encoded_offset)[0]
        p = encoded_offset + 4
        if (flags >> 28) & 1:
            return 0
        if (flags >> 31) & 1:
            return struct.unpack_from("<I", self._encoded, p)[0]
        return struct.unpack_from("<Q", self._encoded, p)[0]


# --------------------------------------------------------------------------
# DXT5 / BC3
# --------------------------------------------------------------------------

def csp_layout(uexp):
    """
    Déduit (taille d'en-tête, largeur, hauteur) d'un .uexp de portrait.
    Renvoie None si la disposition n'est pas celle attendue (mipmaps, etc.).

    Works out (header length, width, height) for a portrait .uexp.
    Returns None when the layout is not the expected one (mip chains, etc.).
    """
    payload = len(uexp) - CSP_HEADER_LEN - CSP_TRAILER_LEN
    if payload <= 0:
        return None
    side = int(round(payload ** 0.5))
    if side * side != payload or side not in SUPPORTED_SIDES:
        return None
    return CSP_HEADER_LEN, side, side


def _dds_header(width, height, payload_len):
    hdr = bytearray(128)
    hdr[0:4] = b"DDS "
    struct.pack_into("<I", hdr, 4, 124)
    struct.pack_into("<I", hdr, 8, 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000)
    struct.pack_into("<I", hdr, 12, height)
    struct.pack_into("<I", hdr, 16, width)
    struct.pack_into("<I", hdr, 20, payload_len)
    struct.pack_into("<I", hdr, 28, 1)
    struct.pack_into("<I", hdr, 76, 32)
    struct.pack_into("<I", hdr, 80, 0x4)
    hdr[84:88] = b"DXT5"
    struct.pack_into("<I", hdr, 108, 0x1000)
    return bytes(hdr)


def decode_csp(uexp):
    """Décode le portrait contenu dans un .uexp. | Decodes the portrait held in a .uexp."""
    layout = csp_layout(uexp)
    if not layout:
        return None
    header_len, width, height = layout
    payload = uexp[header_len:header_len + width * height]
    dds = _dds_header(width, height, len(payload)) + payload
    return Image.open(io.BytesIO(dds)).convert("RGBA")


def _encode_alpha_block(alphas):
    a0, a1 = max(alphas), min(alphas)
    out = bytearray(8)
    out[0], out[1] = a0, a1
    if a0 == a1:
        return bytes(out)          # tous les index à 0 | every index 0
    # Palette BC4 : 0 -> a0, 1 -> a1, puis 6 valeurs interpolées
    # BC4 palette: 0 -> a0, 1 -> a1, then 6 interpolated values
    palette = [a0, a1] + [((8 - i) * a0 + (i - 1) * a1) // 7 for i in range(2, 8)]
    bits = 0
    for i, a in enumerate(alphas):
        best = min(range(8), key=lambda k: abs(palette[k] - a))
        bits |= best << (3 * i)
    out[2:8] = bits.to_bytes(6, "little")
    return bytes(out)


def _to565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def _from565(v):
    r = (v >> 11) & 0x1F
    g = (v >> 5) & 0x3F
    b = v & 0x1F
    return (r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)


def _encode_color_block(pixels):
    # Boîte englobante resserrée : bon compromis vitesse/qualité sur des
    # aplats de couleur. | Inset bounding box: a good speed/quality trade-off
    # for flat-shaded artwork.
    rs = [p[0] for p in pixels]
    gs = [p[1] for p in pixels]
    bs = [p[2] for p in pixels]
    rmin, rmax = min(rs), max(rs)
    gmin, gmax = min(gs), max(gs)
    bmin, bmax = min(bs), max(bs)
    ir = (rmax - rmin) >> 4
    ig = (gmax - gmin) >> 4
    ib = (bmax - bmin) >> 4
    rmin, rmax = min(rmin + ir, 255), max(rmax - ir, 0)
    gmin, gmax = min(gmin + ig, 255), max(gmax - ig, 0)
    bmin, bmax = min(bmin + ib, 255), max(bmax - ib, 0)

    e0 = _to565(rmax, gmax, bmax)
    e1 = _to565(rmin, gmin, bmin)
    if e0 < e1:
        e0, e1 = e1, e0
    out = bytearray(8)
    struct.pack_into("<HH", out, 0, e0, e1)
    if e0 == e1:
        return bytes(out)          # bloc uni | flat block

    c0 = _from565(e0)
    c1 = _from565(e1)
    palette = (
        c0,
        c1,
        tuple((2 * c0[i] + c1[i]) // 3 for i in range(3)),
        tuple((c0[i] + 2 * c1[i]) // 3 for i in range(3)),
    )
    bits = 0
    for i, p in enumerate(pixels):
        best = 0
        best_dist = None
        for k in range(4):
            q = palette[k]
            d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 + (p[2] - q[2]) ** 2
            if best_dist is None or d < best_dist:
                best_dist = d
                best = k
        bits |= best << (2 * i)
    struct.pack_into("<I", out, 4, bits)
    return bytes(out)


def encode_dxt5(image):
    """
    Encode une image RGBA en DXT5 (BC3). Pillow sait décoder ce format mais
    pas l'écrire, d'où cet encodeur.

    Encodes an RGBA image to DXT5 (BC3). Pillow can decode this format but
    not write it, hence this encoder.
    """
    image = image.convert("RGBA")
    width, height = image.size
    px = image.load()
    out = bytearray()
    for by in range(0, height, 4):
        for bx in range(0, width, 4):
            block = [px[bx + x, by + y] for y in range(4) for x in range(4)]
            out += _encode_alpha_block([p[3] for p in block])
            out += _encode_color_block(block)
    return bytes(out)


def csp_wrapper(uexp):
    """
    Extrait l'en-tête et la fin d'un .uexp de portrait (145 octets au
    total). Conservés dans le manifeste, ils suffisent à reconstruire le
    fichier sans jamais relire le jeu.

    Extracts the header and trailer of a portrait .uexp (145 bytes in
    total). Stored in the manifest, they are enough to rebuild the file
    without ever reading the game again.
    """
    if csp_layout(uexp) is None:
        return None
    return uexp[:CSP_HEADER_LEN] + uexp[-CSP_TRAILER_LEN:]


def build_csp_uexp(wrapper, image, side):
    """
    Assemble un .uexp de portrait à partir de l'en-tête/fin conservés et
    d'une image recolorée. Ne nécessite ni le .pak du jeu ni Oodle.

    Assembles a portrait .uexp from the stored header/trailer and a
    recolored image. Needs neither the game .pak nor Oodle.
    """
    expected = CSP_HEADER_LEN + CSP_TRAILER_LEN
    if wrapper is None or len(wrapper) != expected:
        raise ValueError(
            f"en-tête de portrait invalide | invalid portrait wrapper ({len(wrapper) if wrapper else 0} != {expected})")
    if side not in SUPPORTED_SIDES:
        raise ValueError(f"taille non prise en charge | unsupported size {side}")
    if image.size != (side, side):
        image = image.convert("RGBA").resize((side, side), Image.LANCZOS)
    payload = encode_dxt5(image)
    if len(payload) != side * side:
        raise ValueError(f"payload {len(payload)} != {side * side}")
    return wrapper[:CSP_HEADER_LEN] + payload + wrapper[CSP_HEADER_LEN:]


def encode_csp(uexp, image):
    """
    Remplace les pixels d'un .uexp de portrait par ceux de `image`.
    La taille du fichier est inchangée : seul le bloc DXT5 est réécrit.

    Replaces the pixels of a portrait .uexp with those of `image`.
    The file size is unchanged: only the DXT5 payload is rewritten.
    """
    layout = csp_layout(uexp)
    if not layout:
        raise ValueError("disposition de texture non prise en charge | unsupported texture layout")
    header_len, width, height = layout
    if image.size != (width, height):
        image = image.convert("RGBA").resize((width, height), Image.LANCZOS)
    payload = encode_dxt5(image)
    if len(payload) != width * height:
        raise ValueError(f"payload {len(payload)} != {width * height}")
    return uexp[:header_len] + payload + uexp[header_len + len(payload):]
