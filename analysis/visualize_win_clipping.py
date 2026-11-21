"""Windows GDI で usWinAscent / usWinDescent の外側が欠ける様子を可視化する。

dist/ のフォント（現状）と、次の2つの対策案を GDI で実際に描画して比べる。
  A: usWinAscent / usWinDescent を広げる（cmap から届くグリフの最大範囲まで）
  B: win の範囲（800 / -200）からはみ出すグリフを、ベースラインを基準に縮める
対策には B を採り、utatane.py の fit_within_win_metrics() で生成時に縮めている。
縮める前の状態と比べるには、utatane.py を --no-fit-win-metrics 付きで実行して
dist/ を作り直してから、このスクリプトを実行する。

Windows 専用（GDI を ctypes で呼ぶ）。リポジトリ直下で実行する:
    uv run python analysis/visualize_win_clipping.py
出力は tmp/win-clip/ に書く。
"""

import ctypes
import ctypes.wintypes as wt
import math
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

REPO = Path(__file__).resolve().parents[1]
DIST = REPO / "dist"
OUT = REPO / "tmp" / "win-clip"
WEIGHTS = ("Regular", "Bold")
PX = 72  # em のピクセル数
LINES = (
    "EḖ OṌ IḮ AẰ CḈ",  # 上にはみ出す（左は比較用の同じ字）
    "UṸ ⚥ Hg 日本語",
    "AḀ aḁ Hg 日本語",  # 下にはみ出す
)

# 色（dataviz の既定パレット）
INK = "#0b0b0b"
INK_2 = "#52514e"
SURFACE = "#fcfcfb"
LINE_BOX = "#2a78d6"  # series-1: 行の箱（GDI の行の高さ）
CLIPPED = "#d03b3b"  # critical: 欠けた部分


# ---------------------------------------------------------------- フォントの変種


def outline_bounds(glyph_set, name):
    """描画される輪郭の範囲。点が1つだけの輪郭（描画されない迷子の点）は除く"""
    recording = DecomposingRecordingPen(glyph_set)
    glyph_set[name].draw(recording)
    pen = BoundsPen(None)
    contour = []
    for operator, operands in recording.value:
        contour.append((operator, operands))
        if operator in ("closePath", "endPath"):
            points = sum(
                len(args) for op, args in contour if op not in ("closePath", "endPath")
            )
            if points > 1:
                for op, args in contour:
                    getattr(pen, op)(*args)
            contour = []
    return pen.bounds


def glyph_bounds(font):
    glyph_set = font.getGlyphSet()
    bounds = {}
    for name in font.getGlyphOrder():
        box = outline_bounds(glyph_set, name)
        if box:
            bounds[name] = box
    return bounds


def encoded_extent(fonts):
    """cmap から届くグリフの最大の上端と下端（両ウェイト共通の値にする）"""
    top, bottom = 0, 0
    for font in fonts:
        bounds = glyph_bounds(font)
        for name in set(font.getBestCmap().values()):
            if name in bounds:
                top = max(top, bounds[name][3])
                bottom = min(bottom, bounds[name][1])
    return math.ceil(top), math.ceil(-bottom)


def rename(font, family):
    for record in font["name"].names:
        if record.nameID in (1, 4, 16):
            record.string = family
        elif record.nameID == 6:
            record.string = family.replace(" ", "")


