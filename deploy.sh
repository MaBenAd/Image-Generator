#!/bin/bash

# Script de déploiement pour l'application text2image

set -e

echo "🚀 Démarrage du déploiement de l'application text2image..."

# Vérification de Docker et Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez installer Docker d'abord."
    exit 1
fi

# Vérification de Docker Compose (nouvelle syntaxe)
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez installer Docker Compose d'abord."
    exit 1
fi

# Arrêt des conteneurs existants
echo "🛑 Arrêt des conteneurs existants..."
docker compose down

# Nettoyage des images anciennes (optionnel)
read -p "Voulez-vous nettoyer les images Docker anciennes ? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Nettoyage des images Docker..."
    docker system prune -f
fi

# Construction des images
echo "🔨 Construction des images Docker..."
docker compose build --no-cache

# Démarrage des services
echo "🚀 Démarrage des services..."
docker compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 10

# Vérification du statut des services
echo "📊 Statut des services:"
docker compose ps

# Création d'un superuser (optionnel)
read -p "Voulez-vous créer un superuser Django ? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "👤 Création d'un superuser..."
    docker compose exec web python manage.py createsuperuser
fi

echo "✅ Déploiement terminé !"
echo "🌐 L'application est accessible sur: http://localhost"
echo "📊 Interface d'administration: http://localhost/admin"
echo ""
echo "📋 Commandes utiles:"
echo "  - Voir les logs: docker compose logs -f"
echo "  - Arrêter: docker compose down"
echo "  - Redémarrer: docker compose restart"
echo "  - Mettre à jour: ./deploy.sh" 