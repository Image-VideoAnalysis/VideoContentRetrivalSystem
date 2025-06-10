import os
import shutil

# This script processes two sets of keyframes and metadata, copying the fallback keyframes
base_path_1 = 'SBDresults/keyframes'
json_base_path_1 = 'SBDresults/metadata'
base_path_2 = 'SBDresults_with_fallback/keyframes'
json_base_path_2 = 'SBDresults_with_fallback/metadata'


output_path = 'videos_with_fallback'
keyframe_output_path = os.path.join(output_path, 'keyframes')
json_output_path = os.path.join(output_path, 'metadata')

print(f"Ensuring output directories exist: '{keyframe_output_path}' and '{json_output_path}'")
os.makedirs(keyframe_output_path, exist_ok=True)
os.makedirs(json_output_path, exist_ok=True)

try:
    video_folders = os.listdir(base_path_1)
except FileNotFoundError:
    print(f"Error: Source directory not found at '{base_path_1}'. Exiting.")
    exit()

print(f"Found {len(video_folders)} video folders to process.")

for video_folder in video_folders:
    folder_1 = os.path.join(base_path_1, video_folder)
    folder_2 = os.path.join(base_path_2, video_folder)

    if not os.path.isdir(folder_1) or not os.path.isdir(folder_2):
        print(f"Skipping '{video_folder}': Corresponding folder not found in both sources.")
        continue
    keyframes_1 = [f for f in os.listdir(folder_1) if not f.startswith('.')]
    keyframes_2 = [f for f in os.listdir(folder_2) if not f.startswith('.')]

    print(f"\nProcessing '{video_folder}': Original keyframes = {len(keyframes_1)}, Fallback keyframes = {len(keyframes_2)}")

    if len(keyframes_1) < len(keyframes_2):
        print(f"Action: Fallback has more keyframes. Copying assets for '{video_folder}'.")

        src_keyframe_folder = folder_2
        dst_keyframe_folder = os.path.join(keyframe_output_path, video_folder)

        if os.path.exists(dst_keyframe_folder):
            shutil.rmtree(dst_keyframe_folder)

        shutil.copytree(src_keyframe_folder, dst_keyframe_folder)
        print(f"  -> Copied keyframes to '{dst_keyframe_folder}'")
        json_filename = video_folder + '.json'
        src_json_file = os.path.join(json_base_path_2, json_filename)

        if os.path.exists(src_json_file):
            shutil.copy(src_json_file, json_output_path)
            print(f"  -> Copied metadata to '{os.path.join(json_output_path, json_filename)}'")
        else:
            print(f"  -> Warning: Metadata file '{src_json_file}' not found. Skipping copy.")
    else:
        print(f"Action: Original has sufficient keyframes. No action taken for '{video_folder}'.")
