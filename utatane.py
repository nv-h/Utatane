#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
# from __future__ import unicode_literals # Windowsで文字化けするのでコメントアウト

import fontforge
import psMat
import os
import sys
import math

VERSION = '1.2.1'
FONTNAME = 'Utatane'

# Ubuntu Mono (罫線などを削除してあるものを使う)
# 800 x 200 = 1000(Em)
# Win(Ascent, Descent)=(-170, -183)
# hhea(height, width)=(-170, 183)
LATIN_REGULAR_FONT = 'UbuntuMono-Regular_modify.ttf'
LATIN_BOLD_FONT = 'UbuntuMono-Bold_modify.ttf'

# やさしさゴシックボールドV2
# レギュラー版は手動で embold -30 して、一部フォントを調整したもの
# 880 x 120 = 1000(Em)
JAPANESE_REGULAR_FONT = 'YasashisaGothicBold-V2_-30.ttf'
JAPANESE_BOLD_FONT = 'YasashisaGothicBold-V2.ttf'
# M+ 1m 1.063a
# 860 x 140 = 1000(Em)
MPLUS_REGULAR_FONT = 'mplus-1m-regular.ttf'
MPLUS_BOLD_FONT = 'mplus-1m-bold.ttf'

# 幅は日本語に合わせる
LATIN_WIDTH = 1000 # 未使用
JP_WIDTH = 1000
WIDTH = JP_WIDTH

# Ubuntu mono と やさしさゴシックボールドV2 で同じ
ASCENT = 800
DESCENT = 200
HEIGHT = ASCENT + DESCENT

LATIN_ASCENT = 800
LATIN_DESCENT = 200 # 未使用
JP_ASCENT = 880
JP_DESCENT = 120

# Italic時の傾き
SKEW_MAT = psMat.skew(0.25)
# 罫線素片
RULED_LINES = list(range(0x2500, 0x257F+1))
# ブロック要素 ▀▁▂▃▄▅▆▇█▉▊▋▌▍▎▏▐░▒▓▔▕▖▗▘▙▚▛▜▝▞▟
BLOCK_ELEMENTS = list(range(0x2580, 0x259F+1))
FULL_BLOCK_CODE = 0x2588
# 半角カナとかの半角幅のやつ
HALFWIDTH_CJK_KANA = list(range(0xFF61, 0xFF9F+1))
# 全角文字
FULLWIDTH_HIRAGANA_KATAKANA = list(range(0x3040, 0x30FF+1))
FULLWIDTH_CJK_UNIFIED = list(range(0x4E00, 0x9FCF+1))
FULLWIDTH_CJK_COMPATI = list(range(0xF900, 0xFAFF+1))
FULLWIDTH_CJK_UNIFIED_EX_A = list(range(0x3400, 0x4DBF+1))
FULLWIDTH_CJK_UNIFIED_EX_B = list(range(0x20000, 0x2A6DF+1))
FULLWIDTH_CJK_UNIFIED_EX_C = list(range(0x2A700, 0x2B73F+1))
FULLWIDTH_CJK_UNIFIED_EX_D = list(range(0x2B740, 0x2B81F+1))
FULLWIDTH_CJK_COMPATI_SUPP = list(range(0x2F800, 0x2FA1F+1))

FULLWIDTH_CODES = FULLWIDTH_HIRAGANA_KATAKANA + \
    FULLWIDTH_CJK_UNIFIED + \
    FULLWIDTH_CJK_COMPATI + \
    FULLWIDTH_CJK_UNIFIED_EX_A + \
    FULLWIDTH_CJK_UNIFIED_EX_B + \
    FULLWIDTH_CJK_UNIFIED_EX_C + \
    FULLWIDTH_CJK_UNIFIED_EX_D + \
    FULLWIDTH_CJK_COMPATI_SUPP

