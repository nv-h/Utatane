#!/usr/bin/env python

import datetime
import math
import os
import shutil
import subprocess
import sys
import unicodedata

import psMat

import fontforge
from width_policy import expected_cells

VERSION = "1.3.2"
FONTNAME = "Utatane"

# Ubuntu Mono (罫線などを削除してあるものを使う)
# 800 x 200 = 1000(Em)
# Win(Ascent, Descent)=(-170, -183)
# hhea(height, width)=(-170, 183)
LATIN_REGULAR_FONT = "UbuntuMono-Regular_modify.ttf"
LATIN_BOLD_FONT = "UbuntuMono-Bold_modify.ttf"

# やさしさゴシックボールドV2
# レギュラー版は手動で embold -30 して、一部フォントを調整したもの
# 880 x 120 = 1000(Em)
JAPANESE_REGULAR_FONT = "YasashisaGothicBold-V2_-30.ttf"
JAPANESE_BOLD_FONT = "YasashisaGothicBold-V2.ttf"
# M+ 1m 1.063a
# 860 x 140 = 1000(Em)
MPLUS_REGULAR_FONT = "mplus-1m-regular.ttf"
MPLUS_BOLD_FONT = "mplus-1m-bold.ttf"
MPLUS_DESCENT = 140

# 幅は日本語に合わせる
LATIN_WIDTH = 1000  # 未使用
JP_WIDTH = 1000
WIDTH = JP_WIDTH

# Ubuntu mono と やさしさゴシックボールドV2 で同じ
ASCENT = 800
DESCENT = 200
HEIGHT = ASCENT + DESCENT

LATIN_ASCENT = 800
LATIN_DESCENT = 200  # 未使用
JP_ASCENT = 880
JP_DESCENT = 120

# Italic時の傾き
SKEW_MAT = psMat.skew(0.25)
# 罫線素片
RULED_LINES = list(range(0x2500, 0x257F + 1))
# ブロック要素 ▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐░▒▓▔▕▖▗▘▙▚▛▜▝▞▟
BLOCK_ELEMENTS = list(range(0x2580, 0x259F + 1))

ROMAN_NUMERALS = list(range(0x2160, 0x2188 + 1))  # ローマ数字
ARROWS = list(range(0x2190, 0x21FF + 1))  # 矢印
SPECIAL_PUNCTUATION = [0x2010, 0x2015]  # ‐ ― FIXME: これらは試験的に導入中
# 半角用に描かれているウォン記号と制御図記号はM+の輪郭を使う。
MPLUS_NARROW_OUTLINES = {0x20A9, *range(0x2400, 0x2427)}
SHADE_GLYPHS = {0x2591, 0x2592, 0x2593}
COMBINING_KANA_MARKS = {0x3099, 0x309A}
# 上付き結合記号の前で点を外す字形 (i → ı, j → ȷ)
DOTLESS_FORMS = {0x0069: 0x0131, 0x006A: 0x0237}

FULL_BLOCK_CODE = 0x2588
# 半角カナとかの半角幅のやつ
HALFWIDTH_CJK_KANA = list(range(0xFF61, 0xFF9F + 1))
# 全角文字
FULLWIDTH_HIRAGANA_KATAKANA = list(range(0x3040, 0x30FF + 1))
FULLWIDTH_CJK_UNIFIED = list(range(0x4E00, 0x9FCF + 1))
FULLWIDTH_CJK_COMPATI = list(range(0xF900, 0xFAFF + 1))
FULLWIDTH_CJK_UNIFIED_EX_A = list(range(0x3400, 0x4DBF + 1))
FULLWIDTH_CJK_UNIFIED_EX_B = list(range(0x20000, 0x2A6DF + 1))
FULLWIDTH_CJK_UNIFIED_EX_C = list(range(0x2A700, 0x2B73F + 1))
FULLWIDTH_CJK_UNIFIED_EX_D = list(range(0x2B740, 0x2B81F + 1))
FULLWIDTH_CJK_COMPATI_SUPP = list(range(0x2F800, 0x2FA1F + 1))

