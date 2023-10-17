from main import *

def papersManipulation(file_name, edatapath):
    # Leggi il file Excel con pandas
    df = pd.read_excel(os.path.join(edatapath, f"{file_name}.xlsx"))
    print(str(df))
    # Rimuovi le colonne con nomi "unnamed"
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Converti il DataFrame in formato JSON senza includere l'indice
    json_data = df.to_json(orient="records", indent=4)

    # Salva il JSON su un file
    with open(os.path.join(edatapath, f"{file_name}.json"), "w") as json_data_file:
        json_data_file.write(json_data)

    print("Dati estratti e salvati in formato JSON senza campi 'unnamed'.")

    # Leggi il JSON
    with open(os.path.join(edatapath, f"{file_name}.json"), "r") as json_file:
        data = json.load(json_file)

    print("Dati letti dal file JSON.")

    # Converti il JSON in formato BibTeX
    bib_database = BibDatabase()

    for entry in data:
        lines = entry["Paper"].split('\n')
        last_line = lines[-1]

        if entry["BibTex show"] == True:
            updated_entry = '\n'.join(lines[:-1]) + (
                    f",\n  abbr = {{{entry['Abbr']}}},\n  bibtex_show = {{{str(entry['BibTex show']).lower()}}},\n  selected = {{{str(entry['Selected']).lower()}}}" +
                    last_line
            )
        else:
            updated_entry = '\n'.join(lines[:-1]) + (
                f",\n  abbr = {{{entry['Abbr']}}},\n  selected = {{{str(entry['Selected']).lower()}}}"
            ) + last_line

        # Assegna l'entry BibTeX aggiornata
        entry["Paper"] = updated_entry
        bib_database.entries.append(bibtexparser.loads(entry["Paper"]).entries[0])

    print("Dati convertiti in formato BibTeX.")

    with open(os.path.join("drive", "MyDrive", "excel-updater", "data", "static_papers_tag.bib"), "r") as static_papers_tag_file:
        static_papers_tag = static_papers_tag_file.read()

    # Salva il file BibTeX
    with open(os.path.join(edatapath, f"{file_name}.bib"), "w") as bibtex_file:
        writer = BibTexWriter()
        bibtex_file.write(static_papers_tag)
        bibtex_file.write(writer.write(bib_database))

    print("Dati convertiti e salvati in formato BibTeX.")


# Funzione che carica il file BibTeX su GitHub
def gituploader(dati_utente, edatapath):
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
        os.mkdir(bibliography_folder)

    try:
        file = repo.get_contents("_bibliography/papers.bib")
        sha = file.sha
        with open(os.path.join(edatapath, "papers.bib"), "r") as file_content:
            file_content_str = file_content.read()
            # Aggiorna il file con il nuovo contenuto
            repo.update_file("_bibliography/papers.bib", "automatic update", file_content_str, sha)

        print("File file.bib aggiornato su GitHub.")
    except Exception as e:
        print(f"Errore nell'aggiornamento del file: {str(e)}")
