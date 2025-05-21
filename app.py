"""
動画ボーン解析ツール (Video Bone Analysis Tool)

ユーザーがアップロードした動画ファイル (.mp4) に対して、MediaPipeを用いて人物のボーン（骨格）解析を実行し、
解析データの保存（JSONまたはCSV形式）と、ランドマークを可視化した動画の出力・確認ができる
GradioベースのWebアプリケーションです。

This is a Gradio-based web application that allows users to upload video files (.mp4),
perform pose estimation (bone analysis) using MediaPipe, save the analysis data (in JSON or CSV format),
and output/review a video with visualized landmarks.
"""
import gradio as gr
import cv2
import mediapipe as mp
import numpy as np
import json
import csv
import os
from datetime import datetime

def analyze_video(video_path, output_format):
    """
    Analyzes a video file to extract pose landmarks and create an annotated version of the video.

    Args:
        video_path (str): The path to the input video file.
        output_format (str): The desired output format for landmarks data (json or csv).
                             This parameter is not directly used in this function for processing
                             but is part of the broader workflow.

    Returns:
        tuple: A tuple containing:
            - all_frames_data (list): A list of lists, where each inner list contains landmark
                                      dictionaries for a frame.
            - processed_frames (list): A list of OpenCV frames (NumPy arrays) with landmarks drawn.
            - fps (float): The frames per second of the input video.
        Returns (None, None, None) if the video cannot be opened.
    """
    mp_drawing = mp.solutions.drawing_utils # MediaPipe drawing utilities
    mp_pose = mp.solutions.pose # MediaPipe Pose model
    # Initialize Pose model
    pose = mp_pose.Pose(static_image_mode=False, 
                        min_detection_confidence=0.5, 
                        min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return None, None, None # all_frames_data, processed_frames, fps
    
    fps = cap.get(cv2.CAP_PROP_FPS) # Get video FPS
    all_frames_data = [] # To store landmark data for all frames
    processed_frames = [] # To store frames with drawn landmarks
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break # End of video
        
        # Convert the BGR image to RGB for MediaPipe processing.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Process the image and detect poses.
        results = pose.process(rgb_frame)
        
        # Create a copy of the frame to draw landmarks on.
        annotated_frame = frame.copy()
        if results.pose_landmarks:
            # Draw pose landmarks on the frame.
            mp_drawing.draw_landmarks(
                annotated_frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
            )
        
        processed_frames.append(annotated_frame)
        
        # Extract landmark data for the current frame.
        current_frame_landmarks = []
        if results.pose_landmarks:
            for landmark_id, landmark in enumerate(results.pose_landmarks.landmark):
                current_frame_landmarks.append({
                    'id': landmark_id,
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                })
        all_frames_data.append(current_frame_landmarks)
        
    cap.release() # Release video capture object
    pose.close() # Close Pose model
    
    return all_frames_data, processed_frames, fps

def save_landmarks_data(all_frames_data, output_format, original_video_path, fps=30, output_dir_landmarks="output/landmarks_data/"):
    """
    Saves the extracted pose landmark data to a file (JSON or CSV).

    Args:
        all_frames_data (list): A list of lists containing landmark data for each frame.
        output_format (str): The desired output format ("json" or "csv").
        original_video_path (str): Path to the original video file, used for naming the output file.
        output_dir_landmarks (str, optional): Directory to save the landmark data.
                                             Defaults to "output/landmarks_data/".

    Returns:
        str: The full path to the saved landmark data file. Returns path even if all_frames_data is empty (for CSV, header is written).
    """
    # Generate a timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Get the base name of the original video for the output filename
    original_filename_base = os.path.splitext(os.path.basename(original_video_path))[0]
    output_filename = f"{original_filename_base}_{timestamp}_landmarks.{output_format}"
    output_file_path = os.path.join(output_dir_landmarks, output_filename)
    
    # Ensure output directory exists
    os.makedirs(output_dir_landmarks, exist_ok=True)
    
    if output_format == "json":
        with open(output_file_path, 'w') as f:
            # Convert to the format expected by avatar_controller with fps and frames array
            formatted_data = {
                "fps": fps,
                "frames": [
                    {
                        "timestamp": frame_idx / fps if fps > 0 else 0,
                        "poseLandmarks": frame_landmarks
                    }
                    for frame_idx, frame_landmarks in enumerate(all_frames_data)
                ]
            }
            json.dump(formatted_data, f, indent=4)
    elif output_format == "csv":
        with open(output_file_path, 'w', newline='') as f:
            csv_writer = csv.writer(f)
            # Define CSV header
            header = ['frame_index', 'landmark_id', 'x', 'y', 'z', 'visibility']
            csv_writer.writerow(header)
            
            if not all_frames_data: 
                # If there's no landmark data at all (e.g., video had no detectable people),
                # the file will be created with only the header.
                pass # Header is already written.
            else:
                for frame_idx, frame_landmarks in enumerate(all_frames_data):
                    if frame_landmarks: # If there are landmarks for this frame
                        for landmark in frame_landmarks:
                            csv_writer.writerow([
                                frame_idx,
                                landmark['landmark_id'],
                                landmark['x'],
                                landmark['y'],
                                landmark['z'],
                                landmark.get('visibility', 'N/A') # Use .get for safety if visibility might be missing
                            ])
                    else:
                        # If a frame has no landmarks, write a row indicating this
                        csv_writer.writerow([frame_idx, 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'])
    
    return output_file_path

def save_visualized_video(processed_frames, original_video_path, fps, output_dir_visualized="output/visualized/"):
    """
    Saves the processed frames (with landmarks drawn) as an MP4 video file.

    Args:
        processed_frames (list): List of OpenCV frames (NumPy arrays) with landmarks drawn.
        original_video_path (str): Path to the original video file, used for naming.
        fps (float): Frames per second for the output video.
        output_dir_visualized (str, optional): Directory to save the visualized video.
                                               Defaults to "output/visualized/".

    Returns:
        str or None: The full path to the saved video file, or None if no frames to save.
    """
    if not processed_frames:
        return None # No frames to save

    # Get video dimensions from the first frame
    height, width, _ = processed_frames[0].shape
    
    # Create unique filename using timestamp and original video name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename_base = os.path.splitext(os.path.basename(original_video_path))[0]
    output_filename = f"{original_filename_base}_{timestamp}_landmarked.mp4"
    output_video_path = os.path.join(output_dir_visualized, output_filename)
    
    # Ensure output directory exists
    os.makedirs(output_dir_visualized, exist_ok=True)
    
    # Define the codec (MP4V for .mp4) and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
    out_video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Write each frame to the video file
    for frame in processed_frames:
        out_video.write(frame)
        
    out_video.release() # Release the VideoWriter object
    
    return output_video_path

def process_video_and_update_ui(video_file_obj, output_format_choice):
    """
    Handles the entire video processing workflow when the user clicks "Analyze".
    This includes video analysis, data saving, visualized video saving, and updating the UI.

    Args:
        video_file_obj (gradio.File): The uploaded video file object from Gradio.
                                      Its `.name` attribute provides the path to the temp file.
        output_format_choice (str): The output format selected by the user ("json" or "csv").

    Returns:
        tuple: A tuple containing:
            - visualized_video_path (str or None): Path to the visualized video for UI display.
            - landmarks_file_path (str or None): Path to the saved landmarks data file for download.
            - status_message (str): A message indicating the outcome of the processing.
    """
    if not video_file_obj:
        return None, None, "エラー: 動画ファイルを選択してください。" # Error: Please select a video file.

    video_path = video_file_obj.name # Get the temporary path of the uploaded file
    
    try:
        # Step 1: Analyze the video to get landmarks and processed frames
        all_frames_data, processed_frames, fps = analyze_video(video_path, output_format_choice)

        # Handle errors from analyze_video (e.g., video couldn't be opened or processed)
        if all_frames_data is None or processed_frames is None:
            return None, None, "エラー: 動画解析に失敗しました。サポートされていない動画形式か、動画が破損している可能性があります。"
            # Error: Video analysis failed. Unsupported video format or corrupted file.

        if not processed_frames: # Handle cases where no frames were processed (e.g., very short/empty video)
             return None, None, "警告: 動画からフレームを処理できませんでした。動画が空か非常に短い可能性があります。"
             # Warning: Could not process frames from the video. It might be empty or too short.

        # Step 2: Save landmarks data
        landmarks_file_path = save_landmarks_data(all_frames_data, output_format_choice, video_path, fps)
        
        # Step 3: Save visualized video
        visualized_video_path = save_visualized_video(processed_frames, video_path, fps)

        # Step 4: Prepare success message and check if any file saving failed
        if not visualized_video_path and not landmarks_file_path:
            # This case means both saving operations failed.
            return None, None, "エラー: 解析結果の保存に失敗しました。" # Error: Failed to save analysis results.
        
        success_message = "処理が正常に完了しました。" # Processing completed successfully.
        if not visualized_video_path:
            success_message += " (注意: 可視化動画の保存に失敗)" # Warning: Failed to save visualized video.
        if not landmarks_file_path:
            # This is unlikely if save_landmarks_data always returns a path, but good for robustness.
            success_message += " (注意: ランドマークデータの保存に失敗)" # Warning: Failed to save landmark data.

        return visualized_video_path, landmarks_file_path, success_message

    except Exception as e:
        print(f"An error occurred during processing: {e}") # Log the full error for server-side debugging
        # For more detailed debugging during development, uncomment the next line:
        # import traceback; traceback.print_exc()
        return None, None, f"予期せぬエラーが発生しました: {str(e)}" # An unexpected error occurred.

# --- Gradio Interface Setup ---
with gr.Blocks() as demo:
    gr.Markdown("# 🎥 動画ボーン解析ツール")  # Title: Video Bone Analysis Tool

    with gr.Row():
        video_input = gr.File(label="動画ファイル選択", file_types=['.mp4'])
        output_format_radio = gr.Radio(["json", "csv"], label="出力形式:", value="json")

    with gr.Row():
        analyze_button = gr.Button("解析開始ボタン") # Analysis Start Button
        reset_button = gr.Button("クリア") # Clear Button
            
    status_textbox = gr.Textbox(label="処理ステータス", interactive=False) # Processing Status
            
    gr.Markdown("## 解析結果：") # Analysis Results:
    with gr.Row():
        video_output = gr.Video(label="ランドマーク付き動画") # Video with Landmarks
        file_output = gr.File(label="ボーンデータファイル") # Bone Data File

    # Connect button clicks to their respective functions
    analyze_button.click(
        fn=process_video_and_update_ui,
        inputs=[video_input, output_format_radio],
        outputs=[video_output, file_output, status_textbox]
    )

    def reset_ui_elements():
        """
        Resets the Gradio UI elements to their default states.

        This function is called when the 'Clear' button is pressed.
        It returns a tuple of values that Gradio uses to update the
        corresponding UI components.

        Returns:
            tuple: A tuple of values corresponding to the initial states of the UI components
                   (video_input, output_format_radio, status_textbox, video_output, file_output).
        """
        return (
            None,    # Clears gr.File component (video_input)
            "json",  # Resets gr.Radio to "json" (output_format_radio)
            "",      # Clears gr.Textbox (status_textbox)
            None,    # Clears gr.Video component (video_output)
            None     # Clears gr.File download component (file_output)
        )

    reset_button.click(
        fn=reset_ui_elements,
        inputs=None, # No inputs needed for the reset function
        outputs=[
            video_input,
            output_format_radio,
            status_textbox,
            video_output,
            file_output
        ]
    )

# Launch the Gradio app when the script is executed directly
if __name__ == "__main__":
    demo.launch()
