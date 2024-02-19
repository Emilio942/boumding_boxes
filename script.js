document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('groundboxCanvas');
    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    let startX = 0;
    let startY = 0;

    canvas.addEventListener('mousedown', (e) => {
        startX = e.offsetX;
        startY = e.offsetY;
        isDrawing = true;
    });

    canvas.addEventListener('mousemove', (e) => {
        if (isDrawing === true) {
            drawBox(ctx, startX, startY, e.offsetX, e.offsetY);
        }
    });

    canvas.addEventListener('mouseup', (e) => {
        if (isDrawing === true) {
            drawBox(ctx, startX, startY, e.offsetX, e.offsetY);
            isDrawing = false;
        }
    });

    function drawBox(ctx, startX, startY, endX, endY) {
        ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
        ctx.beginPath();
        ctx.rect(startX, startY, endX - startX, endY - startY);
        ctx.stroke();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/kategorien')
        .then(response => response.json())
        .then(kategorien => {
            const kategorienListe = document.getElementById('kategorienListe');
            kategorien.forEach(kategorie => {
                const div = document.createElement('div');
                div.textContent = kategorie;
                div.onclick = function() {
                    // Bildpfad muss entsprechend angepasst werden
                    const bildpfad = `/img/${kategorie}/deinBild.png`; // oder .jpg
                    const img = document.createElement('img');
                    img.src = bildpfad;
                    img.onload = function() {
                        // Stelle sicher, dass das alte Bild entfernt wird, bevor ein neues hinzugefügt wird
                        const bildContainer = document.getElementById('bildContainer');
                        bildContainer.innerHTML = '';
                        bildContainer.appendChild(img);
                    };
                    img.onerror = function() {
                        console.error('Bild konnte nicht geladen werden.');
                    };
                };
                kategorienListe.appendChild(div);
            });
        })
        .catch(error => console.error('Fehler beim Laden der Kategorien:', error));
});


