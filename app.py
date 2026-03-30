import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

# Connexion à MongoDB
# On se connecte à l'instance locale sur le port par défaut
client = MongoClient("mongodb://localhost:27017")
db = client["SocialDB"]  # Base de données du projet

# Collections
users_col = db["users"]
posts_col = db["posts"]
comments_col = db["comments"]

# Configuration de la page 
st.set_page_config(page_title="SocialDB", page_icon="💬", layout="wide")