def shrink_outside(font, top, bottom):
    """win の範囲からはみ出すグリフを、ベースラインと字面の中心を基準に縮める"""
    glyf, hmtx = font["glyf"], font["hmtx"]
    glyph_set = font.getGlyphSet()
    bounds = glyph_bounds(font)
    targets = {n for n, (_, y0, _, y1) in bounds.items() if y1 > top or y0 < -bottom}

    def uses_target(name):
        g = glyf[name]
        return g.isComposite() and any(
            c.glyphName in targets or uses_target(c.glyphName) for c in g.components
        )

    # 縮めるグリフを部品に使う合成グリフは、形を変えないよう分解だけする
    dependents = {
        n for n in font.getGlyphOrder() if n not in targets and uses_target(n)
    }
    recorded = {}
    for name in targets | dependents:
        pen = DecomposingRecordingPen(glyph_set)
        glyph_set[name].draw(pen)
        recorded[name] = pen

    scales = {}
    for name in targets | dependents:
        tt_pen = TTGlyphPen(None)
        pen = tt_pen
        if name in targets:
            x0, y0, x1, y1 = bounds[name]
            scale = min(
                top / y1 if y1 > top else 1, -bottom / y0 if y0 < -bottom else 1
            )
            center = (x0 + x1) / 2
            pen = TransformPen(tt_pen, (scale, 0, 0, scale, center * (1 - scale), 0))
            scales[name] = scale
        recorded[name].replay(pen)
        glyph = tt_pen.glyph()
        glyph.recalcBounds(glyf)
        glyf[name] = glyph
        hmtx[name] = (hmtx[name][0], getattr(glyph, "xMin", 0))
    return scales


def build_variants():
    OUT.mkdir(parents=True, exist_ok=True)
    sources = {w: TTFont(DIST / f"Utatane-{w}.ttf") for w in WEIGHTS}
    win_top, win_bottom = encoded_extent(sources.values())
    variants = {}
    for weight, source in sources.items():
        os2 = source["OS/2"]
        base_top, base_bottom = os2.usWinAscent, os2.usWinDescent
        for key in ("current", "A", "B"):
            font = TTFont(DIST / f"Utatane-{weight}.ttf")
            family = f"UtaClip {key} {weight}"
            rename(font, family)
            note = ""
            if key == "A":
                font["OS/2"].usWinAscent = win_top
                font["OS/2"].usWinDescent = win_bottom
            elif key == "B":
                scales = shrink_outside(font, base_top, base_bottom)
                note = f"{len(scales)}字を縮小（最小 {min(scales.values()):.0%}）"
            path = OUT / f"{key}-{weight}.ttf"
            font.save(path)
            os2 = font["OS/2"]
            variants[(key, weight)] = {
                "path": path,
                "family": family,
                "win": (os2.usWinAscent, os2.usWinDescent),
                "note": note,
            }
            # 欠けた部分を示すための、同じ字形でまったく欠けない基準
            # （win を全グリフの範囲まで広げたもの）
            reference = TTFont(path)
            rename(reference, f"UtaClip {key} full {weight}")
            yMin = min(g[1] for g in glyph_bounds(reference).values())
            yMax = max(g[3] for g in glyph_bounds(reference).values())
            reference["OS/2"].usWinAscent = math.ceil(yMax)
            reference["OS/2"].usWinDescent = math.ceil(-yMin)
            reference_path = OUT / f"{key}-full-{weight}.ttf"
            reference.save(reference_path)
            variants[(key + "-full", weight)] = {
                "path": reference_path,
                "family": f"UtaClip {key} full {weight}",
            }
    return variants, (win_top, win_bottom)


# ---------------------------------------------------------------- GDI 描画


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wt.DWORD),
        ("biWidth", wt.LONG),
        ("biHeight", wt.LONG),
        ("biPlanes", wt.WORD),
        ("biBitCount", wt.WORD),
        ("biCompression", wt.DWORD),
        ("biSizeImage", wt.DWORD),
        ("biXPelsPerMeter", wt.LONG),
        ("biYPelsPerMeter", wt.LONG),
        ("biClrUsed", wt.DWORD),
        ("biClrImportant", wt.DWORD),
    ]