FULLWIDTH_CODES = (
    FULLWIDTH_HIRAGANA_KATAKANA
    + FULLWIDTH_CJK_UNIFIED
    + FULLWIDTH_CJK_COMPATI
    + FULLWIDTH_CJK_UNIFIED_EX_A
    + FULLWIDTH_CJK_UNIFIED_EX_B
    + FULLWIDTH_CJK_UNIFIED_EX_C
    + FULLWIDTH_CJK_UNIFIED_EX_D
    + FULLWIDTH_CJK_COMPATI_SUPP
)

# 日本語フォントの縮小率
JP_A_RAT = LATIN_ASCENT / JP_ASCENT  # 高さの比でいいはず
JP_REDUCTION_MAT = psMat.scale(JP_A_RAT, JP_A_RAT)

# NOTE: JP_REDUCTION_FIX系は未使用にした
# descent位置がずれてもいいなら下記を使う。
JP_REDUCTION_FIX_MAT = psMat.translate(
    WIDTH * (1 - JP_A_RAT) / 2, -WIDTH * (1 - JP_A_RAT) / 2
)
# descent位置が合わないと気持ち悪い場合は下記を使う。
JP_REDUCTION_FIX_MAT_NOHEIGHT = psMat.translate(WIDTH * (1 - JP_A_RAT) / 2, 0.0)

SOURCE = "./sourceFonts"
DIST = "./dist"
JP_TEMP = "./tmp/jp_font.sfd"
EN_TEMP = "./tmp/en_font.sfd"
with open("./LICENSE.txt", encoding="utf-8") as _license_file:
    LICENSE = _license_file.read()
with open("./COPYRIGHT.txt", encoding="utf-8") as _copyright_file:
    COPYRIGHT = _copyright_file.read()

# 出力をデコるときに使う文字
DECO_CHAR = "-"

DEBUG = False

# 設定可能な罫線描画モードを実装予定
BOX_DRAWING_MODE = "console_optimized"  # default (現在仕様)
# BOX_DRAWING_MODE = "mplus_compatible"  # M+完全準拠
# BOX_DRAWING_MODE = "user_defined"      # カスタム設定

fonts = [
    {
        "family": FONTNAME,
        "name": FONTNAME + "-Regular",
        "filename": FONTNAME + "-Regular.ttf",
        "weight": 400,  # レギュラー体の標準値らしい
        "weight_name": "Regular",
        "style_name": "Regular",
        "latin": LATIN_REGULAR_FONT,
        "japanese": JAPANESE_REGULAR_FONT,
        "mplus": MPLUS_REGULAR_FONT,
        "latin_weight_reduce": 0,  # 0以外ではテストしていない
        "japanese_weight_add": 0,  # 0以外の場合、めちゃくちゃ時間かかる
        "italic": False,  # trueは変になる
    },
    {
        "family": FONTNAME,
        "name": FONTNAME + "-Bold",
        "filename": FONTNAME + "-Bold.ttf",
        "weight": 700,  # ボールド体の標準値らしい
        "weight_name": "Bold",
        "style_name": "Bold",
        "latin": LATIN_BOLD_FONT,
        "japanese": JAPANESE_BOLD_FONT,
        "mplus": MPLUS_BOLD_FONT,
        "latin_weight_reduce": 0,  # 0以外ではテストしていない
        "japanese_weight_add": 0,  # 0以外の場合、めちゃくちゃ時間かかる
        "italic": False,  # trueは変になる
    },
]


def deco_print(_str):
    print()
    print(DECO_CHAR * len(_str))
    print(_str)
    print(DECO_CHAR * len(_str))


