import os
import random
import urllib.request
import pandas as pd
import json
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from github import Github

def readexcelfile(file_name):
    # Leggi il file Excel
    df = pd.read_excel(file_name)

    # Rimuovi le colonne con nomi "unnamed"
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Converti il DataFrame in formato JSON senza includere l'indice
    json_data = df.to_json(orient="records", indent=4)

    # Salva il JSON su un file
    with open("C:\\Users\\fede\\Desktop\\dati-json.json", "w") as json_file:
        json_file.write(json_data)

    print("Dati estratti e salvati in formato JSON senza campi 'unnamed'.")

    # Leggi il JSON
    with open("C:\\Users\\fede\\Desktop\\dati-json.json", "r") as json_file:
        data = json.load(json_file)

    print("Dati letti dal file JSON.")

    # Converti il JSON in formato BibTeX
    bib_database = BibDatabase()
    for entry in data:
        bib_entry = {
            'title': entry['Nome'],
            'author': entry['Autore'],
            'year': str(entry['Anno']),
            'visibile': str(entry['Visibile']),
            'ENTRYTYPE': 'article',  # Imposta il tipo di voce BibTeX appropriato
            'ID': str(random.randint(1, 1000)) # Imposta l'ID della voce BibTeX
        }
        bib_database.entries.append(bib_entry)

    print("Dati convertiti in formato BibTeX.")

    # Salva il file BibTeX
    with open("C:\\Users\\fede\\Desktop\\dati-bibtex.bib", "w") as bibtex_file:
        writer = BibTexWriter()
        bibtex_file.write(writer.write(bib_database))

    print("Dati convertiti e salvati in formato BibTeX.")

def web_file_downloader(url, file_name):
    try:
        urllib.request.urlretrieve(url, file_name)
    except Exception as e:
        print(e)
        return False
    print("File downloaded successfully")
    return True


def gituploader(github_username, git_token):

    #retriving the github instance by action token
    g = Github(git_token)

    #g = Github("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")

    #building repo name
    repo_name = github_username + ".github.io"

    #getting the repo
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

if __name__ == "__main__":
    # Utilizza l'URL diretto per il download da Google Drive
    #web_file_downloader("https://drive.google.com/uc?export=download&id=1zPM9n-uXY-oPQWB-oKuz8A5srVEAb6VL", "C:\\Users\\fede\\Desktop\\file-di-prova.xlsx")
    #readexcelfile("C:\\Users\\fede\\Desktop\\file-di-prova.xlsx")
    gituploader("fedemelis", "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")