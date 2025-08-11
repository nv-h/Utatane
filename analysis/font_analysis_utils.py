#!/usr/bin/env python3
"""
Font Analysis Utilities for Utatane Font Project

FontForgeベースのフォント分析用共通ユーティリティ関数群
使用方法: fontforge -lang=py -script analysis_script.py
"""

import sys
import os
from typing import Dict, List, Tuple, Optional, Any, Set, Union

try:
    import fontforge
except ImportError:
    print("このスクリプトはFontForge環境で実行してください")
    print("使用方法: fontforge -lang=py -script <script_name>.py")
    sys.exit(1)


class FontAnalyzer:
    """フォント分析用のメインクラス"""
    
    def __init__(self, font_paths: Dict[str, str]):
        """
        Args:
            font_paths: フォント名とパスの辞書 {"name": "path/to/font.ttf"}
        """
        self.font_paths = font_paths
        self.fonts = {}
        self._load_fonts()
    
    def _load_fonts(self):
        """フォントファイルを読み込む"""
        for name, path in self.font_paths.items():
            try:
                self.fonts[name] = fontforge.open(path)
                print(f"✓ {name}フォントを読み込みました: {path}")
            except Exception as e:
                print(f"✗ {name}フォントの読み込みに失敗: {path}")
                print(f"  エラー: {e}")
                raise
    
    def close_fonts(self):
        """開いているフォントをすべて閉じる"""
        for name, font in self.fonts.items():
            if font:
                font.close()
        self.fonts.clear()
    
    def get_font_info(self, font_name: str) -> Dict[str, Any]:
        """フォントの基本情報を取得"""
        if font_name not in self.fonts:
            raise ValueError(f"フォント '{font_name}' が見つかりません")
        
        font = self.fonts[font_name]
        return {
            'path': self.font_paths[font_name],
            'em_square': font.em,
            'ascent': font.ascent,
            'descent': font.descent,
            'glyph_count': len([g for g in font.glyphs() if g.isWorthOutputting])
        }
    
    def get_glyph_set(self, font_name: str) -> Set[int]:
        """フォント内のグリフのエンコーディング一覧を取得"""
        if font_name not in self.fonts:
            raise ValueError(f"フォント '{font_name}' が見つかりません")
        
        font = self.fonts[font_name]
        return {g.encoding for g in font.glyphs() if g.isWorthOutputting and g.encoding >= 0}
    
    def get_glyph_width(self, font_name: str, char_code: int) -> Optional[int]:
        """指定した文字コードの幅を取得"""
        if font_name not in self.fonts:
            raise ValueError(f"フォント '{font_name}' が見つかりません")
        
        font = self.fonts[font_name]
        if char_code in font and font[char_code].isWorthOutputting:
            return font[char_code].width
        return None
    
    def compare_widths(self, char_codes: List[int], font_names: List[str] = None) -> List[Dict]:
        """複数フォント間で文字幅を比較"""
        if font_names is None:
            font_names = list(self.fonts.keys())
        
        results = []
        for code in char_codes:
            result = {
                'code': code,
                'char': self._format_char(code),
                'widths': {},
                'has_inconsistency': False
            }
            
            widths = []
            for font_name in font_names:
                width = self.get_glyph_width(font_name, code)
                result['widths'][font_name] = width
                if width is not None:
                    widths.append(width)
            
            # 不一致チェック
            if len(set(widths)) > 1:
                result['has_inconsistency'] = True
            
            results.append(result)
        
        return results
    
    def analyze_unicode_ranges(self, font_names: List[str] = None) -> Dict[str, List[Dict]]:
        """Unicode範囲別に文字を分析"""
        if font_names is None:
            font_names = list(self.fonts.keys())
        
        # 共通のグリフを取得
        common_glyphs = set.intersection(*[self.get_glyph_set(name) for name in font_names])
        
        # Unicode範囲定義
        unicode_ranges = self.get_unicode_ranges()
        
        results = {}
        for range_name, (start, end) in unicode_ranges.items():
            range_glyphs = [code for code in common_glyphs if start <= code <= end]
            if range_glyphs:
                results[range_name] = self.compare_widths(range_glyphs, font_names)
        
        return results
    
    @staticmethod
    def get_unicode_ranges() -> Dict[str, Tuple[int, int]]:
        """Unicode範囲の定義を取得"""
        return {
            "ASCII制御": (0x0000, 0x001F),
            "ASCII": (0x0020, 0x007F),
            "基本ラテン拡張": (0x0080, 0x00FF),
            "拡張ラテンA": (0x0100, 0x017F),
            "拡張ラテンB": (0x0180, 0x024F),
            "IPA": (0x0250, 0x02AF),
            "修飾文字": (0x02B0, 0x02FF),
            "結合文字": (0x0300, 0x036F),
            "ギリシャ": (0x0370, 0x03FF),
            "キリル": (0x0400, 0x04FF),
            "一般句読点": (0x2000, 0x206F),
            "上付下付": (0x2070, 0x209F),
            "通貨": (0x20A0, 0x20CF),
            "結合記号": (0x20D0, 0x20FF),
            "文字様記号": (0x2100, 0x214F),
            "数学演算子": (0x2200, 0x22FF),
            "その他技術": (0x2300, 0x23FF),
            "制御図": (0x2400, 0x243F),
            "OCR": (0x2440, 0x245F),
            "囲み英数": (0x2460, 0x24FF),
            "罫線": (0x2500, 0x257F),
            "ブロック要素": (0x2580, 0x259F),
            "幾何図形": (0x25A0, 0x25FF),
            "その他記号": (0x2600, 0x26FF),
            "装飾記号": (0x2700, 0x27BF),
            "矢印": (0x2190, 0x21FF),
            "CJK記号": (0x3000, 0x303F),
            "ひらがな": (0x3040, 0x309F),
            "カタカナ": (0x30A0, 0x30FF),
            "CJK統合漢字": (0x4E00, 0x9FFF),
            "半角カタカナ": (0xFF00, 0xFFEF),
        }
    
    @staticmethod
    def get_symbol_categories() -> Dict[str, List[int]]:
        """記号カテゴリの定義を取得"""
        return {
            "幾何図形": [
                0x25CB, 0x25CF, 0x25B3, 0x25B2, 0x25A1, 0x25A0, 
                0x25C7, 0x25C6
            ],
            "囲み数字": [
                0x2460, 0x2461, 0x2462, 0x2463, 0x2464, 0x2468, 0x2469
            ],
            "演算記号・×類": [
                0x00D7, 0x2715, 0x00F7, 0x00B1, 0x2212, 0x2213
            ],
            "チェック・星印": [
                0x2713, 0x2714, 0x2717, 0x2718, 0x2605, 0x2606
            ],
            "矢印": [
                0x2190, 0x2191, 0x2192, 0x2193, 0x21D0, 0x21D2
            ],
            "その他記号": [
                0x203B, 0x3012, 0x3013, 0x301C, 0xFF5E, 0x2026, 0x22EF
            ]
        }
    
    @staticmethod
    def _format_char(char_code: int) -> str:
        """文字コードを表示用文字列に変換"""
        try:
            if char_code < 0x10000:
                return chr(char_code)
            else:
                return f"[U+{char_code:04X}]"
        except:
            return "[表示不可]"


