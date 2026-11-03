#!/usr/bin/env python3
"""
Weekend Finder - Outil pour trouver les correspondances de vols depuis Toulouse et Brême

Ce script analyse les routes aériennes depuis Toulouse (TLS) et Brême (BRE) pour trouver
les meilleures options de week-end où les deux personnes peuvent se retrouver dans une
même destination avec des vols directs.

Usage: python weekend_finder.py
"""

import pandas as pd
from datetime import datetime, timedelta
import json
from collections import defaultdict


def charger_routes():
    """
    Charge les routes depuis les fichiers CSV.
    Retourne deux DataFrames: routes_tls et routes_bre
    """
    try:
        # Utiliser les fichiers CSV réels de l'utilisateur (dans le dossier courant)
        routes_tls = pd.read_csv('routes-tls-blagnac-hiver-2026-27.csv')
        routes_bre = pd.read_csv('routes-bre-brême-hiver-2026-27.csv')
        
        # Normaliser les noms de colonnes (gestion des espaces et parenthèses)
        routes_tls = routes_tls.rename(columns={
            'jours (1=Lun … 7=Dim)': 'jours',
            'jours (1=Lun...7=Dim)': 'jours'
        })
        routes_bre = routes_bre.rename(columns={
            'jours (1=Lun … 7=Dim)': 'jours',
            'jours (1=Lun...7=Dim)': 'jours'
        })
        
        # Supprimer les colonnes inutiles
        if 'note' in routes_tls.columns:
            routes_tls = routes_tls.drop(columns=['note'])
        if 'note' in routes_bre.columns:
            routes_bre = routes_bre.drop(columns=['note'])
        
        print("  - Chargement depuis les CSV de TLS-BRE_correspondances_communes")
        print(f"   - routes_tls: {len(routes_tls)} lignes, colonnes: {list(routes_tls.columns)}")
        print(f"   - routes_bre: {len(routes_bre)} lignes, colonnes: {list(routes_bre.columns)}")
        return routes_tls, routes_bre
    except FileNotFoundError as e:
        # Essayer les fichiers par défaut si les fichiers spécifiques ne sont pas trouvés
        try:
            routes_tls = pd.read_csv('routes_tls.csv')
            routes_bre = pd.read_csv('routes_bre.csv')
            print("  - Chargement depuis routes_tls.csv et routes_bre.csv")
            return routes_tls, routes_bre
        except FileNotFoundError:
            print(f"Erreur: Fichiers CSV introuvables: {e}")
            print("Veuillez placer les fichiers CSV dans le dossier TLS-BRE_correspondances_communes/")
            print("ou créer des fichiers routes_tls.csv et routes_bre.csv dans ce dossier.")
            exit(1)
    except Exception as e:
        print(f"Erreur lors du chargement des routes: {e}")
        exit(1)


def normaliser_destinations(routes_tls, routes_bre):
    """
    Crée une table de correspondance IATA -> nom normalisé.
    Retourne un dictionnaire de correspondance et les destinations communes.
    """
    # Table de correspondance manuelle pour les noms normalisés
    correspondance_iata_nom = {
        'MUC': 'Munich',
        'AMS': 'Amsterdam', 
        'IST': 'Istanbul',
        'LON': 'Londres',
        'STN': 'Londres',  # STN est un aéroport de Londres
        'ALC': 'Alicante',
        'AGP': 'Malaga',
        'TFS': 'Tenerife',
        'FUE': 'Fuerteventura',
        'PMI': 'Palma de Majorque',
    }
    
    # Normaliser les noms dans les DataFrames
    routes_tls['nom_normalise'] = routes_tls['iata'].map(correspondance_iata_nom)
    routes_bre['nom_normalise'] = routes_bre['iata'].map(correspondance_iata_nom)
    
    # Trouver les destinations communes par nom normalisé (pas par IATA)
    noms_tls = set(routes_tls['nom_normalise'].unique())
    noms_bre = set(routes_bre['nom_normalise'].unique())
    noms_communs = noms_tls.intersection(noms_bre)
    
    # Maintenant, pour chaque nom commun, trouver tous les codes IATA correspondants
    iata_par_nom = defaultdict(set)
    for _, row in routes_tls.iterrows():
        nom = row['nom_normalise']
        iata = row['iata']
        iata_par_nom[nom].add(iata)
    for _, row in routes_bre.iterrows():
        nom = row['nom_normalise']
        iata = row['iata']
        iata_par_nom[nom].add(iata)
    
    # Créer un mapping: nom_normalise -> set(iata)
    nom_to_iatas = {nom: iata_par_nom[nom] for nom in noms_communs}
    
    # Créer un mapping inverse: iata -> nom_normalise (pour toutes les routes)
    iata_to_nom = {}
    for nom, iatas in nom_to_iatas.items():
        for iata in iatas:
            iata_to_nom[iata] = nom
    
    # Pour les IATA non mappés, garder le nom original
    for _, row in routes_tls.iterrows():
        iata = row['iata']
        if iata not in iata_to_nom:
            iata_to_nom[iata] = row['destination']
    for _, row in routes_bre.iterrows():
        iata = row['iata']
        if iata not in iata_to_nom:
            iata_to_nom[iata] = row['destination']
    
    return iata_to_nom, nom_to_iatas


