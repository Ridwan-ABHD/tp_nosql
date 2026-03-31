## Imports
import streamlit as st
from gestion import (
    get_db,
    get_collections,
    ensure_indexes,
    load_users,
    agg_posts_par_utilisateur,
    agg_moyenne_likes,
    get_comments_per_post,
    get_top_engagement,
    render_post_creation,
    render_feed,
    render_user_creation,
    render_profile,
)
from pymongo.errors import PyMongoError


def render_accueil(users_col, posts_col, comments_col):
    """Page Accueil : affiche les statistiques de la plateforme."""
    st.title("Accueil - SocialDB")

    # Indicateurs globaux avec st.metric
    
    stats = agg_moyenne_likes(posts_col)
    nb_users = users_col.count_documents({})
    nb_posts = stats.get("total_posts", 0)
    nb_comments = comments_col.count_documents({})
    moyenne_likes = stats.get("moyenne_likes", 0) or 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Utilisateurs", nb_users)
    with col2:
        st.metric("Publications", nb_posts)
    with col3:
        st.metric("Commentaires", nb_comments)
    with col4:
        st.metric("Moy. likes / post", f"{moyenne_likes:.2f}")

    st.divider()


    # Deux colonnes : Top 5 contributeurs | Top 10 engagement
    
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Top 5 des contributeurs")
        posts_par_user = agg_posts_par_utilisateur(users_col, posts_col)
        if posts_par_user:
            for i, entry in enumerate(posts_par_user, start=1):
                pseudo = entry.get("pseudo", "Inconnu")
                total = entry.get("total_posts", 0)
                st.write(f"{i}. {pseudo} - {total} publication{'s' if total > 1 else ''}")
        else:
            st.info("Aucune publication pour le moment.")

    with col_right:
        st.subheader("Top 10 de l'engagement")
        top_engagement = get_top_engagement(posts_col)
        
        if top_engagement:
            for i, entry in enumerate(top_engagement, start=1):
                auteur = entry.get("pseudo_auteur", "Inconnu")
                nb_com = entry.get("nb_commentaires", 0)
                likes = entry.get("likes", 0)
                score = entry.get("score_engagement", 0)
                st.write(f"{i}. {auteur} - {nb_com} commentaire{'s' if nb_com > 1 else ''}, {likes} like{'s' if likes > 1 else ''} (Score: {score})")
        else:
            st.info("Aucune publication pour le moment.")

    st.divider()

    ## Top 3 des publications les plus commentees
    st.subheader("Top 3 des publications les plus commentees")
    top3 = get_comments_per_post(posts_col)[:3]
    
    if top3:
        for i, entry in enumerate(top3, start=1):
            auteur = entry.get("pseudo_auteur", "Inconnu")
            contenu = entry.get("contenu", "")
            apercu = (contenu[:50] + "...") if len(contenu) > 50 else (contenu or "-")
            nb_com = entry.get("nb_commentaires", 0)
            likes = entry.get("likes", 0)
            st.write(f"{i}. **{auteur}** : \"{apercu}\" - {nb_com} commentaire{'s' if nb_com > 1 else ''}, {likes} like{'s' if likes > 1 else ''}")
    else:
        st.info("Aucune publication pour le moment.")


def main():
    st.set_page_config(page_title="SocialDB", page_icon="S", layout="wide")

    # Connexion MongoDB
    try:
        db = get_db()
        db.command("ping")
        users_col, posts_col, comments_col = get_collections()
        ensure_indexes(users_col)
    except PyMongoError as exc:
        st.error("Connexion MongoDB impossible. Verifie que MongoDB est demarre sur localhost:27017.")
        st.error(str(exc))
        st.stop()


    # Navigation dans la sidebar (st.sidebar.radio)

    st.sidebar.title("Navigation")

    # Selecteur d'utilisateur actif pour interagir
    users = load_users(users_col)
    if users:
        active_user_options = {u.get("pseudo", "sans pseudo"): str(u["_id"]) for u in users}
        selected_active_pseudo = st.sidebar.selectbox(
            "Interagir en tant que",
            options=list(active_user_options.keys()),
            index=0,
        )
        st.session_state["active_user_id"] = active_user_options[selected_active_pseudo]

    # Menu de navigation : 5 pages
    page = st.sidebar.radio(
        "Aller vers",
        ["Accueil", "Utilisateurs", "Posts", "Fil", "Profil"],
        index=0,
    )

    # Affichage de la page selectionnee
 
    if page == "Accueil":
        render_accueil(users_col, posts_col, comments_col)
    elif page == "Utilisateurs":
        render_user_creation(users_col)
    elif page == "Posts":
        render_post_creation(users_col, posts_col)
    elif page == "Fil":
        render_feed(users_col, posts_col, comments_col)
    elif page == "Profil":
        render_profile(users_col, posts_col)


if __name__ == "__main__":
    main()
