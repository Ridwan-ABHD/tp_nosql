from datetime import datetime
import streamlit as st
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except Exception:  # Compatibilite selon version Streamlit
    get_script_run_ctx = None


@st.cache_resource
def get_db():
    client = MongoClient("mongodb://localhost:27017")
    return client["SocialDB"]


def get_collections():
    db = get_db()
    return db["users"], db["posts"], db["comments"]


def load_users(users_col):
    return list(users_col.find().sort("created_at", -1))


def load_posts(posts_col):
    return list(posts_col.find().sort("created_at", -1))


def format_date(value):
    if not value:
        return "date inconnue"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    return str(value)


def create_user(users_col, username, email, bio):
    doc = {
        "username": username.strip(),
        "email": email.strip(),
        "bio": bio.strip(),
        "created_at": datetime.now(),
    }
    return users_col.insert_one(doc)


def create_post(posts_col, author_id, content):
    doc = {
        "author_id": ObjectId(author_id),
        "content": content.strip(),
        "created_at": datetime.now(),
        "likes_count": 0,
    }
    return posts_col.insert_one(doc)


def render_home():
    st.title("SocialDB Admin Panel")
    st.caption("Début d'application de réseau social avec MongoDB + Streamlit")
    st.write("Utilise le menu de gauche pour créer des utilisateurs, publier et consulter le fil.")


def render_user_creation(users_col):
    st.subheader("Créer un utilisateur")
    with st.form("create_user_form", clear_on_submit=True):
        username = st.text_input("Nom d'utilisateur")
        email = st.text_input("Email")
        bio = st.text_area("Bio")
        submit = st.form_submit_button("Ajouter")

    if submit:
        if not username.strip() or not email.strip():
            st.error("Le nom d'utilisateur et l'email sont obligatoires.")
            return

        try:
            create_user(users_col, username, email, bio)
            st.success("Utilisateur ajouté avec succès.")
        except PyMongoError as exc:
            st.error(f"Erreur MongoDB: {exc}")


def render_post_creation(users_col, posts_col):
    st.subheader("Créer un post")
    users = load_users(users_col)

    if not users:
        st.info("Crée d'abord au moins un utilisateur.")
        return

    user_options = {f"{u.get('username', 'sans nom')} ({u.get('email', '-')})": str(u["_id"]) for u in users}

    with st.form("create_post_form", clear_on_submit=True):
        selected_label = st.selectbox("Auteur", options=list(user_options.keys()))
        content = st.text_area("Contenu du post")
        submit = st.form_submit_button("Publier")

    if submit:
        if not content.strip():
            st.error("Le contenu du post est obligatoire.")
            return

        try:
            create_post(posts_col, user_options[selected_label], content)
            st.success("Post publié avec succès.")
        except PyMongoError as exc:
            st.error(f"Erreur MongoDB: {exc}")


def render_feed(users_col, posts_col):
    st.subheader("Fil d'actualites")
    posts = load_posts(posts_col)
    users = {str(u["_id"]): u for u in load_users(users_col)}

    if not posts:
        st.info("Aucun post pour le moment.")
        return

    for post in posts:
        author = users.get(str(post.get("author_id")))
        author_name = author.get("username", "Utilisateur inconnu") if author else "Utilisateur inconnu"
        created_at = format_date(post.get("created_at"))

        with st.container(border=True):
            st.markdown(f"**{author_name}** - {created_at}")
            st.write(post.get("content", ""))
            st.caption(f"Likes: {post.get('likes_count', 0)}")


def main():
    st.set_page_config(page_title="SocialDB", page_icon="💬", layout="wide")

    try:
        db = get_db()
        db.command("ping")
        users_col, posts_col, _comments_col = get_collections()
    except PyMongoError as exc:
        st.error("Connexion MongoDB impossible. Verifie que MongoDB est demarre sur localhost:27017.")
        st.error(str(exc))
        st.stop()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Aller vers",
        ["Accueil", "Utilisateurs", "Posts", "Fil"],
        index=0,
    )

    if page == "Accueil":
        render_home()
    elif page == "Utilisateurs":
        render_user_creation(users_col)
    elif page == "Posts":
        render_post_creation(users_col, posts_col)
    elif page == "Fil":
        render_feed(users_col, posts_col)


if __name__ == "__main__":
    has_streamlit_context = get_script_run_ctx is not None and get_script_run_ctx() is not None
    if not has_streamlit_context:
        print("Ce script doit etre lance avec: streamlit run tp_nosql/app.py")
    else:
        main()