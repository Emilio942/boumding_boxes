import tkinter as tk

def start_drawing(event):
    global start_x, start_y
    start_x, start_y = event.x, event.y
    canvas.create_rectangle(start_x, start_y, start_x + 1, start_y + 1, outline='black', tag='box')

def draw_box(event):
    global start_x, start_y
    canvas.delete('box')
    canvas.create_rectangle(start_x, start_y, event.x, event.y, outline='black', tag='box')

def finish_drawing(event):
    canvas.delete('box')
    canvas.create_rectangle(start_x, start_y, event.x, event.y, outline='black')

root = tk.Tk()
root.title("Bounding Box Zeichner")

canvas = tk.Canvas(root, width=800, height=600, bg='white')
canvas.pack()

start_x = start_y = 0

canvas.bind('<Button-1>', start_drawing)
canvas.bind('<B1-Motion>', draw_box)
canvas.bind('<ButtonRelease-1>', finish_drawing)

root.mainloop()
