from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import streamlit as st

# Connexion à MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["SocialDB"]  # Base de données du projet

# Collections
users_col = db["users"]
posts_col = db["posts"]
comments_col = db["comments"]

# Fonction pour l'application Réseaux Sociaux
def social_media_app():
    st.title("Bienvenue sur SocialDB !")
    st.write("Cette plateforme vous permet de créer des posts, de commenter et d'interagir avec d'autres utilisateurs.")

    # Section pour créer un post
    st.header("Créer un nouveau post")
    post_content = st.text_area("Contenu du post", "")
    if st.button("Publier"):
        if post_content.strip() != "":
            new_post = {
                "content": post_content,
                "created_at": datetime.now(),
                "likes": 0,
                "comments": []
            }
            posts_col.insert_one(new_post)
            st.success("Post publié avec succès !")
        else:
            st.error("Le contenu du post ne peut pas être vide.")

    # Section pour afficher les posts existants
    st.header("Posts récents")
    recent_posts = posts_col.find().sort("created_at", -1).limit(10)
    for post in recent_posts:
        st.subheader(f"Post ID: {post['_id']}")
        st.write(post["content"])
        st.write(f"Publié le: {post['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Likes: {post['likes']}")

        # Section pour ajouter un commentaire
        comment_content = st.text_input(f"Ajouter un commentaire au post {post['_id']}", key=str(post['_id']))
        if st.button(f"Commenter sur le post {post['_id']}"):
            if comment_content.strip() != "":
                new_comment = {
                    "content": comment_content,
                    "created_at": datetime.now(),
                    "post_id": post["_id"]
                }
                comments_col.insert_one(new_comment)
                posts_col.update_one({"_id": post["_id"]}, {"$push": {"comments": new_comment}})
                st.success("Commentaire ajouté avec succès !")
            else:
                st.error("Le contenu du commentaire ne peut pas être vide.")