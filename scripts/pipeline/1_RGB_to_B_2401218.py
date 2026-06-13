# Written by Hiroshi Koyama @ National Institute for Basic Biology 20240416
# Modified by Takayuki Kuraishi @ Kanazawa Univ. 20241218
"""
小山先生のオリジナルからの変更点。
画像ファイルの取得: 隠しファイルやサブディレクトリを除外。JupyterLabを使っており、隠しファイルが生成されることがあるかもしれないため。
"""

import cv2
import os

# 入力画像のフォルダパスと出力画像のフォルダパスを指定
input_folder = "your_folder_name"
print("	*** Input folder name is " + input_folder + ".\n")

output_folder = "your_folder_name_RGB_to_B"

if not os.path.exists(output_folder):
    os.makedirs(output_folder)
    print("	*** Output folder is newly generated. " + output_folder + "\n")

# フォルダ内の画像ファイルを取得（改良版：隠しファイルやサブディレクトリを除外）
image_files = [
    file for file in sorted(os.listdir(input_folder))
    if not file.startswith('.') and not os.path.isdir(os.path.join(input_folder, file))
]

for image_file in image_files:
    # 画像を読み込む
    image_path = os.path.join(input_folder, image_file)
    img_bgr = cv2.imread(image_path)

    # Blueチャネルを抽出
    img_blue = img_bgr[:, :, 0]  # 0はBlueチャネルのインデックス

    # 出力画像のパスを生成
    output_path = os.path.join(output_folder, f"{os.path.splitext(image_file)[0]}_blue_gray.png")

    # 画像を保存
    cv2.imwrite(output_path, img_blue)

print("	*** Program finished!\n")
