#!/bin/bash
# Script pour publier calendrier.html sur GitHub Pages

set -e

# Chemin du fichier à publier
CALENDRIER="calendrier.html"

# Vérifier que le fichier existe
if [ ! -f "$CALENDRIER" ]; then
    echo "Erreur: Le fichier $CALENDRIER est introuvable."
    echo "Exécutez d'abord: python weekend_finder.py"
    exit 1
fi

# Variante 1: Publication sur GitHub Pages (méthode recommandée)
# Configuration requise:
#   - Un dépôt Git configuré pour GitHub Pages (branche gh-pages ou dossier docs)
#   - git installé et configuré sur votre machine
#
# Pour utiliser cette méthode, décommentez les lignes suivantes et configurez les variables
# REPO_URL="git@github.com:votre-utilisateur/votre-depot.git"
# BRANCHE="gh-pages"  # ou "main" si vous utilisez le dossier docs
# DOSSIER_DEST=""     # laissez vide pour la racine, ou "docs" pour le dossier docs

# echo "Publication sur GitHub Pages..."
# git clone "$REPO_URL" /tmp/depot-gh-pages 2>/dev/null || true
# cd /tmp/depot-gh-pages
# git checkout "$BRANCHE" 2>/dev/null || git checkout -b "$BRANCHE"
# cp "$OLDPWD/$CALENDRIER" .
# git add "$CALENDRIER"
# git commit -m "Mise à jour calendrier.html - $(date +'%Y-%m-%d %H:%M:%S')"
# git push origin "$BRANCHE"
# echo "Publication terminée: https://votre-utilisateur.github.io/votre-depot/"$CALENDRIER

# Variante 2: Copie simple dans un dépôt existant (méthode alternative)
# Placez ce script dans le répertoire de votre dépôt GitHub Pages local
# et exécutez-le après avoir généré calendrier.html

echo "========================================"
echo "Publication manuelle nécessaire"
echo "========================================"
echo ""
echo "Pour publier calendrier.html sur GitHub Pages:"
echo ""
echo "1. Assurez-vous d'avoir un dépôt GitHub configuré pour GitHub Pages"
echo "2. Clonez le dépôt sur votre machine"
echo "3. Copiez calendrier.html dans le bon emplacement:"
echo "   - Pour la branche gh-pages: copiez à la racine"
echo "   - Pour la branche main avec dossier docs: copiez dans docs/"
echo "4. Commitez et poussez les changements"
echo ""
echo "Exemple:"
echo "  git clone git@github.com:utilisateur/depot.git"
echo "  cd depôt"
echo "  cp /chemin/vers/calendrier.html ."
echo "  git add calendrier.html"
echo "  git commit -m 'Mise à jour calendrier'"
echo "  git push"
echo ""
echo "Ou simplement glisser-déposer calendrier.html sur Netlify Drop:"
echo "  https://app.netlify.com/drop"
echo ""
echo "Aucune donnée sensible n'est incluse dans calendrier.html"
echo ""

# Si vous souhaitez automatiser, configurez les variables ci-dessus
# et décommentez les lignes de la Variante 1
