from flask import Flask, request, jsonify
import json
import uuid
import os

app = Flask(__name__)
json_dateipfad = "./objekte.json"

@app.route('/api/objekt_daten', methods=['POST'])
def speichere_objekt_daten():
    daten = request.json
    kategorie = daten['kategorie']
    koordinaten = daten['koordinaten']
    objekte = lese_oder_erstelle_datei()
    objekt = {
        "bild_id": str(uuid.uuid4()),
        "kategorie": kategorie,
        "koordinaten": koordinaten
    }
    objekte.append(objekt)
    with open(json_dateipfad, 'w') as datei:
        json.dump(objekte, datei, indent=4)
    return jsonify({"status": "Erfolg", "message": "Daten gespeichert"})

def lese_oder_erstelle_datei():
    if not os.path.exists(json_dateipfad):
        os.makedirs(os.path.dirname(json_dateipfad), exist_ok=True)
        with open(json_dateipfad, 'w') as datei:
            json.dump([], datei)
    with open(json_dateipfad, 'r') as datei:
from flask import Flask, jsonify, request, send_from_directory
import os

app = Flask(__name__, static_folder='frontend')

kategorien_pfad = './kategorien'  # Pfad zum Kategorien-Ordner

# Startseite, die das Interface anzeigt
@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

# Kategorien basierend auf Ordnern lesen
@app.route('/api/kategorien', methods=['GET'])
def get_kategorien():
    kategorien = [name for name in os.listdir(kategorien_pfad)
                  if os.path.isdir(os.path.join(kategorien_pfad, name))]
    return jsonify(kategorien)


if __name__ == '__main__':
    app.run(debug=True)
        return json.load(datei)

if __name__ == '__main__':
    app.run(debug=True)
