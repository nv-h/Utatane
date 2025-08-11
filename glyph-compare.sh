#!/bin/bash
# グリフ形状比較ツール - 統合実行スクリプト
#
# M+、やさしさゴシック、Utataneの3フォントでグリフ形状を比較し、
# 境界ボックスやメトリクス情報を重ね合わせてPDF出力する。
#
# 使用例:
#   ./glyph-compare.sh --priority high                    # 高影響グリフ（32件）
#   ./glyph-compare.sh --category control currency       # 制御図記号と通貨記号
#   ./glyph-compare.sh --unicode U+2400 U+20A9          # 個別Unicode指定

set -e

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# カラー出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 環境チェック
check_environment() {
    echo_info "環境をチェック中..."
    
    # FontForgeチェック
    if [ ! -f "./fontforge/build/bin/fontforge" ]; then
        echo_error "FontForgeが見つかりません。以下を実行してください:"
        echo "  git submodule update --init --recursive"
        echo "  cd fontforge && mkdir -p build && cd build && cmake -GNinja .. && ninja"
        exit 1
    fi
    
    # uv環境チェック
    if [ ! -d ".venv" ]; then
        echo_warning "uv仮想環境が見つかりません。作成します..."
        uv venv
        uv add matplotlib
        echo_success "uv環境を作成しました"
    fi
    
    # フォントファイルチェック
    missing_fonts=()
    fonts=(
        "sourceFonts/mplus-1m-regular.ttf"
        "sourceFonts/YasashisaGothicBold-V2.ttf"
        "dist/Utatane-Regular.ttf"
    )
    
    for font in "${fonts[@]}"; do
        if [ ! -f "$font" ]; then
            missing_fonts+=("$font")
        fi
    done
    
    if [ ${#missing_fonts[@]} -gt 0 ]; then
        echo_error "以下のフォントファイルが見つかりません:"
        printf '  %s\n' "${missing_fonts[@]}"
        exit 1
    fi
    
    echo_success "環境チェック完了"
}

# ヘルプ表示
show_help() {
    cat << EOF
グリフ形状比較ツール - M+、やさしさゴシック、Utataneの3フォント比較

使用方法:
  $0 [オプション]

グリフ選択オプション:
  --category CAT        カテゴリ選択（複数指定可能）
                        ipa, greek, control, currency, math, latin_ext_b, misc
  --priority LEVEL      優先度選択 (high: 32件, all: 184件)
  --unicode U+XXXX      Unicode指定（複数指定可能）
  --range U+XXXX-U+YYYY Unicode範囲指定（複数指定可能）
  --chars CHARS         文字直接指定
  
フォント指定オプション:
  --mplus PATH          M+フォントパス
  --yasashisa PATH      やさしさゴシックフォントパス
  --utatane PATH        Utataneフォントパス

出力オプション:
  --output PATH         PDF出力ファイル名
  --json-only           JSONデータのみ出力（PDF生成しない）
  --keep-json           中間JSONファイルを保持

その他:
  --list-categories     利用可能なカテゴリ一覧表示
  --help, -h            このヘルプを表示

使用例:
  # 高影響グリフ（デフォルト）
  $0

  # 制御図記号のみ
  $0 --category control

  # 複数カテゴリ
  $0 --category control --category currency

  # 特定のUnicode文字
  $0 --unicode U+2400 --unicode U+20A9

  # Unicode範囲指定（制御図記号全体）
  $0 --range U+2400-U+2425

  # 複数範囲指定（制御図記号 + 通貨記号）
  $0 --range U+2400-U+2425 --range U+20A8-U+20B3

  # 全184件のグリフ
  $0 --priority all

  # カスタム出力ファイル名
  $0 --priority high --output high_impact_glyphs.pdf
EOF
}

# メイン処理
main() {
    local args=("$@")
    local json_file
    local pdf_file
    local keep_json=false
    local json_only=false
    
    # ヘルプまたはバージョン表示
    for arg in "$@"; do
        case $arg in
            --help|-h)
                show_help
                exit 0
                ;;
            --list-categories)
                check_environment
                ./fontforge/build/bin/fontforge -lang=py -script test/glyph_data_extractor.py --list-categories
                exit 0
                ;;
        esac
    done
    
    # tmpディレクトリの作成
    mkdir -p tmp
    
    # 出力ファイル名とオプション解析
    json_file="tmp/glyph_data_$(date +%Y%m%d_%H%M%S).json"
    pdf_file=""
    
    new_args=()
    i=0
    while [ $i -lt ${#args[@]} ]; do
        case "${args[i]}" in
            --output)
                if [ $((i+1)) -lt ${#args[@]} ]; then
                    pdf_file="${args[$((i+1))]}"
                    i=$((i+1))
                fi
                ;;
            --keep-json)
                keep_json=true
                ;;
            --json-only)
                json_only=true
                ;;
            *)
                new_args+=("${args[i]}")
                ;;
        esac
        i=$((i+1))
    done
    
    # 環境チェック
    check_environment
    
    echo_info "グリフ形状比較を開始します..."
    
    # ステップ1: FontForgeでグリフデータ抽出
    echo_info "ステップ1: グリフデータ抽出中..."
    ./fontforge/build/bin/fontforge -lang=py -script test/glyph_data_extractor.py "${new_args[@]}" --output "$json_file"
    
    if [ ! -f "$json_file" ]; then
        echo_error "グリフデータ抽出に失敗しました"
        exit 1
    fi
    
    echo_success "グリフデータ抽出完了: $json_file"
    
    # JSON のみの場合はここで終了
    if [ "$json_only" = true ]; then
        echo_success "JSONデータ抽出完了"
        exit 0
    fi
    
    # ステップ2: PDF可視化
    echo_info "ステップ2: PDF可視化中..."
    
    if [ -z "$pdf_file" ]; then
        pdf_file="tmp/${json_file##*/}"
        pdf_file="${pdf_file%.json}_comparison.pdf"
    fi
    
    source .venv/bin/activate
    uv run python test/glyph_visualizer.py "$json_file" --output "$pdf_file"
    
    if [ ! -f "$pdf_file" ]; then
        echo_error "PDF生成に失敗しました"
        exit 1
    fi
    
    echo_success "PDF生成完了: $pdf_file"
    
    # 中間JSONファイルのクリーンアップ
    if [ "$keep_json" = false ]; then
        rm -f "$json_file"
        echo_info "中間JSONファイルを削除しました"
    else
        echo_info "中間JSONファイルを保持しました: $json_file"
    fi
    
    echo_success "グリフ形状比較が完了しました！"
    echo_info "結果を確認してください: $pdf_file"
}

main "$@"