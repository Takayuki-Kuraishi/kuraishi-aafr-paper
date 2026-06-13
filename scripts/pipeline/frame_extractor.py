import cv2
import os
from tqdm import tqdm

def extract_all_frames(video_path):
    current_dir = os.getcwd()
    # 保存フォルダ名を動画ファイル名に基づいて設定
    base_name = os.path.basename(video_path).split('.')[0]
    output_folder = os.path.join(current_dir, base_name + "_frames")
    
    # 出力フォルダが存在しない場合は作成
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 動画を読み込み
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"動画ファイル: {video_path}")
    print(f"総フレーム数: {total_frames}")
    if total_frames == 0:
        print("フレーム数が0です。動画ファイルが正しく読み込まれていない可能性があります。")
        return
    
    # tqdmでプログレスバーを作成
    for i in tqdm(range(total_frames), desc="フレーム抽出中"):
        ret, frame = cap.read()
        if not ret:
            print(f"フレーム {i+1} の読み込みに失敗しました。")
            break
            
        # 6桁のゼロ埋め連番を生成
        img_filename = f"{base_name}_{str(i+1).zfill(6)}.png"
        img_path = os.path.join(output_folder, img_filename)
        
        # フレームをPNG形式で保存
        cv2.imwrite(img_path, frame)
    
    cap.release()
    print(f"全フレーム ({total_frames} 枚) の保存が完了しました。")

def process_video_folder(folder_path):
    # 対応する動画ファイルの拡張子
    video_extensions = ('.mp4', '.avi', '.mov', '.wmv')
    
    # フォルダ内のすべてのファイルを取得
    files = os.listdir(folder_path)
    # 動画ファイルのみをフィルタリング
    video_files = [f for f in files if f.lower().endswith(video_extensions)]
    
    if not video_files:
        print(f"フォルダ {folder_path} に動画ファイルが見つかりませんでした。")
        return
    
    print(f"処理対象の動画ファイル数: {len(video_files)}")
    
    # 各動画ファイルに対して処理を実行
    for video_file in video_files:
        video_path = os.path.join(folder_path, video_file)
        extract_all_frames(video_path)
        print("-" * 50)  # 区切り線を表示

# 実行
folder_name = "processed_videos"  # ここに処理したい動画があるフォルダ名を指定
process_video_folder(folder_name)