class TEXTMETRICW(ctypes.Structure):
    _fields_ = [
        (name, wt.LONG)
        for name in (
            "tmHeight",
            "tmAscent",
            "tmDescent",
            "tmInternalLeading",
            "tmExternalLeading",
            "tmAveCharWidth",
            "tmMaxCharWidth",
            "tmWeight",
            "tmOverhang",
            "tmDigitizedAspectX",
            "tmDigitizedAspectY",
        )
    ] + [
        ("tmFirstChar", wt.WCHAR),
        ("tmLastChar", wt.WCHAR),
        ("tmDefaultChar", wt.WCHAR),
        ("tmBreakChar", wt.WCHAR),
        ("tmItalic", wt.BYTE),
        ("tmUnderlined", wt.BYTE),
        ("tmStruckOut", wt.BYTE),
        ("tmPitchAndFamily", wt.BYTE),
        ("tmCharSet", wt.BYTE),
    ]


gdi32 = None


def load_gdi():
    """GDI を読み込む（Windows 専用）"""
    global gdi32
    if gdi32 is not None:
        return gdi32
    gdi32 = ctypes.WinDLL("gdi32")
    gdi32.CreateCompatibleDC.restype = wt.HDC
    gdi32.CreateDIBSection.restype = wt.HBITMAP
    gdi32.CreateDIBSection.argtypes = [
        wt.HDC,
        ctypes.c_void_p,
        wt.UINT,
        ctypes.POINTER(ctypes.c_void_p),
        wt.HANDLE,
        wt.DWORD,
    ]
    gdi32.SelectObject.argtypes = [wt.HDC, wt.HGDIOBJ]
    gdi32.SelectObject.restype = wt.HGDIOBJ
    gdi32.DeleteObject.argtypes = [wt.HGDIOBJ]
    gdi32.DeleteDC.argtypes = [wt.HDC]
    gdi32.CreateFontW.restype = wt.HFONT
    gdi32.SetBkMode.argtypes = [wt.HDC, ctypes.c_int]
    gdi32.GetTextMetricsW.argtypes = [wt.HDC, ctypes.c_void_p]
    gdi32.TextOutW.argtypes = [
        wt.HDC,
        ctypes.c_int,
        ctypes.c_int,
        wt.LPCWSTR,
        ctypes.c_int,
    ]
    gdi32.AddFontResourceExW.argtypes = [wt.LPCWSTR, wt.DWORD, ctypes.c_void_p]
    gdi32.RemoveFontResourceExW.argtypes = [wt.LPCWSTR, wt.DWORD, ctypes.c_void_p]
    return gdi32


FR_PRIVATE = 0x10


def render(family, weight, width, height, top, line_height=None):
    """GDI の TextOut で1行ずつ描く。戻り値は (グレースケール画像, TEXTMETRIC)"""
    hdc = gdi32.CreateCompatibleDC(None)
    header = BITMAPINFOHEADER(
        ctypes.sizeof(BITMAPINFOHEADER), width, -height, 1, 32, 0, 0, 0, 0, 0, 0
    )
    bits = ctypes.c_void_p()
    bitmap = gdi32.CreateDIBSection(
        hdc, ctypes.byref(header), 0, ctypes.byref(bits), None, 0
    )
    gdi32.SelectObject(hdc, bitmap)
    ctypes.memset(bits, 0xFF, width * height * 4)
    font = gdi32.CreateFontW(
        -PX, 0, 0, 0, 700 if weight == "Bold" else 400, 0, 0, 0, 1, 7, 0, 4, 0, family
    )
    gdi32.SelectObject(hdc, font)
    gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
    metrics = TEXTMETRICW()
    gdi32.GetTextMetricsW(hdc, ctypes.byref(metrics))
    step = line_height or metrics.tmHeight
    for i, text in enumerate(LINES):
        gdi32.TextOutW(hdc, 16, top + i * step, text, len(text))
    pixels = np.ctypeslib.as_array(
        ctypes.cast(bits, ctypes.POINTER(ctypes.c_ubyte)), shape=(height, width, 4)
    )
    gray = pixels[:, :, :3].mean(axis=2).copy()
    gdi32.DeleteObject(font)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(hdc)
    return gray, metrics


