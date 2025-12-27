import streamlit as st
import os
from modules import video_analyzer, font_manager, video_editor
import google.generativeai as genai

# Streamlitページ設定
st.set_page_config(layout="wide", page_title="QuickClip Pro")
st.title("QuickClip Pro: AI動画エディター")

# ImageMagickのバイナリパスが設定されているか確認し、設定を促す
if "IMAGEMAGICK_BINARY" not in os.environ:
    st.warning("MoviePyのTextClipにはImageMagickが必要です。環境変数 IMAGEMAGICK_BINARY を設定するか、sidebarでパスを入力してください。")
    # 例: macOS/Linuxの場合: /usr/local/bin/magick, Windowsの場合: C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe

# 環境変数からGemini APIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    st.error("Gemini APIキーが設定されていません。環境変数 'GEMINI_API_KEY' または Streamlit Secrets に設定してください。")
    st.stop()
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Session Stateの初期化
if 'uploaded_video_file_id' not in st.session_state:
    st.session_state.uploaded_video_file_id = None
if 'uploaded_video_name' not in st.session_state:
    st.session_state.uploaded_video_name = None
if 'video_analysis_result' not in st.session_state:
    st.session_state.video_analysis_result = [] # AI解析によるシーン抽出結果
if 'edited_clips' not in st.session_state:
    st.session_state.edited_clips = [] # ユーザーが編集したクリップリスト
if 'available_fonts' not in st.session_state:
    st.session_state.available_fonts = font_manager.get_available_fonts()
if 'selected_font_path' not in st.session_state:
    st.session_state.selected_font_path = None
if 'temp_output_video' not in st.session_state:
    st.session_state.temp_output_video = None

# ============================================================================
# サイドバー：設定とリソース
# ============================================================================
st.sidebar.header("設定とリソース")

# 動画アップロード
st.sidebar.subheader("動画アップロード")
uploaded_file = st.sidebar.file_uploader("動画ファイルを選択 (最大1GB)", type=["mp4", "mov", "avi", "mpeg", "webm"])

if uploaded_file and st.session_state.uploaded_video_file_id is None:
    st.session_state.uploaded_video_name = uploaded_file.name
    file_id = video_analyzer.upload_video_to_gemini(uploaded_file)
    if file_id:
        st.session_state.uploaded_video_file_id = file_id
        # アップロード後、再解析が必要な場合があるため、既存の解析結果をクリア
        st.session_state.video_analysis_result = []
        st.session_state.edited_clips = []
        st.experimental_rerun()

if st.session_state.uploaded_video_file_id:
    st.sidebar.write(f"**アップロード済み動画:** {st.session_state.uploaded_video_name}")
    # st.sidebar.write(f"ファイルID: {st.session_state.uploaded_video_file_id}")
    if st.sidebar.button("動画を再アップロード / 別の動画を選択"):
        st.session_state.uploaded_video_file_id = None
        st.session_state.uploaded_video_name = None
        st.session_state.video_analysis_result = []
        st.session_state.edited_clips = []
        st.session_state.temp_output_video = None
        st.experimental_rerun()

# フォント管理
st.sidebar.subheader("フォント管理")

# Google Fontsの選択とダウンロード
google_fonts_list = font_manager.get_google_fonts_list()
google_font_names = list(google_fonts_list.keys())
selected_google_font_name = st.sidebar.selectbox(
    "Google日本語フォントを選択してダウンロード",
    ["--- 選択してください ---"] + google_font_names,
    key="google_font_selector"
)

if selected_google_font_name != "--- 選択してください ---":
    font_file_name = google_fonts_list[selected_google_font_name]
    if st.sidebar.button(f"{selected_google_font_name} をダウンロード"):
        downloaded_path = font_manager.download_google_font(selected_google_font_name, font_file_name)
        if downloaded_path and downloaded_path not in st.session_state.available_fonts:
            st.session_state.available_fonts = font_manager.get_available_fonts() # 更新
            st.experimental_rerun()

