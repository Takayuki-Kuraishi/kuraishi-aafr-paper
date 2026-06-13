import os
import cv2
import numpy as np
from tqdm import tqdm
import sys

class MinimalVideoProcessor:
   def __init__(self, frames_per_chunk=5000):
       self.frames_per_chunk = frames_per_chunk

   def get_video_info(self, input_path):
       cap = cv2.VideoCapture(input_path)
       info = {
           'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
           'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
           'fps': cap.get(cv2.CAP_PROP_FPS),
           'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
       }
       cap.release()
       return info

   def process_chunk(self, input_path, start_frame, chunk_size, chamber_coords, writers, total_frames, pbar):
       cap = cv2.VideoCapture(input_path)
       try:
           cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
           for frame_idx in range(start_frame, min(start_frame + chunk_size, total_frames)):
               ret, frame = cap.read()
               if not ret:
                   pbar.update(1)
                   continue
                   
               for (x1, y1, x2, y2), writer in zip(chamber_coords, writers):
                   chamber_frame = frame[y1:y2, x1:x2]
                   writer.write(chamber_frame)
               pbar.update(1)
       finally:
           cap.release()

   def process_video(self, input_path, output_dir):
       os.makedirs(output_dir, exist_ok=True)
       info = self.get_video_info(input_path)
       
       chamber_coords = [
           (200, 100, 520, 430),
           (590, 100, 900, 430),
           (1180, 100, 1480, 430),
           (1570, 100, 1880, 430),
           (200, 500, 520, 830),
           (590, 500, 900, 830),
           (1180, 500, 1480, 830),
           (1560, 500, 1850, 830),
       ]
       
       base_name = os.path.splitext(os.path.basename(input_path))[0]
       output_paths = [
           os.path.join(output_dir, f"{base_name}_L1.avi"),
           os.path.join(output_dir, f"{base_name}_L2.avi"),
           os.path.join(output_dir, f"{base_name}_R1.avi"),
           os.path.join(output_dir, f"{base_name}_R2.avi"),
           os.path.join(output_dir, f"{base_name}_L3.avi"),
           os.path.join(output_dir, f"{base_name}_L4.avi"),
           os.path.join(output_dir, f"{base_name}_R3.avi"),
           os.path.join(output_dir, f"{base_name}_R4.avi")
       ]

       writers = [
           cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'FFV1'), info['fps'], 
                         (x2 - x1, y2 - y1))
           for path, (x1, y1, x2, y2) in zip(output_paths, chamber_coords)
       ]

       total_frames = info['total_frames']
       try:
           with tqdm(total=total_frames, desc="処理進捗", unit="frames") as pbar:
               for start_frame in range(0, total_frames, self.frames_per_chunk):
                   chunk_size = min(self.frames_per_chunk, total_frames - start_frame)
                   self.process_chunk(
                       input_path,
                       start_frame,
                       chunk_size,
                       chamber_coords,
                       writers,
                       total_frames,
                       pbar
                   )
       finally:
           for writer in writers:
               writer.release()

   def process_directory(self, input_dir, output_base_dir):
       video_extensions = ('.avi', '.mp4', '.mov')
       video_files = [f for f in os.listdir(input_dir) if f.lower().endswith(video_extensions)]

       if not video_files:
           print(f"警告: {input_dir} に動画ファイルが見つかりません")
           return

       for video_file in video_files:
           input_path = os.path.join(input_dir, video_file)
           self.process_video(input_path, output_base_dir)

if __name__ == "__main__":
   if len(sys.argv) != 2:
       print("使用方法: python video_processor.py <入力ディレクトリ>")
       sys.exit(1)

   input_dir = sys.argv[1]
   output_base_dir = "processed_videos"
   processor = MinimalVideoProcessor(frames_per_chunk=5000)
   processor.process_directory(input_dir, output_base_dir)