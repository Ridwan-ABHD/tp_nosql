import base64
from datetime import datetime

import streamlit as st
from bson.objectid import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError


@st.cache_resource
def get_db():
    client = MongoClient("mongodb://localhost:27017")
    return client["SocialDB"]


def get_collections():
    db = get_db()
    return db["users"], db["posts"], db["comments"]


def ensure_indexes(users_col):
    users_col.create_index("pseudo", unique=True)


def load_users(users_col):
    return list(users_col.find().sort("date", -1))


def load_posts(posts_col):
    return list(posts_col.find().sort("date", -1))


def load_comments_for_post(comments_col, post_id):
    return list(comments_col.find({"post_id": post_id}).sort("date", -1))


def format_date(value):
    if not value:
        return "date inconnue"
    if isinstance(value, datetime):
        now = datetime.now()
        delta_days = (now.date() - value.date()).days

        if delta_days <= 0:
            return value.strftime("%H:%M")
        if delta_days <= 6:
            return f"{delta_days}j"
        if delta_days < 30:
            return f"{delta_days // 7}sem"
        if delta_days < 365:
            return f"{delta_days // 30}mois"
        return f"{delta_days // 365}an"
    return str(value)


def uploaded_file_to_data_url(uploaded_file):
    if uploaded_file is None:
        return ""
    raw = uploaded_file.getvalue()
    encoded = base64.b64encode(raw).decode("ascii")
    mime_type = uploaded_file.type or "application/octet-stream"
    return f"data:{mime_type};base64,{encoded}"


def data_url_to_bytes(data_url):
    if not isinstance(data_url, str) or not data_url.startswith("data:"):
        return None
    try:
        _, b64_data = data_url.split(",", 1)
        return base64.b64decode(b64_data)
    except Exception:
        return None


def render_avatar(avatar_value, width=140):
    if not avatar_value:
        st.info("Aucun avatar")
        return

    if isinstance(avatar_value, str) and avatar_value.startswith("data:"):
        try:
            _, b64_data = avatar_value.split(",", 1)
            img_bytes = base64.b64decode(b64_data)
            st.image(img_bytes, width=width)
            return
        except Exception:
            st.warning("Avatar invalide")
            return

    st.image(avatar_value, width=width)


