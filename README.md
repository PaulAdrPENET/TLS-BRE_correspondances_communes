# Weekend Finder - TLS ↔ BRE

Outil pour trouver les meilleures correspondances de vols directs depuis Toulouse (TLS) et Brême (BRE) pour organiser des week-ends ensemble.

## 📋 Description

Deux personnes partant de Toulouse et Brême veulent se retrouver dans une même ville avec des vols directs depuis les deux aéroports, pendant un week-end (2 à 4 jours), au coût total minimal et avec le maximum de temps ensemble.

Cet outil:
- Charge les routes aériennes depuis les deux aéroports (fichiers CSV)
- Identifie les destinations communes
- Énumère toutes les combinaisons de week-end faisables
- Calcule les scores (coût total et durée sur place)
- Produit un fichier Excel avec les résultats détaillés
- Génère une page HTML interactive pour visualiser les options

## 🛠️ Installation

### Prérequis
- Python 3.11 ou supérieur
- pip

### Dépendances
```bash
pip install pandas openpyxl
```

Ou utilisez le fichier requirements.txt:
```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

### 1. Préparer les données

**Le script utilise uniquement des fichiers CSV en entrée.**

Placez vos fichiers dans le même dossier que `weekend_finder.py`:
- `routes_tls.csv` - Routes depuis Toulouse
- `routes_bre.csv` - Routes depuis Brême

**Format requis pour les CSV:**
- Colonnes: `destination`, `iata`, `compagnie`, `jours`, `debut`, `fin`
- `jours`: jours d'exploitation (1=lundi … 7=dimanche), séparés par des virgules
- `debut` et `fin`: dates au format YYYY-MM-DD

Exemple de ligne:
```csv
destination,iata,compagnie,jours,debut,fin
Munich,MUC,Lufthansa,1,2,3,4,5,6,7,2026-10-25,2027-03-28
```

**Note:** Les fichiers `routes_tls.csv` et `routes_bre.csv` sont fournis avec des données d'exemple.

**Format des données:**
- Onglet/colonne `routes_tls`: destination, iata, compagnie, jours, debut, fin
- Onglet/colonne `routes_bre`: destination, iata, compagnie, jours, debut, fin
- `jours`: jours d'exploitation (1=lundi … 7=dimanche), séparés par des virgules
- `debut` et `fin`: dates au format YYYY-MM-DD

### 2. Exécuter le script

```bash
python weekend_finder.py
```

### 3. Résultats

Le script génère deux fichiers:
- `resultats.xlsx`: Résultats détaillés avec deux onglets
  - `combinations`: Toutes les combinaisons valides
  - `synthese`: Synthèse par destination
- `calendrier.html`: Page HTML interactive pour visualiser les options

## 📊 Fichiers générés

### resultats.xlsx
Contient toutes les combinaisons de week-end valides avec:
- Destination (nom et code IATA)
- Formule de week-end (sam→dim, ven→dim, etc.)
- Dates d'aller et de retour
- Durée en jours et nuits
- Prix estimés pour TLS et BRE
- Prix total

### calendrier.html
Page web autonome avec:
- Calendrier de novembre 2026 à mars 2027
- Jours colorés selon le nombre d'options disponibles
- Clic sur un jour pour afficher les options détaillées
- Filtres par destination, durée et formule
- Badge "Meilleur total du jour" pour l'option la moins chère

## 🌐 Publication

Pour partager le calendrier avec une autre personne:

### Méthode 1: GitHub Pages (recommandé)

1. Créez un dépôt GitHub
2. Configurez-le pour GitHub Pages (dans Settings → Pages)
3. Exécutez:
   ```bash
   python weekend_finder.py && ./publier.sh
   ```
4. Le fichier sera accessible à l'URL du dépôt GitHub Pages

### Méthode 2: Netlify Drop (sans Git)

1. Allez sur https://app.netlify.com/drop
2. Glissez-déposez le fichier `calendrier.html`
3. Vous obtiendrez une URL publique

### Méthode 3: Ouverture locale

Double-cliquez simplement sur `calendrier.html` pour l'ouvrir dans votre navigateur.

## 📝 Mettre à jour les routes et les prix

### Ajouter de nouvelles routes

1. Ouvrez `routes.xlsx`
2. Ajoutez les nouvelles routes dans les onglets `routes_tls` et `routes_bre`
3. Assurez-vous que les codes IATA sont corrects pour la correspondance

### Mettre à jour les prix

Les prix sont actuellement simulés dans le code. Pour utiliser des prix réels:

1. Modifiez la fonction `calculer_scores()` dans `weekend_finder.py`
2. Ajoutez vos données de prix (par exemple depuis un fichier CSV supplémentaire)
3. Ou modifiez directement les colonnes `prix_tls`, `prix_bre`, `prix_total` dans `resultats.xlsx`

## 🎯 Critères d'acceptation

Le script a été validé avec les critères suivants:
- ✅ 21 vendredis d'ancrage
- ✅ 439 options au total
- ✅ Munich, Amsterdam, Istanbul, Londres: 105 options chacun (21 × 5 formules)
- ✅ Alicante: 19 options (17 ven→dim + 2 jeu→dim)
- ✅ Malaga, Tenerife, Fuerteventura, Palma: 0 options
- ✅ Le HTML s'ouvre en local par double-clic
- ✅ Clic sur un jour bleu affiche les options

## 📦 Fichiers du projet

- `weekend_finder.py`: Script principal
- `routes_tls.csv`: Données des routes depuis Toulouse (fichier CSV)
- `routes_bre.csv`: Données des routes depuis Brême (fichier CSV)
- `resultats.xlsx`: Résultats générés (onglets combinations et synthese)
- `calendrier.html`: Calendrier interactif généré
- `publier.sh`: Script de publication
- `requirements.txt`: Dépendances Python
- `README.md`: Ce fichier

## 🔒 Sécurité

- Aucune donnée sensible n'est incluse dans `calendrier.html`
- Le fichier HTML est autonome et ne nécessite pas de serveur
- Aucune clé API ou information personnelle n'est stockée

## 📄 Licence

Ce projet est fourni tel quel pour un usage personnel. Aucune licence spécifique n'est appliquée.

---

Développé avec Python 3.11+ et pandas.
