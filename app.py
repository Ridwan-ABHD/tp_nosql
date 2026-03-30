import streamlit as st
from gestion import social_media_app

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except Exception:  # Compatibilite selon version Streamlit
    get_script_run_ctx = None

# Utiliser la commande : "streamlit run tp_nosql/app.py" pour lancer l'application


def main():
    st.set_page_config(page_title="SocialDB", page_icon="💬", layout="wide")
    social_media_app()


if __name__ == "__main__":
    has_streamlit_context = get_script_run_ctx is not None and get_script_run_ctx() is not None
    if not has_streamlit_context:
        print("Ce script doit etre lance avec: streamlit run tp_nosql/app.py")
    else:
        main()
