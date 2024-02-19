from flask import Flask, jsonify, request, send_from_directory
import json
import os

app = Flask(__name__, static_folder='.')
json_dateipfad = "./objekte.json"
current_directory = os.getcwd()
kategorien_pfad = "./img"  # Pfad zu den Kategorien/Bildern

def lese_oder_erstelle_datei():
    if not os.path.exists(json_dateipfad):
        os.makedirs(os.path.dirname(json_dateipfad), exist_ok=True)
        with open(json_dateipfad, 'w') as datei:
            json.dump([], datei)
    with open(json_dateipfad, 'r') as datei:
        return json.load(datei)

@app.route('/')
def home():
    return send_from_directory(current_directory, 'index.html')


@app.route('/api/kategorien', methods=['GET'])
def get_kategorien():
    kategorien = [name for name in os.listdir(kategorien_pfad) if os.path.isdir(os.path.join(kategorien_pfad, name))]
    return jsonify(kategorien)

@app.route('/api/objekt_daten', methods=['POST'])
def speichere_objekt_daten():
    daten = request.json
    objekte = lese_oder_erstelle_datei()
    if any(objekt['bild_id'] == daten['bild_id'] for objekt in objekte):
        return jsonify({"status": "Fehler", "message": "Bild bereits bearbeitet"}), 400
    objekte.append(daten)
    with open(json_dateipfad, 'w') as datei:
        json.dump(objekte, datei, indent=4)
    return jsonify({"status": "Erfolg", "message": "Daten gespeichert"})
# Zusätzliche Route, um Bilder aus den Kategorien-Unterordnern auszuliefern
@app.route('/img/<kategorie>/<bildname>')
def kategorie_bild(kategorie, bildname):
    kategorie_pfad = os.path.join('img', kategorie)  # Pfad anpassen
    bild_pfad = os.path.join(kategorie_pfad, bildname)
    return send_from_directory(current_directory, bild_pfad)


if __name__ == '__main__':
    app.run(debug=True)
