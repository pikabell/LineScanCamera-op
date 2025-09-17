import tkinter as tk
from tkinter import ttk, filedialog
import configparser
import os
import threading
import sys
from main import run_scanner

class TextRedirector(object):
    def __init__(self, widget):
        self.widget = widget

    def write(self, str):
        self.widget.insert(tk.END, str)
        self.widget.see(tk.END)

    def flush(self):
        pass

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Line Scan Camera")
        self.geometry("600x500")

        # Create main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Video File")
        file_frame.pack(fill="x", expand=True, pady=5)

        self.filepath_var = tk.StringVar()
        filepath_entry = ttk.Entry(file_frame, textvariable=self.filepath_var, width=60)
        filepath_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        browse_button = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side="left", padx=5)

        # Scan mode
        mode_frame = ttk.LabelFrame(main_frame, text="Scan Mode")
        mode_frame.pack(fill="x", expand=True, pady=5)

        self.mode_var = tk.StringVar(value="column")
        column_radio = ttk.Radiobutton(mode_frame, text="Column", variable=self.mode_var, value="column")
        column_radio.pack(side="left", padx=5)
        width_radio = ttk.Radiobutton(mode_frame, text="Width", variable=self.mode_var, value="width")
        width_radio.pack(side="left", padx=5)

        # Configuration
        config_frame = ttk.LabelFrame(main_frame, text="Configuration")
        config_frame.pack(fill="both", expand=True, pady=5)

        self.config_path = os.path.join(os.getcwd(), "config", "config.ini")
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)

        # width_roi
        width_roi_frame = ttk.Frame(config_frame)
        width_roi_frame.pack(fill="x", expand=True, pady=2)
        width_roi_label = ttk.Label(width_roi_frame, text="Width ROI:")
        width_roi_label.pack(side="left", padx=5)
        self.width_roi_var = tk.StringVar(value=self.config.get("DEFAULT", "width_roi"))
        width_roi_entry = ttk.Entry(width_roi_frame, textvariable=self.width_roi_var, width=10)
        width_roi_entry.pack(side="left", padx=5)

        self.visualize_vars = {}
        for section in ["DEFAULT", "DEBUG", "THRESH", "CONTOUR", "STITCH"]:
            frame = ttk.Frame(config_frame)
            frame.pack(fill="x", expand=True, pady=2)
            var = tk.BooleanVar(value=self.config.getboolean(section, "visualize"))
            self.visualize_vars[section] = var
            checkbox = ttk.Checkbutton(frame, text=f"Visualize {section}", variable=var)
            checkbox.pack(side="left", padx=5)

        # Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill="x", expand=True, pady=10)

        self.start_button = ttk.Button(control_frame, text="Start", command=self.start_scan_thread)
        self.start_button.pack(side="right", padx=5)

        # Status
        status_frame = ttk.LabelFrame(main_frame, text="Status")
        status_frame.pack(fill="both", expand=True, pady=5)

        self.status_text = tk.Text(status_frame, height=5, wrap="word")
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Redirect stdout
        sys.stdout = TextRedirector(self.status_text)


    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*"))
        )
        if filepath:
            self.filepath_var.set(filepath)

    def start_scan_thread(self):
        self.start_button.config(state="disabled")
        self.status_text.delete(1.0, tk.END)
        scan_thread = threading.Thread(target=self.start_scan)
        scan_thread.start()

    def start_scan(self):
        try:
            # Update config
            self.config.set("DEFAULT", "width_roi", self.width_roi_var.get())
            for section, var in self.visualize_vars.items():
                self.config.set(section, "visualize", str(var.get()))
            with open(self.config_path, 'w') as configfile:
                self.config.write(configfile)

            video_path = self.filepath_var.get()
            scan_mode = self.mode_var.get()

            if not video_path:
                print("Please select a video file.")
                return

            print(f"Starting scan with mode: {scan_mode}\n")
            run_scanner(video_path, scan_mode)
            print("\nScan finished.")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.start_button.config(state="normal")


if __name__ == "__main__":
    app = App()
    app.mainloop()
