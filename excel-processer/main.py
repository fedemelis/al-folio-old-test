import os
import random
import string
import time
import urllib.request
from datetime import datetime

import pandas as pd
import json
import bibtexparser
import requests
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from github import Github, GithubException


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
def is_valid_bibliography_link(link):
    try:
        response = requests.get(link)
        return response.status_code == 200
    except Exception as e:
        return False


# Funzione di avvio, crea il file di configurazione con i dati inseriti dall'utente e lancia la ricerca di aggiornamenti
def startup():
    CONFIG = "excel_config.json"

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
            if is_valid_bibliography_link(link_bibliografia):
                break
            else:
                print("Link della bibliografia non valido. Riprova.")
        dati_utente = {
            "_AccountName": account_name,
            "_Token": github_token,
            "_ApiKey": api_key,
            "BibLink": link_bibliografia
        }

        with open(CONFIG, "w") as config_file:
            json.dump(dati_utente, config_file)

        # crea la cartella edata
        if not os.path.exists("edata"):
            os.mkdir("edata")

    searchForUpdate(dati_utente)


# Funzione che controlla se il file su Google Drive è stato modificato più recentemente di quello locale
def searchForUpdate(dati_utente):
    # Estrai l'ID del file dal link
    # TODO modificarlo in modo che prenda sempre il campo dopo /d/
    file_id = dati_utente.get("BibLink").split('/d/')[-1].split('/')[0]
    api_key = dati_utente.get("_ApiKey")

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
            percorso_file_locale = os.path.join("edata", nome_file)
            ultima_modifica_locale = None

            if os.path.exists(percorso_file_locale):
                ultima_modifica_locale = datetime.utcfromtimestamp(os.path.getmtime(percorso_file_locale))

            # Confronta le date di modifica
            if ultima_modifica_locale is None or ultima_modifica_drive > ultima_modifica_locale:
                # Scarica il file solo se il file su Google Drive è stato modificato più recentemente
                web_file_downloader(file_id, nome_file, dati_utente)
            else:
                print(f'Il file locale è già aggiornato.')
        else:
            print(f'Errore nella richiesta dei metadati. Codice di stato: {response.status_code}')
    except Exception as e:
        print(f'Errore durante la richiesta dei metadati o il download del file: {str(e)}')


# Funzione che scarica il file da Google Drive e lo salva nella cartella edata
def web_file_downloader(id, file_name, dati_utente):
    link = f"https://drive.google.com/uc?export=download&id={id}"
    try:
        urllib.request.urlretrieve(link, os.path.join("edata", file_name))
    except Exception as e:
        print(e)
        return False
    print("File downloaded successfully")
    readexcelfile(file_name.replace(".xlsx", ""))
    gituploader(dati_utente)


# Funzione che legge il file Excel e lo converte in JSON e BibTeX
def readexcelfile(file_name):
    # Leggi il file Excel con pandas
    df = pd.read_excel(os.path.join("edata", f"{file_name}.xlsx"))
    print(str(df))
    # Rimuovi le colonne con nomi "unnamed"
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Converti il DataFrame in formato JSON senza includere l'indice
    json_data = df.to_json(orient="records", indent=4)

    # Salva il JSON su un file
    with open(os.path.join("edata", f"{file_name}.json"), "w") as json_data_file:
        json_data_file.write(json_data)

    print("Dati estratti e salvati in formato JSON senza campi 'unnamed'.")

    # Leggi il JSON
    with open(os.path.join("edata", f"{file_name}.json"), "r") as json_file:
        data = json.load(json_file)

    print("Dati letti dal file JSON.")

    # Converti il JSON in formato BibTeX
    bib_database = BibDatabase()

    for entry in data:
        lines = entry["Paper"].split('\n')
        last_line = lines[-1]

        # Aggiungo i campi dopo l'ultima riga
        updated_entry = '\n'.join(lines[:-1]) + (
                f",\n  abbr = {{{entry['Abbr']}}},\n  bibtex_show = {{{str(entry['BibTex show']).lower()}}},\n  selected = {{{str(entry['Selected']).lower()}}}" +
                last_line
        )

        # Assegna l'entry BibTeX aggiornata
        entry["Paper"] = updated_entry
        bib_database.entries.append(bibtexparser.loads(entry["Paper"]).entries[0])

    print("Dati convertiti in formato BibTeX.")

    # Salva il file BibTeX
    with open(os.path.join("edata", f"{file_name}.bib"), "w") as bibtex_file:
        writer = BibTexWriter()
        bibtex_file.write(writer.write(bib_database))

    print("Dati convertiti e salvati in formato BibTeX.")


# Funzione che carica il file BibTeX su GitHub
def gituploader(dati_utente):
    # retriving the GitHub instance by action token
    g = Github(dati_utente.get("_Token"))

    repo_name = dati_utente.get("_AccountName") + ".github.io"

    repo = g.get_user().get_repo(repo_name)

    # Get the current directory path
    current_path = os.getcwd()
    # Go to the parent folder
    parent_folder = os.path.abspath(os.path.join(current_path, ".."))
    # Enter the _bibliography folder
    bibliography_folder = os.path.join(parent_folder, "_bibliography")
    # Check if the _bibliography folder exists
    if os.path.exists(bibliography_folder) and os.path.isdir(bibliography_folder):
        print("Entered the _bibliography folder.")
    else:
        print("The _bibliography folder does not exist.")
        return -1

    try:
        file = repo.get_contents("_bibliography/papers.bib")
        sha = file.sha
        with open(os.path.join("edata", "papers.bib"), "r") as file_content:
            file_content_str = file_content.read()
            # Aggiorna il file con il nuovo contenuto
            repo.update_file("_bibliography/papers.bib", "automatic update", file_content_str, sha)

        print("File file.bib aggiornato su GitHub.")
    except Exception as e:
        print(f"Errore nell'aggiornamento del file: {str(e)}")


if __name__ == "__main__":
    #TODO aggiungere meccanismo start/stop con bottone
    while True:
        print("Starting...")
        startup()
        time.sleep(60)
