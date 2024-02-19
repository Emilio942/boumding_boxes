document.addEventListener('DOMContentLoaded', function() {
    kategorienLaden();
});

function kategorienLaden() {
    fetch('/api/kategorien')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('kategorieContainer');
            container.innerHTML = '';
            data.forEach(kategorie => {
                const div = document.createElement('div');
                div.textContent = kategorie;
                container.appendChild(div);
            });
        })
        .catch(error => console.error('Fehler beim Laden der Kategorien:', error));
}
