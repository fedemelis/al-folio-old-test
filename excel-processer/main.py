import os
import random
import string
import time
import urllib.request
import threading
from datetime import datetime

import pandas as pd
import json
import bibtexparser
import requests
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from github import Github, GithubException
from thesis import *
from bibliography import *


def user_input_thread():
    global should_exit
    user_input = input("Digita \"si\" per uscire: ")
    if user_input == "si" or user_input == "Si" or user_input == "SI" or user_input == "yes" or user_input == "Yes" or user_input == "YES":
        should_exit = True
        print("Quitting...")


# Verifica l'esistenza di un nome utente GitHub
def is_valid_github_username(username):
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url)
    return response.status_code == 200


# Verifica l'efficacia di un token GitHub
def is_valid_github_token(token, repository_name):
    try:
        g = Github(token)
        repo = g.get_user().get_repo(repository_name)

        # Prova a creare un file di test
        try:
            repo.create_file("test.txt", "Creating test file", "test content")
        except GithubException as e:
            if e.status == 422 and "sha" in str(e):
                # Ignora l'errore "Invalid request. \"sha\" wasn't supplied."
                pass
            else:
                raise

        # Prova a rimuovere il file di test
        try:
            file = repo.get_contents("test.txt")
            repo.delete_file(file.path, "Removing test file", file.sha)
        except GithubException as e:
            if e.status == 404:
                # Il file non esiste, ma è stato comunque rimosso con successo
                pass
            else:
                raise

        return True
    except Exception as e:
        print(e)
        return False


# Testa la validità di un link alla bibliografia
def is_valid_drive_link(link):
    try:
        response = requests.get(link)
        return response.status_code == 200
    except Exception as e:
        return False


# Funzione di avvio, crea il file di configurazione con i dati inseriti dall'utente e lancia la ricerca di aggiornamenti
def startup():
    # Se si utilizza Google Colab, rimuovere il commento dalla riga seguente
    # drive.mount('/content/drive')

    if not os.path.exists("drive"):
        os.mkdir("drive")

    if not os.path.exists(os.path.join("drive", "MyDrive")):
        os.mkdir(os.path.join("drive", "MyDrive"))

    if not os.path.exists(os.path.join("drive", "MyDrive", "excel-updater")):
        os.mkdir(os.path.join("drive", "MyDrive", "excel-updater"))

    if not os.path.exists(os.path.join("drive", "MyDrive", "excel-updater", "data")):
        os.mkdir(os.path.join("drive", "MyDrive", "excel-updater", "data"))

    if not os.path.exists(os.path.join("drive", "MyDrive", "excel-updater", "data", "static_papers_tag.bib")):
        with open(os.path.join("drive", "MyDrive", "excel-updater", "data", "static_papers_tag.bib"), "w") as static_papers_tag_file:
            static_papers_tag_file.write(""
                                         "---\n"
                                         "---\n"
                                         "@string{PVLDB = {Proceedings of VLDB Endowment,}}\n"
                                         "@string{SAC = {Symposium on Applied Computing,}}\n"
                                         "@string{SEBD = {Proceedings of Italian Symposium on Advanced Database Systems,}}\n"
                                         "@string{CIKM = {Proceedings of International Conference on Information and Knowledge Management,}}\n"
                                         "@string{EDBT = {Proceedings of International Conference on Extending Database Technology,}}\n"
                                         "@string{SIGMOD = {Proceedings of International Conference on Management of Data (SIGMOD),}}\n"
                                         "@string{Inf.Syst. = {Information Systems,}}\n"
                                         "@string{iiWAS = {Proceedings of International Conference on Information Integration and Web-based Applications (iiWAS),}}\n"
                                         "@string{TKDE = {IEEE Transaction on Knowledge and Data Engineering (TKDE),}}\n")




    CONFIG = os.path.join("drive", "MyDrive", "excel-updater", "data", "excel_config.json")

    if os.path.isfile(CONFIG) and os.access(CONFIG, os.R_OK) and os.path.exists(CONFIG):
        with open(CONFIG, 'r') as config_file:
            dati_utente = json.load(config_file)
    else:
        while True:
            account_name = input("Inserisci il tuo nome utente di GitHub: ")
            if is_valid_github_username(account_name):
                break
            else:
                print("Nome utente di GitHub non valido. Riprova.")

        while True:
            github_token = input("Inserisci il tuo token di GitHub: ")
            if is_valid_github_token(github_token, f"{account_name}.github.io"):
                break
            else:
                print("Token di GitHub non valido. Riprova.")

        while True:
            api_key = input("Inserisci la tua Google API key: ")
            # Aggiungi il controllo dell'API Key qui, se necessario
            break

        while True:
            link_bibliografia = input("Inserisci il link alla bibliografia: ")
            if is_valid_drive_link(link_bibliografia):
                break
            else:
                print("Link alla bibliografia non valido. Riprova.")

        while True:
            link_tesi = input("Inserisci il link alle tesi: ")
            if is_valid_drive_link(link_tesi):
                break
            else:
                print("Link alle tesi non valido. Riprova.")
        dati_utente = {
            "_AccountName": account_name,
            "_Token": github_token,
            "_ApiKey": api_key,
            "BibLink": link_bibliografia,
            "ThesisLink": link_tesi
        }

        with open(CONFIG, "w") as config_file:
            json.dump(dati_utente, config_file)

    edatapath = os.path.join("drive", "MyDrive", "excel-updater", "data", "edata")
    # crea la cartella edata
    if not os.path.exists(edatapath):
        os.mkdir(os.path.join(edatapath))

    searchForUpdate(dati_utente, edatapath)


