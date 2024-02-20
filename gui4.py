import tkinter as tk
from tkinter import Listbox, messagebox
from PIL import Image, ImageTk
import os
import sqlite3
import random
import csv

class BoundingBoxApp:
    def __init__(self, root, img_folder):
        self.root = root
        self.img_folder = img_folder
        self.db_path = 'bounding_boxes.db'
        self.conn = None
        self.cursor = None
        self.photo_img = None
        self.start_x, self.start_y = None, None
        self.rect_id = None
        self.current_image_index = 0
        self.current_image_path = None
        self.images = []
        self.image_cache = {}
        self.setup_database()
        self.setup_ui()
        self.load_categories()

    def setup_database(self):
        """Initialisiert die Datenbankverbindung und Tabellen."""
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
    
    
    def setup_ui(self):
        """Initialisiert die Benutzeroberfläche der Anwendung."""
        self.root.title("Bounding Box Zeichner")

        # Erstellt einen Rahmen für die Listbox und die Scrollbar.
        self.frame_listbox = tk.Frame(self.root)
        self.frame_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Listbox für Kategorien.
        self.kategorien_listbox = Listbox(self.frame_listbox, exportselection=False)
        self.scrollbar = tk.Scrollbar(self.frame_listbox, orient="vertical", command=self.kategorien_listbox.yview)
        self.kategorien_listbox.config(yscrollcommand=self.scrollbar.set)
        self.kategorien_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill="y")

        # Canvas für die Bildanzeige.
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg='white')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        # self.canvas.bind('<Button-1>', self.on_canvas_click)
        # self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)

        # Rahmen für die Steuerungsbuttons.
        self.frame_buttons = tk.Frame(self.root)
        self.frame_buttons.pack(side=tk.LEFT, fill=tk.BOTH, padx=5, pady=5)

        # Steuerungsbuttons hinzufügen.
        self.export_button = tk.Button(self.frame_buttons, text="Bounding Boxes exportieren", command=self.export_bounding_boxes)
        self.export_button.pack(fill=tk.X, padx=5, pady=5)
        self.erase_button = tk.Button(self.frame_buttons, text="Radierer", command=self.delete_last_bounding_box)
        self.erase_button.pack(fill=tk.X, padx=5, pady=5)
        self.help_button = tk.Button(self.frame_buttons, text="Hilfe", command=self.show_help)
        self.help_button.pack(fill=tk.X, padx=5, pady=5)

        # Optional: Weitere UI-Elemente wie Fortschrittsbalken und Bildervorschau-Button können hier hinzugefügt werden.
        
        # Erstellt einen Fortschrittsbalken und fügt ihn zum Frame für die Buttons hinzu.
        self.progress = tk.Progressbar(self.frame_buttons, orient="horizontal", length=200, mode="determinate")
        self.progress.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.preview_button = tk.Button(self.frame_buttons, text="Bildervorschau", command=self.show_image_previews)
        self.preview_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    def load_categories(self):
        """
        Diese Methode lädt die Kategorienamen aus dem Bilderordner und fügt sie der Listbox hinzu.
        Jeder Unterordner im Bilderordner stellt eine Kategorie dar.
        """
        try:
            # Listet alle Einträge im Bilderordner auf, die Verzeichnisse sind (also Kategorien).
            categories = [name for name in os.listdir(self.img_folder) if os.path.isdir(os.path.join(self.img_folder, name))]

            # Fügt jeden Kategorienamen der Listbox hinzu.
            for category in categories:
                self.kategorien_listbox.insert(tk.END, category)
        except Exception as e:
            # Falls ein Fehler auftritt (z.B. das Verzeichnis existiert nicht), wird eine Fehlermeldung angezeigt.
            messagebox.showerror("Error", str(e))

    def on_canvas_release(self, event):
        """
        Wird aufgerufen, wenn der Benutzer die Maustaste loslässt, nachdem er eine Bounding Box gezeichnet hat.
        Speichert die Bounding Box-Daten relativ zum Bild.
        """
        # Sicherstellen, dass eine Bounding Box existiert und ein Bild ausgewählt wurde.
        if self.rect_id and self.current_image_path:
            self.end_x, self.end_y = event.x, event.y
            if self.current_image_position:
                x_position, y_position, img_width, img_height = self.current_image_position
                
                # Berechnen der Koordinaten relativ zum Bild.
                box_x1 = self.start_x - x_position
                box_y1 = self.start_y - y_position
                box_x2 = self.end_x - x_position
                box_y2 = self.end_y - y_position
                
                # Stelle sicher, dass die Koordinaten innerhalb der Bildgrenzen liegen.
                box_x1, box_y1, box_x2, box_y2 = self.clamp_coordinates(box_x1, box_y1, box_x2, box_y2, img_width, img_height)

                # Speichern der angepassten Bounding Box-Daten.
                self.save_bounding_box(self.get_image_id_from_path(self.current_image_path), self.get_category_from_path(self.current_image_path), (box_x1, box_y1, box_x2, box_y2))
                
                # Zurücksetzen der rect_id für die nächste Bounding Box.
                self.rect_id = None

    def clamp_coordinates(self, x1, y1, x2, y2, img_width, img_height):
        """
        Stellt sicher, dass die Koordinaten innerhalb der Grenzen des Bildes liegen.
        """
        x1 = max(0, min(x1, img_width))
        y1 = max(0, min(y1, img_height))
        x2 = max(0, min(x2, img_width))
        y2 = max(0, min(y2, img_height))
        return x1, y1, x2, y2

    # def load_and_display_image(self, image_path):
    #     """
    #     Lädt ein Bild von einem gegebenen Pfad und zeigt es auf dem Canvas an.
        
    #     Parameter:
    #     image_path (str): Der Pfad zum Bild, das geladen und angezeigt werden soll.
        
    #     Diese Methode kapselt zwei Aufgaben: das Laden des Bildes und seine Anzeige.
    #     Das ermöglicht es, diese Aufgaben an verschiedenen Stellen im Code wiederverwendbar zu machen,
    #     ohne redundanten Code zu haben.
    #     """
    #     # Nachdem das Bild auf dem Canvas angezeigt wurde...
    #     self.draw_image_boundaries()
    #     # Versucht, das Bild vom angegebenen Pfad zu laden.
    #     self.photo_img = self.load_image(image_path)
        
    #     # Überprüft, ob das Laden erfolgreich war (self.photo_img ist nicht None).
    #     if self.photo_img:
    #         # Zeigt das geladene Bild auf dem Canvas an.
    #         self.display_image()
    #     else:
    #         # Falls das Bild nicht geladen werden konnte, wird eine Fehlermeldung angezeigt.
    #         messagebox.showerror("Fehler", "Das Bild konnte nicht geladen werden.")
    def load_and_display_image(self, image_path):
        """
        Lädt ein Bild von einem gegebenen Pfad und zeigt es auf dem Canvas an.
        
        Parameter:
        image_path (str): Der Pfad zum Bild, das geladen und angezeigt werden soll.
        
        Diese Methode kapselt zwei Aufgaben: das Laden des Bildes und seine Anzeige.
        Das ermöglicht es, diese Aufgaben an verschiedenen Stellen im Code wiederverwendbar zu machen,
        ohne redundanten Code zu haben.
        """
        try:
            # Lädt das Bild vom angegebenen Pfad.
            self.photo_img = self.load_image(image_path)
            
            # Überprüft, ob das Laden erfolgreich war (self.photo_img ist nicht None).
            if self.photo_img:
                # Bereinigt den Canvas vor dem Anzeigen eines neuen Bildes.
                self.canvas.delete("all")
                
                # Berechnet die Position, um das Bild zentriert auf dem Canvas anzuzeigen.
                img_width = self.photo_img.width()
                img_height = self.photo_img.height()
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                x_position = (canvas_width - img_width) // 2
                y_position = (canvas_height - img_height) // 2
                
                # Zeigt das geladene Bild auf dem Canvas an.
                self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=self.photo_img)
                
                # Speichert die aktuelle Bildposition und -größe für spätere Verwendung.
                self.current_image_position = (x_position, y_position, img_width, img_height)
                
                # Zeichnet die Bildgrenzen.
                self.draw_image_boundaries()
            else:
                # Falls das Bild nicht geladen werden konnte, wird eine Fehlermeldung angezeigt.
                messagebox.showerror("Fehler", "Das Bild konnte nicht geladen werden.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Das Bild konnte nicht geladen werden: {e}")


    
    def save_bounding_box(self, image_id, category, bbox):
        """
        Speichert die Details einer gezeichneten Bounding Box in der Datenbank.

        Parameter:
        image_id (str): Die ID des Bildes, für das die Bounding Box gezeichnet wurde.
        category (str): Die Kategorie des Bildes.
        bbox (tuple): Ein Tupel, das die Koordinaten der Bounding Box enthält (x1, y1, x2, y2).

        Diese Methode versucht, die Bounding Box-Daten in der Datenbank zu speichern.
        Falls ein Eintrag mit der gleichen Image-ID und Kategorie bereits existiert,
        wird ein Fehler erzeugt, um doppelte Einträge zu verhindern.
        """
        try:
            # Führt das SQL-Insert-Statement aus, um die Bounding Box-Daten in der Datenbank zu speichern.
            self.cursor.execute('''
                INSERT INTO boxes (image_id, category, x1, y1, x2, y2)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (image_id, category, *bbox))
            self.conn.commit()  # Bestätigt die Transaktion, um die Änderungen zu speichern.
        except sqlite3.IntegrityError:
            # Bei einem IntegrityError (z.B. wegen eines doppelten Eintrags) wird eine Fehlermeldung angezeigt.
            messagebox.showerror("Fehler", f"Eintrag für Image-ID {image_id} in Kategorie {category} existiert bereits.")

    def is_image_processed(self, image_id, category):
        """
        Überprüft, ob ein Bild bereits verarbeitet wurde, indem nach einem Eintrag in der Datenbank gesucht wird.

        Parameter:
        image_id (str): Die ID des Bildes, die normalerweise der Dateiname ist.
        category (str): Die Kategorie des Bildes.

        Rückgabe:
        bool: True, wenn das Bild bereits verarbeitet wurde, sonst False.

        Diese Methode führt eine SQL-Abfrage aus, um festzustellen, ob bereits ein Eintrag mit der gegebenen
        Image-ID und Kategorie in der Datenbank existiert. Dies hilft, Duplikate zu vermeiden und
        sicherzustellen, dass jedes Bild nur einmal verarbeitet wird.
        """
        self.cursor.execute("SELECT 1 FROM boxes WHERE image_id = ? AND category = ?", (image_id, category))
        result = self.cursor.fetchone()  # Holt das Ergebnis der Abfrage.
        return result is not None  # Gibt True zurück, wenn ein Ergebnis gefunden wurde, sonst False.


    def switch_to_next_category(self):
        """
        Wechselt automatisch zur nächsten Kategorie in der Listbox nach der Verarbeitung der aktuellen Kategorie.

        Diese Methode erhöht den Index der aktuell ausgewählten Kategorie um eins, um zur nächsten Kategorie zu wechseln.
        Wenn die aktuelle Kategorie die letzte in der Listbox ist, wird zum ersten Eintrag zurückgekehrt, um einen zyklischen Durchlauf zu ermöglichen.
        """
        current_index = self.kategorien_listbox.curselection()  # Aktuell ausgewählter Index in der Listbox.

        if current_index:  # Prüft, ob eine Auswahl existiert.
            current_index = current_index[0]  # curselection() gibt ein Tupel zurück, daher extrahieren wir den Index.
            next_index = (current_index + 1) % self.kategorien_listbox.size()  # Berechnet den nächsten Index.
            
            self.kategorien_listbox.selection_clear(current_index)  # Entfernt die aktuelle Auswahl.
            self.kategorien_listbox.selection_set(next_index)  # Setzt die Auswahl auf den nächsten Index.
            self.kategorien_listbox.event_generate('<<ListboxSelect>>')  # Löst das ListboxSelect Ereignis aus.

            # Lädt die Bilder der nächsten Kategorie.
            self.on_category_select(None)  # Ein None-Event wird übergeben, da wir nur die Funktionalität benötigen.
        else:
            messagebox.showinfo("Info", "Bitte wählen Sie eine Kategorie aus.")



    def get_image_id_from_path(self, image_path):
        """
        Extrahiert die Image-ID aus dem vollständigen Pfad des Bildes.

        Die Image-ID wird hier als der Dateiname des Bildes ohne dessen Erweiterung verstanden.
        Diese ID kann verwendet werden, um Bilder eindeutig zu identifizieren, z.B. beim Speichern von Bounding Box-Daten.

        Parameter:
        image_path (str): Der vollständige Pfad zum Bild, von dem die ID extrahiert werden soll.

        Rückgabe:
        str: Die extrahierte Image-ID.
        """
        # os.path.basename extrahiert den Dateinamen aus dem vollständigen Pfad.
        # os.path.splitext teilt den Dateinamen in den Namen und die Erweiterung und gibt den Namen zurück.
        return os.path.splitext(os.path.basename(image_path))[0]

    def get_category_from_path(self, image_path):
        """
        Extrahiert den Kategorienamen aus dem vollständigen Pfad des Bildes.

        Dies ist nützlich, um die Zugehörigkeit eines Bildes zu einer bestimmten Kategorie zu bestimmen,
        basierend auf der Verzeichnisstruktur, in der das Bild gespeichert ist. Die Kategorie entspricht dem Namen
        des übergeordneten Verzeichnisses des Bildpfades.

        Parameter:
        image_path (str): Der vollständige Pfad zum Bild, von dem die Kategorie extrahiert werden soll.

        Rückgabe:
        str: Der Name der Kategorie, zu der das Bild gehört.
        """
        # os.path.dirname extrahiert den Pfad des übergeordneten Verzeichnisses aus dem vollständigen Pfad.
        # os.path.basename gibt dann den Namen dieses übergeordneten Verzeichnisses zurück, der der Kategorie entspricht.
        return os.path.basename(os.path.dirname(image_path))
    

    def on_category_select(self, event):
        """
        Wird aufgerufen, wenn der Benutzer eine Kategorie in der Listbox auswählt.

        Diese Methode lädt alle Bilder der ausgewählten Kategorie, bereitet sie zur Anzeige vor
        und initialisiert den Prozess, um diese Bilder durchzugehen. Sie dient als Brücke zwischen
        der Benutzeroberfläche und der Logik zum Laden und Anzeigen von Bildern.

        Parameter:
        event: Ein Event-Objekt, das Informationen über das Auswahlereignis enthält.
               Dies kann verwendet werden, um zusätzliche Informationen zu extrahieren, wird hier aber nicht benötigt.
        """
        selection = self.kategorien_listbox.curselection()  # Erhält den Index der ausgewählten Kategorie.
        if selection:
            self.current_category = self.kategorien_listbox.get(selection[0])  # Aktualisiert die aktuelle Kategorie.
            self.load_images()  # Lädt alle Bilder der ausgewählten Kategorie.

            # Optional können hier weitere Aktionen durchgeführt werden, z.B. das Zurücksetzen des Canvas.
            self.reset_canvas()  # Angenommen, es gibt eine Methode, die den Canvas zurücksetzt.

    def reset_canvas(self):
        """
        Setzt den Canvas zurück. Dies könnte beinhalten, alle aktuellen Zeichnungen zu löschen,
        um für die Anzeige neuer Bilder bereit zu sein.
        """
        self.canvas.delete("all")  # Löscht alles vom Canvas.


    def load_images(self):
        """
        Lädt alle Bildpfade der ausgewählten Kategorie und bereitet sie für die Anzeige vor.

        Diese Methode wird aufgerufen, nachdem der Benutzer eine Kategorie ausgewählt hat.
        Sie durchsucht das entsprechende Verzeichnis nach allen Bildern und speichert ihre Pfade
        in einer Liste. Anschließend wird das erste Bild zur Anzeige bereitgestellt.
        """
        # Überprüft, ob eine Kategorie ausgewählt wurde.
        if self.current_category:
            # Erstellt den Pfad zum Verzeichnis der ausgewählten Kategorie.
            category_path = os.path.join(self.img_folder, self.current_category)

            # Sammelt alle Bildpfade in diesem Verzeichnis.
            self.images = [os.path.join(category_path, img) for img in os.listdir(category_path) if os.path.isfile(os.path.join(category_path, img))]

            # Setzt den Index des aktuellen Bildes zurück.
            self.current_image_index = 0

            # Bereitet das erste Bild zur Anzeige vor, wenn vorhanden.
            if self.images:
                self.load_and_display_image(self.images[self.current_image_index])
            else:
                messagebox.showinfo("Info", "Keine Bilder in dieser Kategorie gefunden.")
        else:
            messagebox.showinfo("Info", "Bitte wählen Sie zuerst eine Kategorie aus.")


    def next_image(self):
        """
        Wechselt zum nächsten Bild in der aktuellen Kategorie.

        Diese Methode wird aufgerufen, wenn der Benutzer mit dem aktuellen Bild fertig ist und
        zum nächsten Bild übergehen möchte. Sie aktualisiert den Index des aktuellen Bildes und lädt das nächste Bild.
        Falls das aktuelle Bild das letzte in der Liste ist, wird eine Nachricht angezeigt,
        die den Benutzer informiert, dass alle Bilder in der Kategorie bearbeitet wurden.
        """
        # Überprüft, ob es noch weitere Bilder in der Liste gibt.
        if self.current_image_index < len(self.images) - 1:
            # Aktualisiert den Index, um auf das nächste Bild zu verweisen.
            self.current_image_index += 1

            # Lädt und zeigt das nächste Bild an.
            self.load_and_display_image(self.images[self.current_image_index])
        else:
            # Informiert den Benutzer, dass alle Bilder in der Kategorie bearbeitet wurden.
            messagebox.showinfo("Fertig", "Alle Bilder in dieser Kategorie wurden bearbeitet. Bitte wählen Sie eine neue Kategorie.")


    def previous_image(self):
        """
        Wechselt zum vorherigen Bild in der aktuellen Kategorie.

        Diese Methode wird aufgerufen, wenn der Benutzer zurück zum vorherigen Bild navigieren möchte.
        Sie aktualisiert den Index des aktuellen Bildes, um auf das vorherige Bild zu verweisen,
        und lädt dieses Bild dann für die Anzeige. Wenn das erste Bild der Liste angezeigt wird,
        wird eine Nachricht angezeigt, dass es kein weiteres vorheriges Bild gibt.
        """
        # Überprüft, ob es ein vorheriges Bild in der Liste gibt.
        if self.current_image_index > 0:
            # Aktualisiert den Index, um auf das vorherige Bild zu verweisen.
            self.current_image_index -= 1

            # Lädt und zeigt das vorherige Bild an.
            self.load_and_display_image(self.images[self.current_image_index])
        else:
            # Informiert den Benutzer, dass es kein vorheriges Bild gibt, wenn wir beim ersten Bild sind.
            messagebox.showinfo("Hinweis", "Dies ist das erste Bild in der Kategorie. Es gibt kein vorheriges Bild.")


    def reset_canvas(self):
        """
        Bereitet den Canvas für ein neues Bild vor, indem alle Zeichnungen darauf gelöscht werden.

        Diese Methode wird typischerweise aufgerufen, bevor ein neues Bild auf dem Canvas angezeigt wird,
        um sicherzustellen, dass keine Überbleibsel von vorherigen Bildern oder Aktionen sichtbar sind.
        Das schließt alle gezeichneten Bounding Boxes, Markierungen oder sonstige visuelle Hinweise ein.
        """
        self.canvas.delete("all")  # Löscht alle Objekte vom Canvas.

        # Optional können hier weitere Aktionen durchgeführt werden, um den Canvas weiter zu initialisieren,
        # wie das Setzen eines Hintergrundbildes oder das Zeichnen eines Willkommens-Textes.


    def load_images(self):
            """
            Lädt alle Bildpfade der ausgewählten Kategorie und bereitet sie für die Anzeige vor.

            Diese Methode wird aufgerufen, nachdem der Benutzer eine Kategorie ausgewählt hat.
            Sie durchsucht das entsprechende Verzeichnis nach allen Bildern und speichert ihre Pfade
            in einer Liste. Anschließend wird das erste Bild zur Anzeige bereitgestellt, falls vorhanden.
            """
            # Überprüft, ob eine Kategorie ausgewählt wurde.
            if self.current_category:
                # Erstellt den Pfad zum Verzeichnis der ausgewählten Kategorie.
                category_path = os.path.join(self.img_folder, self.current_category)

                # Sammelt alle Bildpfade in diesem Verzeichnis.
                self.images = [os.path.join(category_path, img) for img in os.listdir(category_path) if os.path.isfile(os.path.join(category_path, img))]

                # Setzt den Index des aktuellen Bildes zurück.
                self.current_image_index = 0

                # Bereitet das erste Bild zur Anzeige vor, wenn vorhanden.
                if self.images:
                    self.load_and_display_image(self.images[self.current_image_index])
                else:
                    messagebox.showinfo("Info", "Keine Bilder in dieser Kategorie gefunden.")
            else:
                messagebox.showinfo("Info", "Bitte wählen Sie zuerst eine Kategorie aus.")


    def load_and_display_image(self, image_path):
        """
        Lädt ein Bild von einem gegebenen Pfad und zeigt es auf dem Canvas an.

        Diese Methode nutzt die 'load_image' Funktion, um das Bild zu laden,
        und zeigt es dann auf dem Canvas an. Es wird angenommen, dass 'load_image'
        ein PhotoImage-Objekt zurückgibt, das im Canvas verwendet werden kann.
        Falls das Laden fehlschlägt, wird eine Fehlermeldung angezeigt.

        Parameter:
        image_path (str): Der Pfad zum Bild, das geladen und angezeigt werden soll.
        """
        # Löscht zuerst den aktuellen Inhalt des Canvas.
        self.canvas.delete("all")

        # Versucht, das Bild zu laden.
        photo_image = self.load_image(image_path)
        if photo_image:
            # Zeigt das geladene Bild auf dem Canvas an, zentriert.
            self.canvas.create_image(400, 300, image=photo_image, anchor=tk.CENTER)
            self.photo_img = photo_image  # Speichert eine Referenz, um das Bild im Speicher zu behalten.
        else:
            # Falls das Bild nicht geladen werden konnte, wird eine Fehlermeldung angezeigt.
            messagebox.showerror("Fehler", "Das Bild konnte nicht geladen werden.")

            """
        Lädt ein Bild von einem gegebenen Pfad, passt seine Größe an, und zeigt es auf dem Canvas an.
        Die Bildposition wird berechnet, um das Bild zentriert im Canvas anzuzeigen.

        Parameter:
        image_path (str): Der Pfad zum Bild, das geladen und angezeigt werden soll.
        """
        
        #     # Öffnet das Bild und passt seine Größe an, um es innerhalb der Canvas-Größe optimal darzustellen.
        #     img = Image.open(image_path)
        #     img.thumbnail((self.canvas.winfo_width(), self.canvas.winfo_height()), Image.ANTIALIAS)
        #     self.photo_img = ImageTk.PhotoImage(img)

        #     # Berechnet die Position, um das Bild zentriert auf dem Canvas anzuzeigen.
        #     img_width, img_height = img.size
        #     canvas_width = self.canvas.winfo_width()
        #     canvas_height = self.canvas.winfo_height()
        #     x_position = (canvas_width - img_width) // 2
        #     y_position = (canvas_height - img_height) // 2

        #     # Löscht den aktuellen Inhalt des Canvas und zeigt das neue Bild an.
        #     self.canvas.delete("all")
        #     self.canvas.create_image(x_position, y_position, anchor=tk.NW, image=self.photo_img)

        #     # Speichert die aktuelle Bildposition und -größe für spätere Verwendung.
        #     self.current_image_path = image_path
        # self.current_image_position = (x_position, y_position, img_width, img_height)
        
    def load_image(self, image_path):
        """
        Lädt das Bild von einem gegebenen Pfad und bereitet es für die Anzeige vor.

        Parameter:
        image_path (str): Der Pfad zum Bild.

        Rückgabe:
        Ein PhotoImage Objekt, das im Canvas verwendet werden kann, oder None, falls das Laden fehlschlägt.
        """
        try:
            # Öffnet das Bild, passt seine Größe an und konvertiert es in ein PhotoImage.
            img = Image.open(image_path)
            img.thumbnail((800, 600), Image.ANTIALIAS)  # Passt die Größe des Bildes an.
            return ImageTk.PhotoImage(img)
        except Exception as e:
            messagebox.showerror("Fehler", f"Das Bild konnte nicht geladen werden: {e}")
            return None
        
    def delete_last_bounding_box(self):
        """
        Löscht die zuletzt gezeichnete Bounding Box vom Canvas und aus der Datenbank.
        """
        if self.last_box_id:
            # Löscht die zuletzt gezeichnete Bounding Box vom Canvas.
            self.canvas.delete(self.rect_id)

            # Löscht die zuletzt gezeichnete Bounding Box aus der Datenbank.
            try:
                self.cursor.execute("DELETE FROM boxes WHERE id = ?", (self.last_box_id,))
                self.conn.commit()
                messagebox.showinfo("Erfolg", "Bounding Box erfolgreich gelöscht.")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Löschen der Bounding Box: {e}")
            
            self.rect_id = None
            self.last_box_id = None  # Setzt die ID der zuletzt gezeichneten Box zurück.
        else:
            messagebox.showinfo("Info", "Keine Bounding Box zum Löschen vorhanden.")






    def export_bounding_boxes(self):
        """
        Exportiert die Bounding Box-Daten aller Bilder der aktuellen Kategorie in eine CSV-Datei.

        Die CSV-Datei enthält Spalten für die Image-ID, Kategorie und die Koordinaten der Bounding Box (x1, y1, x2, y2).
        Der Dateiname der CSV wird basierend auf dem Namen der aktuellen Kategorie generiert.
        """
        if not self.current_category:
            messagebox.showinfo("Info", "Bitte wählen Sie zuerst eine Kategorie aus.")
            return

        # Der Dateiname für die CSV-Datei basiert auf dem Namen der aktuellen Kategorie.
        filename = f"{self.current_category}_bounding_boxes.csv"
        
        try:
            # Öffnet eine neue CSV-Datei zum Schreiben.
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                # Schreibt die Kopfzeile in die CSV-Datei.
                writer.writerow(['Image ID', 'Kategorie', 'X1', 'Y1', 'X2', 'Y2'])
                
                # Führt eine Abfrage aus, um alle Bounding Box-Daten der aktuellen Kategorie zu erhalten.
                self.cursor.execute("SELECT image_id, category, x1, y1, x2, y2 FROM boxes WHERE category = ?", (self.current_category,))
                all_boxes = self.cursor.fetchall()
                
                # Schreibt jede Bounding Box als Zeile in die CSV-Datei.
                for box in all_boxes:
                    writer.writerow(box)

            messagebox.showinfo("Erfolg", f"Bounding Box-Daten wurden erfolgreich nach {filename} exportiert.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Exportieren der Bounding Box-Daten: {e}")


    def show_image_previews(self):
        """
        Zeigt eine Vorschau der Bilder in der aktuellen Kategorie an.

        Diese Methode erstellt ein neues Fenster, das kleine Vorschaubilder aller Bilder
        in der ausgewählten Kategorie anzeigt. Es ermöglicht den Benutzern, einen schnellen
        Überblick zu erhalten, ohne jedes Bild einzeln laden zu müssen.
        """
        if not self.current_category:
            messagebox.showinfo("Info", "Bitte wählen Sie zuerst eine Kategorie aus.")
            return

        # Erstellt ein neues Fenster für die Bildervorschau.
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Bildervorschau")

        # Sammelt alle Bildpfade in der aktuellen Kategorie.
        image_paths = self.images  # Nutzt die bereits geladene Liste der Bildpfade.

        for img_path in image_paths:
            # Lädt und zeigt jedes Bild als Vorschau an.
            try:
                img = Image.open(img_path)
                img.thumbnail((100, 100), Image.ANTIALIAS)  # Erstellt eine kleine Vorschau.
                photo = ImageTk.PhotoImage(img)
                label = tk.Label(preview_window, image=photo)
                label.image = photo  # Hält eine Referenz, um das Bild im Speicher zu behalten.
                label.pack(side=tk.LEFT, padx=5, pady=5)
            except Exception as e:
                continue  # Bei einem Fehler wird das Bild übersprungen.
            
    # Beispiel einer Methode, die visuelle Rückmeldung gibt und die Fehlerkorrektur erleichtert
    def delete_last_bounding_box(self):
        if self.last_box_id:
            # Löschen der Bounding Box mit visueller Rückmeldung
            self.canvas.delete(self.rect_id)
            self.canvas.update()  # Aktualisiert den Canvas sofort für direkte Rückmeldung
            messagebox.showinfo("Gelöscht", "Die letzte Bounding Box wurde erfolgreich gelöscht.")
            self.last_box_id = None
        else:
            messagebox.showinfo("Hinweis", "Keine Bounding Box zum Löschen vorhanden.")

    def show_help(self):
        """
        Zeigt ein Hilfefenster mit Anleitungen und Tipps zur Nutzung der Anwendung.
        
        Diese Methode erstellt ein neues Fenster (Toplevel), das verschiedene Hilfetexte enthält,
        welche die Funktionen der Anwendung erläutern. Texte sind in einfacher Sprache verfasst,
        um allen Benutzern das Verständnis zu erleichtern.
        """
        help_window = tk.Toplevel(self.root)
        help_window.title("Hilfe")
        
        # Erstellt einen Scrollbaren Textbereich für die Hilfetexte.
        help_text = tk.Text(help_window, wrap="word", height=10, width=50)
        help_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(help_window, command=help_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        help_text.config(yscrollcommand=scrollbar.set)

        # Fügt die Hilfetexte hinzu.
        help_contents = """
        Willkommen zur Hilfe der Bounding Box App!
        
        - Wählen Sie eine Kategorie aus der Liste links, um Bilder anzuzeigen.
        - Klicken und ziehen Sie auf dem Bild, um eine Bounding Box zu zeichnen.
        - Verwenden Sie die Buttons 'Nächstes Bild' und 'Vorheriges Bild', um durch die Bilder zu navigieren.
        - Der 'Exportieren'-Button speichert alle Bounding Boxes der aktuellen Kategorie in einer CSV-Datei.
        - Mit dem 'Radierer'-Button können Sie die zuletzt gezeichnete Bounding Box löschen.
        
        Für weitere Informationen kontaktieren Sie bitte den Support.
        """
        
        help_text.insert(tk.END, help_contents)
        help_text.config(state=tk.DISABLED) 

    def draw_image_boundaries(self):
        """
        Zeichnet Linien um die Grenzen des Bildes auf dem Canvas, um diese visuell zu markieren.
        Voraussetzung ist, dass die Bildposition und -größe bereits in self.current_image_position gespeichert wurden.
        """
        if not self.current_image_position:
            return  # Beendet die Methode frühzeitig, falls keine Bildposition gespeichert wurde.

        x_position, y_position, img_width, img_height = self.current_image_position

        # Berechnet die Koordinaten für die Grenzen des Bildes.
        top_left = (x_position, y_position)
        top_right = (x_position + img_width, y_position)
        bottom_left = (x_position, y_position + img_height)
        bottom_right = (x_position + img_width, y_position + img_height)

        # Zeichnet Linien entlang der Bildgrenzen.
        self.canvas.create_line(top_left, top_right, fill="red")  # Obere Kante
        self.canvas.create_line(top_left, bottom_left, fill="red")  # Linke Kante
        self.canvas.create_line(bottom_left, bottom_right, fill="red")  # Untere Kante
        self.canvas.create_line(top_right, bottom_right, fill="red")  # Rechte Kante


    def load_image(self, image_path):
        # Prüft, ob das Bild bereits im Cache ist
        if image_path not in self.image_cache:
            try:
                img = Image.open(image_path)
                img.thumbnail((800, 600), Image.ANTIALIAS)
                self.image_cache[image_path] = ImageTk.PhotoImage(img)
            except Exception as e:
                messagebox.showerror("Fehler", f"Das Bild konnte nicht geladen werden: {e}")
                return None
        return self.image_cache[image_path]

def finde_image_folder_path(folder_name="img", root_folder='./'):
    """
    Sucht rekursiv nach einem Ordner im angegebenen Wurzelverzeichnis und allen Unterordnern.
    
    :param folder_name: Name des gesuchten Ordners.
    :param root_folder: Wurzelverzeichnis, in dem die Suche beginnt.
    :return: Den Pfad des gefundenen Ordners oder None, wenn der Ordner nicht gefunden wurde.
    """
    for root, dirs, files in os.walk(root_folder):
        if folder_name in dirs:
            return os.path.join(root, folder_name)
        print("sorry")
    return None



def main():
    root = tk.Tk()
    img_folder = finde_image_folder_path()  # Pfad zum Ordner mit Bildern anpassen
    app = BoundingBoxApp(root, img_folder)
    root.mainloop()

if __name__ == "__main__":
    main()