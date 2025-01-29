import configparser
import requests
import logging
import json
import os
from datetime import datetime, timedelta
from dateutil import parser
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from concurrent.futures import ThreadPoolExecutor, as_completed
import schedule
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/logs/app.log'),
        logging.StreamHandler()
    ]
)


# Récupérer les informations de connexion
API_URL = os.getenv("SYNCTHING_URL")
API_KEY = os.getenv("SYNCTHING_API_KEY")

# Seuil en jours pour filtrer les dossiers
DAYS_THRESHOLD = int(os.getenv("SYNCTHING_DAYS_INACTIVE"))

# Fichier de cache pour éviter les notifications répétitives
CACHE_FILE = Path("/config/cache.json")

# Fichier pour stocker la liste des dossiers inactifs du dernier rapport
LAST_REPORT_FILE = Path("/config/last_report.json")

# Headers pour l'authentification
headers = {
    'X-API-Key': API_KEY
}


def check_directory(path):
    """
    Vérifie si le dossier existe et si on peut écrire dedans.
    Retourne True si tout est OK, sinon False.
    """
    if not os.path.exists(path):
        print(f"Error : Folder '{path}' didn't exists.")
        return False
    
    if not os.path.isdir(path):
        print(f"Error : '{path}' is not a folder.")
        return False
    
    if not os.access(path, os.W_OK):
        print(f"Error : Can't write inside folder '{path}'. Permissions issues.")
        return False
    
    return True


def load_cache():
    """Charge le cache depuis le fichier JSON."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Sauvegarde le cache dans le fichier JSON."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=4)

def load_last_report():
    """Charge la liste des dossiers inactifs du dernier rapport."""
    if LAST_REPORT_FILE.exists():
        with open(LAST_REPORT_FILE, 'r') as f:
            return json.load(f)
    return []

def save_last_report(inactive_folders):
    """Sauvegarde la liste des dossiers inactifs dans le fichier last.json."""
    with open(LAST_REPORT_FILE, 'w') as f:
        json.dump(inactive_folders, f, indent=4)

def is_folder_notified(cache, folder_id):
    """Vérifie si le dossier a déjà été notifié."""
    return folder_id in cache

def update_cache(cache, folder_id):
    """Ajoute un dossier au cache."""
    cache[folder_id] = datetime.now().isoformat()

def should_reprocess_folder(cache, folder_id, last_modified):
    """
    Vérifie si un dossier dans le cache doit être retraité.
    Retourne True si le dossier a été modifié récemment ou s'il n'est plus inactif.
    """
    if folder_id not in cache:
        return True  # Le dossier n'est pas dans le cache, il doit être traité

    cached_date = parser.isoparse(cache[folder_id])
    # Assure que les deux dates sont "conscientes" (avec fuseau horaire)
    if last_modified.tzinfo is None:
        last_modified = last_modified.replace(tzinfo=cached_date.tzinfo)
    elif cached_date.tzinfo is None:
        cached_date = cached_date.replace(tzinfo=last_modified.tzinfo)
    return last_modified > cached_date  # Retraiter si la date de modification est plus récente

def get_synced_folders():
    """Récupère la liste des dossiers synchronisés depuis l'API SyncThing."""
    try:
        logging.info("Syncthing API connection...")
        response = requests.get(f"{API_URL}/rest/system/status", headers=headers)
        response.raise_for_status()

        if response.status_code == 200:
            logging.info("Successfully connected to Syncthing API.")

        logging.info("Retrieve synced folders...")
        folders_response = requests.get(f"{API_URL}/rest/config/folders", headers=headers)
        folders_response.raise_for_status()

        return folders_response.json()

    except requests.exceptions.RequestException as e:
        logging.error(f"Syncthing API error : {e}")
        return []

def get_last_modified_file_date(folder_id):
    """Récupère la date de modification la plus récente parmi les fichiers d'un dossier."""
    try:
        browse_response = requests.get(f"{API_URL}/rest/db/browse?folder={folder_id}", headers=headers)
        browse_response.raise_for_status()

        files_data = browse_response.json()
        most_recent_date = None

        for file in files_data:
            if file.get('modTime'):
                file_date = parser.isoparse(file['modTime'])
                if most_recent_date is None or file_date > most_recent_date:
                    most_recent_date = file_date

        return most_recent_date

    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving content of folder {folder_id} : {e}")
        return None
    except ValueError as e:
        logging.error(f"Date conversion error for folder {folder_id} : {e}")
        return None

def is_older_than_threshold(last_modified_date):
    """Vérifie si la date de dernière modification est plus ancienne que le seuil défini."""
    threshold_date = datetime.now(last_modified_date.tzinfo) - timedelta(days=DAYS_THRESHOLD)
    return last_modified_date < threshold_date