# 日本語フォントの縮小率
JP_A_RAT = (LATIN_ASCENT/JP_ASCENT) # 高さの比でいいはず
JP_REDUCTION_MAT = psMat.scale(JP_A_RAT, JP_A_RAT)
# descent位置がずれてもいいなら下記を使う。
JP_REDUCTION_FIX_MAT = psMat.translate(WIDTH*(1-JP_A_RAT)/2, -WIDTH*(1-JP_A_RAT)/2)
# descent位置が合わないと気持ち悪いので下記を使う。
JP_REDUCTION_FIX_MAT_NOHEIGHT = psMat.translate(WIDTH*(1-JP_A_RAT)/2, 0.0)

SOURCE = './sourceFonts'
DIST = './dist'
JP_TEMP = './tmp/jp_font.sfd'
EN_TEMP = './tmp/en_font.sfd'
LICENSE = open('./LICENSE.txt', encoding='utf-8').read()
COPYRIGHT = open('./COPYRIGHT.txt', encoding='utf-8').read()

# 出力をデコるときに使う文字
DECO_CHAR = '-'

DEBUG = False

fonts = [
    {
        'family': FONTNAME,
        'name': FONTNAME + '-Regular',
        'filename': FONTNAME + '-Regular.ttf',
        'weight': 400, # レギュラー体の標準値らしい
        'weight_name': 'Regular',
        'style_name': 'Regular',
        'latin': LATIN_REGULAR_FONT,
        'japanese': JAPANESE_REGULAR_FONT,
        'mplus': MPLUS_REGULAR_FONT,
        'latin_weight_reduce': 0, # 0以外ではテストしていない
        'japanese_weight_add': 0, # 0以外の場合、めちゃくちゃ時間かかる
        'italic': False, # trueは変になる
    },
    {
        'family': FONTNAME,
        'name': FONTNAME + '-Bold',
        'filename': FONTNAME + '-Bold.ttf',
        'weight': 700, # ボールド体の標準値らしい
        'weight_name': 'Bold',
        'style_name': 'Bold',
        'latin': LATIN_BOLD_FONT,
        'japanese': JAPANESE_BOLD_FONT,
        'mplus': MPLUS_BOLD_FONT,
        'latin_weight_reduce': 0, # 0以外ではテストしていない
        'japanese_weight_add': 0, # 0以外の場合、めちゃくちゃ時間かかる
        'italic': False, # trueは変になる
    }
]

def deco_print(_str):
    print('')
    print(DECO_CHAR*len(_str))
    print(_str)
    print(DECO_CHAR*len(_str))


def indent_print(_str):
    print('')
    print('++ ' + _str)


def print_pdf(_font, _path):
    fontforge.printSetup('pdf-file')
    _font.printSample('fontdisplay', 18, '', _path)


def check_files():
    err = 0
    for f in fonts:
        if not os.path.isfile(SOURCE + '/{}'.format(f.get('latin'))):
            print('{} not exists.'.format(f))
            err = 1

        if not os.path.isfile(SOURCE + '/{}'.format(f.get('japanese'))):
            print('{} not exists.'.format(f))
            err = 1

        if not os.path.isfile(SOURCE + '/{}'.format(f.get('mplus'))):
            print('{} not exists.'.format(f))
            err = 1

    if err > 0:
        sys.exit(err)

def set_os2_values(_font, _info):
    _font.os2_weight = _info.get('weight')
    _font.os2_width = 5
    _font.os2_fstype = 0
    _font.os2_vendor = 'nv-h' # 好きな4文字
    _font.os2_version = 4
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
    style_name = _info.get('style_name')
    if style_name == 'Bold':
        _font.os2_panose = (2, 11, 8, 9, 2, 2, 3, 2, 2, 7)
    else:
        _font.os2_panose = (2, 11, 5, 9, 2, 2, 3, 2, 2, 7)

    return _font

