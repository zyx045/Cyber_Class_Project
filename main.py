from GUI import GUI
from Runner import Runner
import tkinter as tk

if __name__ == "__main__":
    runner = Runner()
    root = tk.Tk()
    app = GUI(root, runner)
    root.mainloop()