import tkinter as tk
from tkinter import ttk, filedialog
import configparser
import os
import threading
import sys
from main import run_scanner, run_camera_scanner
from PIL import Image, ImageTk
import cv2
import numpy as np

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
        self.geometry("800x600")

        # Create main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Input source selection
        source_frame = ttk.LabelFrame(main_frame, text="Input Source")
        source_frame.pack(fill="x", expand=True, pady=5)

        self.source_var = tk.StringVar(value="video")
        video_radio = ttk.Radiobutton(source_frame, text="Video File", variable=self.source_var, value="video", command=self.switch_source_view)
        video_radio.pack(side="left", padx=5)
        camera_radio = ttk.Radiobutton(source_frame, text="Live Camera", variable=self.source_var, value="camera", command=self.switch_source_view)
        camera_radio.pack(side="left", padx=5)

        # Video file frame
        self.file_frame = ttk.LabelFrame(main_frame, text="Video File")
        self.file_frame.pack(fill="x", expand=True, pady=5)

        self.filepath_var = tk.StringVar()
        filepath_entry = ttk.Entry(self.file_frame, textvariable=self.filepath_var, width=60)
        filepath_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        browse_button = ttk.Button(self.file_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side="left", padx=5)

        # Camera frame
        self.camera_frame = ttk.LabelFrame(main_frame, text="Live Camera")

        camera_view_frame = ttk.Frame(self.camera_frame)
        camera_view_frame.pack(fill="both", expand=True)

        self.camera_feed_label = ttk.Label(camera_view_frame)
        self.camera_feed_label.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.composite_image_label = ttk.Label(camera_view_frame)
        self.composite_image_label.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        camera_controls_frame = ttk.Frame(self.camera_frame)
        camera_controls_frame.pack(fill="x", expand=True, pady=5)

        self.start_camera_button = ttk.Button(camera_controls_frame, text="Start Camera", command=self.start_camera_thread)
        self.start_camera_button.pack(side="left", padx=5)
        self.stop_camera_button = ttk.Button(camera_controls_frame, text="Stop Camera", command=self.stop_camera, state="disabled")
        self.stop_camera_button.pack(side="left", padx=5)

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

        self.start_button = ttk.Button(control_frame, text="Start Scan", command=self.start_scan_thread)
        self.start_button.pack(side="right", padx=5)

        self.stop_scan_button = ttk.Button(control_frame, text="Stop Scan", command=self.stop_scan, state="disabled")
        self.stop_scan_button.pack(side="right", padx=5)

        # Status
        status_frame = ttk.LabelFrame(main_frame, text="Status")
        status_frame.pack(fill="both", expand=True, pady=5)

        self.status_text = tk.Text(status_frame, height=5, wrap="word")
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Redirect stdout
        sys.stdout = TextRedirector(self.status_text)

        self.camera_running = False
        self.scanning = False
        self.composite_image = None

    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*"))
        )
        if filepath:
            self.filepath_var.set(filepath)

    def start_scan_thread(self):
        if self.source_var.get() == 'video':
            self.start_button.config(state="disabled")
            self.status_text.delete(1.0, tk.END)
            scan_thread = threading.Thread(target=self.start_scan)
            scan_thread.start()
        else:
            self.start_scan()

    def start_scan(self):
        if self.source_var.get() == 'video':
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
        else: # camera
            self.scanning = True
            self.start_button.config(state="disabled")
            self.stop_scan_button.config(state="normal")
            self.composite_image = None

    def switch_source_view(self):
        if self.source_var.get() == "video":
            self.camera_frame.pack_forget()
            self.file_frame.pack(fill="x", expand=True, pady=5)
            self.start_button.config(text="Start Scan")
            self.stop_scan_button.config(state="disabled")
        else:
            self.file_frame.pack_forget()
            self.camera_frame.pack(fill="both", expand=True, pady=5)
            self.start_button.config(text="Start Scan", state="disabled")
            self.stop_scan_button.config(state="disabled")

    def start_camera_thread(self):
        self.start_camera_button.config(state="disabled")
        self.stop_camera_button.config(state="normal")
        self.start_button.config(state="normal")

        self.camera_running = True
        self.show_camera_feed()

    def stop_camera(self):
        self.camera_running = False
        self.start_camera_button.config(state="normal")
        self.stop_camera_button.config(state="disabled")
        self.start_button.config(state="disabled")

    def show_camera_feed(self):
        if not hasattr(self, 'camera_generator'):
            self.camera_generator = run_camera_scanner()

        frame = next(self.camera_generator, None)
        if frame is not None and self.camera_running:
            height, width, _ = frame.shape
            scan_line_x = width // 2

            if self.scanning:
                scan_line = frame[:, scan_line_x:scan_line_x+1]
                if self.composite_image is None:
                    self.composite_image = scan_line
                else:
                    self.composite_image = np.hstack((self.composite_image, scan_line))

                # Show composite image
                composite_img_tk = self.convert_frame_to_tkinter(self.composite_image)
                self.composite_image_label.imgtk = composite_img_tk
                self.composite_image_label.configure(image=composite_img_tk)

            cv2.line(frame, (scan_line_x, 0), (scan_line_x, height), (0, 255, 0), 2)
            imgtk = self.convert_frame_to_tkinter(frame)
            self.camera_feed_label.imgtk = imgtk
            self.camera_feed_label.configure(image=imgtk)

            self.after(10, self.show_camera_feed)
        else:
            if hasattr(self, 'camera_generator'):
                del self.camera_generator
            self.camera_feed_label.configure(image=None)

    def convert_frame_to_tkinter(self, frame):
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)
        return imgtk

    def stop_scan(self):
        self.scanning = False
        self.start_button.config(state="normal")
        self.stop_scan_button.config(state="disabled")
        if self.composite_image is not None:
            filename = f"linescan_{_get_timestamp()}.jpg"
            save_path = os.path.join(os.getcwd(), "RESULT", filename)
            cv2.imwrite(save_path, self.composite_image)
            print(f"Scan saved to {save_path}")

def _get_timestamp():
    import datetime
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

if __name__ == "__main__":
    app = App()
    app.switch_source_view()
    app.mainloop()
