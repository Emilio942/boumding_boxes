import tkinter as tk
from tkinter import Listbox, messagebox, filedialog, Canvas
from PIL import Image, ImageTk
import os
import sqlite3
import random

class BoundingBoxApp:
    def __init__(self, master, img_folder):
        self.master = master
        self.img_folder = img_folder
        self.database_path = 'bounding_boxes.db'
        self.current_category = None
        self.current_image_index = 0
        self.current_image_path = None
        self.images = []
        self.start_x, self.start_y, self.rect_id = None, None, None
        self.init_db()
        self.setup_ui()

    def init_db(self):
        self.conn = sqlite3.connect(self.database_path)
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
        self.master.title("Bounding Box Zeichner")
        self.kategorien_listbox = Listbox(self.master)
        self.kategorien_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = Canvas(self.master, width=800, height=600, bg='white')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.load_categories()
        self.kategorien_listbox.bind('<<ListboxSelect>>', self.on_category_select)
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)

    def load_categories(self):
        categories = [name for name in os.listdir(self.img_folder) if os.path.isdir(os.path.join(self.img_folder, name))]
        for category in categories:
            self.kategorien_listbox.insert(tk.END, category)

    def on_category_select(self, event):
        selection = self.kategorien_listbox.curselection()
        if selection:
            self.current_category = self.kategorien_listbox.get(selection[0])
            self.load_images()

    def load_images(self):
        category_path = os.path.join(self.img_folder, self.current_category)
        self.images = [os.path.join(category_path, img) for img in os.listdir(category_path) if os.path.isfile(os.path.join(category_path, img))]
        self.current_image_index = 0
        self.display_next_image()

    def display_next_image(self):
        if self.current_image_index < len(self.images):
            self.current_image_path = self.images[self.current_image_index]
            img = Image.open(self.current_image_path)
            img.thumbnail((800, 600), Image.ANTIALIAS)
            self.photo_img = ImageTk.PhotoImage(img)
            self.canvas.create_image(400, 300, image=self.photo_img, anchor=tk.CENTER)
            self.current_image_index += 1
        else:
            messagebox.showinfo("Fertig", "Alle Bilder in dieser Kategorie wurden bearbeitet.")

    def on_canvas_click(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

    def on_canvas_drag(self, event):
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def on_canvas_release(self, event):
        end_x, end_y = event.x, event.y
        if self.rect_id:
            bbox = (self.start_x, self.start_y, end_x, end_y)
            image_id = os.path.basename(self.current_image_path)
            self.save_bounding_box(image_id, self.current_category, bbox)
            self.rect_id = None  # Reset rectangle ID after drawing

    def save_bounding_box(self, image_id, category, bbox):
        try:
            self.cursor.execute('''
                INSERT INTO boxes (image_id, category, x1, y1, x2, y2)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (image_id, category, *bbox))
            self.conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Fehler", "Bounding Box bereits vorhanden für dieses Bild in dieser Kategorie.")

if __name__ == "__main__":
    root = tk.Tk()
    app = BoundingBoxApp(root, "./img")
    root.mainloop()