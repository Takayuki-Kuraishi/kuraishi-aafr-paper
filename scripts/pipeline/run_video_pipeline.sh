#!/bin/bash

echo "動画処理パイプライン開始: $(date)"

# 引数チェック
if [ $# -ne 1 ]; then
    echo "使用方法: $0 <入力ディレクトリ>"
    exit 1
fi

# 入力ディレクトリの確認
check_input_directory() {
    local input_dir="$1"
    if [ ! -d "$input_dir" ]; then
        echo "エラー: 入力ディレクトリ $input_dir が存在しません"
        exit 1
    fi
}

# Pythonスクリプトの実行確認
check_python_script() {
    local script="$1"
    if [ ! -f "$script" ]; then
        echo "エラー: Pythonスクリプト $script が見つかりません"
        exit 1
    fi
}

# メイン処理
main() {
    local input_dir="$1"
    local chamber_script="video_processor.py"
    local frame_script="frame_extractor.py"

    # 入力ディレクトリの確認
    check_input_directory "$input_dir"

    # Pythonスクリプトの存在確認
    check_python_script "$chamber_script"
    check_python_script "$frame_script"

    # ステップ1: チャンバー分割処理
    echo "ステップ1: チャンバー分割処理を開始します..."
    python3 "$chamber_script" "$input_dir"
    if [ $? -ne 0 ]; then
        echo "エラー: チャンバー分割処理中にエラーが発生しました"
        exit 1
    fi
    echo "チャンバー分割処理が完了しました"

    # ステップ2: フレーム抽出処理
    echo "ステップ2: フレーム抽出処理を開始します..."
    python3 "$frame_script"
    if [ $? -ne 0 ]; then
        echo "エラー: フレーム抽出処理中にエラーが発生しました"
        exit 1
    fi
    echo "フレーム抽出処理が完了しました"
}

# スクリプトの実行（引数を渡す）
main "$1"

echo "パイプライン終了: $(date)"