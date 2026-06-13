# Written by Hiroshi Koyama @ National Institute for Basic Biology 20240416
# Modified by Takayuki Kuraishi @ Kanazawa Univ. 20241218
"""
小山先生のオリジナルからの変更点。
画像リストのソート:ファイル名をソートし、処理順序を統一。
"""

import cv2
import numpy as np
import glob
import os

# 2値化の閾値の設定　＝　ユーザーが指定する。
threshold = 50
print("	*** Threshold value is set to 50.\n")

# 画像ファイルのパスを取得
print("	*** Input folder name is your_folder_name_subtracted.\n")
pics = 'your_folder_name_subtracted/*.png'
pic_list = sorted(glob.glob(pics))  # ソートを明示的に追加

# 出力フォルダ名
output_folder = 'your_folder_name_binary_images'
print("	*** Output folder name is "+output_folder+".\n")
if not os.path.exists(output_folder):
	os.makedirs(output_folder)

# 各画像を2値化して保存
for i, pic in enumerate(pic_list):
    img = cv2.imread(pic, cv2.IMREAD_GRAYSCALE)
    _, binary_img = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    #cv2.imwrite(f'binary_{i}.jpg', binary_img)
    
    filename = f'binary_{i:05d}.png'
    full_path = os.path.join(output_folder, filename)
    cv2.imwrite(full_path, binary_img)

print("	*** Program finished!\n")