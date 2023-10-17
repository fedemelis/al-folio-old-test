from main import *
import json
import os
from operator import itemgetter

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
    sorted_thesis = sorted(data, key=lambda x: (custom_order.index(x["Tipologia"]), x["Anno"]))

    # Sovrascrivi il file JSON originale con i dati ordinati
    with open(os.path.join(edatapath, f"{file_name}.json"), "w") as json_data_file:
        json.dump(sorted_thesis, json_data_file, indent=4)

    print("Tesi ordinate per Tipologia personalizzata e Anno e salvate nel file JSON.")

    # Elimina il file temporaneo
    os.remove(temp_json_file)
