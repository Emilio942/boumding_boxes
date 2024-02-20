import tkinter as tk
from tkinter import filedialog, Listbox, messagebox
from PIL import Image, ImageTk
import os
import json
import sqlite3 
# Datenbank-Setup

db_path = 'bounding_boxes.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
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
    def __init__(self, root, img_folder):
        self.root = root
        self.img_folder = img_folder
        
        self.root.title("Bounding Box Zeichner")

        self.kategorien_listbox = Listbox(self.root)
        self.kategorien_listbox.pack(side=tk.LEFT, fill=tk.Y)

        self.load_categories()

        self.canvas = tk.Canvas(root, width=800, height=600, bg='white')
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.load_obj_data()

        # Binding canvas mouse events for drawing bounding boxes
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        
        self.start_x, self.start_y, self.rect_id = None, None, None

    def load_categories(self):
        try:
            categories = [name for name in os.listdir(self.img_folder) if os.path.isdir(os.path.join(self.img_folder, name))]
            for category in categories:
                self.kategorien_listbox.insert(tk.END, category)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_obj_data(self):
        if os.path.exists(self.obj_data_file):
            with open(self.obj_data_file, 'r') as file:
                self.obj_data = json.load(file)
        else:
            self.obj_data = []

    def on_canvas_click(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

    def on_canvas_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_canvas_release(self, event):
        end_x, end_y = event.x, event.y
        if self.rect_id:
            bbox = (self.start_x, self.start_y, end_x, end_y)
            self.save_bounding_box(bbox)
            self.rect_id = None

def save_bounding_box(self, image_id, category, bbox):
    try:
        cursor.execute('''
            INSERT INTO boxes (image_id, category, x1, y1, x2, y2)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (image_id, category, bbox[0], bbox[1], bbox[2], bbox[3]))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Eintrag für Image-ID {image_id} in Kategorie {category} existiert bereits.")



if __name__ == "__main__":
    root = tk.Tk()
    img_folder = "./img"  # Anpassen an deinen Pfad
    app = BoundingBoxApp(root, img_folder,)
    root.mainloop()
# Vergiss nicht, die Verbindung zu schließen, wenn du fertig bist
conn.close()