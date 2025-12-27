from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.config import change_settings
import os
from typing import List, Dict, Tuple

# ImageMagickのパスを設定（環境に合わせて適宜変更してください）
# Streamlitアプリ内で設定する場合、os.environで設定する方が良いかもしれません。
# 例えば、ユーザーにImageMagickのインストールパスを入力させ、それを基に設定する。
# change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})
# change_settings({"IMAGEMAGICK_BINARY": "/usr/local/bin/magick"})

def set_imagemagick_binary(path: str):
    """
    ImageMagickのバイナリパスを設定します。
    """
    change_settings({"IMAGEMAGICK_BINARY": path})

def create_text_clip(text: str, font_path: str, font_size: int, font_color: str, text_position: Tuple[str, str], bg_color: str = None, duration: float = None):
    """
    MoviePyのTextClipを作成します。
    """
    try:
        txt_clip = TextClip(
            text,
            fontsize=font_size,
            color=font_color,
            font=font_path, # フォントファイルの絶対パスを指定
            bg_color=bg_color,
            method='caption' # 日本語対応のために 'caption' を推奨
        )
        if duration:
            txt_clip = txt_clip.set_duration(duration)
        txt_clip = txt_clip.set_position(text_position)
        return txt_clip
    except Exception as e:
        print(f"TextClipの作成中にエラーが発生しました: {e}")
        return None

def process_subclip_with_text(video_path: str, start_time: float, end_time: float, text_params: Dict = None):
    """
    指定された開始時間と終了時間に基づいて動画クリップを抽出し、テロップを合成します。
    動画全体をメモリに読み込まず、必要なサブクリップのみを処理します。
    """
    try:
        full_clip = VideoFileClip(video_path, audio=True, video=True)
        subclip = full_clip.subclip(start_time, end_time)

        final_clip = subclip

        if text_params:
            txt_clip = create_text_clip(
                text=text_params.get("text", ""),
                font_path=text_params.get("font_path"),
                font_size=text_params.get("font_size", 50),
                font_color=text_params.get("font_color", "white"),
                text_position=text_params.get("text_position", ("center", "bottom")),
                bg_color=text_params.get("bg_color"),
                duration=subclip.duration
            )
            if txt_clip:
                final_clip = CompositeVideoClip([subclip, txt_clip])
        
        # full_clipはまだ閉じない。後続の処理で再びsubclipを生成する可能性があるため。
        # 各process_subclip_with_textの呼び出し後、full_clip.close()はしない。
        # 最終的なレンダリング時に一度だけ閉じる。
        return final_clip

    except Exception as e:
        print(f"動画サブクリップの処理中にエラーが発生しました: {e}")
        return None

def render_video(video_path: str, edited_clips_data: List[Dict], output_filename: str = "output.mp4"):
    """
    編集されたクリップデータに基づいて最終動画をレンダリングします。
    """
    final_clips = []
    full_video_clip = None # 全体動画クリップは一度だけ生成し、再利用する

    try:
        # 動画ファイルを一度だけ読み込む
        full_video_clip = VideoFileClip(video_path, audio=True, video=True)

        for clip_data in edited_clips_data:
            start_time = clip_data["start_time"]
            end_time = clip_data["end_time"]
            text_params = clip_data.get("text_params")

            # subclipを生成
            subclip = full_video_clip.subclip(start_time, end_time)

            processed_clip = subclip
            if text_params:
                txt_clip = create_text_clip(
                    text=text_params.get("text", ""),
                    font_path=text_params.get("font_path"),
                    font_size=text_params.get("font_size", 50),
                    font_color=text_params.get("font_color", "white"),
                    text_position=text_params.get("text_position", ("center", "bottom")),
                    bg_color=text_params.get("bg_color"),
                    duration=subclip.duration
                )
                if txt_clip:
                    processed_clip = CompositeVideoClip([subclip, txt_clip])
            
            final_clips.append(processed_clip)

        if not final_clips:
            print("レンダリングするクリップがありません。")
            return False

        # 全てのクリップを結合
        final_video = concatenate_videoclips(final_clips)

        # ビデオの書き出し
        output_path = os.path.join(".", output_filename)
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True)

        print(f"動画が正常にレンダリングされました: {output_path}")
        return output_path

    except Exception as e:
        print(f"動画のレンダリング中にエラーが発生しました: {e}")
        return False
    finally:
        # 全体動画クリップと中間クリップを閉じる
        if full_video_clip:
            full_video_clip.close()
        for clip in final_clips:
            clip.close()

# 使用例 (StreamlitのSession Stateで管理されるデータ構造を想定)
# video_file_path = "path/to/your/uploaded_video.mp4"
# edited_clips = [
#     {
#         "start_time": 0,
#         "end_time": 5,
#         "text_params": {
#             "text": "はじめのシーン",
#             "font_path": "./fonts/NotoSansJP-Regular.ttf",
#             "font_size": 60,
#             "font_color": "white",
#             "text_position": ("center", 0.8), # 画面下部80%の位置
#             "bg_color": "black"
#         }
#     },
#     {
#         "start_time": 10,
#         "end_time": 15,
#         "text_params": {
#             "text": "次の重要なポイント",
#             "font_path": "./fonts/custom_fonts/MyCustomFont.ttf",
#             "font_size": 70,
#             "font_color": "yellow",
#             "text_position": ("center", "center")
#         }
#     }
# ]
# set_imagemagick_binary("/usr/local/bin/magick") # 環境に合わせる
# rendered_video_path = render_video(video_file_path, edited_clips, "final_output.mp4")
# if rendered_video_path:
#     st.video(rendered_video_path)
