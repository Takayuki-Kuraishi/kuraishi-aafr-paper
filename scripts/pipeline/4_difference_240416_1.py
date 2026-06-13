# Written by Hiroshi Koyama @ National Institute for Basic Biology 20240416

import cv2
import numpy as np
import glob
import csv
import os

# 画像ファイルのパスを取得
input_folder = 'your_folder_name_binary_images'

print("	*** Input folder name is "+input_folder+".\n")
pics = input_folder+'/*png'

#pics = 'binary_images/*.png'
#pics = '*.png'
pic_list = sorted(glob.glob(pics))  # ファイル名の連番順にソート

# 輝度の相違を計算してCSVファイルに出力
with open('your_folder_name_brightness_differences.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Image Pair', 'Brightness Difference'])

    for i in range(len(pic_list) - 1):
        img1 = cv2.imread(pic_list[i], cv2.IMREAD_GRAYSCALE).astype(np.float32)
        img2 = cv2.imread(pic_list[i + 1], cv2.IMREAD_GRAYSCALE).astype(np.float32)

        # 輝度の差分を計算
        diff = np.abs(img1 - img2).sum()

        # CSVファイルに書き込み
        writer.writerow([f"{i} - {i + 1}", diff])

print("	*** Program finished!\n")