# Funzione che controlla se il file su Google Drive è stato modificato più recentemente di quello locale
def searchForUpdate(dati_utente, edatapath):
    # Estrai l'ID del file dal link
    # TODO modificarlo in modo che prenda sempre il campo dopo /d/
    file_id_bib = dati_utente.get("BibLink").split('/d/')[-1].split('/')[0]
    file_id_thesis = dati_utente.get("ThesisLink").split('/d/')[-1].split('/')[0]
    api_key = dati_utente.get("_ApiKey")
    link = [file_id_bib, file_id_thesis]
    if not os.path.exists(edatapath):
        os.mkdir(edatapath)
    for file_id in link:
        # URL per ottenere i metadati del file utilizzando la chiave API
        metadata_url = f'https://www.googleapis.com/drive/v3/files/{file_id}?fields=name,modifiedTime&key={api_key}'
        print(metadata_url)
        try:
            # Effettua una richiesta GET ai metadati del file
            response = requests.get(metadata_url)

            if response.status_code == 200:
                # Estrai l'ora dell'ultima modifica e il nome del file dai metadati
                data = response.json()
                ultima_modifica_drive = datetime.fromisoformat(data['modifiedTime'][:-1])
                # prendo il nome del file dal json dei metadati
                nome_file = data['name']

                # Ottieni l'ora dell'ultima modifica del file locale, se esiste
                percorso_file_locale = os.path.join(edatapath, nome_file)
                ultima_modifica_locale = None

                if os.path.exists(percorso_file_locale):
                    ultima_modifica_locale = datetime.utcfromtimestamp(os.path.getmtime(percorso_file_locale))

                # Confronta le date di modifica
                if ultima_modifica_locale is None or ultima_modifica_drive > ultima_modifica_locale:
                    # Scarica il file solo se il file su Google Drive è stato modificato più recentemente
                    web_file_downloader(file_id, nome_file, dati_utente, edatapath)
                else:
                    print(f'Il file locale è già aggiornato.')
            else:
                print(f'Errore nella richiesta dei metadati. Codice di stato: {response.status_code}')
        except Exception as e:
            print(f'Errore durante la richiesta dei metadati o il download del file: {str(e)}')


# Funzione che scarica il file da Google Drive e lo salva nella cartella edata
def web_file_downloader(id, file_name, dati_utente, edatapath):
    link = f"https://drive.google.com/uc?export=download&id={id}"
    try:
        urllib.request.urlretrieve(link, os.path.join(edatapath, file_name))
    except Exception as e:
        print(e)
        return False
    print("File downloaded successfully")
    if file_name.endswith("papers.xlsx"):
        papersManipulation(file_name.replace(".xlsx", ""), edatapath)
        gitPapersUploader(dati_utente, edatapath)
    else:
        thesisManipulation(file_name.replace(".xlsx", ""), edatapath)
        gitThesisUploader(dati_utente, edatapath)


# Funzione che legge il file Excel e lo converte in JSON e BibTeX


if __name__ == "__main__":
    # drive.mount('/content/drive')
    input_thread = threading.Thread(target=user_input_thread)
    should_exit = False
    first_exec = True
    while not should_exit:
        if first_exec:
            print("Starting...")
            startup()
            first_exec = False
            input_thread.start()
        else:
            time.sleep(20)
            if should_exit:
                break
            else:
                # chiudi il thread
                startup()
    print("Exited.")

    input_thread.join()