def panel(variants, key, weight, width, height):
    """GDI の描画結果に、欠けた部分（赤）と行の箱（青）を重ねた RGB 画像を返す"""
    info = variants[(key, weight)]
    full = variants[(key + "-full", weight)]
    top = 12
    shown, metrics = render(info["family"], weight, width, height, top)
    # 基準: 同じ行送り・同じベースラインで、まったく欠けない版を描く
    _, full_metrics = render(full["family"], weight, 8, 8, 0)
    offset = metrics.tmAscent - full_metrics.tmAscent
    reference, _ = render(
        full["family"], weight, width, height, top + offset, metrics.tmHeight
    )
    ink = 1 - shown / 255
    missing = np.clip((1 - reference / 255) - ink, 0, 1)
    missing[missing < 0.25] = 0

    rgb = np.ones((height, width, 3)) * matplotlib.colors.to_rgb(SURFACE)
    ink_rgb = np.array(matplotlib.colors.to_rgb(INK))
    red = np.array(matplotlib.colors.to_rgb(CLIPPED))
    rgb = rgb * (1 - ink[..., None]) + ink_rgb * ink[..., None]
    rgb = rgb * (1 - missing[..., None]) + red * missing[..., None]
    boxes = [top + i * metrics.tmHeight for i in range(len(LINES) + 1)]
    return rgb, metrics, boxes, int((missing > 0).sum())


# ---------------------------------------------------------------- 図


def main():
    if sys.platform != "win32":
        sys.exit("Windows の GDI を使うので Windows で実行してください")
    load_gdi()
    variants, (win_top, win_bottom) = build_variants()
    for info in variants.values():
        gdi32.AddFontResourceExW(os.fspath(info["path"]), FR_PRIVATE, None)

    titles = {
        "current": "現状（win 800 / 200）",
        "A": f"A: win を広げる（{win_top} / {win_bottom}）",
        "B": "B: はみ出すグリフを縮める（win 800 / 200）",
    }
    width = 760
    height = 12 + len(LINES) * PX * (win_top + win_bottom) // 1000 + 24
    plt.rcParams["font.family"] = ["Yu Gothic", "Meiryo", "sans-serif"]
    fig, axes = plt.subplots(
        len(WEIGHTS), 3, figsize=(19, 3.4 * len(WEIGHTS) + 1.2), facecolor=SURFACE
    )
    summary = []
    for row, weight in enumerate(WEIGHTS):
        for col, key in enumerate(("current", "A", "B")):
            ax = axes[row][col]
            rgb, metrics, boxes, missing_px = panel(
                variants, key, weight, width, height
            )
            ax.imshow(rgb, interpolation="nearest")
            for y in boxes:
                ax.axhline(y - 0.5, color=LINE_BOX, linewidth=1, alpha=0.6)
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_color("#d8d7d2")
            ratio = metrics.tmHeight / PX
            info = variants[(key, weight)]
            caption = f"行の高さ {metrics.tmHeight}px（em の {ratio:.2f} 倍）"
            if info["note"]:
                caption += f"　{info['note']}"
            caption += f"\n欠けたピクセル {missing_px:,}"
            ax.set_title(
                f"{titles[key]} — {weight}", loc="left", fontsize=12, color=INK
            )
            ax.set_xlabel(caption, loc="left", fontsize=10, color=INK_2)
            summary.append((weight, key, metrics.tmHeight, missing_px, info["note"]))
    fig.suptitle(
        "Windows GDI（TextOut）での描画。赤 = 欠けて描かれなかった部分、青線 = GDI の行の箱",
        x=0.01,
        ha="left",
        fontsize=13,
        color=INK,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    path = OUT / "win_clipping.png"
    fig.savefig(path, dpi=100, facecolor=SURFACE)
    for info in variants.values():
        gdi32.RemoveFontResourceExW(os.fspath(info["path"]), FR_PRIVATE, None)

    print(f"図: {path}")
    print("weight\tvariant\tline_px\tmissing_px\tnote")
    for weight, key, line_px, missing_px, note in summary:
        print(f"{weight}\t{key}\t{line_px}\t{missing_px}\t{note}")


if __name__ == "__main__":
    main()