class ReportGenerator:
    """分析結果のレポート生成クラス"""
    
    @staticmethod
    def print_font_info(analyzer: FontAnalyzer, font_name: str):
        """フォント基本情報を出力"""
        info = analyzer.get_font_info(font_name)
        print(f"\n【{font_name}フォント情報】")
        print(f"  パス: {info['path']}")
        print(f"  Em square: {info['em_square']}")
        print(f"  Ascent: {info['ascent']}, Descent: {info['descent']}")
        print(f"  グリフ数: {info['glyph_count']}")
    
    @staticmethod
    def print_width_comparison_summary(comparison_results: List[Dict], title: str = "文字幅比較結果"):
        """文字幅比較結果のサマリーを出力"""
        total = len(comparison_results)
        inconsistencies = [r for r in comparison_results if r['has_inconsistency']]
        consistent = total - len(inconsistencies)
        
        print(f"\n【{title}】")
        print(f"一致: {consistent}/{total} ({consistent/total*100:.1f}%)")
        print(f"不一致: {len(inconsistencies)}/{total} ({len(inconsistencies)/total*100:.1f}%)")
        
        if not inconsistencies:
            print("🎉 すべての文字幅が一致しています！")
        
        return inconsistencies
    
    @staticmethod
    def print_width_details(inconsistencies: List[Dict], max_display: int = 20):
        """文字幅不一致の詳細を出力"""
        if not inconsistencies:
            return
        
        print(f"\n【不一致詳細】（最大{max_display}件表示）")
        print(f"{'文字':<8} {'コード':<12} {'フォント別幅':>20}")
        print("-" * 50)
        
        for i, result in enumerate(inconsistencies[:max_display]):
            char_display = result['char']
            code_str = f"U+{result['code']:04X}"
            
            width_parts = []
            for font_name, width in result['widths'].items():
                if width is not None:
                    width_parts.append(f"{font_name}:{width}")
                else:
                    width_parts.append(f"{font_name}:なし")
            
            width_str = " | ".join(width_parts)
            print(f"{char_display:<8} {code_str:<12} {width_str}")
        
        if len(inconsistencies) > max_display:
            print(f"... 他{len(inconsistencies) - max_display}件")
    
    @staticmethod
    def print_range_analysis(range_results: Dict[str, List[Dict]], show_details: bool = False):
        """Unicode範囲別分析結果を出力"""
        print("\n【Unicode範囲別分析】")
        
        for range_name, results in range_results.items():
            if not results:
                continue
            
            inconsistencies = [r for r in results if r['has_inconsistency']]
            total = len(results)
            consistent = total - len(inconsistencies)
            
            status = "✓" if len(inconsistencies) == 0 else "⚠️"
            print(f"{status} {range_name}: {consistent}/{total} ({consistent/total*100:.1f}%)")
            
            if show_details and inconsistencies:
                print(f"  不一致文字: ", end="")
                for i, result in enumerate(inconsistencies[:5]):
                    if i > 0:
                        print(", ", end="")
                    print(f"U+{result['code']:04X}", end="")
                if len(inconsistencies) > 5:
                    print(f" ...他{len(inconsistencies)-5}件", end="")
                print()