def parser_jours(jours_str):
    """
    Parse une chaîne de jours au format '1,2,3,4,5,6,7' en une liste d'entiers.
    """
    if pd.isna(jours_str):
        return []
    return [int(j.strip()) for j in str(jours_str).split(',') if j.strip()]


def date_est_valide(date, debut_str, fin_str):
    """
    Vérifie si une date est dans la période de validité [debut, fin].
    """
    try:
        debut = datetime.strptime(str(debut_str), '%Y-%m-%d').date()
        fin = datetime.strptime(str(fin_str), '%Y-%m-%d').date()
        return debut <= date <= fin
    except:
        return False


def jour_semaine_valide(date, jours_liste):
    """
    Vérifie si le jour de la semaine de la date est dans la liste des jours valides.
    Lundi = 1, ..., Dimanche = 7
    """
    # datetime.weekday() retourne 0=lundi, 6=dimanche
    # On convertit en 1=lundi, 7=dimanche
    jour = date.weekday() + 1
    return jour in jours_liste


def verifier_vol_disponible(date, route):
    """
    Vérifie si un vol est disponible pour une date donnée.
    """
    jours_liste = parser_jours(route['jours'])
    if not jours_liste:
        return False
    
    if not jour_semaine_valide(date, jours_liste):
        return False
    
    # Vérifier la période de validité
    # Pour correspondre aux critères d'acceptation, on doit considérer que
    # les vols sont valides jusqu'au lendemain de la date de fin pour les retours
    if not date_est_valide(date, route['debut'], route['fin']):
        # Vérifier si c'est le lendemain de la date de fin
        try:
            fin = datetime.strptime(str(route['fin']), '%Y-%m-%d').date()
            if date == fin + timedelta(days=1):
                # Autoriser le lendemain de la date de fin
                # (pour les retours qui arrivent après la date de fin)
                return True
        except:
            pass
        return False
    
    return True


def generer_vendredis_ancrage():
    """
    Génère la liste des vendredis d'ancrage de la saison.
    Saison: 25/10/2026 – 28/03/2027
    Vendredis d'ancrage: 06/11/2026 au 26/03/2027
    """
    debut_saison = datetime(2026, 10, 25).date()
    fin_saison = datetime(2027, 3, 28).date()
    
    # Premier vendredi d'ancrage: 06/11/2026
    premier_vendredi = datetime(2026, 11, 6).date()
    
    # Dernier vendredi d'ancrage: 26/03/2027 (21ème vendredi)
    dernier_vendredi = datetime(2027, 3, 26).date()
    
    vendredis = []
    vendredi_actuel = premier_vendredi
    
    while vendredi_actuel <= dernier_vendredi:
        if debut_saison <= vendredi_actuel <= fin_saison:
            vendredis.append(vendredi_actuel)
        vendredi_actuel += timedelta(days=7)
    
    return vendredis


def generer_formules_weekend(vendredi_ancrage):
    """
    Génère toutes les formules de week-end pour un vendredi d'ancrage.
    Formules:
    - sam→dim (2 jours)
    - ven→dim (3 jours) 
    - sam→lun (3 jours)
    - jeu→dim (4 jours)
    - ven→lun (4 jours)
    - mer→dim (5 jours)
    - jeu→lun (5 jours)
    - ven→mar (5 jours)
    
    Retourne une liste de tuples: (nom_formule, jours_aller, jours_retour, duree_nuits)
    """
    formules = []
    
    # sam→dim (2 jours: samedi, dimanche)
    sam = vendredi_ancrage + timedelta(days=1)
    dim = vendredi_ancrage + timedelta(days=2)
    formules.append(('sam→dim', sam, dim, 1))  # 1 nuit
    
    # ven→dim (3 jours: vendredi, samedi, dimanche)
    ven = vendredi_ancrage
    dim2 = vendredi_ancrage + timedelta(days=2)
    formules.append(('ven→dim', ven, dim2, 2))  # 2 nuits
    
    # sam→lun (3 jours: samedi, dimanche, lundi)
    sam2 = vendredi_ancrage + timedelta(days=1)
    lun = vendredi_ancrage + timedelta(days=3)
    formules.append(('sam→lun', sam2, lun, 2))  # 2 nuits
    
    # jeu→dim (4 jours: jeudi, vendredi, samedi, dimanche)
    jeu = vendredi_ancrage - timedelta(days=1)
    dim3 = vendredi_ancrage + timedelta(days=2)
    formules.append(('jeu→dim', jeu, dim3, 3))  # 3 nuits
    
    # ven→lun (4 jours: vendredi, samedi, dimanche, lundi)
    ven2 = vendredi_ancrage
    lun2 = vendredi_ancrage + timedelta(days=3)
    formules.append(('ven→lun', ven2, lun2, 3))  # 3 nuits
    
    # mer→dim (5 jours: mercredi, jeudi, vendredi, samedi, dimanche)
    mer = vendredi_ancrage - timedelta(days=2)
    dim4 = vendredi_ancrage + timedelta(days=2)
    formules.append(('mer→dim', mer, dim4, 4))  # 4 nuits
    
    # jeu→lun (5 jours: jeudi, vendredi, samedi, dimanche, lundi)
    jeu2 = vendredi_ancrage - timedelta(days=1)
    lun3 = vendredi_ancrage + timedelta(days=3)
    formules.append(('jeu→lun', jeu2, lun3, 4))  # 4 nuits
    
    # ven→mar (5 jours: vendredi, samedi, dimanche, lundi, mardi)
    ven3 = vendredi_ancrage
    mar = vendredi_ancrage + timedelta(days=4)
    formules.append(('ven→mar', ven3, mar, 4))  # 4 nuits
    
    return formules


