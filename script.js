document.addEventListener('DOMContentLoaded', function() {
    const kategorienListe = document.getElementById('kategorienListe');
    const bildContainer = document.getElementById('bildContainer');
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    let startX, startY;

    // Canvas-Styling und -Eigenschaften
    canvas.width = 800;  // Breite anpassen
    canvas.height = 600; // Höhe anpassen
    canvas.style.border = '1px solid black';
    bildContainer.appendChild(canvas);

    // Funktion zum Zeichnen der Bounding Box
    function drawBox(x, y, width, height) {
        ctx.clearRect(0, 0, canvas.width, canvas.height); // Vorheriges Zeichnen löschen
        ctx.beginPath();
        ctx.rect(x, y, width, height);
        ctx.stroke();
    }

    // Canvas-Event-Handler
    canvas.onmousedown = (e) => {
        startX = e.offsetX;
        startY = e.offsetY;
        isDrawing = true;
    };

    canvas.onmousemove = (e) => {
        if (isDrawing) {
            drawBox(startX, startY, e.offsetX - startX, e.offsetY - startY);
        }
    };

    canvas.onmouseup = () => {
        isDrawing = false;
    };

    // Funktion zum Laden der Kategorien vom Server
    function loadCategories() {
        fetch('/api/kategorien')
            .then(response => response.json())
            .then(kategorien => {
                kategorien.forEach(kategorie => {
                    const kategorieDiv = document.createElement('div');
                    kategorieDiv.textContent = kategorie;
                    kategorieDiv.classList.add('kategorie');
                    kategorienListe.appendChild(kategorieDiv);
                });
            })
            .catch(error => {
                console.error('Fehler beim Laden der Kategorien:', error);
            });
    }

    loadCategories(); // Kategorien beim Start laden
});
