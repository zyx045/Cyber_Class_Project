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
        self.master.geometry("800x600")

        self.carrier_files = []
        self.sliders = {}
        self.percent_labels = {}
        self.row_frames = {}
        self.lock_states = {}  # Track lock state for each file
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

        # Create a frame for slider and percentage
        slider_frame = tk.Frame(row_frame)
        slider_frame.pack(side="left", fill="x", expand=True)
        
        # Add lock button
        self.lock_states[file_path] = False
        lock_btn = tk.Button(
            row_frame, 
            text="🔓",  # Unlocked by default
            command=lambda f=file_path: self.toggle_lock(f)
        )
        lock_btn.pack(side="left", padx=(0, 5))
        
        slider = ttk.Scale(
            slider_frame,
            from_=0,
            to=100,
            orient="horizontal",
            value=100 / len(self.carrier_files),
            command=lambda val, f=file_path: self.slider_changed(f, val)
        )
        slider.pack(side="left", fill="x", expand=True)

        percent_label = tk.Label(slider_frame, text=f"{100 / len(self.carrier_files):.0f}%", width=5)
        percent_label.pack(side="left", padx=5)

        delete_btn = tk.Button(row_frame, text="Delete", command=lambda f=file_path: self.delete_carrier(f))
        delete_btn.pack(side="right", padx=5)
        
        # Store the lock button for later reference
        self.lock_buttons = getattr(self, 'lock_buttons', {})
        self.lock_buttons[file_path] = lock_btn

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
            # Clean up lock button and state
            if file_path in getattr(self, 'lock_buttons', {}):
                self.lock_buttons[file_path].destroy()
                del self.lock_buttons[file_path]
            if file_path in getattr(self, 'lock_states', {}):
                del self.lock_states[file_path]
            del self.sliders[file_path]
            del self.percent_labels[file_path]
            del self.row_frames[file_path]
            self.rebalance_sliders()

    def toggle_lock(self, file_path):
        """Toggle the lock state for a carrier file."""
        self.lock_states[file_path] = not self.lock_states[file_path]
        # Update lock button appearance
        self.lock_buttons[file_path].config(
            text="🔒" if self.lock_states[file_path] else "🔓"
        )
        # If we're locking this file, ensure its value is an integer
        if self.lock_states[file_path]:
            current_val = self.sliders[file_path].get()
            self.sliders[file_path].set(round(current_val))
            self.percent_labels[file_path].config(text=f"{round(current_val):.0f}%")

    def slider_changed(self, changed_file, new_value):
        if self._updating:
            return

        self._updating = True
        new_value = float(new_value)
        
        # If the changed slider is locked, revert its value
        if self.lock_states.get(changed_file, False):
            old_value = self.sliders[changed_file].get()
            self.sliders[changed_file].set(old_value)
            self.percent_labels[changed_file].config(text=f"{old_value:.0f}%")
            self._updating = False
            return
            
        # Only update the slider if it's not locked
        self.sliders[changed_file].set(new_value)
        
        # Get all unlocked sliders (excluding the changed one)
        unlocked_sliders = [f for f in self.sliders 
                          if f != changed_file and not self.lock_states.get(f, False)]
        
        total = sum(
            slider.get() 
            for f, slider in self.sliders.items() 
            if not self.lock_states.get(f, False) or f == changed_file
        )

        if total == 0:
            # If all sliders are at 0, distribute evenly
            even_value = 100 / len(self.sliders)
            for f, s in self.sliders.items():
                if not self.lock_states.get(f, False):  # Only update unlocked sliders
                    s.set(even_value)
                    self.percent_labels[f].config(text=f"{even_value:.0f}%")
        else:
            # Calculate how much is left after accounting for locked sliders
            locked_total = sum(
                slider.get() 
                for f, slider in self.sliders.items() 
                if self.lock_states.get(f, False)
            )
            remaining = 100 - locked_total
            
            # If the changed slider is the only one unlocked, set it to 100%
            if not unlocked_sliders:
                self.sliders[changed_file].set(100 - locked_total)
                self.percent_labels[changed_file].config(text=f"{100 - locked_total:.0f}%")
            else:
                # Distribute remaining percentage among unlocked sliders
                for f in unlocked_sliders:
                    if f != changed_file:
                        val = self.sliders[f].get() * (remaining / total)
                        self.sliders[f].set(val)
                        self.percent_labels[f].config(text=f"{val:.0f}%")
        
        # Ensure the changed slider's label is updated
        self.percent_labels[changed_file].config(text=f"{self.sliders[changed_file].get():.0f}%")
        self._updating = False

    def rebalance_sliders(self):
        if not self.sliders:
            return
            
        # Get total of all unlocked sliders
        unlocked_sliders = [f for f in self.sliders if not self.lock_states.get(f, False)]
        locked_total = sum(
            slider.get() 
            for f, slider in self.sliders.items() 
            if self.lock_states.get(f, False)
        )
        
        remaining = 100 - locked_total
        
        if not unlocked_sliders:
            # If all sliders are locked, don't change anything
            return
            
        if len(unlocked_sliders) == 1:
            # If only one slider is unlocked, set it to the remaining percentage
            f = unlocked_sliders[0]
            self.sliders[f].set(remaining)
            self.percent_labels[f].config(text=f"{remaining:.0f}%")
        else:
            # Otherwise, distribute remaining percentage proportionally
            total = sum(self.sliders[f].get() for f in unlocked_sliders)
            if total == 0:
                # If all unlocked sliders are at 0, distribute remaining evenly
                even_val = remaining / len(unlocked_sliders)
                for f in unlocked_sliders:
                    self.sliders[f].set(even_val)
                    self.percent_labels[f].config(text=f"{even_val:.0f}%")
            else:
                # Distribute remaining based on current proportions
                for f in unlocked_sliders:
                    new_val = (self.sliders[f].get() / total) * remaining
                    self.sliders[f].set(new_val)
                    self.percent_labels[f].config(text=f"{new_val:.0f}%")

    def run_steganography(self):
        hidden_file = self.hidden_file_var.get()
        if not hidden_file:
            messagebox.showerror("Error", "Please select a file to hide first.")
            return
        if not self.carrier_files:
            messagebox.showerror("Error", "Please add at least one carrier file.")
            return

        try:
            carriers_data = [(f, int(round(self.sliders[f].get()))) for f in self.carrier_files]
            self.runner.run(hidden_file, carriers_data)
            messagebox.showinfo("Success", "Data hidden successfully in carrier files!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to hide data: {str(e)}")
            import traceback
            traceback.print_exc()

    def extract_data(self):
        """Handle the extraction of hidden data from carrier files."""
        try:
            # Let the user select the directory containing carrier files
            input_dir = filedialog.askdirectory(
                title="Select directory containing carrier files",
                mustexist=True
            )
            
            if not input_dir:  # User cancelled
                return
                
            # Call the runner's extract method to handle the extraction
            result = self.runner.extract(input_dir)
            
            if result:
                messagebox.showinfo("Success", f"File extracted successfully to:\n{result}")
            else:
                messagebox.showerror("Error", "Failed to extract data. Please check the console for details.")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during extraction: {str(e)}")
            import traceback
            traceback.print_exc()
