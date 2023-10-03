import os
import random
import urllib.request
from datetime import datetime

import pandas as pd
import json
import bibtexparser
import requests
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from github import Github

def readexcelfile(file_name):
    #TODO PROBLEMA IN LETTURA FILE EXCEL
    # Leggi il file Excel con pandas
    df = pd.read_excel(os.path.join("edata", f"{file_name}.xlsx"))

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
        bib_entry = {
            'title': entry['title'],
            'author': entry['author'],
            'journal': entry['journal'],
            'volume': str(entry['volume']),
            'number': str(entry['number']),
            'pages': str(entry['pages']),
            'year': str(entry['Anno']),
            'visivle': "true",
            'ENTRYTYPE': 'article',
            #'visibile': str(entry['Visibile']),
            #'ENTRYTYPE': 'article',  # Imposta il tipo di voce BibTeX appropriato
            'ID': str(random.randint(1, 1000)) # Imposta l'ID della voce BibTeX
        }
        bib_database.entries.append(bib_entry)

    print("Dati convertiti in formato BibTeX.")

    # Salva il file BibTeX
    with open(os.path.join("edata", f"{file_name}.bib"), "w") as bibtex_file:
        writer = BibTexWriter()
        bibtex_file.write(writer.write(bib_database))

    print("Dati convertiti e salvati in formato BibTeX.")

    #TODO gestire l'upload dei file con il metodo gituploader

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


def gituploader(dati_utente):

    #retriving the github instance by action token
    g = Github(dati_utente.get("_Token"))

    #g = Github("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")
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
        with open("C:\\Users\\fede\\Desktop\\dati-bibtex.bib", "r") as file_content:
            file_content_str = file_content.read()
            # Aggiorna il file con il nuovo contenuto
            repo.update_file("_bibliography/papers.bib", "update", file_content_str, sha)

        print("File file.bib aggiornato su GitHub.")
    except Exception as e:
        print(f"Errore nell'aggiornamento del file: {str(e)}")


def startup():
    CONFIG = "excel_config.json"

    if os.path.isfile(CONFIG) and os.access(CONFIG, os.R_OK) and os.path.exists(CONFIG):
        with open(CONFIG, 'r') as config_file:
            dati_utente = json.load(config_file)
    else:
        account_name = input("Inserisci il tuo nome utente di GitHub: ")
        github_token = input("Inserisci il tuo token di GitHub: ")
        api_key = input("Inserisci la tua Google API key: ")
        link_bibliografia = input("Inserisci il link alla bibliografia: ")
        #TODO: aggiungere campi da compilare

        dati_utente = {
            "_AccountName": account_name,
            "_Token": github_token,
            "_ApiKey": api_key,
            "BibLink": link_bibliografia
        }

        with open(CONFIG, "w") as config_file:
            json.dump(dati_utente, config_file)

    searchForUpdate(dati_utente)


def searchForUpdate(dati_utente):
    # Estrai l'ID del file dal link
    #TODO modificarlo in modo che prenda sempre il campo dopo /d/
    file_id = dati_utente.get("BibLink").split('/')[-1]
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
            #prendo il nome del file dal json dei metadati
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


if __name__ == "__main__":
    #web_file_downloader("https://drive.google.com/uc?export=download&id=1zPM9n-uXY-oPQWB-oKuz8A5srVEAb6VL", "C:\\Users\\fede\\Desktop\\file-di-prova.xlsx")
    #readexcelfile("C:\\Users\\fede\\Desktop\\file-di-prova.xlsx")
    startup()
    "https://docs.google.com/spreadsheets/d/17znBoG8Fge2EatZi8j6BFZIP_cbph5CP/edit?usp=drive_link&ouid=105879917516520212135&rtpof=true&sd=true"
    #gituploader("fedemelis", "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")