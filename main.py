from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)
json_dateipfad = "./objekte.json"

@app.route('/api/objekt_daten', methods=['POST'])
def speichere_objekt_daten():
    daten = request.json
    bild_id = daten['bild_id']  # Nehmen wir an, dass die Bild-ID im Body enthalten ist
    kategorie = daten['kategorie']
    position = daten.get('position', {})
    groesse = daten.get('groesse', {})

    objekte = lese_oder_erstelle_datei()
    
    # Überprüfen, ob die Bild-ID bereits existiert
    if any(objekt['bild_id'] == bild_id for objekt in objekte):
        return jsonify({"status": "Fehler", "message": "Bild bereits bearbeitet"}), 400

    objekt = {
        "bild_id": bild_id,
        "kategorie": kategorie,
        "position": position,
        "groesse": groesse
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
        return json.load(datei)

if __name__ == '__main__':
    app.run(debug=True)
