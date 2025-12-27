import streamlit as st
import google.generativeai as genai
import os

# Google Gemini APIキーの設定
# 環境変数 'GEMINI_API_KEY' から取得するか、st.secrets を使用
# genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def upload_video_to_gemini(uploaded_file):
    """
    StreamlitのUploadedFileオブジェクトを受け取り、Gemini File APIに動画をアップロードします。
    アップロードが成功した場合、Fileオブジェクトのname (ファイルID) を返します。
    """
    if uploaded_file is not None:
        st.info(f"動画ファイル '{uploaded_file.name}' をアップロード中...", icon="upload")
        try:
            # アップロードされたファイルを一時的に保存（File APIがファイルパスを必要とするため）
            # Note: 1GB対応のため、メモリに直接読み込まずファイルとして扱う
            temp_file_path = os.path.join("/tmp", uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Gemini File APIにアップロード
            # get_default_retrying_client().upload_file(file_path=temp_file_path) のように使うことも可能
            file = genai.upload_file(path=temp_file_path, display_name=uploaded_file.name)
            st.success(f"動画ファイル '{uploaded_file.name}' のアップロードが完了しました。ファイルID: {file.name}", icon="\u2705")

            # 一時ファイルを削除
            os.remove(temp_file_path)

            return file.name # ファイルIDを返す

        except Exception as e:
            st.error(f"動画ファイルのアップロード中にエラーが発生しました: {e}", icon="\u274C")
            if "429 Resource Exhausted" in str(e):
                st.warning("APIレート制限に達した可能性があります。しばらく待ってから再試行してください。")
            return None
    return None

def get_gemini_file(file_id: str):
    """
    Gemini File APIからファイルIDに基づいてFileオブジェクトを取得します。
    """
    try:
        file = genai.get_file(name=file_id)
        return file
    except Exception as e:
        st.error(f"Gemini File APIからのファイル取得中にエラーが発生しました: {e}", icon="\u274C")
        return None

# Streamlit Session Stateでの利用例
# if 'uploaded_video_file_id' not in st.session_state:
#     st.session_state.uploaded_video_file_id = None

# uploaded_file = st.sidebar.file_uploader("動画をアップロード", type=["mp4", "mov", "avi"])
# if uploaded_file and st.session_state.uploaded_video_file_id is None:
#     file_id = upload_video_to_gemini(uploaded_file)
#     if file_id:
#         st.session_state.uploaded_video_file_id = file_id
#         st.session_state.uploaded_video_name = uploaded_file.name
#         st.experimental_rerun()

# if st.session_state.uploaded_video_file_id:
#     st.sidebar.write(f"アップロード済み動画: {st.session_state.uploaded_video_name} (ID: {st.session_state.uploaded_video_file_id})")
#     # ここでGemini APIを使って動画解析を行う
