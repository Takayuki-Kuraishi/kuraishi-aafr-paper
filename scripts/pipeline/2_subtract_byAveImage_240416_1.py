# Written by Hiroshi Koyama @ National Institute for Basic Biology 20240416

import cv2
import numpy as np
import glob
import os

# 画像ファイルのパスを取得
print("	*** Input folder name is your_folder_name_RGB_to_B.\n")
pics = 'your_folder_name_RGB_to_B/*png'
pic_list = sorted(glob.glob(pics))  # ファイル名の連番順にソート

# 出力フォルダの作成
output_folder = 'your_folder_name_subtracted'
print("	*** Output folder name is "+output_folder+".\n")
if not os.path.exists(output_folder):
	os.makedirs(output_folder)

# 最初の画像を読み込んでサイズを取得
img = cv2.imread(pic_list[0], cv2.IMREAD_GRAYSCALE)
h, w = img.shape[:2]

# 平均画像の作成
base_array = np.zeros((h, w), np.int32)
for pic in pic_list:
    img = cv2.imread(pic, cv2.IMREAD_GRAYSCALE)
    base_array = base_array + img


# 画像の数で割って平均を計算
base_array = base_array / len(pic_list)
base_array = base_array.astype(np.uint8)

cv2.imwrite(f'your_folder_name_stack_average.png', base_array)
print("	*** An averaged image from the stack images is generated.\n")

# 各画像と平均画像の差分を計算
diff_images = []
for pic in pic_list:
    img = cv2.imread(pic, cv2.IMREAD_GRAYSCALE)
    diff = cv2.absdiff(img, base_array)
    diff_images.append(diff)

# 輝度の絶対値を取り、画像として保存
for i, diff in enumerate(diff_images):
    abs_diff = cv2.convertScaleAbs(diff)
    filename = f'diff_{i:05d}.png'
    full_path = os.path.join(output_folder, filename)
    cv2.imwrite(full_path, abs_diff)
    #cv2.imwrite(f'./subtracted/diff_{i:05d}.png', abs_diff)

print("	*** Program finished!\n")
