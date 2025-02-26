import tkinter as tk
from tkinter import Listbox, messagebox, ttk
from PIL import Image, ImageTk
import os
import sqlite3
import csv
import logging

class BoundingBoxApp:
    def __init__(self, root, img_folder):
        """
        Initialisiert die Bounding Box App.
        
        Args:
            root: Das Tkinter Root-Widget
            img_folder: Pfad zum Ordner mit den Bildern
        """
        self.root = root
        self.img_folder = img_folder
        self.db_path = 'bounding_boxes.db'
        
        # Datenbank-Variablen
        self.conn = None
        self.cursor = None
        
        # Bild-Variablen
        self.photo_img = None
        self.current_image_path = None
        self.current_image_index = 0
        self.current_image_position = None
        self.images = []
        self.image_cache = {}
        
        # Bounding Box-Variablen
        self.start_x, self.start_y = None, None
        self.end_x, self.end_y = None, None
        self.rect_id = None
        self.last_box_id = None
        
        # Kategorie-Variable
        self.current_category = None
        
        # Setup
        self.setup_database()
        self.setup_ui()
        self.setup_logging()
        self.load_categories()
        
        # Event-Binding
        self.setup_event_bindings()
    
    def setup_logging(self):
        """Konfiguriert das Logging für die Anwendung."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='bounding_box_app.log'
        )
        self.logger = logging.getLogger('BoundingBoxApp')
        self.logger.info("Anwendung gestartet")

    def setup_database(self):
        """Initialisiert die Datenbankverbindung und Tabellen."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
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
            self.conn.commit()
            self.logger.info("Datenbankverbindung erfolgreich hergestellt")
        except sqlite3.Error as e:
            self.logger.error(f"Fehler beim Einrichten der Datenbank: {e}")
            messagebox.showerror("Datenbankfehler", f"Fehler beim Einrichten der Datenbank: {e}")
    
    def setup_ui(self):
        """Initialisiert die Benutzeroberfläche der Anwendung."""
        self.root.title("Bounding Box Zeichner")
        self.root.geometry("1200x700")  # Startgröße festlegen
        
        # Erstellt den Hauptrahmen
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Linker Bereich für Kategorien
        left_frame = tk.LabelFrame(main_frame, text="Kategorien")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Listbox für Kategorien
        self.kategorien_listbox = Listbox(left_frame, exportselection=False, width=20)
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=self.kategorien_listbox.yview)
        self.kategorien_listbox.config(yscrollcommand=scrollbar.set)
        self.kategorien_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        # Mittlerer Bereich für Bildanzeige
        center_frame = tk.LabelFrame(main_frame, text="Bildanzeige")
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas für die Bildanzeige
        self.canvas = tk.Canvas(center_frame, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Rechter Bereich für Steuerelemente
        right_frame = tk.LabelFrame(main_frame, text="Steuerung")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Status-Label
        self.status_label = tk.Label(right_frame, text="Bereit", anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Navigation
        nav_frame = tk.Frame(right_frame)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.prev_button = tk.Button(nav_frame, text="Vorheriges Bild", command=self.previous_image)
        self.prev_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        self.next_button = tk.Button(nav_frame, text="Nächstes Bild", command=self.next_image)
        self.next_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # Steuerungsbuttons
        self.erase_button = tk.Button(right_frame, text="Letzte Box löschen", command=self.delete_last_bounding_box)
        self.erase_button.pack(fill=tk.X, padx=5, pady=5)
        
        self.export_button = tk.Button(right_frame, text="Bounding Boxes exportieren", command=self.export_bounding_boxes)
        self.export_button.pack(fill=tk.X, padx=5, pady=5)
        
        self.help_button = tk.Button(right_frame, text="Hilfe", command=self.show_help)
        self.help_button.pack(fill=tk.X, padx=5, pady=5)
        
        # Fortschrittsbalken
        self.progress_label = tk.Label(right_frame, text="Fortschritt:")
        self.progress_label.pack(fill=tk.X, padx=5, pady=(10, 0))
        
        self.progress = ttk.Progressbar(right_frame, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # Status-Bereich
        self.status_frame = tk.LabelFrame(right_frame, text="Status")
        self.status_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_text = tk.Text(self.status_frame, height=5, width=25, wrap=tk.WORD, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_event_bindings(self):
        """Richtet alle Event-Bindings für die Anwendung ein."""
        # Canvas-Events für das Zeichnen von Bounding Boxes
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        
        # Listbox-Events für die Kategorieauswahl
        self.kategorien_listbox.bind('<<ListboxSelect>>', self.on_category_select)
        
        # Tastatur-Shortcuts
        self.root.bind('<Right>', lambda event: self.next_image())
        self.root.bind('<Left>', lambda event: self.previous_image())
        self.root.bind('<Delete>', lambda event: self.delete_last_bounding_box())
    
    def update_status(self, message):
        """Aktualisiert das Status-Text-Widget mit einer neuen Nachricht."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.status_label.config(text=message)
        self.logger.info(message)
    
    def load_categories(self):
        """Lädt die Kategorien aus dem Bilderordner und fügt sie der Listbox hinzu."""
        try:
            # Listet alle Einträge im Bilderordner auf, die Verzeichnisse sind
            categories = [name for name in os.listdir(self.img_folder) 
                         if os.path.isdir(os.path.join(self.img_folder, name))]
            
            # Löscht alte Einträge
            self.kategorien_listbox.delete(0, tk.END)
            
            # Fügt neue Kategorien hinzu
            for category in categories:
                self.kategorien_listbox.insert(tk.END, category)
            
            self.update_status(f"{len(categories)} Kategorien geladen")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Kategorien: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Laden der Kategorien: {e}")
    
    def auto_load_image_from_category(self, category_name):
        """
        Lädt automatisch Bilder aus einer bestimmten Kategorie.
        
        Args:
            category_name: Name der zu ladenden Kategorie
        """
        try:
            categories = self.kategorien_listbox.get(0, tk.END)
            if category_name in categories:
                category_index = categories.index(category_name)
                self.kategorien_listbox.selection_clear(0, tk.END)
                self.kategorien_listbox.selection_set(category_index)
                self.on_category_select(None)  # Simuliere eine Kategorieauswahl
                self.update_status(f"Kategorie '{category_name}' automatisch geladen")
            else:
                self.logger.warning(f"Kategorie '{category_name}' nicht gefunden")
                messagebox.showerror("Fehler", f"Kategorie '{category_name}' nicht gefunden.")
        except Exception as e:
            self.logger.error(f"Fehler beim automatischen Laden der Kategorie: {e}")
            messagebox.showerror("Fehler", f"Fehler beim automatischen Laden: {e}")
    
    def on_category_select(self, event):
        """Wird aufgerufen, wenn eine Kategorie in der Listbox ausgewählt wird."""
        selection = self.kategorien_listbox.curselection()
        if selection:
            self.current_category = self.kategorien_listbox.get(selection[0])
            self.load_images()
            self.update_status(f"Kategorie '{self.current_category}' ausgewählt")
    
    def load_images(self):
        """Lädt alle Bildpfade der ausgewählten Kategorie."""
        if not self.current_category:
            self.update_status("Keine Kategorie ausgewählt")
            return
        
        try:
            # Erstellt den Pfad zum Verzeichnis der ausgewählten Kategorie
            category_path = os.path.join(self.img_folder, self.current_category)
            
            # Sammelt alle Bildpfade in diesem Verzeichnis
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            self.images = [
                os.path.join(category_path, img) 
                for img in os.listdir(category_path) 
                if os.path.isfile(os.path.join(category_path, img)) and
                any(img.lower().endswith(ext) for ext in allowed_extensions)
            ]
            
            # Setzt den Index des aktuellen Bildes zurück
            self.current_image_index = 0
            
            if self.images:
                # Aktualisiert den Fortschrittsbalken
                self.progress["maximum"] = len(self.images)
                self.progress["value"] = 0
                
                # Lädt das erste Bild
                self.load_and_display_image(self.images[0])
                self.update_status(f"{len(self.images)} Bilder in Kategorie '{self.current_category}' gefunden")
            else:
                self.reset_canvas()
                self.update_status(f"Keine Bilder in Kategorie '{self.current_category}' gefunden")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Bilder: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Laden der Bilder: {e}")
    
    def load_image(self, image_path):
        """
        Lädt ein Bild aus dem Dateisystem oder Cache.
        
        Args:
            image_path: Pfad zum Bild
            
        Returns:
            PhotoImage-Objekt oder None bei Fehler
        """
        # Prüft, ob das Bild bereits im Cache ist
        if image_path in self.image_cache:
            return self.image_cache[image_path]
        
        try:
            img = Image.open(image_path)
            # Behält das Seitenverhältnis bei, wenn das Bild verkleinert wird
            canvas_width = self.canvas.winfo_width() or 800
            canvas_height = self.canvas.winfo_height() or 600
            
            # Berechnet die maximale Größe für das Bild
            img_width, img_height = img.size
            ratio = min(canvas_width / img_width, canvas_height / img_height)
            new_width = int(img_width * ratio * 0.9)  # 90% der verfügbaren Breite
            new_height = int(img_height * ratio * 0.9)  # 90% der verfügbaren Höhe
            
            if ratio < 1:  # Nur verkleinern, nicht vergrößern
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            photo_img = ImageTk.PhotoImage(img)
            self.image_cache[image_path] = photo_img
            return photo_img
        except Exception as e:
            self.logger.error(f"Fehler beim Laden des Bildes '{image_path}': {e}")
            return None
    
    def load_and_display_image(self, image_path):
        """
        Lädt ein Bild und zeigt es auf dem Canvas an.
        
        Args:
            image_path: Pfad zum Bild
        """
        self.reset_canvas()
        
        try:
            self.photo_img = self.load_image(image_path)
            if not self.photo_img:
                self.update_status(f"Fehler beim Laden des Bildes: {image_path}")
                return
            
            # Berechnet die Position, um das Bild zentriert anzuzeigen
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img_width = self.photo_img.width()
            img_height = self.photo_img.height()
            x_position = max(0, (canvas_width - img_width) // 2)
            y_position = max(0, (canvas_height - img_height) // 2)
            
            # Zeigt das Bild an
            image_item = self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=self.photo_img)
            
            # Speichert die aktuelle Bildposition und Pfad
            self.current_image_position = (x_position, y_position, img_width, img_height)
            self.current_image_path = image_path
            
            # Lädt vorhandene Bounding Boxes, falls vorhanden
            self.load_existing_bounding_boxes()
            
            # Aktualisiert den Fortschrittsbalken
            self.progress["value"] = self.current_image_index + 1
            
            # Aktualisiert den Status
            image_id = self.get_image_id_from_path(image_path)
            self.update_status(f"Bild geladen: {image_id} ({self.current_image_index + 1}/{len(self.images)})")
            
            # Zeichnet die Bildgrenzen für visuelle Orientierung
            self.draw_image_boundaries()
        except Exception as e:
            self.logger.error(f"Fehler beim Anzeigen des Bildes: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Anzeigen des Bildes: {e}")
    
    def reset_canvas(self):
        """Setzt den Canvas zurück und löscht alle Zeichnungen."""
        self.canvas.delete("all")
        self.rect_id = None
    
    def draw_image_boundaries(self):
        """Zeichnet Linien um die Grenzen des Bildes auf dem Canvas."""
        if not self.current_image_position:
            return
        
        x_position, y_position, img_width, img_height = self.current_image_position
        
        # Zeichnet einen dünnen Rahmen um das Bild
        self.canvas.create_rectangle(
            x_position - 1, y_position - 1, 
            x_position + img_width + 1, y_position + img_height + 1,
            outline="gray", width=1, tags="boundary"
        )
    
    def on_canvas_click(self, event):
        """Handler für Mausklick auf dem Canvas."""
        if not self.current_image_position:
            return
        
        x_position, y_position, img_width, img_height = self.current_image_position
        
        # Prüft, ob der Klick innerhalb des Bildbereichs liegt
        if (x_position <= event.x <= x_position + img_width and 
            y_position <= event.y <= y_position + img_height):
            
            self.start_x, self.start_y = event.x, event.y
            
            # Erstellt ein neues Rechteck mit Start- und Endpunkt am selben Ort
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, 
                self.start_x, self.start_y,
                outline="red", width=2, tags="bbox"
            )
    
    def on_canvas_drag(self, event):
        """Handler für Mausbewegung mit gedrückter Taste auf dem Canvas."""
        if not self.rect_id or not self.current_image_position:
            return
        
        x_position, y_position, img_width, img_height = self.current_image_position
        
        # Begrenzt die Mausposition auf den Bildbereich
        event_x = max(x_position, min(event.x, x_position + img_width))
        event_y = max(y_position, min(event.y, y_position + img_height))
        
        # Aktualisiert das Rechteck
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event_x, event_y)
    
    def on_canvas_release(self, event):
        """Handler für Loslassen der Maustaste auf dem Canvas."""
        if not self.rect_id or not self.current_image_position or not self.current_image_path:
            return
        
        x_position, y_position, img_width, img_height = self.current_image_position
        
        # Speichert die Endposition
        self.end_x = max(x_position, min(event.x, x_position + img_width))
        self.end_y = max(y_position, min(event.y, y_position + img_height))
        
        # Berechnet die Koordinaten relativ zum Bild
        box_x1 = self.start_x - x_position
        box_y1 = self.start_y - y_position
        box_x2 = self.end_x - x_position
        box_y2 = self.end_y - y_position
        
        # Stellt sicher, dass x1 < x2 und y1 < y2
        if box_x1 > box_x2:
            box_x1, box_x2 = box_x2, box_x1
        if box_y1 > box_y2:
            box_y1, box_y2 = box_y2, box_y1
        
        # Prüft, ob die Box eine Mindestgröße hat
        min_size = 5
        if (box_x2 - box_x1 > min_size and box_y2 - box_y1 > min_size):
            # Speichert die Bounding Box
            image_id = self.get_image_id_from_path(self.current_image_path)
            category = self.get_category_from_path(self.current_image_path)
            self.save_bounding_box(image_id, category, (box_x1, box_y1, box_x2, box_y2))
        else:
            # Löscht das zu kleine Rechteck
            self.canvas.delete(self.rect_id)
            self.update_status("Bounding Box zu klein - verworfen")
        
        # Setzt das Rechteck-ID zurück
        self.rect_id = None
    
    def load_existing_bounding_boxes(self):
        """Lädt vorhandene Bounding Boxes für das aktuelle Bild aus der Datenbank."""
        if not self.current_image_path or not self.current_image_position:
            return
        
        image_id = self.get_image_id_from_path(self.current_image_path)
        category = self.get_category_from_path(self.current_image_path)
        
        try:
            self.cursor.execute(
                "SELECT id, x1, y1, x2, y2 FROM boxes WHERE image_id = ? AND category = ?", 
                (image_id, category)
            )
            boxes = self.cursor.fetchall()
            
            x_position, y_position, _, _ = self.current_image_position
            
            for box_id, x1, y1, x2, y2 in boxes:
                # Zeichnet die Bounding Box auf dem Canvas
                display_x1 = x1 + x_position
                display_y1 = y1 + y_position
                display_x2 = x2 + x_position
                display_y2 = y2 + y_position
                
                self.canvas.create_rectangle(
                    display_x1, display_y1, display_x2, display_y2,
                    outline="green", width=2, tags=f"box_{box_id}"
                )
                
                # Speichert die ID der letzten Box
                self.last_box_id = box_id
        except sqlite3.Error as e:
            self.logger.error(f"Fehler beim Laden vorhandener Bounding Boxes: {e}")
    
    def save_bounding_box(self, image_id, category, bbox):
        """
        Speichert eine Bounding Box in der Datenbank.
        
        Args:
            image_id: ID des Bildes
            category: Kategorie des Bildes
            bbox: Tuple mit (x1, y1, x2, y2) Koordinaten
        """
        try:
            # Prüft, ob bereits ein Eintrag existiert
            self.cursor.execute(
                "SELECT id FROM boxes WHERE image_id = ? AND category = ?", 
                (image_id, category)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                # Aktualisiert den vorhandenen Eintrag
                box_id = existing[0]
                self.cursor.execute(
                    "UPDATE boxes SET x1 = ?, y1 = ?, x2 = ?, y2 = ? WHERE id = ?",
                    (*bbox, box_id)
                )
                message = "Bounding Box aktualisiert"
            else:
                # Fügt einen neuen Eintrag hinzu
                self.cursor.execute(
                    "INSERT INTO boxes (image_id, category, x1, y1, x2, y2) VALUES (?, ?, ?, ?, ?, ?)",
                    (image_id, category, *bbox)
                )
                box_id = self.cursor.lastrowid
                message = "Neue Bounding Box gespeichert"
            
            self.conn.commit()
            self.last_box_id = box_id
            self.update_status(message)
            
            # Zeigt die gespeicherte Box visuell an
            x_position, y_position, _, _ = self.current_image_position
            x1, y1, x2, y2 = bbox
            
            # Zeichnet die gespeicherte Box in einer anderen Farbe
            self.canvas.create_rectangle(
                x1 + x_position, y1 + y_position, 
                x2 + x_position, y2 + y_position,
                outline="green", width=2, tags=f"box_{box_id}"
            )
            
            return box_id
        except sqlite3.Error as e:
            self.logger.error(f"Fehler beim Speichern der Bounding Box: {e}")
            messagebox.showerror("Datenbankfehler", f"Fehler beim Speichern: {e}")
            return None
    
    def delete_last_bounding_box(self):
        """Löscht die zuletzt gezeichnete Bounding Box."""
        if not self.last_box_id:
            self.update_status("Keine Bounding Box zum Löschen vorhanden")
            return
        
        try:
            # Löscht die Box aus der Datenbank
            self.cursor.execute("DELETE FROM boxes WHERE id = ?", (self.last_box_id,))
            self.conn.commit()
            
            # Löscht die Box visuell vom Canvas
            self.canvas.delete(f"box_{self.last_box_id}")
            
            self.update_status(f"Bounding Box mit ID {self.last_box_id} gelöscht")
            
            # Setzt die letzte Box ID zurück
            self.last_box_id = None
            
            # Lädt die vorherige Box (falls vorhanden) als neue "letzte" Box
            if self.current_image_path:
                image_id = self.get_image_id_from_path(self.current_image_path)
                category = self.get_category_from_path(self.current_image_path)
                
                self.cursor.execute(
                    "SELECT id FROM boxes WHERE image_id = ? AND category = ? ORDER BY id DESC LIMIT 1",
                    (image_id, category)
                )
                last_box = self.cursor.fetchone()
                
                if last_box:
                    self.last_box_id = last_box[0]
        except sqlite3.Error as e:
            self.logger.error(f"Fehler beim Löschen der Bounding Box: {e}")
            messagebox.showerror("Datenbankfehler", f"Fehler beim Löschen: {e}")
    
    def next_image(self):
        """Wechselt zum nächsten Bild in der Kategorie."""
        if not self.images:
            self.update_status("Keine Bilder geladen")
            return
        
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.load_and_display_image(self.images[self.current_image_index])
        else:
            self.update_status("Letztes Bild erreicht. Wechsle zur nächsten Kategorie?")
            if messagebox.askyesno("Navigationshinweis", 
                                   "Sie haben das letzte Bild in dieser Kategorie erreicht. " 
                                   "Möchten Sie zur nächsten Kategorie wechseln?"):
                self.switch_to_next_category()
    
    def previous_image(self):
        """Wechselt zum vorherigen Bild in der Kategorie."""
        if not self.images:
            self.update_status("Keine Bilder geladen")
            return
        
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_and_display_image(self.images[self.current_image_index])
        else:
            self.update_status("Erstes Bild der Kategorie erreicht")
    
    def switch_to_next_category(self):
        """Wechselt zur nächsten Kategorie in der Listbox."""
        current_index = self.kategorien_listbox.curselection()
        
        if current_index:
            current_index = current_index[0]
            next_index = (current_index + 1) % self.kategorien_listbox.size()
            
            self.kategorien_listbox.selection_clear(0, tk.END)
            self.kategorien_listbox.selection_set(next_index)
            self.kategorien_listbox.see(next_index)
            self.on_category_select(None)
            
            self.update_status(f"Gewechselt zur Kategorie: {self.current_category}")
        else:
            self.update_status("Keine Kategorie ausgewählt")
    
    def get_image_id_from_path(self, image_path):
        """Extrahiert die Bild-ID aus dem Pfad."""
        return os.path.splitext(os.path.basename(image_path))[0]
    
    def get_category_from_path(self, image_path):
        """Extrahiert die Kategorie aus dem Pfad."""
        return os.path.basename(os.path.dirname(image_path))
    
    def is_image_processed(self, image_id, category):
        """Prüft, ob ein Bild bereits Bounding Boxes hat."""
        self.cursor.execute(
            "SELECT 1 FROM boxes WHERE image_id = ? AND category = ?", 
            (image_id, category)
        )
        return self.cursor.fetchone() is not None
    
    def export_bounding_boxes(self):
        """Exportiert alle Bounding Boxes der aktuellen Kategorie in eine CSV-Datei."""
        if not self.current_category:
            self.update_status("Keine Kategorie ausgewählt")
            return
        
        try:
            filename = f"{self.current_category}_bounding_boxes.csv"
            
            # Holt alle Boxen der Kategorie
            self.cursor.execute(
                "SELECT image_id, category, x1, y1, x2, y2 FROM boxes WHERE category = ?", 
                (self.current_category,)
            )
            boxes = self.cursor.fetchall()
            
            if not boxes:
                self.update_status(f"Keine Bounding Boxes in Kategorie '{self.current_category}' zum Exportieren")
                messagebox.showinfo("Export", "Keine Daten zum Exportieren vorhanden.")
                return
            
            # Schreibt die Daten in die CSV-Datei
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Image ID', 'Kategorie', 'X1', 'Y1', 'X2', 'Y2'])
                writer.writerows(boxes)
            
            self.update_status(f"Bounding Boxes nach '{filename}' exportiert")
            messagebox.showinfo("Export erfolgreich", f"Bounding Boxes wurden in '{filename}' exportiert.")
        except Exception as e:
            self.logger.error(f"Fehler beim Exportieren: {e}")
            messagebox.showerror("Exportfehler", f"Fehler beim Exportieren: {e}")
    
    def show_help(self):
        """Zeigt ein Hilfefenster mit Anweisungen an."""
        help_window = tk.Toplevel(self.root)
        help_window.title("Bounding Box App - Hilfe")
        help_window.geometry("600x400")
        
        help_text = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        help_text.pack(fill=tk.BOTH, expand=True)
        
        # Fügt Hilfetext hinzu
        help_content = """
Bounding Box App - Benutzerhandbuch

Übersicht:
Diese Anwendung ermöglicht es Ihnen, Bounding Boxes um Objekte in Bildern zu zeichnen und die Daten zu exportieren.

Verwendung:
1. Wählen Sie eine Kategorie aus der Liste auf der linken Seite.
2. Das erste Bild der Kategorie wird automatisch geladen.
3. Zeichnen Sie eine Bounding Box, indem Sie mit der Maus auf dem Bild ziehen.
4. Navigieren Sie mit den Buttons oder Pfeiltasten zwischen den Bildern.

Tastaturbefehle:
- Rechte Pfeiltaste: Nächstes Bild
- Linke Pfeiltaste: Vorheriges Bild
- Entf-Taste: Letzte Bounding Box löschen

Tipps:
- Die Bounding Box wird automatisch gespeichert, sobald Sie die Maustaste loslassen.
- Grün umrandete Boxen sind bereits gespeicherte Bounding Boxes.
- Exportieren Sie Ihre Arbeit regelmäßig mit dem "Exportieren"-Button.

Bei Problemen oder Fragen wenden Sie sich bitte an den Support.
"""
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)
        
        # Schließen-Button
        close_button = tk.Button(help_window, text="Schließen", command=help_window.destroy)
        close_button.pack(pady=10)

def find_image_folder(folder_name="img", root_folder='./'):
    """
    Sucht nach dem Bildordner im aktuellen Verzeichnis oder in Unterverzeichnissen.
    
    Args:
        folder_name: Name des gesuchten Ordners
        root_folder: Startverzeichnis für die Suche
        
    Returns:
        Pfad zum gefundenen Ordner oder None, wenn nicht gefunden
    """
    # Prüft, ob der Ordner direkt im Startverzeichnis existiert
    direct_path = os.path.join(root_folder, folder_name)
    if os.path.isdir(direct_path):
        return direct_path
    
    # Durchsucht alle Unterverzeichnisse
    for root, dirs, files in os.walk(root_folder):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
    
    return None

def main():
    """Hauptfunktion zum Starten der Anwendung."""
    root = tk.Tk()
    
    # Sucht den Bildordner
    img_folder = find_image_folder()
    
    if not img_folder:
        messagebox.showerror("Fehler", "Bildordner 'img' nicht gefunden.")
        return
    
    app = BoundingBoxApp(root, img_folder)
    
    # Setzt die minimale Größe des Fensters
    root.update()
    root.minsize(root.winfo_width(), root.winfo_height())
    
    root.mainloop()

if __name__ == "__main__":
    main()