def vertical_line_to_broken_bar(_font):
    _font.selection.select(0x00a6) # ¦ BROKEN BAR
    _font.copy()
    _font.selection.select(0x007c) # | VERTICAL LINE
    _font.paste()
    return _font

def emdash_to_broken_dash(_font):
    # FIXME: 点になる
    _font.selection.select(0x006c) # l LATIN SMALL LETTER L
    _font.copy()
    _font.selection.select(0x2014) # — EM DASH
    _font.pasteInto()
    _font.intersect()

    return _font

def zenkaku_space(_font):
    _font.selection.select(0x2610) # ☐ ballot box
    _font.copy()
    _font.selection.select(0x3000) # 　 IDEOGRAPHIC SPACE
    _font.paste()
    _font.selection.select(0x271a) # ✚ HEAVY GREEK CROSS
    _font.copy()
    _font.selection.select(0x3000) # 　 IDEOGRAPHIC SPACE
    _font.pasteInto()
    _font.intersect()

    return _font

def add_smalltriangle(_font):
    _font.selection.select(0x25bc) # ▼ BLACK DOWN-POINTING TRIANGLE
    _font.copy()
    _font.selection.select(0x25be) # ▾ BLACK DOWN-POINTING SMALL TRIANGLE
    _font.paste()
    _font.transform(psMat.compose(psMat.scale(0.64), psMat.translate(0, 68)))
    _font.copy()
    _font.selection.select(0x25b8) # ▸ BLACK RIGHT-POINTING SMALL TRIANGLE
    _font.paste()
    _font.transform(psMat.rotate(math.radians(90)))

    for g in _font.glyphs():
        if g.encoding == 0x25be or g.encoding == 0x25b8:
            g.width = int(WIDTH//2)
            g.left_side_bearing = g.right_side_bearing = int((g.left_side_bearing + g.right_side_bearing)/2)
            g.width = int(WIDTH//2)

    return _font


def set_height(_font):
    _font.em = HEIGHT
    _font.ascent = ASCENT
    _font.descent = DESCENT
    return _font


def post_process(_font):
    '''座標値などをいい感じに処理する。
    removeOverlap()を実行しないと文字が消えることがある。
    refer: http://www.rs.tus.ac.jp/yyusa/ricty/ricty_generator.sh
    '''
    indent_print('post processing ... (This may take a few minutes.)')

    _font.selection.all()
    _font.removeOverlap()
    _font.round()
    _font.autoHint()
    _font.autoInstr()
    _font.selection.none()

    return _font


def modify_and_save_latin(_f, _savepath):
    deco_print('modify latin : {}'.format(_f.get('latin')))

    latin_font = fontforge.open(SOURCE + '/{}'.format(_f.get('latin')))
    latin_font = set_height(latin_font)

    for g in latin_font.glyphs():
        if (not g.isWorthOutputting):
            # 不要っぽいやつを削除
            latin_font.selection.select(g)
            latin_font.clear()
            break

        if _f.get('italic'):
            # FIXME: 動作確認未
            g.transform(SKEW_MAT)

        if _f.get('latin_weight_reduce') != 0:
            # FIXME: 動作確認未
            # g.changeWeight(_f.get('latin_weight_reduce'), 'auto', 0, 0, 'auto')
            g.stroke("circular", _f.get('latin_weight_reduce'), 'butt', 'round', 'removeexternal')


    latin_font.save(_savepath)
    latin_font.close()


def modify_and_save_jp(_f, _savepath):
    deco_print('modify jp : {}'.format(_f.get('japanese')))

    jp_font = fontforge.open(SOURCE + '/{}'.format(_f.get('japanese')))

    # 日本語フォントをいじる処理は、マージ後に行うと機能しない
    # 設定が足りていないかもしれないが詳細不明。
    jp_font = zenkaku_space(jp_font)
    jp_font = add_smalltriangle(jp_font)
    jp_font = set_height(jp_font)


    mplus_font = fontforge.open(SOURCE + '/{}'.format(_f.get('mplus')))

    for g in mplus_font.glyphs():
        # 罫線はM+へ置き換えて半角にする(コンソール表示などで半角を期待されることが多かった)
        if g.encoding in RULED_LINES:
            # いったん半角幅中央が中心になるよう平行移動(左に250移動)
            g.transform(psMat.translate(-WIDTH//4, 0))
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


        elif g.encoding in BLOCK_ELEMENTS:
            # ブロック要素などはM+へ置き換えて幅もそのまま
            mplus_font.selection.select(g.encoding)
            mplus_font.copy()
            jp_font.selection.select(g.encoding)
            jp_font.paste()

    mplus_font.close()


    for g in jp_font.glyphs():
        if not g.isWorthOutputting:
            # 不要っぽいやつは消しちゃう
            jp_font.selection.select(g)
            jp_font.clear()
            break

        # 太さ調整
        if _f.get('japanese_weight_add') != 0:
            g.changeWeight(_f.get('japanese_weight_add'), 'auto', 0, 0, 'auto')
            # g.stroke("caligraphic", _f.get('japanese_weight_add'), _f.get('japanese_weight_add'), 45, 'removeinternal')
            # g.stroke("circular", _f.get('japanese_weight_add'), 'butt', 'round', 'removeinternal')

        # 個別の拡大縮小処理
        width = None
        if g.encoding in HALFWIDTH_CJK_KANA:
            # 半角カナは半角へ
            g.transform(JP_REDUCTION_MAT)  # いい塩梅で縮小
            g.transform(JP_REDUCTION_FIX_MAT_NOHEIGHT)  # 縮小して左に寄った分と上に寄った分を復帰
            width = int(WIDTH//2)
        elif g.encoding in FULLWIDTH_CODES:
            # 全角文字は全角へ
            g.transform(JP_REDUCTION_MAT)  # いい塩梅で縮小
            g.transform(JP_REDUCTION_FIX_MAT_NOHEIGHT)  # 縮小して左に寄った分と上に寄った分を復帰
            width = WIDTH
        elif g.encoding in RULED_LINES:
            width = int(WIDTH//2)
        elif g.encoding in BLOCK_ELEMENTS:
            if g.encoding in [0x2591, 0x2592, 0x2593]:
                width = int(WIDTH)  # M+で全角幅だったやつ
            else:
                width = int(WIDTH//2)
        else:
            g.transform(JP_REDUCTION_MAT)  # いい塩梅で縮小
            g.transform(JP_REDUCTION_FIX_MAT_NOHEIGHT)  # 縮小して左に寄った分と上に寄った分を復帰
            if g.width > WIDTH * 0.7:
                width = WIDTH
            else:
                width = int(WIDTH//2)

        # 幅の微調整(微妙に幅が違うやつがいるので)
        if g.width != width:
            g.transform(psMat.translate((width - g.width)/2, 0))
            g.width = width

        if _f.get('italic'):
            # FIXME: 動作確認未
            g.transform(SKEW_MAT)

    jp_font.save(_savepath)
    jp_font.close()


def set_sfnt_names(_font, _f):
    _font.appendSFNTName('English (US)', 'Copyright',        COPYRIGHT)
    _font.appendSFNTName('English (US)', 'Family',           _f.get('family'))
    _font.appendSFNTName('English (US)', 'SubFamily',        _f.get('style_name'))
    _font.appendSFNTName('English (US)', 'Fullname',         _f.get('name'))
    _font.appendSFNTName('English (US)', 'Version',          'Version ' + VERSION)
    _font.appendSFNTName('English (US)', 'PostScriptName',   _f.get('name'))
    _font.appendSFNTName('English (US)', 'Preferred Family', _f.get('family'))
    _font.appendSFNTName('English (US)', 'Preferred Styles', _f.get('style_name'))
    _font.appendSFNTName('Japanese',     'Preferred Family', _f.get('family'))
    _font.appendSFNTName('Japanese',     'Preferred Styles', _f.get('style_name'))

    return _font


def set_gasp_table(_font):
    _font.gasp_version = 1
    _font.gasp = (
        (8, ('antialias',)),
        (13, ('antialias', 'symmetric-smoothing',)),
        (65535, ('gridfit', 'antialias', 'symmetric-smoothing', 'gridfit+smoothing',)),
    )

    return _font


def fix_xAvgCharWidth(_src_ttf, _dst_ttf):
    '''AvgCharWidthがおかしくなるので、元のフォントの値に書き換える
    require: `sudo pip install fonttools` or `uv tool install fonttools`

    refer: https://ja.osdn.net/projects/mplus-fonts/lists/archive/dev/2011-July/000619.html
    '''
    import xml.etree.ElementTree as ET

    deco_print('fix xAvgCharWidth: {} to {}'.format(_src_ttf, _dst_ttf))

    # 元のフォントからxAvgCharWidth読み出し
    src_root, _ = os.path.splitext(_src_ttf)
    os.system('ttx -f -t OS/2 ' + _src_ttf)
    src_tree = ET.parse(src_root + '.ttx')
    src_AvgCharWidth = src_tree.find('OS_2').find('xAvgCharWidth').get('value')

    # 作成したフォントへxAvgCharWidthを設定
    dst_root, _ = os.path.splitext(_dst_ttf)
    os.system('ttx -f -t OS/2 ' + _dst_ttf)
    dst_tree = ET.parse(dst_root + '.ttx')
    dst_tree.find('OS_2').find('xAvgCharWidth').set('value', '{}'.format(src_AvgCharWidth))
    dst_tree.write(dst_root + '.ttx', 'utf-8', True)

    # 変更したやつを反映
    os.system('ttx -f -m ' + _dst_ttf + ' ' + dst_root + '.ttx')

    # 後片付け
    if not DEBUG: os.remove(src_root + '.ttx')
    if not DEBUG: os.remove(dst_root + '.ttx')


def build_font(_f):

    modify_and_save_latin(_f, EN_TEMP)
    modify_and_save_jp(_f, JP_TEMP)

    deco_print('merge modified {} and modified {}'.format(_f.get('latin'), _f.get('japanese')))

    target_font = fontforge.font()
    target_font = set_height(target_font)

    target_font.upos = -115  # アンダーライン`_`と、装飾のアンダーラインの位置が同じになるように調整
    target_font.fontname   = _f.get('family')
    target_font.familyname = _f.get('family')
    target_font.fullname   = _f.get('name')
    target_font.weight     = _f.get('weight_name')

    target_font = set_os2_values(target_font, _f)
    target_font = set_sfnt_names(target_font, _f)
    target_font = set_gasp_table(target_font)

    target_font.mergeFonts(EN_TEMP)
    if not DEBUG: os.remove(EN_TEMP)
    target_font.mergeFonts(JP_TEMP)
    if not DEBUG: os.remove(JP_TEMP)

    target_font = vertical_line_to_broken_bar(target_font)
    # target_font = emdash_to_broken_dash(target_font) # あまり必要性を感じないので削除
    # 全角をいじるのはマージ前に行う

    target_font = post_process(target_font)

    fontpath = DIST + '/{}'.format(_f.get('filename'))
    if DEBUG: print_pdf(target_font, fontpath + '.pdf')

    target_font.generate(fontpath)
    target_font.close()

    fix_xAvgCharWidth(SOURCE + '/{}'.format(_f.get('japanese')), fontpath)

    deco_print('Generate {} completed.'.format(_f.get('name')))


def main():
    check_files()
    deco_print('Generating ' + FONTNAME + ' started.')

    for _f in fonts:
        build_font(_f)

    deco_print('Succeeded!!')


if __name__ == '__main__':
    main()
