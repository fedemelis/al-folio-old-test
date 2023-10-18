from main import *
import json
import os
from operator import itemgetter

def is_type(entry_type, target_type):
    return entry_type.lower() == target_type.lower()

def thesisManipulation(file_name, edatapath):
    df = pd.read_excel(os.path.join(edatapath, f"{file_name}.xlsx"))
    print(str(df))
    # Rimuovi le colonne con nomi "unnamed"
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Converti il DataFrame in formato JSON senza includere l'indice
    json_data = df.to_json(orient="records", indent=4)

    # Salva il JSON su un file temporaneo
    temp_json_file = os.path.join(edatapath, f"temp_{file_name}.json")
    with open(temp_json_file, "w") as json_data_file:
        json_data_file.write(json_data)

    print("Dati estratti e salvati in formato JSON senza campi 'unnamed'.")

    # Leggi il JSON
    with open(temp_json_file, "r") as json_file:
        data = json.load(json_file)

    # Definisci l'ordine delle tipologie
    custom_order = ["PhD", "Master", "Bachelor"]

    # Ordina le tesi in base alla tipologia personalizzata e poi per "anno"
    sorted_thesis = sorted(data, key=lambda x: (custom_order.index(x["Tipologia"]), x["Ciclo/Anno Accademico"]))

    # Sovrascrivi il file JSON originale con i dati ordinati
    with open(os.path.join(edatapath, f"{file_name}.json"), "w") as json_data_file:
        json.dump(sorted_thesis, json_data_file, indent=4)

    print("Tesi ordinate per Tipologia personalizzata e Anno e salvate nel file JSON.")

    # Elimina il file temporaneo
    os.remove(temp_json_file)

    with open(os.path.join(edatapath, f"{file_name}.json"), "r") as json_file:
        data = json.load(json_file)

    # Traccia le prime occorrenze delle tipologie di tesi [PhD, Master, Bachelor]
    firstOccurrence = [True, True, True]
    markdownText = ""
    seenYear = []
    bachelorCount = 0

    markdownText = "---\n" \
                   "layout: page\n" \
                   "permalink: /thesis/\n" \
                   "title: Students\n" \
                   "description: List of students I have tutored.\n" \
                   "nav: false\n" \
                   "nav_order: 5\n" \
                   "---\n\n"

    for entry in data:
        tipologia = entry["Tipologia"]
        nome = entry["Nome"].upper()
        cognome = entry["Cognome"].upper()
        anno = entry["Ciclo/Anno Accademico"]
        titolo = entry["Titolo"]

        # Controlla il tipo dell'entry (case-insensitive) e aggiorna la lista firstOccurrence
        if is_type(tipologia, "PhD") and firstOccurrence[0]:
            # Primo PhD
            print("Formatto le PhD")
            markdownText += f"## Advisor of {tipologia} student (Doctorate Course in ICT)\n\n"
            firstOccurrence[0] = False
            markdownText += f"- {nome} {cognome} ({anno} Ciclo)\n"
        elif is_type(tipologia, "PhD"):
            markdownText += f"- {nome} {cognome}\n"
        if is_type(tipologia, "Master") and firstOccurrence[1]:
            # Primo Master
            print("Formatto le Master")
            markdownText += f"\n## Advisor in {tipologia} Thesis (Dipartimento di Ingegneria \"Enzo Ferrari\")\n\n"
            firstOccurrence[1] = False
            seenYear.append(anno)
            markdownText += f"\n{anno}\n"
            markdownText += f"- {cognome} {nome}: {titolo}, ({anno})\n"
        elif is_type(tipologia, "Master"):
            if anno not in seenYear:
                seenYear.append(anno)
                markdownText += f"\n{anno}\n"
                markdownText += f"- {cognome} {nome}: {titolo}, ({anno})\n"
            else:
                markdownText += f"- {cognome} {nome}: {titolo}, ({anno})\n"
        if is_type(tipologia, "Bachelor") and firstOccurrence[2]:
            # Primo Bachelor
            print("Formatto le Bachelor")
            markdownText += f"\n## Advisor in {tipologia} Thesis (Dipartimento di Ingegneria \"Enzo Ferrari\")\n\n"
            firstOccurrence[2] = False
            bachelorCount += 1
            markdownText += f"{bachelorCount}.  {nome} {cognome}: {titolo}, a.a. ({anno})\n"
        elif is_type(tipologia, "Bechelor"):
            bachelorCount += 1
            markdownText += f"{bachelorCount}.  {nome} {cognome}: {titolo}, a.a. ({anno})\n"

    print(markdownText)

    mdThesis = os.path.join(edatapath, f"{file_name}.md")
    with open(mdThesis, "w") as markdownTheis:
        markdownTheis.write(markdownText)
        print("Tesi salvate in formato markdown")


def gitThesisUploader(dati_utente, edatapath):
    # Ottieni un'istanza di GitHub usando il token
    g = Github(dati_utente.get("_Token"))

    repo_name = dati_utente.get("_AccountName") + ".github.io"
    repo = g.get_user().get_repo(repo_name)

    try:
        # Prova a ottenere il contenuto del file thesis.md
        file = repo.get_contents("_pages/thesis.md")
        sha = file.sha
        print("File delle tesi esiste su GitHub.")
    except Exception as e:
        # Se il file non esiste, crealo
        if "404" in str(e):
            with open(os.path.join(edatapath, "thesis.md"), "r") as file_content:
                file_content_str = file_content.read()
                repo.create_file("_pages/thesis.md", "Initial thesis file", file_content_str)
            print("File delle tesi creato su GitHub.")

            with open(os.path.join(edatapath, "thesis.md"), "r") as file_content:
                file_content_str = file_content.read()
                repo.update_file("_pages/thesis.md", "automatic thesis update", file_content_str, sha)
                print("File delle tesi aggiornato su GitHub.")
                return

    # Se il file esiste, aggiorna il contenuto
    with open(os.path.join(edatapath, "thesis.md"), "r") as file_content:
        file_content_str = file_content.read()
        repo.update_file("_pages/thesis.md", "automatic thesis update", file_content_str, sha)
        print("File delle tesi aggiornato su GitHub.")