// script.js
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/objekt_daten')
        .then(response => response.json())
        .then(data => {
            const objektListe = document.getElementById('objektListe');
            data.forEach(objekt => {
                const div = document.createElement('div');
                div.className = 'objekt';
                div.innerHTML = `
                    <img src="/pfad/zu/bildern/${objekt.bild_id}.jpg" alt="${objekt.kategorie}">
                    <div>Kategorie: ${objekt.kategorie}</div>
                    <div class="koordinaten">Koordinaten: x=${objekt.koordinaten.x}, y=${objekt.koordinaten.y}, breite=${objekt.koordinaten.breite}, höhe=${objekt.koordinaten.hoehe}</div>
                `;
                objektListe.appendChild(div);
            });
        })
        .catch(error => console.error('Fehler beim Laden der Daten:', error));
});

function kategorieHinzufuegen() {
    const kategorieName = document.getElementById('kategorieName').value;

    fetch('/api/kategorie_hinzufuegen', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: kategorieName }),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        // Hier könnten Sie die Kategorienliste aktualisieren
    })
    .catch(error => {
        console.error('Fehler beim Hinzufügen der Kategorie:', error);
    });
}


function ladeKategorien() {
    const kategorien = ['Kategorie 1', 'Kategorie 2', 'Kategorie 3']; // Beispielkategorien
    const kategorienListe = document.getElementById('kategorienListe');
    kategorien.forEach(kategorie => {
        const div = document.createElement('div');
        div.textContent = kategorie;
        kategorienListe.appendChild(div);
    });
}

function zeigeBild(bildPfad) {
    const bild = document.getElementById('aktuellesBild');
    bild.src = bildPfad;
}
document.addEventListener('DOMContentLoaded', function() {
    kategorienLaden();
});

function kategorienLaden() {
    fetch('/api/kategorien')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('kategorieContainer');
            container.innerHTML = ''; // Container leeren
            data.forEach(kategorie => {
                const div = document.createElement('div');
                div.textContent = kategorie;
                container.appendChild(div);
            });
        })
        .catch(error => console.error('Fehler beim Laden der Kategorien:', error));
}

function kategorieHinzufuegen() {
    const kategorieName = document.getElementById('kategorieName').value;
    fetch('/api/kategorie_hinzufuegen', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: kategorieName }),
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        kategorienLaden(); // Kategorien neu laden, um die Liste zu aktualisieren
    })
    .catch(error => {
        console.error('Fehler beim Hinzufügen der Kategorie:', error);
    });
}