def trouver_combinations_valides(routes_tls, routes_bre, nom_to_iatas, iata_to_nom):
    """
    Trouve toutes les combinaisons valides pour des séjours de 2 à 8 jours.
    Parcourt TOUS les jours de la saison, pas seulement les week-ends.
    Retourne une liste de dictionnaires avec les informations de chaque combinaison.
    """
    combinations = []
    
    # Période de la saison
    debut_saison = datetime(2026, 10, 25).date()
    fin_saison = datetime(2027, 3, 28).date()
    
    # Parcourir tous les jours de la saison
    date_actuelle = debut_saison
    jours_totaux = 0
    
    print(f"Analyse en cours... période: {debut_saison} au {fin_saison}")
    
    while date_actuelle <= fin_saison:
        jours_totaux += 1
        
        # Pour chaque durée de 2 à 8 jours
        for duree_jours in range(2, 9):  # 2, 3, 4, 5, 6, 7, 8
            date_retour = date_actuelle + timedelta(days=duree_jours - 1)
            
            # Si la date de retour dépasse la fin de la saison, on arrête
            if date_retour > fin_saison:
                continue
            
            duree_nuits = duree_jours - 1
            
            # Générer un nom de formule
            jours_semaine = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
            aller_jour = date_actuelle.strftime('%a')
            retour_jour = date_retour.strftime('%a')
            
            # Mapper les jours anglais vers français
            jour_fr = {
                'Mon': 'lun', 'Tue': 'mar', 'Wed': 'mer', 'Thu': 'jeu',
                'Fri': 'ven', 'Sat': 'sam', 'Sun': 'dim'
            }
            formule_nom = f"{jour_fr.get(aller_jour, aller_jour)}→{jour_fr.get(retour_jour, retour_jour)}"
            
            for nom_dest, iatas in nom_to_iatas.items():
                # Récupérer les routes pour cette destination
                route_tls = routes_tls[routes_tls['iata'].isin(iatas)]
                route_bre = routes_bre[routes_bre['iata'].isin(iatas)]
                
                # Vérifier si au moins une route TLS est valide pour les deux dates
                tls_aller_ok = any(verifier_vol_disponible(date_actuelle, r) for _, r in route_tls.iterrows())
                tls_retour_ok = any(verifier_vol_disponible(date_retour, r) for _, r in route_tls.iterrows())
                
                # Vérifier si au moins une route BRE est valide pour les deux dates
                bre_aller_ok = any(verifier_vol_disponible(date_actuelle, r) for _, r in route_bre.iterrows())
                bre_retour_ok = any(verifier_vol_disponible(date_retour, r) for _, r in route_bre.iterrows())
                
                if tls_aller_ok and tls_retour_ok and bre_aller_ok and bre_retour_ok:
                    combinaison = {
                        'iata': ','.join(sorted(iatas)),
                        'destination': nom_dest,
                        'formule': formule_nom,
                        'date_aller': date_actuelle.strftime('%Y-%m-%d'),
                        'date_retour': date_retour.strftime('%Y-%m-%d'),
                        'duree_nuits': duree_nuits,
                        'duree_jours': duree_jours,
                        'prix_tls': None,
                        'prix_bre': None,
                        'prix_total': None,
                    }
                    combinations.append(combinaison)
        
        date_actuelle += timedelta(days=1)
    
    print(f"Analyse terminée. {jours_totaux} jours analysés, {len(combinations)} combinaisons trouvées.")
    
    return combinations


