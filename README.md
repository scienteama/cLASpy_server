# cLASpy Server

Serveur API Web pour cLASpy_T - Plateforme d'analyse de données et apprentissage automatique.

## Installation

### Prérequis

- Python 3.11 ou supérieur
- Poetry (gestionnaire de dépendances)

### Installation rapide

1. **Cloner le dépôt**
   ```bash
   git clone <repository-url>
   cd cLASpy_Server
   ```

2. **Installer les dépendances avec Poetry**
   ```bash
   poetry install
   ```

3. **Configurer l'environnement**
   ```bash
   cp .env .env.backup  # Sauvegarder si nécessaire
   # Éditer .env selon vos besoins
   ```

## Configuration de la base de données

Le serveur supporte deux modes de base de données :

### Mode PostgreSQL (Serveur)

Pour les environnements de production sur serveur avec PostgreSQL :

```env
ENV=development
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

**Initialisation :**
```bash
# Appliquer les migrations
poetry run alembic -c db/alembic.ini upgrade head

# Peupler la base avec les données par défaut
poetry run python db/seed.py
```

### Mode SQLite (Bureau - Local)

Pour le développement local sans PostgreSQL, utilisez SQLite :

```env
ENV=desktop
```

**Initialisation :**
```bash
# Créer les tables SQLite
poetry run python db/init_sqlite.py

# Peupler la base avec les données par défaut
poetry run python -m db.seed
```

La base SQLite sera créée dans `data/db/desktop.db`.

## Lancement de l'application

### Démarrage simple

```bash
poetry run python launcher.py
```

### Avec rechargement automatique (développement)

Le rechargement automatique est activé automatiquement en mode `development`.

### Configuration des ports et hôtes

Modifiez les variables dans `.env` :
- `PORT` : Port d'écoute (défaut: 8000)
- `HOST` : Interface d'écoute (défaut: localhost)

## Développement

### Formatage du code

```bash
poetry run black .
```

### Vérification du code (linting)

```bash
# Vérifier les problèmes
poetry run ruff check .

# Corriger automatiquement
poetry run ruff check . --fix
```

### Migrations de base de données

#### Pour PostgreSQL (avec Alembic)

Créer une nouvelle migration :
```bash
poetry run alembic -c db/alembic.ini revision --autogenerate -m "Description de la migration"
```

Appliquer les migrations :
```bash
poetry run alembic -c db/alembic.ini upgrade head
```

#### Pour SQLite (mode bureau)

SQLite n'utilise pas les migrations Alembic. Utilisez plutôt :
```bash
poetry run python db/init_sqlite.py
```

### Infrastructure de tâches (TaskRunner mode serveur uniquement)

**Démarrer l'infrastructure :**
```bash
poetry run python -m taskrunner.cli start-infra --env-file .env
```

**Démarrer un worker :**
```bash
poetry run python -m taskrunner.cli start-worker --queue ml --env-file .env
```

## Structure du projet

```
cLASpy_Server/
├── app/                   # Code de l'application
│   ├── api/               # Routes et middlewares API
│   ├── core/              # Configuration et services core
│   ├── dao/               # Couche d'accès aux données
│   ├── models/            # Modèles SQLAlchemy
│   ├── schemas/           # Schémas Pydantic
│   ├── services/          # Logique métier
│   └── utils/             # Utilitaires
├── db/                    # Scripts de base de données
│   ├── migrations/        # Migrations Alembic
│   ├── init_sqlite.py     # Initialisation SQLite
│   └── seed.py            # Init BDD
├── data/                  # Données persistantes
├── certificats/           # Certificats SSL (optionnel)
├── launcher.py            # Point d'entrée principal
├── pyproject.toml         # Configuration Poetry
└── README.md              # Ce fichier
```

## API Documentation

Une fois l'application démarrée, la documentation interactive Swagger est disponible sur :
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Sécurité

### Certificats SSL (optionnel)

Pour activer HTTPS en développement, placez les certificats dans le dossier `certificats/` :
- `claspy_cert.pem` : Certificat
- `claspy_key.pem` : Clé privée

Le serveur utilisera automatiquement HTTPS si ces fichiers sont présents (sauf en production).

## Variables

### Variables principales

- `ENV` : Environnement (`development`, `desktop`, `production`)
- `DATABASE_URL` : URL de connexion à la base de données
- `SECRET_KEY` : Clé secrète pour JWT
- `PORT` : Port d'écoute (défaut: 8000)
- `HOST` : Interface d'écoute (défaut: localhost)

### Variables optionnelles

- `UPLOAD_DIR` : Répertoire d'upload (défaut: data/storage)
- `TEMP_DIR` : Répertoire temporaire (défaut: data/storage/temp)
- `TRASH_DIR` : Corbeille (défaut: data/storage/trash)
- `RECOVERY_DIR` : Récupération (défaut: data/storage/recovery)
- `DEFAULT_OUTPUT_DIR` : Sorties par défaut (défaut: data/storage/outputs)

## Support

Pour les questions ou problèmes, contactez l'équipe de développement.

## License

(See `LICENSE` file for further details).

CeCILL FREE SOFTWARE LICENSE AGREEMENT

Version 2.1 dated 2013-06-21

### Notice

This Agreement is a Free Software license agreement that is the result
of discussions between its authors in order to ensure compliance with
the two main principles guiding its drafting:

- firstly, compliance with the principles governing the distribution
    of Free Software: access to source code, broad rights granted to users,

- secondly, the election of a governing law, French law, with which it
    is conformant, both as regards the law of torts and intellectual
    property law, and the protection that it offers to both authors and
    holders of the economic rights over software.

The authors of the CeCILL (for Ce[a] C[nrs] I[nria] L[ogiciel] L[ibre])
license are:

Commissariat à l'énergie atomique et aux énergies alternatives - CEA, a
public scientific, technical and industrial research establishment,
having its principal place of business at 25 rue Leblanc, immeuble Le
Ponant D, 75015 Paris, France.

Centre National de la Recherche Scientifique - CNRS, a public scientific
and technological establishment, having its principal place of business
at 3 rue Michel-Ange, 75794 Paris cedex 16, France.

Institut National de Recherche en Informatique et en Automatique -
Inria, a public scientific and technological establishment, having its
principal place of business at Domaine de Voluceau, Rocquencourt, BP
105, 78153 Le Chesnay cedex, France.
