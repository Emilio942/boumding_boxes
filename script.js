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
                kategorienListe.appendChild(div);
            });
        })
        .catch(error => console.error('Fehler beim Laden der Kategorien:', error));
});