def timestamped_log(message):
    """タイムスタンプ付きログ"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now} {message}")


def improved_width_adjustment(glyph, target_width):
    """元の手法を拡張した安全な幅調整（ベアリング比率保持）"""
    if glyph.width != target_width:
        # 現在のベアリング比率を保持
        total_bearing = glyph.left_side_bearing + glyph.right_side_bearing
        if total_bearing > 0:
            left_ratio = glyph.left_side_bearing / total_bearing
        else:
            # ベアリングがゼロまたは負の場合は均等分散
            left_ratio = 0.5

        # 幅差分をベアリングに配分
        width_diff = target_width - glyph.width
        new_total_bearing = total_bearing + width_diff

        # 新しいベアリング値を計算（整数丸め）
        new_left_bearing = int(new_total_bearing * left_ratio)
        new_right_bearing = int(new_total_bearing * (1 - left_ratio))

        # メトリクスを直接設定（transformは使用しない）
        glyph.left_side_bearing = new_left_bearing
        glyph.right_side_bearing = new_right_bearing
        glyph.width = target_width

    return glyph


def unicode_mappings(glyph):
    if glyph.unicode >= 0:
        yield glyph.unicode
    for codepoint, selector, _ in glyph.altuni or ():
        if selector == -1:
            yield codepoint


def read_mplus_widths():
    reference = fontforge.open(SOURCE + "/" + MPLUS_REGULAR_FONT)
    half = reference.em // 2
    widths = {
        codepoint: glyph.width // half
        for glyph in reference.glyphs()
        if glyph.isWorthOutputting and glyph.width in (half, 2 * half)
        for codepoint in unicode_mappings(glyph)
    }
    reference.close()
    return widths


def fit_grid_outline(glyph, codepoints, target_width, x_min, x_max):
    """Horizontally fit a changed outline into its cell, keeping its height.

    ``codepoints`` holds every Unicode mapping of the glyph, including altuni,
    so a glyph selected through a secondary mapping gets the same treatment.
    """
    old_width = glyph.width
    if target_width == 0:
        # Put combining marks over the preceding cell when no positioning
        # lookup applies. Kana voicing marks belong near the upper right.
        offset = -old_width
        if any(cp in COMBINING_KANA_MARKS for cp in codepoints):
            offset += WIDTH // 4
        elif any(0x035C <= cp <= 0x0362 for cp in codepoints):
            # Double diacritics are centered between the two base letters.
            offset += old_width // 2
        glyph.transform(psMat.translate(offset, 0))
    elif any(cp in SHADE_GLYPHS for cp in codepoints):
        glyph.transform(psMat.scale(target_width / old_width, 1))
    elif target_width > old_width:
        glyph.transform(psMat.translate((target_width - old_width) / 2, 0))
    elif x_min != x_max:
        # Leave room between narrowed glyphs without shrinking ones that fit.
        scale = min(1, (target_width * 0.92) / (x_max - x_min))
        offset = (target_width - scale * (x_min + x_max)) / 2
        glyph.transform((scale, 0, 0, 1, offset, 0))
    glyph.width = target_width


def apply_width_policy(font, mplus_cells, latin_codepoints):
    pending = []
    for glyph in font.glyphs():
        if not glyph.isWorthOutputting:
            continue
        codepoints = tuple(unicode_mappings(glyph))
        widths = {expected_cells(codepoint, mplus_cells) for codepoint in codepoints}
        widths.discard(None)
        if not widths:
            continue
        if len(widths) > 1:
            raise ValueError(
                f"Conflicting advances for {glyph.glyphname}: {codepoints}"
            )

        target = widths.pop() * (WIDTH // 2)
        x_min, _, x_max, _ = glyph.boundingBox()
        # Existing Ubuntu Mono overhang is part of its typography. Correct
        # halfwidth Japanese-source glyphs that would paint into a neighbor.
        overhang = (
            target == WIDTH // 2
            and not any(codepoint in latin_codepoints for codepoint in codepoints)
            and (x_min < 0 or x_max > target)
        )
        if glyph.width != target or overhang:
            pending.append((glyph, codepoints, target, x_min, x_max))

    # Freeze the old component outlines before changing any referenced glyphs.
    for glyph, *_ in pending:
        glyph.unlinkThisGlyph()
        glyph.unlinkRef()
    for glyph, codepoints, target, x_min, x_max in pending:
        fit_grid_outline(glyph, codepoints, target, x_min, x_max)


def match_angle_bracket_outlines(font):
    # U+2329/U+232A are canonically equivalent to the CJK brackets.
    # Keep their opening/closing side bearings as well as their outlines.
    pairs = {0x2329: 0x3008, 0x232A: 0x3009}
    codes = pairs.keys() | pairs.values()
    brackets = {
        cp: glyph
        for glyph in font.glyphs()
        for cp in unicode_mappings(glyph)
        if cp in codes
    }
    for legacy, canonical in pairs.items():
        glyph, source = brackets.get(legacy), brackets.get(canonical)
        if glyph is None or source is None or glyph.glyphname == source.glyphname:
            continue
        glyph.unlinkThisGlyph()
        glyph.foreground = source.foreground
        glyph.references = source.references
        glyph.width = source.width


def position_latin_above_marks(font):
    """Attach an above mark to a Latin letter or an earlier above mark."""
    base_class = "Latin above base"
    stack_class = "Latin above stack"
    scripts = (("latn", ("dflt",)),)
    font.addLookup(base_class, "gpos_mark2base", (), (("mark", scripts),))
    font.addLookup(stack_class, "gpos_mark2mark", (), (("mkmk", scripts),), base_class)
    for name in (base_class, stack_class):
        subtable = name + " anchors"
        font.addLookupSubtable(name, subtable)
        font.addAnchorClass(subtable, name)

    gap = 50
    above_marks = []
    for glyph in font.glyphs():
        if glyph.unicode < 0 or not glyph.isWorthOutputting:
            continue
        character = chr(glyph.unicode)
        if glyph.width == 0 and unicodedata.combining(character) == 230:
            x_min, y_min, x_max, y_max = glyph.boundingBox()
            center = round((x_min + x_max) / 2)
            glyph.addAnchorPoint(base_class, "mark", center, round(y_min))
            glyph.addAnchorPoint(stack_class, "mark", center, round(y_min))
            glyph.addAnchorPoint(stack_class, "basemark", center, round(y_max) + gap)
            above_marks.append(glyph.glyphname)
        elif (
            glyph.width == WIDTH // 2
            and unicodedata.category(character).startswith("L")
            and unicodedata.name(character, "").startswith("LATIN ")
        ):
            x_min, _, x_max, y_max = glyph.boundingBox()
            center = round((x_min + x_max) / 2)
            glyph.addAnchorPoint(
                base_class, "base", center, max(540, round(y_max) + gap)
            )

    use_dotless_before_above_marks(font, above_marks, scripts)


def use_dotless_before_above_marks(font, above_marks, scripts):
    """Replace i/j with their dotless forms before an above mark (ccmp).

    The base anchor of a dotted letter sits above its dot, so the mark would
    otherwise be stacked on top of the dot instead of replacing it.
    """
    glyphs = {
        glyph.unicode: glyph
        for glyph in font.glyphs()
        if glyph.unicode in DOTLESS_FORMS.keys() | DOTLESS_FORMS.values()
        and glyph.isWorthOutputting
    }
    pairs = [
        (glyphs[dotted], glyphs[dotless])
        for dotted, dotless in DOTLESS_FORMS.items()
        if dotted in glyphs and dotless in glyphs
    ]
    if not pairs or not above_marks:
        return

    single = "Dotless before above mark"
    font.addLookup(single, "gsub_single", (), ())
    font.addLookupSubtable(single, single + " subtable")
    for dotted, dotless in pairs:
        dotted.addPosSub(single + " subtable", dotless.glyphname)

    context = "Dotless context"
    font.addLookup(context, "gsub_contextchain", (), (("ccmp", scripts),))
    rule = "| [{}] @<{}> | [{}]".format(
        " ".join(dotted.glyphname for dotted, _ in pairs), single, " ".join(above_marks)
    )
    font.addContextualSubtable(context, context + " subtable", "coverage", rule)


def indent_print(_str):
    print()
    print("++ " + _str)


def print_pdf(_font, _path):
    fontforge.printSetup("pdf-file")
    _font.printSample("fontdisplay", 18, "", _path)


def check_files():
    err = 0
    for f in fonts:
        for key in ("latin", "japanese", "mplus"):
            path = SOURCE + "/" + f.get(key)
            if not os.path.isfile(path):
                print(f"{path} not exists.")
                err = 1

    # xAvgCharWidthの修正にfontToolsのttxを使う。フォント生成後に失敗しないよう先に確認する。
    # 古いシムなど、見つかっても動かないttxがあるので実際に起動してみる。
    ttx = shutil.which("ttx")
    if (
        ttx is None
        or subprocess.run(
            [ttx, "--version"], capture_output=True, check=False
        ).returncode
        != 0
    ):
        print(f"ttx (fontTools) が見つからないか、実行できません: {ttx}")
        print("uv sync のあと、uv run 経由で実行してください:")
        print("  uv run <fontforgeのパス> -lang=py -script ./utatane.py")
        err = 1

    if err > 0:
        sys.exit(err)


def set_os2_values(_font, _info):
    _font.os2_weight = _info.get("weight")
    _font.os2_width = 5
    _font.os2_fstype = 0
    _font.os2_vendor = "nv-h"  # 好きな4文字
    _font.os2_version = 4

    # os2_stylemapの明示的設定
    style_name = _info.get("style_name")
    if style_name == "Regular":
        _font.os2_stylemap = 64  # Regular
    elif style_name == "Bold":
        _font.os2_stylemap = 32  # Bold
    elif style_name == "Italic":
        _font.os2_stylemap = 1  # Italic
    elif style_name == "Bold Italic":
        _font.os2_stylemap = 33  # Bold + Italic
    _font.os2_winascent = ASCENT
    _font.os2_winascent_add = False
    _font.os2_windescent = DESCENT
    _font.os2_windescent_add = False

    _font.os2_typoascent = ASCENT
    _font.os2_typoascent_add = False
    _font.os2_typodescent = -DESCENT
    _font.os2_typodescent_add = False
    _font.os2_typolinegap = 0

    _font.hhea_ascent = ASCENT
    _font.hhea_ascent_add = False
    _font.hhea_descent = -DESCENT
    _font.hhea_descent_add = False
    _font.hhea_linegap = 0

    """ panose definitions
    refer: [The 'OS/2' table](https://developer.apple.com/fonts/TrueType-Reference-Manual/RM06/Chap6OS2.html)

    * bFamilyType
        - 2:  Text and Display
    * bSerifStyle
        - 11: Normal Sans
    * bWeight
        - 5:  Book
        - 8:  Bold
    * bProportion
        - 9:  Monospaced
    * bContrast
        - 2:  None
    * bStrokeVariation
        - 2:  Gradual/Diagonal
    * bArmStyle
        - 3:  Straight Arms/Wedge
    * bLetterform
        - 2:  Normal/Contact
    * bMidline
        - 2:  Standard/Trimmed
    * bXHeight
        - 7:  Ducking/Large
    """
    style_name = _info.get("style_name")
    if style_name == "Bold":
        _font.os2_panose = (2, 11, 8, 9, 2, 2, 3, 2, 2, 7)
    else:
        _font.os2_panose = (2, 11, 5, 9, 2, 2, 3, 2, 2, 7)

    return _font


def vertical_line_to_broken_bar(_font):
    _font.selection.select(0x00A6)  # ¦ BROKEN BAR
    _font.copy()
    _font.selection.select(0x007C)  # | VERTICAL LINE
    _font.paste()
    return _font


def emdash_to_broken_dash(_font):
    # FIXME: 点になる
    _font.selection.select(0x006C)  # l LATIN SMALL LETTER L
    _font.copy()
    _font.selection.select(0x2014)  # — EM DASH
    _font.pasteInto()
    _font.intersect()

    return _font


def zenkaku_space(_font):
    _font.selection.select(0x2610)  # ☐ ballot box
    _font.copy()
    _font.selection.select(0x3000)  # 　 IDEOGRAPHIC SPACE
    _font.paste()
    _font.selection.select(0x271A)  # ✚ HEAVY GREEK CROSS
    _font.copy()
    _font.selection.select(0x3000)  # 　 IDEOGRAPHIC SPACE
    _font.pasteInto()
    _font.intersect()

    return _font


def add_smalltriangle(_font):
    _font.selection.select(0x25BC)  # ▼ BLACK DOWN-POINTING TRIANGLE
    _font.copy()
    _font.selection.select(0x25BE)  # ▾ BLACK DOWN-POINTING SMALL TRIANGLE
    _font.paste()
    _font.transform(psMat.compose(psMat.scale(0.64), psMat.translate(0, 68)))
    _font.copy()
    _font.selection.select(0x25B8)  # ▸ BLACK RIGHT-POINTING SMALL TRIANGLE
    _font.paste()
    _font.transform(psMat.rotate(math.radians(90)))

    for g in _font.glyphs():
        if g.encoding == 0x25BE or g.encoding == 0x25B8:
            g.width = int(WIDTH // 2)
            g.left_side_bearing = g.right_side_bearing = int(
                (g.left_side_bearing + g.right_side_bearing) / 2
            )
            g.width = int(WIDTH // 2)

    return _font


def set_height(_font):
    _font.em = HEIGHT
    _font.ascent = ASCENT
    _font.descent = DESCENT
    return _font


def post_process(_font):
    """座標値などをいい感じに処理する。
    removeOverlap()を実行しないと文字が消えることがある。
    refer: http://www.rs.tus.ac.jp/yyusa/ricty/ricty_generator.sh
    """
    indent_print("post processing ... (This may take a few minutes.)")

    _font.selection.all()
    _font.removeOverlap()
    _font.round()
    _font.autoHint()
    _font.autoInstr()
    _font.selection.none()

    return _font


def modify_and_save_latin(_f, _savepath):
    deco_print("modify latin : {}".format(_f.get("latin")))

    latin_font = fontforge.open(SOURCE + "/{}".format(_f.get("latin")))
    latin_font = set_height(latin_font)

    for g in latin_font.glyphs():
        if not g.isWorthOutputting:
            # 不要っぽいやつを削除
            latin_font.selection.select(g)
            latin_font.clear()
            continue

        if _f.get("italic"):
            # FIXME: 動作確認未
            g.transform(SKEW_MAT)

        if _f.get("latin_weight_reduce") != 0:
            # FIXME: 動作確認未
            # g.changeWeight(_f.get('latin_weight_reduce'), 'auto', 0, 0, 'auto')
            g.stroke(
                "circular",
                _f.get("latin_weight_reduce"),
                "butt",
                "round",
                "removeexternal",
            )

    codepoints = {
        codepoint
        for glyph in latin_font.glyphs()
        if glyph.isWorthOutputting
        for codepoint in unicode_mappings(glyph)
    }
    cap_height = latin_font.capHeight
    latin_font.save(_savepath)
    latin_font.close()
    return codepoints, cap_height


def modify_and_save_jp(_f, _savepath, _latin_cap_height):
    deco_print("modify jp : {}".format(_f.get("japanese")))

    jp_font = fontforge.open(SOURCE + "/{}".format(_f.get("japanese")))

    # 日本語フォントをいじる処理は、マージ後に行うと機能しない
    # 設定が足りていないかもしれないが詳細不明。
    jp_font = zenkaku_space(jp_font)
    jp_font = add_smalltriangle(jp_font)
    jp_font = set_height(jp_font)

    mplus_font = fontforge.open(SOURCE + "/{}".format(_f.get("mplus")))
    # 半角用のM+輪郭は欧文の大文字高さに合わせ、ベースラインとセル中央を基準に縮小する
    narrow_scale = _latin_cap_height / mplus_font.capHeight
    narrow_mat = psMat.compose(
        psMat.compose(psMat.translate(-WIDTH // 4, 0), psMat.scale(narrow_scale)),
        psMat.translate(WIDTH // 4, 0),
    )
    mplus_narrow_pasted = set()

    for g in mplus_font.glyphs():
        # 罫線はM+へ置き換えて半角にする(コンソール表示などで半角を期待されることが多かった)
        if g.encoding in RULED_LINES:
            # いったん半角幅中央が中心になるよう平行移動(左に250移動)
            g.transform(psMat.translate(-WIDTH // 4, 0))
            # `█` FULL BLOCK との積にすることで半角化
            mplus_font.selection.select(FULL_BLOCK_CODE)
            mplus_font.copy()
            jp_font.selection.select(g.encoding)
            jp_font.paste()
            mplus_font.selection.select(g.encoding)
            mplus_font.copy()
            jp_font.selection.select(g.encoding)
            jp_font.pasteInto()
            jp_font.intersect()
            # Utatane座標系に合わせて下移動
            jp_font[g.encoding].transform(
                psMat.translate(0, -(DESCENT - MPLUS_DESCENT))
            )

        elif (
            g.encoding in BLOCK_ELEMENTS
            or g.encoding in ROMAN_NUMERALS
            or g.encoding in ARROWS
            or g.encoding in SPECIAL_PUNCTUATION
        ):
            # ブロック要素などはM+へ置き換えて幅もそのまま
            mplus_font.selection.select(g.encoding)
            mplus_font.copy()
            jp_font.selection.select(g.encoding)
            jp_font.paste()
            # Utatane座標系に合わせて下移動
            jp_font[g.encoding].transform(
                psMat.translate(0, -(DESCENT - MPLUS_DESCENT))
            )

        elif g.encoding in MPLUS_NARROW_OUTLINES and g.encoding in jp_font:
            # ベースラインに乗る字形なので下移動はしない
            mplus_font.selection.select(g.encoding)
            mplus_font.copy()
            jp_font.selection.select(g.encoding)
            jp_font.paste()
            jp_font[g.encoding].transform(narrow_mat)
            # transformは送り幅も動かすので、セル中央に置いたまま半角幅へ戻す
            jp_font[g.encoding].width = WIDTH // 2
            mplus_narrow_pasted.add(g.encoding)

    mplus_font.close()

    for g in jp_font.glyphs():
        if not g.isWorthOutputting:
            # 不要っぽいやつは消しちゃう
            jp_font.selection.select(g)
            jp_font.clear()
            continue

        # 太さ調整
        if _f.get("japanese_weight_add") != 0:
            g.changeWeight(_f.get("japanese_weight_add"), "auto", 0, 0, "auto")
            # g.stroke("caligraphic", _f.get('japanese_weight_add'), _f.get('japanese_weight_add'), 45, 'removeinternal')
            # g.stroke("circular", _f.get('japanese_weight_add'), 'butt', 'round', 'removeinternal')

        # 個別の拡大縮小処理
        width = None
        if g.encoding in HALFWIDTH_CJK_KANA:
            # 半角カナは半角へ
            g.transform(JP_REDUCTION_MAT)  # いい塩梅で縮小
            width = int(WIDTH // 2)
        elif g.encoding in FULLWIDTH_CODES:
            # 全角文字は全角へ
            g.transform(JP_REDUCTION_MAT)  # いい塩梅で縮小
            width = WIDTH
        elif g.encoding in RULED_LINES:
            width = int(WIDTH // 2)
        elif g.encoding in mplus_narrow_pasted:
            # M+から貼った半角字形は縮小済み
            width = int(WIDTH // 2)
        elif g.encoding in BLOCK_ELEMENTS:
            # NOTE: M+で全角幅だったやつをいったん全角にしている
            #       ░ LIGHT SHADE, ▒ MEDIUM SHADE, ▓ DARK SHADE
            if g.encoding in [0x2591, 0x2592, 0x2593]:
                width = int(WIDTH)
            else:
                width = int(WIDTH // 2)
        elif (
            g.encoding in ROMAN_NUMERALS
            or g.encoding in ARROWS
            or g.encoding in SPECIAL_PUNCTUATION
        ):
            # ローマ数字は全角維持
            g.transform(JP_REDUCTION_MAT)  # いい塩梅で縮小
            width = WIDTH
        else:
            g.transform(JP_REDUCTION_MAT)  # いい塩梅で縮小
            # 元の輪郭配置と参照グリフ用の幅。Unicodeの既定送りは合成後に確定する。
            if g.width > WIDTH * 0.7:
                width = WIDTH
            else:
                width = int(WIDTH // 2)

        # 幅の微調整(微妙に幅が違うやつがいるので)
        if width is not None:
            g = improved_width_adjustment(g, width)

        if _f.get("italic"):
            # FIXME: 動作確認未
            g.transform(SKEW_MAT)

    jp_font.save(_savepath)
    jp_font.close()


def set_sfnt_names(_font, _f):
    _font.appendSFNTName("English (US)", "Copyright", COPYRIGHT)
    _font.appendSFNTName("English (US)", "Family", _f.get("family"))
    _font.appendSFNTName("English (US)", "SubFamily", _f.get("style_name"))
    _font.appendSFNTName("English (US)", "Fullname", _f.get("name"))
    _font.appendSFNTName("English (US)", "Version", "Version " + VERSION)
    _font.appendSFNTName("English (US)", "PostScriptName", _f.get("name"))
    _font.appendSFNTName("English (US)", "Preferred Family", _f.get("family"))
    _font.appendSFNTName("English (US)", "Preferred Styles", _f.get("style_name"))
    _font.appendSFNTName("Japanese", "Preferred Family", _f.get("family"))
    _font.appendSFNTName("Japanese", "Preferred Styles", _f.get("style_name"))

    return _font


def set_gasp_table(_font):
    _font.gasp_version = 1
    _font.gasp = (
        (8, ("antialias",)),
        (
            13,
            (
                "antialias",
                "symmetric-smoothing",
            ),
        ),
        (
            65535,
            (
                "gridfit",
                "antialias",
                "symmetric-smoothing",
                "gridfit+smoothing",
            ),
        ),
    )

    return _font


def run_ttx(*args):
    """ttxを実行し、失敗したらその場で止める"""
    subprocess.run([shutil.which("ttx"), *args], check=True)


def fix_xAvgCharWidth(_src_ttf, _dst_ttf):
    """AvgCharWidthがおかしくなるので、元のフォントの値に書き換える
    require: fontToolsのttx (`uv sync` でインストールし、`uv run` 経由で実行する)

    refer: https://web.archive.org/web/20240205173549/https://osdn.net/projects/mplus-fonts/lists/archive/dev/2011-July/000619.html
           (OSDN終了のためWayback Machineのアーカイブ)
    """
    import xml.etree.ElementTree as ET

    deco_print(f"fix xAvgCharWidth: {_src_ttf} to {_dst_ttf}")

    # 元のフォントからxAvgCharWidth読み出し
    src_root, _ = os.path.splitext(_src_ttf)
    run_ttx("-f", "-t", "OS/2", _src_ttf)
    src_tree = ET.parse(src_root + ".ttx")
    src_AvgCharWidth = src_tree.find("OS_2").find("xAvgCharWidth").get("value")

    # 作成したフォントへxAvgCharWidthを設定
    dst_root, _ = os.path.splitext(_dst_ttf)
    run_ttx("-f", "-t", "OS/2", _dst_ttf)
    dst_tree = ET.parse(dst_root + ".ttx")
    dst_tree.find("OS_2").find("xAvgCharWidth").set("value", f"{src_AvgCharWidth}")
    dst_tree.write(dst_root + ".ttx", "utf-8", True)

    # 変更したやつを反映
    run_ttx("-f", "-m", _dst_ttf, dst_root + ".ttx")

    # 後片付け
    if not DEBUG:
        os.remove(src_root + ".ttx")
    if not DEBUG:
        os.remove(dst_root + ".ttx")


def build_font(_f, mplus_cells):

    latin_codepoints, latin_cap_height = modify_and_save_latin(_f, EN_TEMP)
    modify_and_save_jp(_f, JP_TEMP, latin_cap_height)

    deco_print(
        "merge modified {} and modified {}".format(_f.get("latin"), _f.get("japanese"))
    )

    target_font = fontforge.font()
    target_font = set_height(target_font)

    target_font.upos = (
        -115
    )  # アンダーライン`_`と、装飾のアンダーラインの位置が同じになるように調整
    target_font.fontname = _f.get("family")
    target_font.familyname = _f.get("family")
    target_font.fullname = _f.get("name")
    target_font.weight = _f.get("weight_name")

    target_font = set_os2_values(target_font, _f)
    target_font = set_sfnt_names(target_font, _f)
    target_font = set_gasp_table(target_font)

    target_font.mergeFonts(EN_TEMP)
    if not DEBUG:
        os.remove(EN_TEMP)
    target_font.mergeFonts(JP_TEMP)
    if not DEBUG:
        os.remove(JP_TEMP)

    target_font = vertical_line_to_broken_bar(target_font)
    # target_font = emdash_to_broken_dash(target_font) # あまり必要性を感じないので削除
    # 全角をいじるのはマージ前に行う

    apply_width_policy(target_font, mplus_cells, latin_codepoints)
    match_angle_bracket_outlines(target_font)
    target_font = post_process(target_font)
    position_latin_above_marks(target_font)

    fontpath = DIST + "/{}".format(_f.get("filename"))
    if DEBUG:
        print_pdf(target_font, fontpath + ".pdf")

    target_font.generate(fontpath)
    target_font.close()

    fix_xAvgCharWidth(SOURCE + "/{}".format(_f.get("japanese")), fontpath)

    deco_print("Generate {} completed.".format(_f.get("name")))


def main():
    check_files()
    deco_print("Generating " + FONTNAME + " started.")

    mplus_cells = read_mplus_widths()
    for _f in fonts:
        build_font(_f, mplus_cells)

    deco_print("Succeeded!!")


if __name__ == "__main__":
    main()