def render_round_avatar(avatar_value, size=140):
    if not avatar_value:
        st.info("Aucun avatar")
        return

    st.markdown(
        f"""
        <div style=\"display:flex;justify-content:center;\">
            <img src=\"{avatar_value}\" style=\"width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:3px solid #e5e7eb;\" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_post_media(post):
    media_value = post.get("media", "")
    post_type = post.get("type", "")
    if not media_value:
        return

    if post_type == "image":
        media_bytes = data_url_to_bytes(media_value)
        if media_bytes is not None:
            st.image(media_bytes, use_container_width=True)
        else:
            st.image(media_value, use_container_width=True)
    elif post_type == "video":
        media_bytes = data_url_to_bytes(media_value)
        if media_bytes is not None:
            st.video(media_bytes)
        else:
            st.video(media_value)


def relation_count(value):
    if isinstance(value, list):
        return len(value)
    if isinstance(value, int):
        return value
    return 0


def toggle_follow_user(users_col, follower_id, target_id):
    if not follower_id or not target_id or follower_id == target_id:
        return None

    follower_obj_id = ObjectId(follower_id)
    target_obj_id = ObjectId(target_id)

    follower = users_col.find_one({"_id": follower_obj_id}, {"following": 1})
    if not follower:
        return None

    following = follower.get("following", [])
    is_following = target_id in following

    if is_following:
        users_col.update_one({"_id": follower_obj_id}, {"$pull": {"following": target_id}})
        users_col.update_one({"_id": target_obj_id}, {"$pull": {"followers": follower_id}})
        return False

    users_col.update_one({"_id": follower_obj_id}, {"$addToSet": {"following": target_id}})
    users_col.update_one({"_id": target_obj_id}, {"$addToSet": {"followers": follower_id}})
    return True


def delete_post(users_col, posts_col, comments_col, post_id):
    post = posts_col.find_one({"_id": ObjectId(post_id)}, {"creator_id": 1})
    if not post:
        return False

    creator_id = post.get("creator_id")
    comments_col.delete_many({"post_id": ObjectId(post_id)})
    posts_col.delete_one({"_id": ObjectId(post_id)})

    if creator_id:
        users_col.update_one({"_id": creator_id}, {"$inc": {"numberOfPosts": -1}})

    return True


def create_user(users_col, pseudo, avatar, gender, birthday, language, biography, password):
    birthday_dt = datetime.combine(birthday, datetime.min.time())
    doc = {
        "pseudo": pseudo.strip(),
        "avatar": (avatar or "").strip(),
        "followers": [],
        "following": [],
        "numberOfPosts": 0,
        "gender": gender,
        "birthday": birthday_dt,
        "language": language.strip(),
        "biography": biography.strip(),
        "password": password,
        "date": datetime.now(),
    }
    return users_col.insert_one(doc)


def create_post(users_col, posts_col, creator_id, biography, post_type, media_data, media_name):
    doc = {
        "creator_id": ObjectId(creator_id),
        "biography": biography.strip(),
        "type": post_type,
        "media": media_data,
        "media_name": media_name,
        "like": 0,
        "share": 0,
        "date": datetime.now(),
    }
    result = posts_col.insert_one(doc)
    users_col.update_one({"_id": ObjectId(creator_id)}, {"$inc": {"numberOfPosts": 1}})
    return result


def create_comment(comments_col, user_id, post_id, text):
    doc = {
        "user_id": ObjectId(user_id),
        "text": text.strip(),
        "date": datetime.now(),
        "like": 0,
        "share": 0,
        "post_id": ObjectId(post_id),
    }
    return comments_col.insert_one(doc)


def increment_post_like(posts_col, post_id):
    posts_col.update_one({"_id": ObjectId(post_id)}, {"$inc": {"like": 1}})


def increment_post_share(posts_col, post_id):
    posts_col.update_one({"_id": ObjectId(post_id)}, {"$inc": {"share": 1}})


def increment_comment_like(comments_col, comment_id):
    comments_col.update_one({"_id": ObjectId(comment_id)}, {"$inc": {"like": 1}})


def increment_comment_share(comments_col, comment_id):
    comments_col.update_one({"_id": ObjectId(comment_id)}, {"$inc": {"share": 1}})


def toggle_post_reaction(posts_col, post_id, user_key, reaction):
    if reaction not in ["like", "share"]:
        return False

    array_field = f"{reaction}_users"
    count_field = reaction
    post = posts_col.find_one({"_id": ObjectId(post_id)}, {array_field: 1})
    users = post.get(array_field, []) if post else []

    if user_key in users:
        users.remove(user_key)
        active = False
    else:
        users.append(user_key)
        active = True

    posts_col.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {array_field: users, count_field: len(users)}},
    )
    return active


def toggle_comment_reaction(comments_col, comment_id, user_key, reaction):
    if reaction not in ["like", "share"]:
        return False

    array_field = f"{reaction}_users"
    count_field = reaction
    comment = comments_col.find_one({"_id": ObjectId(comment_id)}, {array_field: 1})
    users = comment.get(array_field, []) if comment else []

    if user_key in users:
        users.remove(user_key)
        active = False
    else:
        users.append(user_key)
        active = True

    comments_col.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {array_field: users, count_field: len(users)}},
    )
    return active


def render_home():
    st.title("SocialDB Admin Panel")
    st.caption("Schéma aligné sur USER, Posts et Comments")
    st.write("Utilise le menu de gauche pour gérer les utilisateurs, posts et commentaires.")


def render_user_creation(users_col):
    st.subheader("Créer un utilisateur")
    with st.form("create_user_form", clear_on_submit=True):
        pseudo = st.text_input("Pseudo (unique)")        
        password = st.text_input("Mot de passe", type="password")
        avatar = st.file_uploader("Uploader un avatar", type=["png", "jpg", "jpeg", "webp"])
        gender = st.selectbox("Genre", ["Non spécifié", "Homme", "Femme", "Autre"], index=0)
        birthday = st.date_input("Birthday")
        language = st.selectbox("Langage", ["Français", "English"], index=0)
        biography = st.text_area("Biographie")
        submit = st.form_submit_button("Ajouter")

    if submit:
        if not pseudo.strip() or not password:
            st.error("Pseudo et mot de passe sont obligatoires.")
            return

        try:
            avatar_value = uploaded_file_to_data_url(avatar)
            create_user(users_col, pseudo, avatar_value, gender, birthday, language, biography, password)
            st.success("Utilisateur ajouté avec succes.")
        except PyMongoError as exc:
            st.error(f"Erreur MongoDB: {exc}")


def render_profile(users_col, posts_col):
    st.markdown("<h2 style='text-align:center;'>Profil utilisateur</h2>", unsafe_allow_html=True)
    users = load_users(users_col)

    if not users:
        st.info("Aucun utilisateur disponible.")
        return

    options = {u.get("pseudo", "sans pseudo"): u for u in users}
    pseudo_list = list(options.keys())
    default_pseudo = st.session_state.get("selected_profile_pseudo")
    default_index = pseudo_list.index(default_pseudo) if default_pseudo in pseudo_list else 0

    selected_pseudo = st.selectbox(
        "Sélectionner un profil",
        options=pseudo_list,
        index=default_index,
        key="profile_select_pseudo",
    )
    st.session_state["selected_profile_pseudo"] = selected_pseudo
    user = options[selected_pseudo]

    user_id = user.get("_id")
    target_user_id = str(user_id)
    active_user_id = str(st.session_state.get("active_user_id", ""))
    user_posts = list(posts_col.find({"creator_id": user_id}).sort("date", -1))
    total_likes = sum(int(p.get("like", 0)) for p in user_posts)

    col_left, col_right = st.columns([1, 1])
    with col_left:
        render_round_avatar(user.get("avatar", ""), size=170)
        st.markdown(f"### {user.get('pseudo', 'sans pseudo')}")
        st.write(user.get("biography", "Aucune biographie"))

        if active_user_id and active_user_id != target_user_id:
            active_user = users_col.find_one({"_id": ObjectId(active_user_id)}, {"following": 1})
            active_following = active_user.get("following", []) if active_user else []
            is_following = target_user_id in active_following
            follow_label = "Se desabonner" if is_following else "S'abonner"

            if st.button(follow_label, key=f"follow_btn_{target_user_id}"):
                try:
                    toggle_follow_user(users_col, active_user_id, target_user_id)
                    st.rerun()
                except PyMongoError as exc:
                    st.error(f"Erreur MongoDB: {exc}")
        else:
            st.caption("Tu ne peux pas t'abonner a ton propre profil.")

    with col_right:
        st.markdown("### Statistiques")
        stat_col_1, stat_col_2 = st.columns(2)
        with stat_col_1:
            st.metric("Posts", int(user.get("numberOfPosts", len(user_posts))))
            st.metric("Abonnés", relation_count(user.get("followers", [])))
        with stat_col_2:
            st.metric("Likes totaux", total_likes)
            st.metric("Abonnements", relation_count(user.get("following", [])))

    st.markdown("<h4 style='text-align:center;'>Posts de l'utilisateur</h4>", unsafe_allow_html=True)
    if not user_posts:
        st.caption("Aucun post pour cet utilisateur")
        return

    for post in user_posts:
        left, center, right = st.columns([1, 2.4, 1])
        with center:
            with st.container(border=True):
                st.caption(format_date(post.get("date")))
                st.write(post.get("biography", ""))
                render_post_media(post)
                st.caption(f"Likes: {post.get('like', 0)} | Shares: {post.get('share', 0)}")


def render_post_creation(users_col, posts_col):
    st.subheader("Créer un post")
    users = load_users(users_col)

    if not users:
        st.info("Crée d'abord au moins un utilisateur.")
        return

    user_options = {u.get("pseudo", "sans pseudo"): str(u["_id"]) for u in users}

    with st.form("create_post_form", clear_on_submit=True):
        selected_label = st.selectbox("Creator", options=list(user_options.keys()))
        biography = st.text_area("Biographie")
        media_file = st.file_uploader("Ajouter une image ou une vidéo", type=["png", "jpg", "jpeg", "webp", "mp4", "mov", "avi", "mkv"])
        submit = st.form_submit_button("Publier")

    if submit:
        biography_value = biography.strip()
        has_biography = bool(biography_value)
        has_media = media_file is not None

        if not has_biography and not has_media:
            st.error("Ajoute une biographie, une image/vidéo, ou les deux.")
            return

        post_type = "text"
        media_data = ""
        media_name = ""

        if has_media:
            media_type = media_file.type or ""
            if media_type.startswith("image/"):
                post_type = "image"
            elif media_type.startswith("video/"):
                post_type = "video"
            else:
                st.error("Format media non supporte. Utilise une image ou une vidéo.")
                return
            media_data = uploaded_file_to_data_url(media_file)
            media_name = media_file.name

        try:
            create_post(
                users_col,
                posts_col,
                user_options[selected_label],
                biography_value,
                post_type,
                media_data,
                media_name,
            )
            st.success("Post publié avec succès.")
        except PyMongoError as exc:
            st.error(f"Erreur MongoDB: {exc}")


def render_feed(users_col, posts_col, comments_col):
    st.markdown("<h2 style='text-align:center;'>Fil d'actualités</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        .stButton > button {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
            padding: 0.15rem 0.4rem !important;
        }
        .stButton > button:hover {
            background: #868686 !important;
        }
        [class*="st-key-go_profile_"] button {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            min-height: 1.35rem !important;
            line-height: 1.05 !important;
            margin-top: 0.80rem !important;
        }
        [class*="st-key-post_menu_btn_"] button {
            color: #dc2626 !important;
            font-size: 24px !important;
            font-weight: 800 !important;
            min-height: 1.35rem !important;
            line-height: 1 !important;
        }
        [class*="st-key-post_menu_btn_"] button:hover {
            background: #fecaca !important;
        }
        [class*="st-key-delete_post_btn_"] button {
            background: #dc2626 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    posts = load_posts(posts_col)
    users = {str(u["_id"]): u for u in load_users(users_col)}

    if not posts:
        st.info("Aucun post pour le moment.")
        return

    for post in posts:
        creator = users.get(str(post.get("creator_id")))
        creator_name = creator.get("pseudo", "Utilisateur inconnu") if creator else "Utilisateur inconnu"
        created_at = format_date(post.get("date"))
        post_id = post.get("_id")
        menu_state_key = f"post_menu_open_{post_id}"
        active_user_key = str(st.session_state.get("active_user_id", "anonymous"))

        post_like_users = post.get("like_users", [])
        post_share_users = post.get("share_users", [])
        post_liked = active_user_key in post_like_users
        post_shared = active_user_key in post_share_users

        comments = load_comments_for_post(comments_col, post_id)

        left, center, right = st.columns([1, 2.6, 1])
        with center:
            if menu_state_key not in st.session_state:
                st.session_state[menu_state_key] = False

            post_col, menu_col = st.columns([14, 1], vertical_alignment="top")

            with post_col:
                with st.container(border=True):
                    header_avatar_col, header_text_col = st.columns([0.9, 8], vertical_alignment="center")
                    with header_avatar_col:
                        avatar_value = creator.get("avatar", "") if creator else ""
                        if avatar_value:
                            st.markdown(
                                f"""
                                <div style="display:flex;align-items:center;justify-content:center;">
                                    <img src="{avatar_value}" style="width:44px;height:44px;border-radius:50%;object-fit:cover;border:2px solid #d1d5db;" />
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                """
                                <div style="width:44px;height:44px;border-radius:50%;background:#4b5563;color:#ffffff;display:flex;align-items:center;justify-content:center;font-size:20px;">
                                    👤
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                    with header_text_col:
                        name_col, date_col = st.columns([4, 1], vertical_alignment="center")
                        with name_col:
                            if creator:
                                if st.button(f"{creator_name}", key=f"go_profile_{post_id}"):
                                    st.session_state["selected_profile_pseudo"] = creator_name
                                    st.session_state["pending_page"] = "Profil"
                                    st.rerun()
                            else:
                                st.markdown("**Utilisateur inconnu**")
                        with date_col:
                            st.markdown(
                                f"<div style='text-align:right;color:#6b7280;font-size:14px;'>{created_at}</div>",
                                unsafe_allow_html=True,
                            )

                    st.write(post.get("biography", ""))
                    render_post_media(post)

                    col_like, col_spacer, col_share = st.columns([1, 4, 1])
                    with col_like:
                        like_icon = "❤️" if post_liked else "🤍"
                        if st.button(f"{like_icon} {post.get('like', 0)}", key=f"post_like_{post_id}"):
                            try:
                                toggle_post_reaction(posts_col, str(post_id), active_user_key, "like")
                                st.rerun()
                            except PyMongoError as exc:
                                st.error(f"Erreur MongoDB: {exc}")

                    with col_share:
                        share_icon = "🔁" if post_shared else "🔄"
                        if st.button(f"{share_icon} {post.get('share', 0)}", key=f"post_share_{post_id}"):
                            try:
                                toggle_post_reaction(posts_col, str(post_id), active_user_key, "share")
                                st.rerun()
                            except PyMongoError as exc:
                                st.error(f"Erreur MongoDB: {exc}")

                    st.markdown(
                        f"""
                        <div style="background:#5b5b5b;border-left:4px solid #2f2f2f;color:#ffffff;padding:8px 10px;border-radius:8px;margin:10px 0 8px 0;font-weight:600;">
                            Commentaires ({len(comments)})
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if comments:
                        for comment in comments:
                            comment_user = users.get(str(comment.get("user_id")))
                            comment_user_name = comment_user.get("pseudo", "Utilisateur inconnu") if comment_user else "Utilisateur inconnu"
                            comment_id = comment.get("_id")

                            comment_like_users = comment.get("like_users", [])
                            comment_liked = active_user_key in comment_like_users

                            c_msg, c_like = st.columns([6, 1], vertical_alignment="center")
                            with c_msg:
                                st.markdown(
                                    f"""
                                    <div style="background:#3a3a3a;border:1px solid #2c2c2c;border-radius:10px;padding:8px 10px;margin:8px 0;color:#f3f4f6;min-height:76px;">
                                        <div style="font-size:12px;color:#d1d5db;">{comment_user_name} - {format_date(comment.get('date'))}</div>
                                        <div style="margin-top:4px;">{comment.get('text', '')}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            with c_like:
                                c_like_icon = "❤️" if comment_liked else "🤍"
                                like_count = comment.get("like", 0)
                                if st.button(f"{c_like_icon}\n{like_count}", key=f"comment_like_{comment_id}"):
                                    try:
                                        toggle_comment_reaction(comments_col, str(comment_id), active_user_key, "like")
                                        st.rerun()
                                    except PyMongoError as exc:
                                        st.error(f"Erreur MongoDB: {exc}")
                    else:
                        st.caption("Aucun commentaire")

                    if users:
                        active_comment_user = str(st.session_state.get("active_user_id", ""))
                        active_comment_profile = users.get(active_comment_user)

                        if active_comment_profile:
                            st.caption(f"Commentaire en tant que: {active_comment_profile.get('pseudo', 'Utilisateur inconnu')}")

                            with st.form(f"comment_form_{post_id}", clear_on_submit=True):
                                new_comment = st.text_input("Ajouter un commentaire", key=f"comment_{post_id}")
                                submit_comment = st.form_submit_button("Commenter")

                            if submit_comment:
                                if not new_comment.strip():
                                    st.error("Le texte du commentaire est obligatoire.")
                                else:
                                    try:
                                        create_comment(comments_col, active_comment_user, str(post_id), new_comment)
                                        st.success("Commentaire ajoute avec succes.")
                                    except PyMongoError as exc:
                                        st.error(f"Erreur MongoDB: {exc}")
                        else:
                            st.warning("Selectionne un utilisateur actif dans la navigation pour commenter.")

            with menu_col:
                if st.button("⋮", key=f"post_menu_btn_{post_id}"):
                    st.session_state[menu_state_key] = not st.session_state[menu_state_key]

                if st.session_state.get(menu_state_key, False):
                    if st.button("🗑", key=f"delete_post_btn_{post_id}"):
                        try:
                            delete_post(users_col, posts_col, comments_col, str(post_id))
                            st.success("Post supprime.")
                            st.rerun()
                        except PyMongoError as exc:
                            st.error(f"Erreur MongoDB: {exc}")


def social_media_app():
    try:
        db = get_db()
        db.command("ping")
        users_col, posts_col, comments_col = get_collections()
        ensure_indexes(users_col)
    except PyMongoError as exc:
        st.error("Connexion MongoDB impossible. Verifie que MongoDB est demarre sur localhost:27017.")
        st.error(str(exc))
        st.stop()

    if "page" not in st.session_state:
        st.session_state["page"] = "Accueil"

    pending_page = st.session_state.pop("pending_page", None)
    if pending_page in ["Accueil", "Utilisateurs", "Posts", "Fil", "Profil"]:
        st.session_state["page"] = pending_page

    st.sidebar.title("Navigation")
    users = load_users(users_col)
    if users:
        active_user_options = {u.get("pseudo", "sans pseudo"): str(u["_id"]) for u in users}
        selected_active_pseudo = st.sidebar.selectbox(
            "Interagir en tant que",
            options=list(active_user_options.keys()),
            index=0,
        )
        st.session_state["active_user_id"] = active_user_options[selected_active_pseudo]

    page = st.sidebar.radio(
        "Aller vers",
        ["Accueil", "Utilisateurs", "Posts", "Fil", "Profil"],
        key="page",
    )

    if page == "Accueil":
        render_home()
    elif page == "Utilisateurs":
        render_user_creation(users_col)
    elif page == "Posts":
        render_post_creation(users_col, posts_col)
    elif page == "Fil":
        render_feed(users_col, posts_col, comments_col)
    elif page == "Profil":
        render_profile(users_col, posts_col)
