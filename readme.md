# Ticky - Plateforme de Billetterie En Ligne

Ticky est une plateforme moderne de vente de billets en ligne qui permet aux organisateurs de créer et gérer leurs événements, et aux utilisateurs d'acheter des billets en toute simplicité.

## Fonctionnalités

- Création et gestion d'événements
- Vente de billets en ligne
- Gestion des participants
- Système de paiement sécurisé
- Génération de billets électroniques
- Dashboard pour les organisateurs

## Prérequis

- Python 3.12+
- pip
- virtualenv ou venv

## Installation

1. Cloner le projet depuis GitHub :

```bash
git clone https://github.com/votre-username/ticky.git
cd ticky
```

2. Créer un environnement virtuel :

```bash
python -m venv venv
source venv/bin/activate  # Sur Linux/Mac
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :

```bash
cp .env.example .env
# Modifier le fichier .env avec vos configurations
```

5. Lancer les migrations :

```bash
python manage.py migrate
```

6. Démarrer le serveur :

```bash
python manage.py runserver
```

Le site sera accessible à l'adresse : http://localhost:8000

## Technologies Utilisées

- Django
- SQlite (dev) - MySQL (prod)
- Bootstrap5 ou tailwindcss
- JavaScript (vanilla)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer votre branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.