# カスタムフォントのアップロード
custom_font_file = st.sidebar.file_uploader("カスタムフォントをアップロード (.ttf / .otf)", type=["ttf", "otf"])
if custom_font_file:
    uploaded_path = font_manager.upload_custom_font(custom_font_file)
    if uploaded_path and uploaded_path not in st.session_state.available_fonts:
        st.session_state.available_fonts = font_manager.get_available_fonts() # 更新
        st.experimental_rerun()

# 利用可能なフォントの表示と選択
font_display_names = [font_manager.get_font_display_name(f) for f in st.session_state.available_fonts]
selected_font_display_name = st.sidebar.selectbox(
    "使用するフォントを選択",
    ["--- 選択してください ---"] + font_display_names,
    key="app_font_selector"
)

if selected_font_display_name != "--- 選択してください ---":
    st.session_state.selected_font_path = next(
        (f for f in st.session_state.available_fonts if font_manager.get_font_display_name(f) == selected_font_display_name),
        None
    )
else:
    st.session_state.selected_font_path = None

if st.session_state.selected_font_path:
    st.sidebar.write(f"選択中のフォント: **{font_manager.get_font_display_name(st.session_state.selected_font_path)}**")

# テロップスタイル設定
st.sidebar.subheader("テロップスタイル設定 (デフォルト)")
default_font_size = st.sidebar.slider("フォントサイズ", 10, 100, 50)
default_font_color = st.sidebar.color_picker("フォント色", "#FFFFFF")
default_text_position_options = {"下部中央": ("center", "bottom"), "中央": ("center", "center"), "上部中央": ("center", "top"), "下部左": ("left", "bottom"), "下部右": ("right", "bottom")}
default_text_position_label = st.sidebar.selectbox("位置", list(default_text_position_options.keys()))
default_text_position = default_text_position_options[default_text_position_label]
default_bg_enabled = st.sidebar.checkbox("背景を有効にする (テロップ)", value=False)
default_bg_color = st.sidebar.color_picker("背景色", "#000000") if default_bg_enabled else None

# ImageMagickのパス設定（サイドバー）
st.sidebar.subheader("ImageMagick設定")
current_imagemagick_path = os.environ.get("IMAGEMAGICK_BINARY", "")
imagemagick_path_input = st.sidebar.text_input("ImageMagickバイナリパス", value=current_imagemagick_path, help="例: /usr/local/bin/magick (macOS/Linux) または C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe (Windows)")
if st.sidebar.button("ImageMagickパスを設定"): # ユーザーがボタンを押したときのみ設定
    if os.path.exists(imagemagick_path_input) or (os.path.basename(imagemagick_path_input) == "magick" and "magick.exe" not in imagemagick_path_input.lower()): # magick.exeがない場合もOK
        video_editor.set_imagemagick_binary(imagemagick_path_input)
        os.environ["IMAGEMAGICK_BINARY"] = imagemagick_path_input # 環境変数にも設定して次回以降も利用
        st.sidebar.success(f"ImageMagickパスを '{imagemagick_path_input}' に設定しました。")
        st.experimental_rerun()
    else:
        st.sidebar.error("指定されたImageMagickバイナリパスが見つからないか、不正なパスです。")

# ============================================================================
# メインパネル：指示と編集
# ============================================================================

if not st.session_state.uploaded_video_file_id:
    st.info("まずサイドバーから動画をアップロードしてください。", icon="")
