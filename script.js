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