def get_default_font_paths() -> Dict[str, str]:
    """デフォルトのフォントパス設定を取得（固定パス）"""
    return {
        'mplus': './sourceFonts/mplus-1m-regular.ttf',
        'mplus_bold': './sourceFonts/mplus-1m-bold.ttf',
        'ubuntu': './sourceFonts/UbuntuMono-Regular_modify.ttf',
        'ubuntu_bold': './sourceFonts/UbuntuMono-Bold_modify.ttf',
        'yasashisa': './sourceFonts/YasashisaGothicBold-V2_-30.ttf',
        'yasashisa_orig': './sourceFonts/YasashisaGothicBold-V2.ttf',
        'utatane': './dist/Utatane-Regular.ttf',
        'utatane_bold': './dist/Utatane-Bold.ttf'
    }

def find_available_fonts() -> Dict[str, str]:
    """利用可能なフォントファイルを動的に検索"""
    import glob
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patterns = [
        "dist/*.ttf",
        "dist/*.otf",
        "dist/*/*.ttf", 
        "sourceFonts/*.ttf"
    ]
    
    fonts = {}
    for pattern in patterns:
        for font_path in glob.glob(os.path.join(base_dir, pattern)):
            rel_path = os.path.relpath(font_path, base_dir)
            font_name = os.path.splitext(os.path.basename(font_path))[0]
            
            # バージョン情報を含む場合
            dir_name = os.path.dirname(rel_path)
            if dir_name and dir_name not in ['dist', 'sourceFonts']:
                key = f"{os.path.basename(dir_name)}_{font_name}"
            else:
                key = font_name
                
            fonts[key] = rel_path
    
    return fonts


def get_all_font_paths() -> Dict[str, str]:
    """固定パス + 動的検索の全フォントパスを取得"""
    default_fonts = get_default_font_paths()
    discovered_fonts = find_available_fonts()
    
    # 重複を避けつつマージ
    all_fonts = default_fonts.copy()
    for key, path in discovered_fonts.items():
        if key not in all_fonts:
            all_fonts[key] = path
    
    return all_fonts


def list_available_fonts() -> None:
    """利用可能なフォント一覧を表示"""
    all_fonts = get_all_font_paths()
    existing_fonts = {}
    missing_fonts = {}
    
    for name, path in all_fonts.items():
        if os.path.exists(path):
            existing_fonts[name] = path
        else:
            missing_fonts[name] = path
    
    print("利用可能なフォント:")
    for name, path in sorted(existing_fonts.items()):
        print(f"  ✓ {name:<20} -> {path}")
    
    if missing_fonts:
        print("\n見つからないフォント:")
        for name, path in sorted(missing_fonts.items()):
            print(f"  ✗ {name:<20} -> {path}")
    
    print(f"\n合計: {len(existing_fonts)} 個のフォントが利用可能")


def create_analyzer_with_error_handling(font_selection: List[str] = None) -> Optional[FontAnalyzer]:
    """エラーハンドリング付きでFontAnalyzerを作成"""
    if font_selection is None:
        font_selection = ['mplus', 'ubuntu', 'yasashisa']
    
    all_font_paths = get_all_font_paths()
    selected_paths = {}
    unknown_fonts = []
    
    for name in font_selection:
        if name in all_font_paths:
            selected_paths[name] = all_font_paths[name]
        else:
            unknown_fonts.append(name)
    
    # 不明なフォント名がある場合の処理
    if unknown_fonts:
        print(f"不明なフォント名: {', '.join(unknown_fonts)}")
        print("\n利用可能なフォント一覧:")
        existing_fonts = {k: v for k, v in all_font_paths.items() if os.path.exists(v)}
        for name in sorted(existing_fonts.keys()):
            print(f"  {name}")
        return None
    
    # 存在チェック
    missing_fonts = []
    for name, path in selected_paths.items():
        if not os.path.exists(path):
            missing_fonts.append(f"{name}: {path}")
    
    if missing_fonts:
        print("以下のフォントファイルが見つかりません:")
        for missing in missing_fonts:
            print(f"  ✗ {missing}")
        return None
    
    try:
        return FontAnalyzer(selected_paths)
    except Exception as e:
        print(f"FontAnalyzerの初期化に失敗しました: {e}")
        return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--list-fonts':
        list_available_fonts()
    else:
        print("Font Analysis Utilities")
        print("このファイルは他のスクリプトからimportして使用してください")
        print()
        print("使用可能なオプション:")
        print("  --list-fonts    利用可能なフォント一覧を表示")