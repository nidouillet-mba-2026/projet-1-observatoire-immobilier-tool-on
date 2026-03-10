import subprocess
import sys

if __name__ == "__main__":
    print("INFO: L'architecture a été modularisée.")
    print("INFO: Redirection automatique vers app/Home.py...")
    # On délègue l'exécution à Streamlit sur le vrai fichier principal
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/Home.py"])