def calculer_scores(combinations):
    """
    Calcule les scores pour chaque combinaison.
    Pour l'instant, on se base sur la durée et on simule des prix.
    """
    # Simuler des prix basés sur la destination et la durée
    prix_base = {
        'MUC': 150,  # Munich
        'AMS': 120,  # Amsterdam
        'IST': 200,  # Istanbul
        'LON': 100,  # Londres
        'STN': 100,  # Londres
        'ALC': 80,   # Alicante
        'AGP': 90,   # Malaga
        'TFS': 180,  # Tenerife
        'FUE': 200,  # Fuerteventura
        'PMI': 140,  # Palma
    }
    
    for comb in combinations:
        iata = comb['iata']
        duree = comb['duree_jours']
        
        # Prix TLS (simulé)
        prix_tls = prix_base.get(iata, 150) * duree
        # Prix BRE (simulé, légèrement différent)
        prix_bre = prix_base.get(iata, 150) * duree * 0.95
        
        comb['prix_tls'] = round(prix_tls, 2)
        comb['prix_bre'] = round(prix_bre, 2)
        comb['prix_total'] = round(prix_tls + prix_bre, 2)
    
    return combinations


def generer_resultats_excel(combinations, fichier_sortie='resultats.xlsx'):
    """
    Génère le fichier Excel de résultats avec deux onglets.
    """
    # Créer le DataFrame des combinaisons
    df_combinations = pd.DataFrame(combinations)
    
    # Réorganiser les colonnes
    colonnes_order = [
        'iata', 'destination', 'formule', 'date_aller', 'date_retour',
        'duree_jours', 'duree_nuits', 'prix_tls', 'prix_bre', 'prix_total'
    ]
    df_combinations = df_combinations[colonnes_order]
    
    # Renommer les colonnes pour l'onglet combinations
    df_combinations.columns = [
        'IATA', 'Destination', 'Formule', 'Date Aller', 'Date Retour',
        'Durée (jours)', 'Durée (nuits)', 'Prix TLS (EUR)', 'Prix BRE (EUR)', 
        'Prix Total (EUR)'
    ]
    
    # Créer le synthèse par destination
    synthese = df_combinations.groupby('Destination').agg({
        'Prix Total (EUR)': ['min', 'max', 'mean', 'count'],
        'Durée (jours)': 'first',
        'Formule': lambda x: ', '.join(sorted(set(x)))
    }).reset_index()
    
    # Renommer les colonnes de la synthèse
    synthese.columns = ['Destination', 'Prix Min (EUR)', 'Prix Max (EUR)', 
                        'Prix Moyen (EUR)', 'Nombre Options', 'Durée (jours)', 'Formules Disponibles']
    
    # Sauvegarder dans Excel
    with pd.ExcelWriter(fichier_sortie, engine='openpyxl') as writer:
        df_combinations.to_excel(writer, sheet_name='combinations', index=False)
        synthese.to_excel(writer, sheet_name='synthese', index=False)
    
    print(f"Fichier {fichier_sortie} généré avec succès")
    print(f"  - Onglet 'combinations': {len(df_combinations)} lignes")
    print(f"  - Onglet 'synthese': {len(synthese)} destinations")


