import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from Runner import Runner
import os


class GUI:
    SUPPORTED_HIDDEN_TYPES = ['.txt', '.md', '.py', '.html', '.css', '.js', '.json', '.xml', '.csv', '.log']
    SUPPORTED_CARRIER_TYPES = ['.wav', '.mp3', '.mp4', '.png', '.tiff', '.gif', '.bmp']

    def __init__(self, master, runner):
        self.master = master
        self.runner = runner
        self.master.title("Steganography Project - Liles - zyx045")
        self.master.geometry("800x550")

        self.carrier_files = []
        self.sliders = {}
        self.percent_labels = {}
        self.row_frames = {}
        self._updating = False

        hidden_frame = tk.LabelFrame(master, text="Hidden File", padx=10, pady=10)
        hidden_frame.pack(fill="x", padx=10, pady=5)

        self.hidden_file_var = tk.StringVar()
        tk.Entry(hidden_frame, textvariable=self.hidden_file_var, width=60, state="readonly").pack(side="left", padx=5)
        tk.Button(hidden_frame, text="Browse", command=self.load_hidden_file).pack(side="left", padx=5)

        carrier_frame = tk.LabelFrame(master, text="Carrier Files", padx=10, pady=10)
        carrier_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.carrier_container = tk.Frame(carrier_frame)
        self.carrier_container.pack(fill="both", expand=True)

        tk.Button(carrier_frame, text="Add Carrier File", command=self.add_carrier_file).pack(pady=5)

        button_frame = tk.Frame(master)
        button_frame.pack(fill="x", pady=10)

        tk.Button(button_frame, text="Run Steganography", command=self.run_steganography).pack(side="right", padx=10)
        tk.Button(button_frame, text="Extract", command=self.extract_data).pack(side="right", padx=10)
        tk.Button(button_frame, text="Quit", command=self.master.quit).pack(side="right")

    def load_hidden_file(self):
        file_path = filedialog.askopenfilename(title="Select file to hide")
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.SUPPORTED_HIDDEN_TYPES:
                messagebox.showerror("Unsupported File", f"Hidden file must be one of: {', '.join(self.SUPPORTED_HIDDEN_TYPES)}")
                return
            self.hidden_file_var.set(file_path)

    def add_carrier_file(self):
        file_path = filedialog.askopenfilename(title="Select carrier file")
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.SUPPORTED_CARRIER_TYPES:
            messagebox.showerror("Unsupported File", f"Carrier file must be one of: {', '.join(self.SUPPORTED_CARRIER_TYPES)}")
            return

        if file_path in self.carrier_files:
            messagebox.showwarning("Duplicate File", "This carrier file has already been added.")
            return

        self.carrier_files.append(file_path)

        row_frame = tk.Frame(self.carrier_container)
        row_frame.pack(fill="x", pady=5)

        label = tk.Label(row_frame, text=file_path.split("/")[-1], anchor="w")
        label.pack(side="left", fill="x", expand=True)

        slider = ttk.Scale(
            row_frame,
            from_=0,
            to=100,
            orient="horizontal",
            value=100 / len(self.carrier_files),
            command=lambda val, f=file_path: self.slider_changed(f, val)
        )
        slider.pack(side="left", padx=10, fill="x", expand=True)

        percent_label = tk.Label(row_frame, text=f"{100 / len(self.carrier_files):.0f}%")
        percent_label.pack(side="left", padx=5)

        delete_btn = tk.Button(row_frame, text="Delete", command=lambda f=file_path: self.delete_carrier(f))
        delete_btn.pack(side="right", padx=5)

        self.sliders[file_path] = slider
        self.percent_labels[file_path] = percent_label
        self.row_frames[file_path] = row_frame

        self.rebalance_sliders()

    def delete_carrier(self, file_path):
        if file_path in self.carrier_files:
            self.carrier_files.remove(file_path)
            self.sliders[file_path].destroy()
            self.percent_labels[file_path].destroy()
            self.row_frames[file_path].destroy()
            del self.sliders[file_path]
            del self.percent_labels[file_path]
            del self.row_frames[file_path]
            self.rebalance_sliders()

    def slider_changed(self, changed_file, new_value):
        if self._updating:
            return

        self._updating = True
        new_value = float(new_value)
        self.sliders[changed_file].set(new_value)
        total = sum(slider.get() for slider in self.sliders.values())

        if total == 0:
            even_value = 100 / len(self.sliders)
            for f, s in self.sliders.items():
                s.set(even_value)
                self.percent_labels[f].config(text=f"{even_value:.0f}%")
        else:
            diff = 100 - new_value
            other_files = [f for f in self.sliders if f != changed_file]
            if other_files:
                others_total = sum(self.sliders[f].get() for f in other_files)
                for f in other_files:
                    if others_total > 0:
                        val = self.sliders[f].get() * (diff / others_total)
                    else:
                        val = diff / len(other_files)
                    self.sliders[f].set(val)
                    self.percent_labels[f].config(text=f"{val:.0f}%")

        self.percent_labels[changed_file].config(text=f"{new_value:.0f}%")
        self._updating = False

    def rebalance_sliders(self):
        total = sum(s.get() for s in self.sliders.values())
        if total == 0 and self.sliders:
            total = 1
        for f, s in self.sliders.items():
            new_val = (s.get() / total) * 100
            s.set(new_val)
            self.percent_labels[f].config(text=f"{new_val:.0f}%")

    def run_steganography(self):
        hidden_file = self.hidden_file_var.get()
        if not hidden_file:
            messagebox.showerror("Error", "Please select a file to hide first.")
            return
        if not self.carrier_files:
            messagebox.showerror("Error", "Please add at least one carrier file.")
            return

        carriers_data = [(f, int(round(self.sliders[f].get()))) for f in self.carrier_files]
        self.runner.run(hidden_file, carriers_data)

    def extract_data(self):
        self.runner.extract("input_files")