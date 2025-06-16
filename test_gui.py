import tkinter as tk

root = tk.Tk()
root.title("Test Window")
root.geometry("300x200")
label = tk.Label(root, text="Hello, Tkinter!", bg="white", fg="black") # Added explicit colors
label.pack(pady=20)
root.mainloop()