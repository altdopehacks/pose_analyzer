# 🎥 動画ボーン解析ツール (Video Bone Analysis Tool)

本アプリは、ユーザーがアップロードした動画ファイルに対して、MediaPipeを用いて人物のボーン（骨格）解析を実行し、解析データの保存とランドマーク可視化動画を出力・確認できるPython製Webアプリケーションです。GUIはGradioで構築されています。

(This application is a Python web app that performs bone (skeleton) analysis on user-uploaded video files using MediaPipe. It saves the analysis data and outputs a video with visualized landmarks for confirmation. The GUI is built with Gradio.)

## Features

-   MP4動画ファイルのアップロード (Upload .mp4 video files)
-   骨格データの出力形式選択（JSONまたはCSV）(Select output format for skeleton data: JSON or CSV)
-   MediaPipeによるボーン解析処理 (Bone analysis using MediaPipe)
-   骨格データファイルの保存（タイムスタンプ付き）(Save skeleton data file with timestamp)
-   ランドマーク描画付き動画の生成と保存 (Generate and save video with landmarks drawn)
-   UI上での可視化動画再生 (Playback of visualized video in the UI)
-   生成された骨格データファイルのダウンロード (Download generated skeleton data file)
-   UIリセット機能 (UI reset functionality)

## Requirements

-   Python 3.7+
-   Dependencies listed in `requirements.txt`

## Setup and Installation

1.  Clone the repository (if applicable).
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

1.  Execute the application:
    ```bash
    python app.py
    ```
2.  Open the displayed URL (usually `http://127.0.0.1:7860`) in your web browser.

## File Structure

-   `app.py`: Main application code.
-   `requirements.txt`: Python dependencies.
-   `output/`: Directory for generated files.
    -   `output/visualized/`: Stores videos with landmarks.
    -   `output/landmarks_data/`: Stores skeleton data files (JSON/CSV).
-   `README.md`: This file.
