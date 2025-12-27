import streamlit as st
import os
import requests
from typing import List, Dict

FONT_DIR = "./fonts"
GOOGLE_FONTS_DIR = os.path.join(FONT_DIR, "google_fonts")
CUSTOM_FONTS_DIR = os.path.join(FONT_DIR, "custom_fonts")

# フォントディレクトリが存在しない場合は作成
os.makedirs(GOOGLE_FONTS_DIR, exist_ok=True)
os.makedirs(CUSTOM_FONTS_DIR, exist_ok=True)

def get_google_fonts_list() -> Dict[str, str]:
    """
    Google Fonts APIから日本語フォントのリストを取得します。
    """
    # 実際にはGoogle Fonts Developer APIを使用するか、事前にリストを準備します。
    # ここでは例としていくつかの日本語フォントをハードコードします。
    # 実際のプロダクション環境では、APIキーを設定して動的に取得することを推奨します。
    return {
        "Noto Sans JP": "NotoSansJP-Regular.ttf",
        "Zen Kaku Gothic New": "ZenKakuGothicNew-Regular.ttf",
        "M PLUS Rounded 1c": "MPLUSRounded1c-Regular.ttf",
    }

def download_google_font(font_name: str, file_name: str) -> str or None:
    """
    指定されたGoogle Fontをダウンロードし、ローカルに保存します。
    """
    font_path = os.path.join(GOOGLE_FONTS_DIR, file_name)
    if os.path.exists(font_path):
        st.info(f"{font_name} は既にダウンロードされています。")
        return font_path

    # Google FontsのダウンロードURLは、各フォントのCSSから取得する必要があります。
    # ここではNoto Sans JPの例を示しますが、他のフォントも同様に探し出す必要があります。
    # 実際の運用では、Google Fonts APIを利用してダウンロードURLを取得する方が良いでしょう。
    st.info(f"{font_name} をダウンロード中...")
    try:
        # 例: Noto Sans JPのダウンロードURL (実際にはweightなどを指定する)
        # 暫定的にCDNから直接ダウンロードするが、これは本番環境では適切ではない可能性がある。
        # Google Fonts APIの利用を検討するか、woff2ファイルを事前に用意する。
        if "NotoSansJP" in file_name:
            url = f"https://fonts.gstatic.com/ea/notosansjp/v5/NotoSansJP-Regular.otf"
        elif "ZenKakuGothicNew" in file_name:
            url = f"https://fonts.gstatic.com/s/zenkakugothicnew/v18/DtNoDxwz6Eo_MvPekbS3JY4_RzEw7_I_g-Y-H9_G.ttf"
        elif "MPLUSRounded1c" in file_name:
            url = f"https://fonts.gstatic.com/s/mplusrounded1c/v25/VibzRvVHAxLgFG7FD5nkKLmrBP4.ttf"
        else:
            st.warning(f"'{font_name}' のダウンロードURLが見つかりませんでした。手動でアップロードしてください。")
            return None

        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(font_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        st.success(f"{font_name} のダウンロードが完了しました。", icon="\u2705")
        return font_path
    except Exception as e:
        st.error(f"{font_name} のダウンロード中にエラーが発生しました: {e}", icon="\u274C")
        return None

def upload_custom_font(uploaded_file) -> str or None:
    """
    ユーザーがアップロードしたカスタムフォントファイルを保存します。
    """
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if file_extension not in [".ttf", ".otf"]:
            st.error("対応しているフォント形式は .ttf および .otf です。", icon="\u274C")
            return None

        font_path = os.path.join(CUSTOM_FONTS_DIR, uploaded_file.name)
        try:
            with open(font_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"カスタムフォント '{uploaded_file.name}' がアップロードされました。", icon="\u2705")
            return font_path
        except Exception as e:
            st.error(f"カスタムフォントのアップロード中にエラーが発生しました: {e}", icon="\u274C")
            return None
    return None

def get_available_fonts() -> List[str]:
    """
    利用可能な全てのフォントファイル（Google Fontsとカスタムフォント）のパスをリストで返します。
    """
    available_fonts = []
    for root, _, files in os.walk(FONT_DIR):
        for file in files:
            if file.lower().endswith(('.ttf', '.otf')):
                available_fonts.append(os.path.join(root, file))
    return available_fonts

def get_font_display_name(font_path: str) -> str:
    """
    フォントファイルのパスから表示名を生成します。
    """
    return os.path.basename(font_path).split('.')[0]

# Streamlit Session Stateでの利用例:
# if 'available_fonts' not in st.session_state:
#     st.session_state.available_fonts = get_available_fonts()
# if 'selected_font' not in st.session_state:
#     st.session_state.selected_font = None

# st.sidebar.header("フォント管理")

# # Google Fontsの選択とダウンロード
# st.sidebar.subheader("Google日本語フォント")
# google_fonts = get_google_fonts_list()
# selected_google_font_name = st.sidebar.selectbox(
#     "ダウンロードするフォントを選択",
#     list(google_fonts.keys()),
#     key="google_font_selector"
# )
# if st.sidebar.button(f"{selected_google_font_name} をダウンロード"):
#     font_file = google_fonts[selected_google_font_name]
#     downloaded_path = download_google_font(selected_google_font_name, font_file)
#     if downloaded_path and downloaded_path not in st.session_state.available_fonts:
#         st.session_state.available_fonts.append(downloaded_path)
#         st.experimental_rerun()

# # カスタムフォントのアップロード
# st.sidebar.subheader("カスタムフォント")
# custom_font_file = st.sidebar.file_uploader("カスタムフォントをアップロード (.ttf/.otf)", type=["ttf", "otf"])
# if custom_font_file:
#     uploaded_path = upload_custom_font(custom_font_file)
#     if uploaded_path and uploaded_path not in st.session_state.available_fonts:
#         st.session_state.available_fonts.append(uploaded_path)
#         st.experimental_rerun()

# # 利用可能なフォントの表示と選択
# if st.session_state.available_fonts:
#     st.sidebar.subheader("利用可能なフォント")
#     font_display_names = [get_font_display_name(f) for f in st.session_state.available_fonts]
#     selected_font_display_name = st.sidebar.selectbox(
#         "使用するフォントを選択",
#         font_display_names,
#         key="app_font_selector"
#     )
#     st.session_state.selected_font = next(
#         (f for f in st.session_state.available_fonts if get_font_display_name(f) == selected_font_display_name),
#         None
#     )
#     if st.session_state.selected_font:
#         st.sidebar.write(f"選択中のフォント: {get_font_display_name(st.session_state.selected_font)}")