def generate_report(folders, inactive_folders):
    """Génère un rapport hebdomadaire."""
    report = {
        "total_folders": len(folders),
        "inactive_folders_count": len(inactive_folders),
        "inactive_folders": inactive_folders,
        "generated_at": datetime.now().isoformat()
    }
    return report

def send_email(report):
    """Envoie le rapport par email."""
    sender_email        = os.getenv("SMTP_SENDER")
    receiver_email      = os.getenv("SMTP_RECEIVER")
    smtp_server         = os.getenv("SMTP_SERVER")
    smtp_port           = int(os.getenv("SMTP_PORT"))
    smtp_username       = os.getenv("SMTP_USERNAME")
    smtp_password       = os.getenv("SMTP_PASSWORD")

    subject = "Syncthing Daily Report"
    body = f"""
    Syncthing Daily Report :
    - Sync folders : {report['total_folders']}
    - Inactive folders : {report['inactive_folders_count']}
    - List :
    {json.dumps(report['inactive_folders'], indent=4)}
    """

    msg             = MIMEMultipart()
    msg['From']     = sender_email
    msg['To']       = receiver_email
    msg['Subject']  = subject
    msg['Date']     = formatdate(localtime=True)  # Ajouter la date actuelle
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        logging.info("Report sent by email.")
    except Exception as e:
        logging.error(f"Error on sending report by email : {e}")

def send_gotify(report):
    """Envoie le rapport via Gotify."""
    gotify_url      = os.getenv("GOTIFY_URL")
    gotify_token    = os.getenv("GOTIFY_TOKEN")

    message = f"""
    Syncthing Daily Report :
    - Sync folders : {report['total_folders']}
    - Inactive folders : {report['inactive_folders_count']}
    """

    try:
        response = requests.post(
            f"{gotify_url}/message",
            headers={"X-Gotify-Key": gotify_token},
            json={"message": message, "priority": 5}
        )
        response.raise_for_status()
        logging.info("Report sent to Gotify.")
    except Exception as e:
        logging.error(f"Error on sending report to Gotify : {e}")

def send_discord(report):
    """Envoie le rapport via un webhook Discord."""
    webhook_url = os.getenv("DISCORD_WEBHOOK")

    message = {
        "content": "Syncthing Daily Report :",
        "embeds": [
            {
                "title": "Stats",
                "fields": [
                    {"name": "Sync folders", "value": str(report['total_folders'])},
                    {"name": "Inactive folders", "value": str(report['inactive_folders_count'])},
                ]
            }
        ]
    }

    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
        logging.info("Report sent to Discord.")
    except Exception as e:
        logging.error(f"Error when sending report to Discord : {e}")

def job():
    """Fonction à exécuter tous les jours à 20h."""
    logging.info(f"Planned task running at {datetime.now()}")
    main()

def main():
    logging.info("Running check...")
    cache               = load_cache()
    last_report         = load_last_report()
    folders             = get_synced_folders()
    inactive_folders    = []

    for folder in folders:
        folder_id       = folder['id']
        last_modified   = get_last_modified_file_date(folder_id)
        if last_modified:
            if is_older_than_threshold(last_modified):
                if should_reprocess_folder(cache, folder_id, last_modified):
                    inactive_folders.append({
                        "id": folder_id,
                        "label": folder.get('label', 'No label'),
                        "last_modified": last_modified.isoformat()
                    })
                    update_cache(cache, folder_id)
            else:
                # Si le dossier n'est plus inactif, le retirer du cache
                if folder_id in cache:
                    logging.info(f"Folder {folder_id} is no more inactive. Removed from cache.")
                    del cache[folder_id]

    if inactive_folders:
        report = generate_report(folders, inactive_folders)
        
        smtp_enable = os.getenv("SMTP_ENABLE")
        if smtp_enable.lower() == "true":
            send_email(report)

        gotify_enable = os.getenv("GOTIFY_ENABLE")
        if gotify_enable.lower() == "true":
            send_gotify(report)

        discord_enable = os.getenv("DISCORD_ENABLE")
        if discord_enable.lower() == "true":
            send_discord(report)

        save_cache(cache)
        save_last_report(inactive_folders)

    logging.info("Done.")

if __name__ == "__main__":

    # Chemins des dossiers à vérifier
    directories_to_check = ["/config", "/logs"]

    # Vérifie chaque dossier
    for directory in directories_to_check:
        if not check_directory(directory):
            print(f"App stopped because of an error with folder '{directory}'.")
            sys.exit(1)  # Arrête le script avec un code d'erreur

    main()

    # Planifie l'exécution de la fonction `job` tous les jours à 20h
    schedule.every().day.at("08:00").do(job)

    logging.info("Waiting for next run...")

    # Boucle pour maintenir le script en vie et vérifier les tâches planifiées
    while True:
        schedule.run_pending()
        time.sleep(1)  # Attendre 1 seconde avant de vérifier à nouveauc