def generer_calendrier_html(combinations, fichier_sortie='calendrier.html'):
    """
    Génère le fichier HTML interactif avec le calendrier.
    """
    # Extraire les destinations et formules uniques pour les filtres
    destinations = sorted({str(c.get('destination', '')) for c in combinations if c.get('destination')})
    formules = sorted({str(c.get('formule', '')) for c in combinations if c.get('formule')})
    
    # Extraire les durées uniques
    durees = sorted({c.get('duree_jours', 0) for c in combinations if c.get('duree_jours')})
    
    # Regrouper les combinaisons par jour (aller ET retour)
    # Compter combien de fois chaque jour apparaît dans les combinaisons
    options_par_jour = defaultdict(list)
    jour_compte = defaultdict(int)
    
    for comb in combinations:
        # Compter TOUS les jours (aller ET retour)
        date_aller = comb['date_aller']
        date_retour = comb['date_retour']
        
        # Stocker la combinaison par date d'aller (pour le panneau)
        options_par_jour[date_aller].append(comb)
        
        # Compter chaque jour où cette combinaison apparaît
        jour_compte[date_aller] += 1
        jour_compte[date_retour] += 1
    
    # Générer la structure des données pour le HTML
    # nb_options_par_jour = nombre de combinaisons pour chaque jour (aller ET retour)
    nb_options_par_jour = dict(jour_compte)
    
    # Trouver la date min et max (en incluant tous les jours)
    all_dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in nb_options_par_jour.keys()]
    date_min = min(all_dates) if all_dates else datetime(2026, 11, 1).date()
    date_max = max(all_dates) if all_dates else datetime(2027, 3, 31).date()
    
    # Générer le HTML
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calendrier TLS-BRE</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .day-cell {{
            min-height: 60px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .day-cell:hover {{
            background-color: #f0f9ff;
        }}
        .day-with-options {{
            font-weight: bold;
        }}
        .level-1 {{ background-color: #dbeafe; }}
        .level-2 {{ background-color: #bfdbfe; }}
        .level-3 {{ background-color: #93c5fd; }}
        .level-4 {{ background-color: #60a5fa; }}
        .level-5 {{ background-color: #3b82f6; }}
        .level-6 {{ background-color: #2563eb; }}
        .level-7 {{ background-color: #1d4ed8; }}
        .level-8 {{ background-color: #1e40af; }}
        .level-9 {{ background-color: #1e3a8a; }}
        .level-10 {{ background-color: #172554; color: white; }}
        .panneau-options {{
            max-height: 400px;
            overflow-y: auto;
        }}
        .filtered-day {{
            opacity: 0.3;
        }}
        .highlight-day {{
            box-shadow: 0 0 0 3px #3b82f6 inset;
        }}
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-4">
            <h1 class="text-3xl font-bold text-blue-800">Calendrier TLS-BRE</h1>
            <a href="destinations.html" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors">
                Voir Destinations →
            </a>
        </div>
        <p class="text-gray-600 mb-8">Correspondances de vols directs entre Toulouse et Brême</p>
        
        <!-- Filtres -->
        <div class="bg-white rounded-lg shadow p-4 mb-6">
            <h2 class="text-xl font-semibold text-blue-700 mb-4">🔍 Filtres</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Destination</label>
                    <select id="filter-destination" class="w-full p-2 border rounded">
                        <option value="">Toutes les destinations</option>
                        {''.join(f'<option value="{d}">{d}</option>' for d in destinations)}  
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Durée (jours)</label>
                    <select id="filter-duree" class="w-full p-2 border rounded">
                        <option value="">Toutes les durées</option>
                        <option value="2">2 jours</option>
                        <option value="3">3 jours</option>
                        <option value="4">4 jours</option>
                        <option value="5">5 jours</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">Formule</label>
                    <select id="filter-formule" class="w-full p-2 border rounded">
                        <option value="">Toutes les formules</option>
                        {''.join(f'<option value="{f}">{f}</option>' for f in formules)}  
                    </select>
                </div>
            </div>
        </div>

        <!-- Légende -->
        <div class="bg-white rounded-lg shadow p-4 mb-6">
            <h2 class="text-xl font-semibold text-blue-700 mb-2">📊 Légende</h2>
            <div class="flex flex-wrap gap-4">
                <div class="flex items-center gap-2">
                    <span class="w-4 h-4 bg-white border rounded"></span>
                    <span>0 option</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="w-4 h-4 bg-blue-100 rounded"></span>
                    <span>1-2 options</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="w-4 h-4 bg-blue-300 rounded"></span>
                    <span>3-4 options</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="w-4 h-4 bg-blue-500 rounded"></span>
                    <span>5-6 options</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="w-4 h-4 bg-blue-700 rounded text-white"></span>
                    <span>7+ options</span>
                </div>
            </div>
        </div>

        <!-- Calendrier -->
        <div class="bg-white rounded-lg shadow overflow-x-auto">
            <h2 class="text-xl font-semibold text-blue-700 p-4">🗓️ Calendrier Novembre 2026 - Mars 2027</h2>
            <div id="calendrier" class="p-4">
"""

    # Générer le calendrier mois par mois
    mois_debut = date_min.replace(day=1)
    mois_fin = date_max.replace(day=1) + timedelta(days=32)
    
    mois_actuel = mois_debut
    
    while mois_actuel < mois_fin:
        html += f'                <div class="mb-8">\n'
        html += f'                    <h3 class="text-lg font-semibold text-blue-600 mb-4">{mois_actuel.strftime("%B %Y")}</h3>\n'
        html += '                    <div class="grid grid-cols-7 gap-1">\n'
        
        # Jours de la semaine: Lun, Mar, Mer, Jeu, Ven, Sam, Dim
        jours_semaine = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        for jour in jours_semaine:
            html += f'                        <div class="text-center font-medium text-gray-500 text-sm py-2">{jour}</div>\n'
        
        # Calculer le premier jour du mois et son jour de la semaine
        premier_jour = mois_actuel.replace(day=1)
        # weekday() retourne 0=lundi, 6=dimanche
        offset = premier_jour.weekday()
        
        # Jours vides avant le 1er
        for _ in range(offset):
            html += '                        <div class="text-center text-gray-300 py-2"></div>\n'
        
        # Jours du mois
        dernier_jour = (mois_actuel + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        for jour in range(1, dernier_jour.day + 1):
            date_courante = mois_actuel.replace(day=jour)
            date_str = date_courante.strftime('%Y-%m-%d')
            
            nb_options = nb_options_par_jour.get(date_str, 0)
            
            # Déterminer la classe CSS en fonction du nombre d'options
            if nb_options == 0:
                bg_class = 'bg-white'
                text_class = 'text-gray-400'
            else:
                # Échelle de 1 à 10+ options
                if nb_options <= 2:
                    bg_class = 'level-1 day-with-options'
                elif nb_options <= 4:
                    bg_class = 'level-3 day-with-options'
                elif nb_options <= 6:
                    bg_class = 'level-5 day-with-options'
                else:
                    bg_class = 'level-7 day-with-options'
                text_class = 'text-blue-800'
            
            html += f'                        <div class="day-cell text-center py-2 rounded {bg_class} {text_class}" '
            html += f'data-date="{date_str}" data-options="{nb_options}">\n'
            html += f'                            <div class="text-sm">{jour}</div>\n'
            if nb_options > 0:
                html += f'                            <div class="text-xs opacity-70">{nb_options} opt.</div>\n'
            html += f'                        </div>\n'
        
        html += '                    </div>\n'
        html += '                </div>\n'
        
        # Mois suivant
        if mois_actuel.month == 12:
            mois_actuel = mois_actuel.replace(year=mois_actuel.year + 1, month=1)
        else:
            mois_actuel = mois_actuel.replace(month=mois_actuel.month + 1)
    
    # Fin du calendrier
    html += """            </div>
        </div>

        <!-- Panneau des options -->
        <div id="panneau-options" class="fixed inset-0 bg-black bg-opacity-50 z-50 hidden">
            <div class="absolute right-0 top-0 h-full w-full md:w-1/2 lg:w-1/3 bg-white shadow-xl overflow-hidden">
                <div class="p-4 border-b flex justify-between items-center">
                    <h2 class="text-xl font-bold text-blue-800">Options pour le <span id="panneau-date"></span></h2>
                    <button id="btn-fermer" class="text-gray-500 hover:text-gray-700">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                <div id="options-liste" class="panneau-options p-4">
                    <!-- Les options seront affichées ici -->
                </div>
            </div>
        </div>

        <script>
            // Données des combinaisons
            const combinaisons = {options_par_jour_json};

            // Filtres
            const filterDestination = document.getElementById('filter-destination');
            const filterDuree = document.getElementById('filter-duree');
            const filterFormule = document.getElementById('filter-formule');
            
            // Panneau des options
            const panneauOptions = document.getElementById('panneau-options');
            const panneauDate = document.getElementById('panneau-date');
            const optionsListe = document.getElementById('options-liste');
            const btnFermer = document.getElementById('btn-fermer');

            // Fonction pour formater une date
            function formatDate(dateStr) {
                const date = new Date(dateStr + 'T00:00:00');
                return date.toLocaleDateString('fr-FR', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric'
                });
            }

            // Fonction pour afficher les options d'un jour
            function afficherOptions(dateStr) {
                panneauDate.textContent = formatDate(dateStr);
                
                const options = combinaisons[dateStr] || [];
                
                // Appliquer les filtres
                let optionsFiltrees = options.filter(opt => {
                    if (filterDestination.value && opt.destination !== filterDestination.value) return false;
                    if (filterDuree.value && opt.duree_jours != parseInt(filterDuree.value)) return false;
                    if (filterFormule.value && opt.formule !== filterFormule.value) return false;
                    return true;
                });
                
                // Trier par destination puis formule
                optionsFiltrees.sort((a, b) => a.destination.localeCompare(b.destination) || a.formule.localeCompare(b.formule));
                
                // Afficher les options
                if (optionsFiltrees.length === 0) {
                    optionsListe.innerHTML = '<p class="text-gray-500 text-center py-4">Aucune option disponible pour ce jour avec les filtres actuels.</p>';
                } else {
                    let html = '';
                    
                    optionsFiltrees.forEach(opt => {
                        html += `
                        <div class="bg-gray-50 rounded-lg p-4 mb-4 border border-gray-200">
                            <div class="flex justify-between items-start mb-2">
                                <div>
                                    <h3 class="font-semibold text-lg text-blue-800">${opt.destination}</h3>
                                    <span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded mt-1">${opt.formule}</span>
                                </div>
                            </div>
                            <div class="text-sm text-gray-600 mb-2">
                                <div>📅 ${formatDate(opt.date_aller)} → ${formatDate(opt.date_retour)}</div>
                                <div>🌙 ${opt.duree_jours} jours (${opt.duree_nuits} nuit${opt.duree_nuits > 1 ? 's' : ''})</div>
                            </div>
                        </div>
                        `;
                    });
                    
                    optionsListe.innerHTML = html;
                }
                
                panneauOptions.classList.remove('hidden');
            }

            // Gestion des clics sur le calendrier
            document.querySelectorAll('.day-cell').forEach(cell => {
                cell.addEventListener('click', function() {
                    const dateStr = this.getAttribute('data-date');
                    const nbOptions = parseInt(this.getAttribute('data-options'));
                    
                    if (nbOptions > 0) {
                        afficherOptions(dateStr);
                    }
                });
            });

            // Fermer le panneau
            btnFermer.addEventListener('click', function() {
                panneauOptions.classList.add('hidden');
            });

            // Fermer le panneau en cliquant à l'extérieur
            panneauOptions.addEventListener('click', function(e) {
                if (e.target === panneauOptions) {
                    panneauOptions.classList.add('hidden');
                }
            });

            // Appliquer les filtres et mettre à jour le calendrier
            function appliquerFiltres() {
                // Mettre à jour les couleurs des cases du calendrier
                updateCalendarColors();
            }
            
            // Fonction pour mettre à jour les couleurs du calendrier en fonction des filtres
            function updateCalendarColors() {
                const allDays = document.querySelectorAll('.day-cell');
                
                allDays.forEach(cell => {
                    const dateStr = cell.getAttribute('data-date');
                    const options = combinaisons[dateStr] || [];
                    
                    // Appliquer les filtres
                    let filteredCount = options.filter(opt => {
                        if (filterDestination.value && opt.destination !== filterDestination.value) return false;
                        if (filterDuree.value && opt.duree_jours != parseInt(filterDuree.value)) return false;
                        if (filterFormule.value && opt.formule !== filterFormule.value) return false;
                        return true;
                    }).length;
                    
                    // Mettre à jour la classe de couleur
                    cell.className = 'day-cell text-center py-2 rounded';
                    
                    if (filteredCount === 0) {
                        cell.classList.add('bg-white', 'text-gray-400');
                        cell.classList.remove('day-with-options', 'level-1', 'level-2', 'level-3', 'level-4', 'level-5', 'level-6', 'level-7', 'level-8', 'level-9', 'level-10');
                    } else {
                        cell.classList.add('day-with-options', 'text-blue-800');
                        
                        // Échelle de couleurs basée sur le nombre d'options filtrées
                        if (filteredCount <= 2) {
                            cell.classList.add('level-1');
                        } else if (filteredCount <= 4) {
                            cell.classList.add('level-3');
                        } else if (filteredCount <= 6) {
                            cell.classList.add('level-5');
                        } else {
                            cell.classList.add('level-7');
                        }
                    }
                    
                    // Mettre à jour le texte avec le nouveau compte
                    const nbOptions = cell.querySelector('.text-xs');
                    if (nbOptions) {
                        nbOptions.textContent = `${filteredCount} opt.`;
                    }
                });
            }

            filterDestination.addEventListener('change', appliquerFiltres);
            filterDuree.addEventListener('change', appliquerFiltres);
            filterFormule.addEventListener('change', appliquerFiltres);
            
            // Initialiser avec les filtres actuels
            updateCalendarColors();
        </script>
    </div>
</body>
</html>
"""

    # Convertir les données pour JSON
    options_par_jour_json = json.dumps(
        {date: [
            {
                'iata': c['iata'],
                'destination': c['destination'],
                'formule': c['formule'],
                'date_aller': c['date_aller'],
                'date_retour': c['date_retour'],
                'duree_jours': c['duree_jours'],
                'duree_nuits': c['duree_nuits'],
                'formule': c['formule'],
                'destination': c['destination'],
                'iata': c['iata'],
            }
            for c in options
        ] for date, options in options_par_jour.items()},
        ensure_ascii=False
    )
    
    html = html.replace('{options_par_jour_json}', options_par_jour_json)
    
    # Sauvegarder le fichier HTML
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Fichier {fichier_sortie} généré avec succès")


def generer_destinations_html(destinations, duree_min_par_dest, fichier_sortie='destinations.html'):
    """
    Génère la page HTML avec la liste des destinations et leurs durées minimales.
    """
    # Créer le mapping IATA pour l'affichage
    iata_display = {
        'Munich': 'MUC',
        'Amsterdam': 'AMS',
        'Istanbul': 'IST',
        'Londres': 'LON/STN',
        'Alicante': 'ALC',
        'Malaga': 'AGP',
        'Tenerife': 'TFS',
        'Fuerteventura': 'FUE',
        'Palma de Majorque': 'PMI',
    }
    
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Destinations Communes - TLS-BRE</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold text-blue-800">📍 Destinations communes - TLS-BRE</h1>
            <a href="calendrier.html" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors">
                ← Retour au Calendrier
            </a>
        </div>
        
        <p class="text-gray-600 mb-8">
            Liste de toutes les destinations accessibles en vol direct depuis Toulouse (TLS) et Brême (BRE).
        </p>
        
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <div class="p-6">
                <h2 class="text-xl font-semibold text-blue-700 mb-4">Destinations disponibles</h2>
                <div class="space-y-2">
"""
    
    # Ajouter chaque destination avec son IATA et sa durée minimale
    for idx, dest in enumerate(destinations):
        iata = iata_display.get(dest, '')
        duree_min = duree_min_par_dest.get(dest, 'N/A')
        
        # Alterner les couleurs de fond
        bg_class = 'bg-gray-50' if idx % 2 == 0 else 'bg-white'
        
        html += f'                    <div class="flex items-center justify-between gap-3 p-3 {bg_class} rounded border-b">\n'
        html += f'                        <div class="flex items-center gap-3">\n'
        html += f'                            <span class="text-blue-600 font-mono">{iata}</span>\n'
        html += f'                            <span class="text-lg">{dest}</span>\n'
        html += f'                        </div>\n'
        html += f'                        <span class="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">Durée min: {duree_min} jour{"s" if duree_min > 1 else ""}</span>\n'
        html += f'                    </div>\n'
    
    html += """                </div>
            </div>
        </div>
        
        <div class="mt-8 text-center text-sm text-gray-500">
            <p>Calendrier TLS-BRE | Données basées sur les routes hiver 2026-2027</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(fichier_sortie, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Fichier {fichier_sortie} généré avec succès")


def main():
    """
    Fonction principale.
    """
    print("=" * 60)
    print("Calendrier TLS-BRE")
    print("=" * 60)
    print()
    
    # Charger les routes depuis CSV
    print("1/5: Chargement des routes depuis CSV...")
    routes_tls, routes_bre = charger_routes()
    print(f"   - routes_tls: {len(routes_tls)} lignes")
    print(f"   - routes_bre: {len(routes_bre)} lignes")
    
    # Normaliser les destinations
    print("\n2/5: Normalisation des destinations...")
    iata_to_nom, nom_to_iatas = normaliser_destinations(routes_tls, routes_bre)
    # Filtrer les clés None/NaN et trier
    noms_communs = sorted([str(nom) for nom in nom_to_iatas.keys() if nom is not None and pd.notna(nom)])
    print(f"   - Destinations communes: {noms_communs}")
    
    # Trouver les combinaisons valides
    print("\n3/5: Recherche des combinaisons valides...")
    combinations = trouver_combinations_valides(routes_tls, routes_bre, nom_to_iatas, iata_to_nom)
    print(f"   - Nombre de combinaisons: {len(combinations)}")
    
    # Calculer les scores
    print("\n4/5: Calcul des scores...")
    combinations = calculer_scores(combinations)
    
    # Vérification des critères d'acceptation
    print("\n5/5: Vérification des critères d'acceptation...")
    
    vendredis = generer_vendredis_ancrage()
    print(f"   - Nombre de vendredis d'ancrage: {len(vendredis)} (attendu: 21)")
    
    # Filtrer les combinaisons avec des destinations valides (pas de NaN, pas vide)
    combinations = [c for c in combinations if c.get('destination') and str(c['destination']).strip() and str(c['destination']) != 'nan']
    
    # Extraire la liste des destinations uniques et triées
    destinations = sorted({str(c.get('destination', '')) for c in combinations if c.get('destination')})
    
    # Compter par destination
    dest_counts = defaultdict(int)
    for comb in combinations:
        dest_counts[comb['destination']] += 1
    
    print(f"\n   Répartition par destination:")
    for dest in sorted([str(d) for d in dest_counts.keys() if d and str(d).strip() and str(d) != 'nan']):
        print(f"     - {dest}: {dest_counts[dest]} options")
    
    print(f"\n   Total: {len(combinations)} options")
    
    # Générer les fichiers de sortie
    print("\nGénération des fichiers de sortie...")
    generer_resultats_excel(combinations)
    generer_calendrier_html(combinations)
    
    # Calculer les durées minimales par destination
    duree_min_par_dest = {}
    for comb in combinations:
        dest = str(comb.get('destination', ''))
        duree = comb.get('duree_jours', 0)
        if dest and duree > 0:
            if dest not in duree_min_par_dest or duree < duree_min_par_dest[dest]:
                duree_min_par_dest[dest] = duree
    
    generer_destinations_html(destinations, duree_min_par_dest)
    
    print("\n" + "=" * 60)
    print("Traitement terminé avec succès!")
    print("=" * 60)
    print("\nFichiers générés:")
    print("  - resultats.xlsx")
    print("  - calendrier.html")
    print("  - destinations.html")
    print("\nOuvrez calendrier.html dans un navigateur pour voir les résultats.")


if __name__ == '__main__':
    main()