else:
    st.subheader("シーン抽出指示")
    prompt = st.text_area("AIへの指示を自然言語で入力してください (例: \"特定の商品が登場するシーンをすべて抽出して、それぞれのシーンにテロップを付けて\" ")
    if st.button("AIにシーン抽出を依頼"): # AI解析はFile APIの課金対象
        if prompt:
            with st.spinner("AIが動画を解析中... (これには時間がかかる場合があります)"):
                # ここでGemini API (vision-pro) を呼び出して動画解析を行う
                # 仮の解析結果を生成（実際にはGemini APIのレスポンスを処理する）
                st.session_state.video_analysis_result = [
                    {"start_time": 0, "end_time": 5, "caption": "製品Aの紹介"},
                    {"start_time": 10, "end_time": 18, "caption": "製品Aの使用デモ"},
                    {"start_time": 25, "end_time": 30, "caption": "製品Bが登場"},
                ]
                st.session_state.edited_clips = [] # 解析結果を元に編集クリップを初期化
                for res in st.session_state.video_analysis_result:
                    st.session_state.edited_clips.append({
                        "start_time": res["start_time"],
                        "end_time": res["end_time"],
                        "text": res["caption"],
                        "font_path": st.session_state.selected_font_path if st.session_state.selected_font_path else font_manager.get_available_fonts()[0] if font_manager.get_available_fonts() else None,
                        "font_size": default_font_size,
                        "font_color": default_font_color,
                        "text_position": default_text_position,
                        "bg_color": default_bg_color
                    })
            st.success("AIによるシーン抽出が完了しました！")
        else:
            st.warning("シーン抽出の指示を入力してください。")

    st.subheader("編集ワークスペース")
    if st.session_state.edited_clips:
        for i, clip in enumerate(st.session_state.edited_clips):
            st.markdown(f"### クリップ {i+1}")
            col1, col2, col3 = st.columns(3)
            with col1:
                clip["start_time"] = st.number_input(f"開始時間 (秒)##{i}", value=float(clip["start_time"]), step=0.1, key=f"start_{i}")
            with col2:
                clip["end_time"] = st.number_input(f"終了時間 (秒)##{i}", value=float(clip["end_time"]), step=0.1, key=f"end_{i}")
            with col3:
                clip["text"] = st.text_input(f"テロップ##{i}", value=clip["text"], key=f"text_{i}")
            
            # 個別クリップのテロップスタイル設定
            with st.expander(f"クリップ {i+1} テロップスタイルを調整"):
                clip["font_path"] = st.selectbox(
                    f"フォント##{i}",
                    st.session_state.available_fonts, # font_pathを直接渡す
                    format_func=font_manager.get_font_display_name,
                    index=st.session_state.available_fonts.index(clip["font_path"]) if clip["font_path"] in st.session_state.available_fonts else 0,
                    key=f"font_path_{i}"
                )
                clip["font_size"] = st.slider(f"フォントサイズ##{i}", 10, 100, clip["font_size"], key=f"font_size_{i}")
                clip["font_color"] = st.color_picker(f"フォント色##{i}", clip["font_color"], key=f"font_color_{i}")
                text_position_label_current = next((key for key, val in default_text_position_options.items() if val == clip["text_position"]), list(default_text_position_options.keys())[0])
                clip["text_position"] = default_text_position_options[st.selectbox(f"位置##{i}", list(default_text_position_options.keys()), index=list(default_text_position_options.keys()).index(text_position_label_current), key=f"text_pos_{i}")]
                bg_enabled_current = True if clip["bg_color"] else False
                clip["bg_enabled"] = st.checkbox(f"背景を有効にする (クリップ {i+1})##{i}", value=bg_enabled_current, key=f"bg_enabled_{i}")
                clip["bg_color"] = st.color_picker(f"背景色 (クリップ {i+1})##{i}", clip["bg_color"] if clip["bg_color"] else "#000000", key=f"bg_color_{i}") if clip["bg_enabled"] else None

            st.button(f"クリップ {i+1} を削除", key=f"delete_clip_{i}", on_click=lambda idx=i: st.session_state.edited_clips.pop(idx))
            st.markdown("--- ")

        if st.button("新しいクリップを追加"):
            st.session_state.edited_clips.append({
                "start_time": 0,
                "end_time": 0,
                "text": "新しいテロップ",
                "font_path": st.session_state.selected_font_path if st.session_state.selected_font_path else font_manager.get_available_fonts()[0] if font_manager.get_available_fonts() else None,
                "font_size": default_font_size,
                "font_color": default_font_color,
                "text_position": default_text_position,
                "bg_color": default_bg_color
            })
            st.experimental_rerun()
    else:
        st.info("AIにシーン抽出を依頼するか、手動でクリップを追加してください。")

    st.subheader("最終プレビューとレンダリング")
    if st.button("レンダリング実行"):
        if not st.session_state.uploaded_video_file_id:
            st.error("動画がアップロードされていません。", icon="\u274C")
        elif not st.session_state.edited_clips:
            st.error("編集するクリップがありません。", icon="\u274C")
        elif not os.environ.get("IMAGEMAGICK_BINARY"):
            st.error("ImageMagickのバイナリパスが設定されていません。サイドバーで設定してください。", icon="\u274C")
        else:
            with st.spinner("動画をレンダリング中... (これには時間がかかります)"):
                # Gemini File APIから動画をダウンロードする必要がある（仮に一時ファイルとして保存）
                # TODO: 実際のGemini File APIからのダウンロード処理を実装
                # ここではアップロード時に保存した一時ファイルをそのまま使うことを想定
                temp_video_path = os.path.join("/tmp", st.session_state.uploaded_video_name) # アップロード時に一時保存したパスを仮定
                # 実際には video_analyzer.get_gemini_file(st.session_state.uploaded_video_file_id) でFileオブジェクトを取得後、ダウンロードが必要

                # edited_clipsのデータ構造をvideo_editor.render_videoが期待する形式に変換
                clips_to_render = []
                for clip in st.session_state.edited_clips:
                    clips_to_render.append({
                        "start_time": clip["start_time"],
                        "end_time": clip["end_time"],
                        "text_params": {
                            "text": clip["text"],
                            "font_path": clip["font_path"],
                            "font_size": clip["font_size"],
                            "font_color": clip["font_color"],
                            "text_position": clip["text_position"],
                            "bg_color": clip["bg_color"]
                        }
                    })

                output_filename = f"rendered_{os.path.splitext(st.session_state.uploaded_video_name)[0]}.mp4"
                rendered_video_path = video_editor.render_video(temp_video_path, clips_to_render, output_filename)
                
                if rendered_video_path:
                    st.session_state.temp_output_video = rendered_video_path
                    st.success("動画のレンダリングが完了しました！")
                else:
                    st.error("動画のレンダリング中にエラーが発生しました。", icon="\u274C")
            st.experimental_rerun() # レンダリング結果を反映するために再実行
    
    if st.session_state.temp_output_video:
        st.subheader("レンダリング結果")
        st.video(st.session_state.temp_output_video)
        with open(st.session_state.temp_output_video, "rb") as file:
            st.download_button(
                label="レンダリングされた動画をダウンロード",
                data=file,
                file_name=os.path.basename(st.session_state.temp_output_video),
                mime="video/mp4"
            )
        if st.button("一時出力ファイルを削除"):
            os.remove(st.session_state.temp_output_video)
            st.session_state.temp_output_video = None
            st.experimental_rerun()


# 注意事項/ヒント
st.sidebar.markdown("""
---
**ヒント:**
- `ImageMagick` は `MoviePy` の `TextClip` に必要です。インストールされていない場合は、[ImageMagick公式サイト](https://imagemagick.org/script/download.php) からダウンロードしてください。
  - macOS (Homebrew): `brew install imagemagick`
  - Windows (winget): `winget install ImageMagick.ImageMagick`
- Google FontsのダウンロードURLは、API経由での取得が理想的ですが、現在簡易実装のため一部ハードコードされています。
- 大容量動画の`Gemini File API`からのダウンロードは、レンダリング時に一時的に行われます。\n""")
