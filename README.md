# SocialDB - Application Web

Une application de réseau social construite avec **Streamlit** et **MongoDB**.

## 📋 Prérequis

Avant de lancer l'application, assurez-vous d'avoir :

- **Python 3.8+** installé
- **MongoDB** installé et en cours d'exécution localement (sur le port 27017)

## Installation

### 1. Installer les dépendances

Ouvrez un terminal dans le dossier `tp_nosql/` et exécutez :

```bash
pip install streamlit pymongo
```

Cela installe :
- **streamlit** : framework web pour l'interface utilisateur
- **pymongo** : driver MongoDB pour Python

### 2. Vérifier que MongoDB est démarré

MongoDB doit être en cours d'exécution sur `localhost:27017`. 

**Sur Windows** (si MongoDB est installé en tant que service) :
```bash
mongod
```

Ou vérifiez que le service MongoDB est actif.

##  Lancer l'application

Dans le dossier `tp_nosql/`, exécutez :

```bash
streamlit run app.py
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse :
```
http://localhost:8501
```

## 📂 Structure du projet

```
tp_nosql/
├── app.py           # Point d'entrée principal
├── gestion.py       # Fonctions métier et interfaces
├── donnees/
│   ├── Comments.csv
│   ├── Posts.csv
│   └── Users.csv
└── README.md        # Ce fichier
```

## Dépendances utilisées

| Package    | Utilité |
|-----------|---------|
| **streamlit** | Interface web interactive |
| **pymongo** | Connexion à MongoDB |
| **bson** | Gestion des ObjectId MongoDB (inclus dans pymongo) |

## Configuration

L'application se connecte à MongoDB sur :
```
mongodb://localhost:27017
```

La base de données utilisée est : `SocialDB`

Collections :
- `users` : Utilisateurs du réseau social
- `posts` : Publications
- `comments` : Commentaires

## Utilisation

Une fois l'application lancée, utilisez la barre latérale pour naviguer :

1. **Accueil** : Statistiques globales de la plateforme
2. **Utilisateurs** : Créer un nouvel utilisateur
3. **Posts** : Créer une nouvelle publication
4. **Fil** : Afficher le fil d'actualités avec chargement progressif
5. **Profil** : Consulter les profils utilisateurs

## Dépannage

**Erreur : "Connexion MongoDB impossible"**
- Assurez-vous que MongoDB est démarré
- Vérifiez qu'il écoute sur le port 27017

**Erreur : "No module named 'streamlit'"**
- Assurez-vous d'avoir exécuté `pip install streamlit pymongo`

**L'application ne s'ouvre pas dans le navigateur**
- Accédez manuellement à `http://localhost:8501`

## Notes

- Les images uploadées sont converties en base64 et stockées dans MongoDB
- Le fil d'actualités charge 5 posts à la fois pour optimiser les performances
- Les utilisateurs sont identifiés par leur pseudo (unique)

---

**Prêt à lancer ? Exécutez simplement :**
```bash
streamlit run app.py
```
