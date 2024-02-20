import tkinter as tk
from tkinter import filedialog, Listbox, messagebox
from PIL import Image, ImageTk
import os
import json
import sqlite3 
# Datenbank-Setup
# Initialisierung der SQLite-Datenbank für die Speicherung der Bounding Boxes
db_path = 'bounding_boxes.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
# Erstellen der Tabelle 'boxes', wenn sie nicht existiert. Jede Box wird eindeutig durch ihre Image-ID und Kategorie identifiziert.
cursor.execute('''
    CREATE TABLE IF NOT EXISTS boxes (
    id INTEGER PRIMARY KEY,
    image_id TEXT NOT NULL,
    category TEXT NOT NULL,
    x1 INTEGER NOT NULL,
    y1 INTEGER NOT NULL,
    x2 INTEGER NOT NULL,
    y2 INTEGER NOT NULL,
    UNIQUE(image_id, category)
)
''')
conn.commit()

class BoundingBoxApp:
    # Initialisiert die Hauptkomponenten der Anwendung.
    def __init__(self, root, img_folder):
        self.root = root  # Das Hauptfenster der Anwendung
        self.img_folder = img_folder  # Der Pfad zum Ordner, der die Bilder enthält
        
        self.root.title("Bounding Box Zeichner")  # Setzt den Titel des Fensters

        # Erstellt eine Listbox für die Anzeige der Kategorien und fügt sie dem Hauptfenster hinzu.
        self.kategorien_listbox = Listbox(self.root)
        self.kategorien_listbox.pack(side=tk.LEFT, fill=tk.Y)

        # Initialisiert und zeigt das Zeichenfeld (Canvas) an.
        self.canvas = tk.Canvas(root, width=800, height=600, bg='white')
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Bindet Mausereignisse an Funktionen für das Zeichnen der Bounding Boxes.
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)

        # Variablen für die aktuelle Zeichnung.
        self.start_x, self.start_y, self.rect_id = None, None, None
        
        self.load_categories()  # Lädt die Kategorien aus den Bildordnern.

    # Lädt die Bildkategorien aus den Ordnernamen und fügt sie der Listbox hinzu.
    def load_categories(self):
        try:
            categories = [name for name in os.listdir(self.img_folder) if os.path.isdir(os.path.join(self.img_folder, name))]
            for category in categories:
                self.kategorien_listbox.insert(tk.END, category)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Startet das Zeichnen einer Bounding Box beim Klicken auf das Canvas.
    def on_canvas_click(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

     # Aktualisiert die Größe der Bounding Box beim Bewegen der Maus mit gedrückter Taste.
    def on_canvas_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def save_bounding_box(self, image_id, category, bbox):
        try:
            cursor.execute('''
                INSERT INTO boxes (image_id, category, x1, y1, x2, y2)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (image_id, category, bbox[0], bbox[1], bbox[2], bbox[3]))
            conn.commit()
        except sqlite3.IntegrityError:
            print(f"Eintrag für Image-ID {image_id} in Kategorie {category} existiert bereits.")
    # Beendet das Zeichnen der Bounding Box und speichert sie, wenn die Maustaste losgelassen wird.
    
   

    def get_image_id_from_path(image_path):
        """
            Extrahiert die Image-ID aus dem vollständigen Pfad des Bildes.
            Annahme: Die Image-ID ist der Dateiname ohne Erweiterung.
        """
        return os.path.basename(image_path).split('.')[0]
    def get_category_from_path(image_path):
        """
            Extrahiert den Kategorienamen aus dem vollständigen Pfad des Bildes.
            Annahme: Die Kategorie ist der Name des übergeordneten Verzeichnisses des Bildes.
        """
        return os.path.basename(os.path.dirname(image_path))

    def on_canvas_release(self, event):
        end_x, end_y = event.x, event.y
        if self.rect_id:
            bbox = (self.start_x, self.start_y, end_x, end_y)
            
            if hasattr(self, 'selected_image_path') and self.selected_image_path:
                image_id = get_image_id_from_path(self.selected_image_path)
                category = get_category_from_path(self.selected_image_path)
                self.save_bounding_box(image_id=image_id, category=category, bbox=bbox)
            else:
                messagebox.showinfo("Info", "Kein Bild ausgewählt.")
            
            self.rect_id = None

    def process_images_in_category(self):
        # Annahme: Die ausgewählte Kategorie wird aus der Listbox geholt
        selected_category_index = self.kategorien_listbox.curselection()
        if not selected_category_index:
            messagebox.showinfo("Info", "Bitte wählen Sie eine Kategorie aus.")
            return
        selected_category = self.kategorien_listbox.get(selected_category_index[0])

        # Liste aller Bildpfade in der ausgewählten Kategorie
        image_paths = [os.path.join(self.img_folder, selected_category, f) for f in os.listdir(os.path.join(self.img_folder, selected_category)) if os.path.isfile(os.path.join(self.img_folder, selected_category, f))]

        # Berechnung von 20% der Bilder
        total_images = len(image_paths)
        validation_set_size = int(total_images * 0.2)

        # Zufällige Auswahl von Bildern für die Verarbeitung
        selected_images = random.sample(image_paths, validation_set_size)

        # Verarbeitung der ausgewählten Bilder
        for image_path in selected_images:
            image_id = os.path.basename(image_path).split('.')[0]
            if not self.is_image_processed(image_id, selected_category):
                self.process_image(image_path, selected_category)

        # Automatisches Wechseln zur nächsten Kategorie, falls implementiert
        self.switch_to_next_category()

    def switch_to_next_category(self):
        # Logik zum Wechseln zur nächsten Kategorie
        current_index = self.kategorien_listbox.curselection()[0]
        next_index = current_index + 1 if current_index < self.kategorien_listbox.size() - 1 else 0
        self.kategorien_listbox.selection_clear(current_index)
        self.kategorien_listbox.selection_set(next_index)
        self.kategorien_listbox.event_generate("<<ListboxSelect>>")
    
    def is_image_processed(self, image_id, category):
        # Überprüfung, ob das Bild bereits verarbeitet wurde
        cursor.execute("SELECT 1 FROM boxes WHERE image_id = ? AND category = ?", (image_id, category))
        return cursor.fetchone() is not None




 



if __name__ == "__main__":
    root = tk.Tk()
    img_folder = "./img"  # Anpassen an deinen Pfad
    app = BoundingBoxApp(root, img_folder)
    root.mainloop()
# Vergiss nicht, die Verbindung zu schließen, wenn du fertig bist
conn.close()