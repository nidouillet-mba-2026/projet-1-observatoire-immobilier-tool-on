import csv
import os

def clean_dvf_data(input_file, output_folder):
    # on crée le dossier de sortie s'il n'existe pas encore pour pas que ça plante
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # le nom du fichier propre qu'on va générer
    output_file = os.path.join(output_folder, "DVF-83-Toulon-2024-2025clean.csv")
    
    # on prépare un dico pour regrouper les bouts d'une même vente (ex: appart + cave)
    mutations = {}

    print(f"--- on commence à nettoyer {input_file} ---")

    # on ouvre le fichier brut pour piocher les données réelles [cite: 5, 28]
    with open(input_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for row in reader:
            # on ne garde que les vraies ventes [cite: 52]
            if row['nature_mutation'] != 'Vente':
                continue
            # on cible uniquement les appartements et les maisons [cite: 56]
            if row['type_local'] not in ['Appartement', 'Maison']:
                continue

            id_mut = row['id_mutation']
            
            try:
                # on transforme le prix en un nombre que python comprend
                prix = float(row['valeur_fonciere'].replace(',', '.'))
                
                # si la surface réelle est vide, on essaie de récupérer la surface carrez
                surf_reelle = row['surface_reelle_bati'].replace(',', '.')
                surf_carrez = row['lot1_surface_carrez'].replace(',', '.')
                
                surf_val = 0.0
                if surf_reelle and float(surf_reelle) > 0:
                    surf_val = float(surf_reelle)
                elif surf_carrez and float(surf_carrez) > 0:
                    surf_val = float(surf_carrez)

                # si c'est une nouvelle vente, on crée l'entrée
                if id_mut not in mutations:
                    mutations[id_mut] = {
                        'valeur_fonciere': prix,
                        'surface_totale': surf_val,
                        'type_local': row['type_local'],
                        'code_postal': row['code_postal']
                    }
                else:
                    # si l'id existe déjà, c'est que la vente a plusieurs lots, on cumule la surface
                    mutations[id_mut]['surface_totale'] += surf_val

            except (ValueError, TypeError):
                # en cas de donnée bizarre, on passe à la ligne suivante
                continue

    # on prépare l'écriture du fichier final pour les conseillers niddouillet [cite: 9, 14]
    count_final = 0
    fieldnames = ['id_mutation', 'valeur_fonciere', 'surface_totale', 'type_local', 'code_postal']
    
    with open(output_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        
        for id_mut, data in mutations.items():
            # on vire les trucs trop chers ou trop petits pour rester cohérent avec le marché [cite: 17, 62]
            if 20000 <= data['valeur_fonciere'] <= 1500000 and data['surface_totale'] > 9:
                writer.writerow({
                    'id_mutation': id_mut,
                    'valeur_fonciere': data['valeur_fonciere'],
                    'surface_totale': data['surface_totale'],
                    'type_local': data['type_local'],
                    'code_postal': data['code_postal']
                })
                count_final += 1

    print(f"nettoyage fini !")
    print(f"on a gardé {count_final} transactions bien propres.")
    print(f"ton fichier est ici : {output_file}")

if __name__ == "__main__":
    # on trouve automatiquement le dossier du script pour pas avoir d'erreur de chemin
    dossier_script = os.path.dirname(os.path.abspath(__file__))
    fichier_entree = os.path.join(dossier_script, 'DVF-83-Toulon-2024-2025Brut.csv')
    
    # on lance le nettoyage dans le même dossier [cite: 63]
    clean_dvf_data(fichier_entree, dossier_script)