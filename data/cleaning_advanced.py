import csv
import os

def detect_outliers_iqr(values):
    """detecte les outliers avec la methode de l'interquartile range."""
    sorted_vals = sorted(values)
    n = len(sorted_vals)

    # calcul du premier quartile q1 (25eme percentile)
    q1_idx = n // 4
    q1 = sorted_vals[q1_idx]

    # calcul du troisieme quartile q3 (75eme percentile)
    q3_idx = (3 * n) // 4
    q3 = sorted_vals[q3_idx]

    # l'ecart interquartile
    iqr = q3 - q1

    # on definit les bornes pour detecter les outliers
    # on utilise 1.5 * iqr comme seuil classique
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    return lower_bound, upper_bound


def clean_dvf_advanced(input_file, output_folder):
    """nettoyage avance avec detection automatique des outliers."""

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file = os.path.join(output_folder, "DVF-83-Toulon-2024-2025advanced.csv")

    # premiere passe : on collecte toutes les donnees pour calculer les statistiques
    mutations = {}

    print(f"--- premiere passe : lecture des donnees brutes ---")

    with open(input_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')

        for row in reader:
            if row['nature_mutation'] != 'Vente':
                continue
            if row['type_local'] not in ['Appartement', 'Maison']:
                continue

            id_mut = row['id_mutation']

            try:
                prix = float(row['valeur_fonciere'].replace(',', '.'))

                surf_reelle = row['surface_reelle_bati'].replace(',', '.')
                surf_carrez = row['lot1_surface_carrez'].replace(',', '.')

                surf_val = 0.0
                if surf_reelle and float(surf_reelle) > 0:
                    surf_val = float(surf_reelle)
                elif surf_carrez and float(surf_carrez) > 0:
                    surf_val = float(surf_carrez)

                if id_mut not in mutations:
                    mutations[id_mut] = {
                        'valeur_fonciere': prix,
                        'surface_totale': surf_val,
                        'type_local': row['type_local'],
                        'code_postal': row['code_postal']
                    }
                else:
                    mutations[id_mut]['surface_totale'] += surf_val

            except (ValueError, TypeError):
                continue

    # on prepare les listes pour l'analyse statistique
    all_surfaces = []
    all_prix = []
    all_prix_m2 = []

    for data in mutations.values():
        if data['surface_totale'] > 9:  # on garde que les surfaces valides
            all_surfaces.append(data['surface_totale'])
            all_prix.append(data['valeur_fonciere'])
            prix_m2 = data['valeur_fonciere'] / data['surface_totale']
            all_prix_m2.append(prix_m2)

    print(f"transactions initiales : {len(all_surfaces)}")
    print()

    # detection des outliers avec iqr
    surf_lower, surf_upper = detect_outliers_iqr(all_surfaces)
    prix_lower, prix_upper = detect_outliers_iqr(all_prix)
    prixm2_lower, prixm2_upper = detect_outliers_iqr(all_prix_m2)

    print("--- bornes detectees automatiquement (methode iqr) ---")
    print(f"surface acceptable : {surf_lower:.2f} - {surf_upper:.2f} m²")
    print(f"prix acceptable : {prix_lower:,.2f} - {prix_upper:,.2f} euros")
    print(f"prix/m² acceptable : {prixm2_lower:,.2f} - {prixm2_upper:,.2f} euros/m²")
    print()

    # on ajoute aussi des filtres metier pour niddouillet
    # budget max 450k, surfaces raisonnables pour des primo-accedants
    budget_max = 500000  # on met un peu plus large que 450k pour garder plus de donnees
    surface_max_raisonnable = 200  # au dela c'est probablement des erreurs ou des villas

    # deuxieme passe : on ecrit seulement les donnees propres
    count_final = 0
    fieldnames = ['id_mutation', 'valeur_fonciere', 'surface_totale', 'prix_m2', 'type_local', 'code_postal']

    with open(output_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        for id_mut, data in mutations.items():
            surf = data['surface_totale']
            prix = data['valeur_fonciere']

            if surf > 9:
                prix_m2 = prix / surf

                # on applique tous les filtres
                if (surf_lower <= surf <= min(surf_upper, surface_max_raisonnable) and
                    prix_lower <= prix <= min(prix_upper, budget_max) and
                    prixm2_lower <= prix_m2 <= prixm2_upper):

                    writer.writerow({
                        'id_mutation': id_mut,
                        'valeur_fonciere': prix,
                        'surface_totale': surf,
                        'prix_m2': prix_m2,
                        'type_local': data['type_local'],
                        'code_postal': data['code_postal']
                    })
                    count_final += 1

    print(f"--- nettoyage termine ---")
    print(f"transactions conservees : {count_final}")
    print(f"taux de retention : {100 * count_final / len(all_surfaces):.1f}%")
    print(f"fichier genere : {output_file}")


if __name__ == "__main__":
    dossier_script = os.path.dirname(os.path.abspath(__file__))
    fichier_entree = os.path.join(dossier_script, 'DVF-83-Toulon-2024-2025Brut.csv')

    clean_dvf_advanced(fichier_entree, dossier_script)
