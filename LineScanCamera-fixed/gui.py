import tkinter as tk
from tkinter import ttk, filedialog
import configparser
import os
import threading
import sys
from main import run_scanner, CameraScanner
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

        # Camera feed label with placeholder
        self.camera_feed_label = ttk.Label(camera_view_frame, text="Camera feed will appear here\n(Click 'Start Camera')", 
                                          background="black", foreground="white", anchor="center")
        self.camera_feed_label.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Composite image label with placeholder  
        self.composite_image_label = ttk.Label(camera_view_frame, text="Line scan result\n(Click 'Start Scan')", 
                                              background="gray", foreground="white", anchor="center")
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

        # Motion Detection
        motion_frame = ttk.LabelFrame(main_frame, text="Motion Detection")
        motion_frame.pack(fill="x", expand=True, pady=5)

        # Load motion detection settings from config
        motion_default = self.config.getboolean("DEFAULT", "motion_detection") if self.config.has_option("DEFAULT", "motion_detection") else True
        sensitivity_default = self.config.get("DEFAULT", "motion_sensitivity") if self.config.has_option("DEFAULT", "motion_sensitivity") else "1000"
        
        self.motion_enabled_var = tk.BooleanVar(value=motion_default)
        motion_checkbox = ttk.Checkbutton(motion_frame, text="Enable Motion Detection", variable=self.motion_enabled_var)
        motion_checkbox.pack(side="left", padx=5)

        # Motion sensitivity
        sensitivity_frame = ttk.Frame(motion_frame)
        sensitivity_frame.pack(side="left", padx=20)
        sensitivity_label = ttk.Label(sensitivity_frame, text="Sensitivity:")
        sensitivity_label.pack(side="left", padx=5)
        self.motion_sensitivity_var = tk.StringVar(value=sensitivity_default)
        sensitivity_entry = ttk.Entry(sensitivity_frame, textvariable=self.motion_sensitivity_var, width=8)
        sensitivity_entry.pack(side="left", padx=5)

        # Status indicator
        self.motion_status_label = ttk.Label(motion_frame, text="Motion: Not Active", foreground="gray")
        self.motion_status_label.pack(side="right", padx=5)

        # Frame Blending
        blending_frame = ttk.LabelFrame(main_frame, text="Frame Blending")
        blending_frame.pack(fill="x", expand=True, pady=5)

        # Load blending settings from config
        blending_default = self.config.getboolean("DEFAULT", "frame_blending") if self.config.has_option("DEFAULT", "frame_blending") else True
        blend_strength_default = self.config.get("DEFAULT", "blend_strength") if self.config.has_option("DEFAULT", "blend_strength") else "0.3"
        
        self.blending_enabled_var = tk.BooleanVar(value=blending_default)
        blending_checkbox = ttk.Checkbutton(blending_frame, text="Enable Frame Blending", variable=self.blending_enabled_var)
        blending_checkbox.pack(side="left", padx=5)

        # Blend strength
        blend_frame = ttk.Frame(blending_frame)
        blend_frame.pack(side="left", padx=20)
        blend_label = ttk.Label(blend_frame, text="Blend Strength:")
        blend_label.pack(side="left", padx=5)
        self.blend_strength_var = tk.StringVar(value=blend_strength_default)
        blend_entry = ttk.Entry(blend_frame, textvariable=self.blend_strength_var, width=8)
        blend_entry.pack(side="left", padx=5)
        
        # Blend info label
        blend_info_label = ttk.Label(blending_frame, text="(0.1=subtle, 0.5=strong)", foreground="gray")
        blend_info_label.pack(side="right", padx=5)

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
        self.camera_scanner = None
        
        # Motion detection variables
        self.previous_frame = None
        self.motion_threshold = 1000  # Adjust this value to control sensitivity
        self.frames_since_motion = 0
        self.max_frames_without_motion = 5  # Pause after 5 frames without motion
        
        # Frame blending variables
        self.previous_scan_region = None

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
            
            # Reset motion detection for new scan
            self.previous_frame = None
            self.frames_since_motion = 0
            
            # Reset blending state for new scan
            self.previous_scan_region = None
            
            # Print mode selection for user feedback
            scan_mode = self.mode_var.get()
            width_roi = self.width_roi_var.get()
            motion_enabled = self.motion_enabled_var.get()
            print(f"Starting live scan in {scan_mode.upper()} mode")
            if scan_mode == "width":
                print(f"Width ROI: {width_roi} pixels")
            else:
                print("Extracting single column line")
            if motion_enabled:
                sensitivity = self.motion_sensitivity_var.get()
                region_type = f"{width_roi}px width ROI" if scan_mode == "width" else "column line"
                print(f"Motion detection ENABLED in {region_type} (sensitivity: {sensitivity})")
            else:
                print("Motion detection DISABLED - capturing all frames")
            
            # Print blending information
            blending_enabled = self.blending_enabled_var.get()
            if blending_enabled:
                blend_strength = self.blend_strength_var.get()
                print(f"Frame blending ENABLED (strength: {blend_strength})")
            else:
                print("Frame blending DISABLED - sharp transitions")

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

        # Import here to avoid circular import
        from main import CameraScanner
        self.camera_scanner = CameraScanner()
        
        if self.camera_scanner.start():
            self.camera_running = True
            self.show_camera_feed()
        else:
            print("Failed to start camera")
            self.stop_camera()

    def stop_camera(self):
        self.camera_running = False
        if self.camera_scanner:
            self.camera_scanner.stop()
            self.camera_scanner = None
        self.start_camera_button.config(state="normal")
        self.stop_camera_button.config(state="disabled")
        self.start_button.config(state="disabled")
        # Clear camera display and restore placeholder text
        self.camera_feed_label.configure(image="", text="Camera feed will appear here\n(Click 'Start Camera')")
        self.composite_image_label.configure(image="", text="Line scan result\n(Click 'Start Scan')")
        # Remove image references
        if hasattr(self.camera_feed_label, 'image'):
            del self.camera_feed_label.image
        if hasattr(self.composite_image_label, 'image'):
            del self.composite_image_label.image
        # Reset motion detection
        self.previous_frame = None
        self.motion_status_label.configure(text="Motion: Not Active", foreground="gray")

    def detect_motion(self, current_frame, scan_mode=None, scan_line_x=None, width_roi=None):
        """Detect motion in the scanning region only"""
        if not self.motion_enabled_var.get():
            return True  # Always capture if motion detection is disabled
        
        # Get scanning parameters if not provided
        if scan_mode is None:
            scan_mode = self.mode_var.get()
        if scan_line_x is None:
            scan_line_x = current_frame.shape[1] // 2
        if width_roi is None:
            width_roi = int(self.width_roi_var.get())
        
        # Extract the scanning region from current frame
        height = current_frame.shape[0]
        if scan_mode == "width":
            # Width mode: extract width ROI region
            start_x = max(0, scan_line_x - width_roi // 2)
            end_x = min(current_frame.shape[1], scan_line_x + width_roi // 2)
            scan_region = current_frame[:, start_x:end_x]
        else:
            # Column mode: extract single line (with small buffer for stability)
            buffer = 2  # 2 pixels on each side for more stable detection
            start_x = max(0, scan_line_x - buffer)
            end_x = min(current_frame.shape[1], scan_line_x + buffer + 1)
            scan_region = current_frame[:, start_x:end_x]
        
        if self.previous_frame is None:
            # First frame, always capture
            self.previous_frame = cv2.cvtColor(scan_region, cv2.COLOR_BGR2GRAY)
            return True
        
        # Convert current scan region to grayscale
        current_gray = cv2.cvtColor(scan_region, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference in scanning region only
        frame_diff = cv2.absdiff(self.previous_frame, current_gray)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)
        
        # Calculate total white pixels (changed pixels) in scanning region
        motion_amount = cv2.countNonZero(thresh)
        
        # Update previous frame with current scan region
        self.previous_frame = current_gray.copy()
        
        # Check if motion exceeds threshold
        threshold = int(self.motion_sensitivity_var.get())
        has_motion = motion_amount > threshold
        
        # Calculate region info for status display
        region_info = f"{scan_region.shape[1]}px" if scan_mode == "width" else "line"
        
        # Update motion status
        if has_motion:
            self.motion_status_label.configure(text=f"Motion: DETECTED ({motion_amount}) in {region_info}", foreground="green")
            self.frames_since_motion = 0
        else:
            self.frames_since_motion += 1
            self.motion_status_label.configure(text=f"Motion: No Change ({motion_amount}) in {region_info}", foreground="orange")
        
        return has_motion

    def blend_frames(self, current_region, previous_region, blend_strength):
        """Blend current scan region with previous region for smooth transitions"""
        if previous_region is None or not self.blending_enabled_var.get():
            return current_region
        
        # Ensure both regions have the same shape
        if current_region.shape != previous_region.shape:
            return current_region
        
        try:
            # Convert to float for blending calculations
            current_float = current_region.astype(np.float64)
            previous_float = previous_region.astype(np.float64)
            
            # Blend: result = (1-strength) * current + strength * previous
            strength = float(blend_strength)
            strength = max(0.0, min(1.0, strength))  # Clamp between 0 and 1
            
            blended = (1.0 - strength) * current_float + strength * previous_float
            
            # Convert back to uint8
            return blended.astype(np.uint8)
        except Exception as e:
            print(f"Blending error: {e}")
            return current_region

    def show_camera_feed(self):
        if not self.camera_running or not self.camera_scanner:
            return

        try:
            frame = self.camera_scanner.get_frame()
            if frame is not None:
                height, width, _ = frame.shape
                scan_line_x = width // 2
                
                # Get width ROI from config for width mode
                width_roi = int(self.width_roi_var.get())
                scan_mode = self.mode_var.get()

                # Handle line scanning
                if self.scanning:
                    # Check for motion in the scanning region before capturing
                    has_motion = self.detect_motion(frame, scan_mode, scan_line_x, width_roi)
                    
                    if has_motion:
                        if scan_mode == "width":
                            # Width mode: extract a width region around center line
                            start_x = max(0, scan_line_x - width_roi // 2)
                            end_x = min(width, scan_line_x + width_roi // 2)
                            scan_region = frame[:, start_x:end_x]
                        else:
                            # Column mode: extract single line
                            scan_region = frame[:, scan_line_x:scan_line_x+1]
                        
                        # Apply blending if enabled
                        if self.blending_enabled_var.get():
                            blend_strength = float(self.blend_strength_var.get())
                            scan_region = self.blend_frames(scan_region, self.previous_scan_region, blend_strength)
                            self.previous_scan_region = scan_region.copy()
                        
                        if self.composite_image is None:
                            self.composite_image = scan_region
                        else:
                            self.composite_image = np.hstack((self.composite_image, scan_region))

                        # Show composite image
                        if self.composite_image.shape[1] > 0:
                            composite_img_tk = self.convert_frame_to_tkinter(self.composite_image)
                            if composite_img_tk:
                                self.composite_image_label.configure(image=composite_img_tk, text="")
                                self.composite_image_label.image = composite_img_tk

                # Draw scan visualization on frame (in BGR format)
                if scan_mode == "width":
                    # Draw width ROI rectangle
                    start_x = max(0, scan_line_x - width_roi // 2)
                    end_x = min(width, scan_line_x + width_roi // 2)
                    cv2.rectangle(frame, (start_x, 0), (end_x, height), (0, 255, 0), 2)
                else:
                    # Draw single scan line
                    cv2.line(frame, (scan_line_x, 0), (scan_line_x, height), (0, 255, 0), 2)
                
                # Display main camera feed
                imgtk = self.convert_frame_to_tkinter(frame)
                if imgtk:
                    self.camera_feed_label.configure(image=imgtk, text="")
                    self.camera_feed_label.image = imgtk

                # Schedule next frame update
                self.after(33, self.show_camera_feed)  # ~30 FPS
            else:
                print("No frame received from camera")
                self.stop_camera()
        except Exception as e:
            print(f"Error in camera feed: {e}")
            self.stop_camera()

    def convert_frame_to_tkinter(self, frame):
        """Convert OpenCV frame to tkinter PhotoImage with proper color handling"""
        try:
            # OpenCV uses BGR, but PIL expects RGB, so we need to convert
            if len(frame.shape) == 3:  # Color image
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:  # Grayscale image
                rgb_image = frame
            
            # Resize frame if it's too large for display
            height, width = rgb_image.shape[:2]
            max_width, max_height = 400, 300
            
            if width > max_width or height > max_height:
                # Calculate scaling factor to maintain aspect ratio
                scale = min(max_width/width, max_height/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                rgb_image = cv2.resize(rgb_image, (new_width, new_height))
            
            # Convert to PIL Image then to PhotoImage
            img = Image.fromarray(rgb_image)
            imgtk = ImageTk.PhotoImage(image=img)
            return imgtk
        except Exception as e:
            print(f"Error converting frame: {e}")
            return None

    def stop_scan(self):
        self.scanning = False
        self.start_button.config(state="normal")
        self.stop_scan_button.config(state="disabled")
        if self.composite_image is not None:
            # Create RESULT directory if it doesn't exist
            result_dir = os.path.join(os.getcwd(), "RESULT")
            os.makedirs(result_dir, exist_ok=True)
            
            filename = f"linescan_{_get_timestamp()}.jpg"
            save_path = os.path.join(result_dir, filename)
            cv2.imwrite(save_path, self.composite_image)
            print(f"Scan saved to {save_path}")

def _get_timestamp():
    import datetime
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

if __name__ == "__main__":
    app = App()
    app.switch_source_view()
    app.mainloop()
