#!/usr/bin/env python3
"""
GUI Module for Line Scan Camera

This module contains the graphical user interface for the Line Scan Camera application.
Provides both video file processing and live camera functionality.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
import threading
import sys
import datetime
import numpy as np
import cv2
from PIL import Image, ImageTk

from ..core import run_scanner, CameraScanner
from ..utils import get_config
from ..utils.gpu_acceleration import is_gpu_available


class TextRedirector:
    """Redirect text output to a tkinter widget"""
    
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.insert(tk.END, text)
        self.widget.see(tk.END)

    def flush(self):
        pass


class LineScanGUI(tk.Tk):
    """
    Main GUI application for Line Scan Camera
    
    Provides interface for:
    - Video file processing
    - Live camera scanning
    - Configuration management
    - Real-time visualization
    """
    
    def __init__(self):
        super().__init__()
        self.title("Line Scan Camera v2.0")
        self.geometry("950x800")
        self.minsize(800, 600)  # Set minimum window size
        
        # Initialize configuration
        self.config_manager = get_config()
        
        # Check GPU availability
        self.gpu_available = is_gpu_available()
        if self.gpu_available:
            print("✓ GPU acceleration available and enabled")
        else:
            print("! GPU acceleration not available - using CPU processing")
        
        # Initialize state variables
        self.camera_running = False
        self.scanning = False
        self.composite_image = None
        self.camera_scanner = None
        
        # Motion detection variables
        self.previous_frame = None
        self.frames_since_motion = 0
        self.max_frames_without_motion = 5
        
        # Frame blending variables
        self.previous_scan_region = None
        
        # Create GUI
        self._create_widgets()
        
        # Set initial view
        self.switch_source_view()
    
    def _create_widgets(self):
        """Create all GUI widgets with scrollable interface"""
        # Create main canvas and scrollbar for scrolling functionality
        self.main_canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        # Create window in canvas
        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas scrolling
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind mousewheel to canvas
        self.bind_mousewheel()
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        
        # Main frame (now inside scrollable_frame)
        main_frame = ttk.Frame(self.scrollable_frame, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Input source selection
        self._create_source_selection(main_frame)
        
        # GPU status indicator
        self._create_gpu_status(main_frame)
        
        # Video file frame
        self._create_video_frame(main_frame)
        
        # Camera frame
        self._create_camera_frame(main_frame)
        
        # Scan mode selection
        self._create_mode_selection(main_frame)
        
        # Configuration frame
        self._create_config_frame(main_frame)
        
        # Motion detection frame
        self._create_motion_frame(main_frame)
        
        # Frame blending frame
        self._create_blending_frame(main_frame)
        
        # Control buttons
        self._create_controls(main_frame)
        
        # Status display
        self._create_status_display(main_frame)
        
        # Bind canvas resize to update scroll region
        self.main_canvas.bind('<Configure>', self._on_canvas_configure)
    
    def bind_mousewheel(self):
        """Bind mouse wheel events and keyboard shortcuts for scrolling"""
        def _on_mousewheel(event):
            # Handle both Windows and Linux mouse wheel events
            if event.delta:
                # Windows
                self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            else:
                # Linux
                if event.num == 4:
                    self.main_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.main_canvas.yview_scroll(1, "units")
        
        def _on_key_scroll(event):
            if event.keysym == 'Up':
                self.main_canvas.yview_scroll(-1, "units")
            elif event.keysym == 'Down':
                self.main_canvas.yview_scroll(1, "units")
            elif event.keysym == 'Page_Up':
                self.main_canvas.yview_scroll(-1, "pages")
            elif event.keysym == 'Page_Down':
                self.main_canvas.yview_scroll(1, "pages")
            elif event.keysym == 'Home':
                self.main_canvas.yview_moveto(0)
            elif event.keysym == 'End':
                self.main_canvas.yview_moveto(1)
        
        def _bind_to_mousewheel(event):
            # Bind both Windows and Linux mouse wheel events
            self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
            self.main_canvas.bind_all("<Button-4>", _on_mousewheel)    # Linux scroll up
            self.main_canvas.bind_all("<Button-5>", _on_mousewheel)    # Linux scroll down
        
        def _unbind_from_mousewheel(event):
            self.main_canvas.unbind_all("<MouseWheel>")
            self.main_canvas.unbind_all("<Button-4>")
            self.main_canvas.unbind_all("<Button-5>")
        
        # Bind mouse wheel when entering and unbind when leaving
        self.main_canvas.bind('<Enter>', _bind_to_mousewheel)
        self.main_canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        # Bind keyboard scrolling (always active)
        self.bind_all('<Key-Up>', _on_key_scroll)
        self.bind_all('<Key-Down>', _on_key_scroll)
        self.bind_all('<Key-Page_Up>', _on_key_scroll)
        self.bind_all('<Key-Page_Down>', _on_key_scroll)
        self.bind_all('<Key-Home>', _on_key_scroll)
        self.bind_all('<Key-End>', _on_key_scroll)
        
        # Make sure the canvas can receive focus for keyboard events
        self.main_canvas.focus_set()
    
    def _on_canvas_configure(self, event):
        """Handle canvas resize events"""
        # Update the canvas window width to match canvas width
        canvas_width = event.width
        self.main_canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _create_source_selection(self, parent):
        """Create input source selection widgets"""
        source_frame = ttk.LabelFrame(parent, text="Input Source")
        source_frame.pack(fill="x", pady=5)
        
        self.source_var = tk.StringVar(value="video")
        video_radio = ttk.Radiobutton(
            source_frame, text="Video File", 
            variable=self.source_var, value="video", 
            command=self.switch_source_view
        )
        video_radio.pack(side="left", padx=5)
        
        camera_radio = ttk.Radiobutton(
            source_frame, text="Live Camera", 
            variable=self.source_var, value="camera", 
            command=self.switch_source_view
        )
        camera_radio.pack(side="left", padx=5)
    
    def _create_gpu_status(self, parent):
        """Create GPU status indicator"""
        gpu_frame = ttk.LabelFrame(parent, text="Performance")
        gpu_frame.pack(fill="x", pady=5)
        
        if self.gpu_available:
            status_text = "✓ GPU Acceleration Enabled"
            status_color = "green"
        else:
            status_text = "! CPU Processing Mode"
            status_color = "orange"
        
        gpu_status_label = ttk.Label(
            gpu_frame, text=status_text, foreground=status_color
        )
        gpu_status_label.pack(side="left", padx=5)
        
        # Add performance tip
        if self.gpu_available:
            tip_text = "(Automatic GPU acceleration for large videos)"
        else:
            tip_text = "(Install CuPy for GPU acceleration)"
        
        tip_label = ttk.Label(
            gpu_frame, text=tip_text, foreground="gray"
        )
        tip_label.pack(side="right", padx=5)
    
    def _create_video_frame(self, parent):
        """Create video file selection widgets with preview"""
        self.file_frame = ttk.LabelFrame(parent, text="Video File")
        self.file_frame.pack(fill="x", pady=5)
        
        # File selection frame
        file_select_frame = ttk.Frame(self.file_frame)
        file_select_frame.pack(fill="x", pady=5)
        
        self.filepath_var = tk.StringVar()
        filepath_entry = ttk.Entry(
            file_select_frame, textvariable=self.filepath_var, width=60
        )
        filepath_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        browse_button = ttk.Button(
            file_select_frame, text="Browse", command=self.browse_file
        )
        browse_button.pack(side="left", padx=5)
        
        preview_button = ttk.Button(
            file_select_frame, text="Preview", command=self.preview_video
        )
        preview_button.pack(side="left", padx=5)
        
        # Video preview frame
        video_preview_frame = ttk.Frame(self.file_frame)
        video_preview_frame.pack(fill="both", expand=True, pady=5)
        
        # Video preview display
        self.video_preview_label = ttk.Label(
            video_preview_frame, 
            text="Video preview will appear here\\n(Select video file and click Preview)",
            background="black", foreground="white", anchor="center"
        )
        self.video_preview_label.pack(side="left", fill="both", expand=True, padx=5)
        
        # Video scan result display
        self.video_result_label = ttk.Label(
            video_preview_frame,
            text="Scan result will appear here\\n(Click 'Start Scan')",
            background="gray", foreground="white", anchor="center"
        )
        self.video_result_label.pack(side="right", fill="both", expand=True, padx=5)
    
    def _create_camera_frame(self, parent):
        """Create live camera widgets"""
        self.camera_frame = ttk.LabelFrame(parent, text="Live Camera")
        
        # Camera selection frame
        camera_select_frame = ttk.Frame(self.camera_frame)
        camera_select_frame.pack(fill="x", pady=5)
        
        ttk.Label(camera_select_frame, text="Camera Index:").pack(side="left", padx=5)
        self.camera_index_var = tk.StringVar(value="0")
        camera_index_entry = ttk.Entry(
            camera_select_frame, textvariable=self.camera_index_var, width=5
        )
        camera_index_entry.pack(side="left", padx=5)
        
        ttk.Label(camera_select_frame, text="(0=default, 1=USB, 2=external...)").pack(side="left", padx=5)
        
        # Camera view frame
        camera_view_frame = ttk.Frame(self.camera_frame)
        camera_view_frame.pack(fill="both", expand=True)
        
        # Camera feed display
        self.camera_feed_label = ttk.Label(
            camera_view_frame, 
            text="Camera feed will appear here\\n(Click 'Start Camera')",
            background="black", foreground="white", anchor="center"
        )
        self.camera_feed_label.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Composite image display
        self.composite_image_label = ttk.Label(
            camera_view_frame,
            text="Line scan result\\n(Click 'Start Scan')",
            background="gray", foreground="white", anchor="center"
        )
        self.composite_image_label.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Camera controls
        camera_controls_frame = ttk.Frame(self.camera_frame)
        camera_controls_frame.pack(fill="x", pady=5)
        
        self.start_camera_button = ttk.Button(
            camera_controls_frame, text="Start Camera", 
            command=self.start_camera_thread
        )
        self.start_camera_button.pack(side="left", padx=5)
        
        self.stop_camera_button = ttk.Button(
            camera_controls_frame, text="Stop Camera", 
            command=self.stop_camera, state="disabled"
        )
        self.stop_camera_button.pack(side="left", padx=5)
    
    def _create_mode_selection(self, parent):
        """Create scan mode selection widgets"""
        mode_frame = ttk.LabelFrame(parent, text="Scan Mode")
        mode_frame.pack(fill="x", pady=5)
        
        self.mode_var = tk.StringVar(value="column")
        column_radio = ttk.Radiobutton(
            mode_frame, text="Column", variable=self.mode_var, value="column"
        )
        column_radio.pack(side="left", padx=5)
        
        width_radio = ttk.Radiobutton(
            mode_frame, text="Width", variable=self.mode_var, value="width"
        )
        width_radio.pack(side="left", padx=5)
    
    def _create_config_frame(self, parent):
        """Create configuration widgets"""
        config_frame = ttk.LabelFrame(parent, text="Configuration")
        config_frame.pack(fill="x", pady=5)
        
        # Width ROI setting
        width_roi_frame = ttk.Frame(config_frame)
        width_roi_frame.pack(fill="x", pady=2)
        
        width_roi_label = ttk.Label(width_roi_frame, text="Width ROI:")
        width_roi_label.pack(side="left", padx=5)
        
        self.width_roi_var = tk.StringVar(
            value=str(self.config_manager.get_int('DEFAULT', 'width_roi', 20))
        )
        width_roi_entry = ttk.Entry(
            width_roi_frame, textvariable=self.width_roi_var, width=10
        )
        width_roi_entry.pack(side="left", padx=5)
        
        # Debug visualization toggle
        debug_frame = ttk.Frame(config_frame)
        debug_frame.pack(fill="x", pady=2)
        
        self.debug_visualization_var = tk.BooleanVar(
            value=self.config_manager.get_boolean('DEFAULT', 'visualize', False)
        )
        debug_checkbox = ttk.Checkbutton(
            debug_frame, text="Enable Debug Visualization", 
            variable=self.debug_visualization_var
        )
        debug_checkbox.pack(side="left", padx=5)
    
    def _create_motion_frame(self, parent):
        """Create motion detection widgets"""
        motion_frame = ttk.LabelFrame(parent, text="Motion Detection")
        motion_frame.pack(fill="x", pady=5)
        
        # Motion detection toggle
        motion_enabled = self.config_manager.get_boolean('DEFAULT', 'motion_detection', True)
        self.motion_enabled_var = tk.BooleanVar(value=motion_enabled)
        
        motion_checkbox = ttk.Checkbutton(
            motion_frame, text="Enable Motion Detection", 
            variable=self.motion_enabled_var
        )
        motion_checkbox.pack(side="left", padx=5)
        
        # Motion sensitivity
        sensitivity_frame = ttk.Frame(motion_frame)
        sensitivity_frame.pack(side="left", padx=20)
        
        sensitivity_label = ttk.Label(sensitivity_frame, text="Sensitivity:")
        sensitivity_label.pack(side="left", padx=5)
        
        sensitivity_default = str(self.config_manager.get_int('DEFAULT', 'motion_sensitivity', 1000))
        self.motion_sensitivity_var = tk.StringVar(value=sensitivity_default)
        
        sensitivity_entry = ttk.Entry(
            sensitivity_frame, textvariable=self.motion_sensitivity_var, width=8
        )
        sensitivity_entry.pack(side="left", padx=5)
        
        # Motion status
        self.motion_status_label = ttk.Label(
            motion_frame, text="Motion: Not Active", foreground="gray"
        )
        self.motion_status_label.pack(side="right", padx=5)
    
    def _create_blending_frame(self, parent):
        """Create frame blending widgets"""
        blending_frame = ttk.LabelFrame(parent, text="Frame Blending")
        blending_frame.pack(fill="x", pady=5)
        
        # Blending toggle
        blending_enabled = self.config_manager.get_boolean('DEFAULT', 'frame_blending', True)
        self.blending_enabled_var = tk.BooleanVar(value=blending_enabled)
        
        blending_checkbox = ttk.Checkbutton(
            blending_frame, text="Enable Frame Blending", 
            variable=self.blending_enabled_var
        )
        blending_checkbox.pack(side="left", padx=5)
        
        # Blend strength
        blend_frame = ttk.Frame(blending_frame)
        blend_frame.pack(side="left", padx=20)
        
        blend_label = ttk.Label(blend_frame, text="Blend Strength:")
        blend_label.pack(side="left", padx=5)
        
        blend_default = str(self.config_manager.get_float('DEFAULT', 'blend_strength', 0.3))
        self.blend_strength_var = tk.StringVar(value=blend_default)
        
        blend_entry = ttk.Entry(
            blend_frame, textvariable=self.blend_strength_var, width=8
        )
        blend_entry.pack(side="left", padx=5)
        
        # Info label
        blend_info_label = ttk.Label(
            blending_frame, text="(0.1=subtle, 0.5=strong)", foreground="gray"
        )
        blend_info_label.pack(side="right", padx=5)
    
    def _create_controls(self, parent):
        """Create control buttons"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill="x", pady=10)
        
        self.start_button = ttk.Button(
            control_frame, text="Start Scan", command=self.start_scan_thread
        )
        self.start_button.pack(side="right", padx=5)
        
        self.stop_scan_button = ttk.Button(
            control_frame, text="Stop Scan", command=self.stop_scan, state="disabled"
        )
        self.stop_scan_button.pack(side="right", padx=5)
        
        self.reset_button = ttk.Button(
            control_frame, text="Reset / New Scan", command=self.reset_scan
        )
        self.reset_button.pack(side="right", padx=5)
    
    def _create_status_display(self, parent):
        """Create status display area"""
        status_frame = ttk.LabelFrame(parent, text="Status")
        status_frame.pack(fill="both", expand=True, pady=5)
        
        self.status_text = tk.Text(status_frame, height=5, wrap="word")
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Redirect stdout to status display
        sys.stdout = TextRedirector(self.status_text)
    
    def browse_file(self):
        """Open file dialog to select video file"""
        filepath = filedialog.askopenfilename(
            title="Select a video file",
            filetypes=(
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            )
        )
        if filepath:
            self.filepath_var.set(filepath)
    
    def preview_video(self):
        """Preview the selected video file"""
        video_path = self.filepath_var.get()
        if not video_path or not os.path.exists(video_path):
            print("Please select a valid video file first.")
            return
        
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error: Could not open video file {video_path}")
                return
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            # Read a sample frame (middle of video)
            frame_pos = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            
            if ret:
                # Display frame info
                print(f"Video: {os.path.basename(video_path)}")
                print(f"Resolution: {frame.shape[1]}x{frame.shape[0]}")
                print(f"Frames: {total_frames}, FPS: {fps:.1f}, Duration: {duration:.1f}s")
                
                # Show preview with scan line overlay
                height, width = frame.shape[:2]
                scan_mode = self.mode_var.get()
                
                if scan_mode == "width":
                    # Draw width ROI rectangle
                    roi_width = int(self.width_roi_var.get())
                    center_x = width // 2
                    start_x = max(0, center_x - roi_width // 2)
                    end_x = min(width, center_x + roi_width // 2)
                    cv2.rectangle(frame, (start_x, 0), (end_x, height), (0, 255, 0), 2)
                    cv2.putText(frame, f"Width ROI: {roi_width}px", (start_x, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    # Draw column line
                    center_x = width // 2
                    cv2.line(frame, (center_x, 0), (center_x, height), (0, 255, 0), 2)
                    cv2.putText(frame, "Column Line", (center_x + 10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Convert and display
                preview_img = self.convert_frame_to_tkinter(frame)
                if preview_img:
                    self.video_preview_label.configure(image=preview_img, text="")
                    self.video_preview_label.image = preview_img
            
            cap.release()
            
        except Exception as e:
            print(f"Error previewing video: {e}")
    
    def switch_source_view(self):
        """Switch between video file and camera input views"""
        if self.source_var.get() == "video":
            self.camera_frame.pack_forget()
            self.file_frame.pack(fill="x", pady=5)
            self.start_button.config(text="Start Scan")
            self.stop_scan_button.config(state="disabled")
        else:
            self.file_frame.pack_forget()
            self.camera_frame.pack(fill="both", expand=True, pady=5)
            self.start_button.config(text="Start Scan", state="disabled")
            self.stop_scan_button.config(state="disabled")
    
    def start_scan_thread(self):
        """Start scanning in a separate thread"""
        if self.source_var.get() == 'video':
            self.start_button.config(state="disabled")
            self.status_text.delete(1.0, tk.END)
            scan_thread = threading.Thread(target=self.start_video_scan)
            scan_thread.daemon = True
            scan_thread.start()
        else:
            self.start_camera_scan()
    
    def start_video_scan(self):
        """Process video file with preview updates"""
        try:
            video_path = self.filepath_var.get()
            scan_mode = self.mode_var.get()
            
            if not video_path:
                print("Please select a video file.")
                return
            
            print(f"Starting scan with mode: {scan_mode}\\n")
            
            # Update configuration with debug visualization setting
            self._update_config()
            
            # Enable debug visualization if user selected it
            debug_viz = self.debug_visualization_var.get()
            self.config_manager.config.set('DEFAULT', 'visualize', str(debug_viz))
            self.config_manager.config.set('DEBUG', 'visualize', str(debug_viz))
            self.config_manager.config.set('THRESH', 'visualize', str(debug_viz))
            self.config_manager.config.set('CONTOUR', 'visualize', str(debug_viz))
            self.config_manager.config.set('STITCH', 'visualize', str(debug_viz))
            
            # Run scanner
            success = run_scanner(video_path, scan_mode)
            
            if success:
                print("\\nScan finished successfully.")
                print("Click 'Reset / New Scan' to perform another scan.")
                
                # Show result in preview pane
                self._show_scan_result(video_path, scan_mode)
            else:
                print("\\nScan failed.")
                print("Click 'Reset / New Scan' to try again.")
        
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.start_button.config(state="normal")
    
    def _show_scan_result(self, video_path, scan_mode):
        """Show the scan result in the video result preview pane"""
        try:
            result_dir = os.path.join(os.getcwd(), "RESULT")
            video_name = os.path.basename(os.path.splitext(video_path)[0])
            
            if scan_mode == "column":
                result_file = os.path.join(result_dir, f"{video_name}-ColumnROi.jpg")
            else:
                result_file = os.path.join(result_dir, f"{video_name}-WidthROi.jpg")
            
            if os.path.exists(result_file):
                # Load and display result
                result_image = cv2.imread(result_file)
                if result_image is not None:
                    result_img_tk = self.convert_frame_to_tkinter(result_image)
                    if result_img_tk:
                        self.video_result_label.configure(image=result_img_tk, text="")
                        self.video_result_label.image = result_img_tk
                        print(f"Result displayed in preview pane")
                else:
                    print(f"Could not load result image: {result_file}")
            else:
                print(f"Result file not found: {result_file}")
                
        except Exception as e:
            print(f"Error showing scan result: {e}")
    
    def start_camera_scan(self):
        """Start live camera scanning"""
        self.scanning = True
        self.start_button.config(state="disabled")
        self.stop_scan_button.config(state="normal")
        self.composite_image = None
        
        # Reset motion detection
        self.previous_frame = None
        self.frames_since_motion = 0
        
        # Reset blending state
        self.previous_scan_region = None
        
        # Print scan configuration
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
        
        blending_enabled = self.blending_enabled_var.get()
        if blending_enabled:
            blend_strength = self.blend_strength_var.get()
            print(f"Frame blending ENABLED (strength: {blend_strength})")
        else:
            print("Frame blending DISABLED - sharp transitions")
    
    def start_camera_thread(self):
        """Start camera in a separate thread"""
        self.start_camera_button.config(state="disabled")
        self.stop_camera_button.config(state="normal")
        self.start_button.config(state="normal")
        
        # Get camera index from user input
        try:
            camera_index = int(self.camera_index_var.get())
        except ValueError:
            print(f"Error: Invalid camera index '{self.camera_index_var.get()}'. Using default camera 0.")
            camera_index = 0
            self.camera_index_var.set("0")
        
        self.camera_scanner = CameraScanner(camera_index)
        
        if self.camera_scanner.start():
            self.camera_running = True
            self.show_camera_feed()
        else:
            print("Failed to start camera")
            self.stop_camera()
    
    def stop_camera(self):
        """Stop camera and cleanup"""
        self.camera_running = False
        if self.camera_scanner:
            self.camera_scanner.stop()
            self.camera_scanner = None
        
        self.start_camera_button.config(state="normal")
        self.stop_camera_button.config(state="disabled")
        self.start_button.config(state="disabled")
        
        # Clear displays
        self.camera_feed_label.configure(
            image="", text="Camera feed will appear here\\n(Click 'Start Camera')"
        )
        self.composite_image_label.configure(
            image="", text="Line scan result\\n(Click 'Start Scan')"
        )
        
        # Remove image references
        if hasattr(self.camera_feed_label, 'image'):
            del self.camera_feed_label.image
        if hasattr(self.composite_image_label, 'image'):
            del self.composite_image_label.image
        
        # Reset motion detection
        self.previous_frame = None
        self.motion_status_label.configure(text="Motion: Not Active", foreground="gray")
    
    def reset_scan(self):
        """Reset the scan interface for a new scan"""
        try:
            # Clear status text
            self.status_text.delete(1.0, tk.END)
            print("Scan interface reset. Ready for new scan.")
            
            # Reset video preview panes if they exist
            if hasattr(self, 'video_preview_label'):
                self.video_preview_label.configure(
                    image="", 
                    text="Video preview\\n(Click 'Preview' to load video)"
                )
                if hasattr(self.video_preview_label, 'image'):
                    delattr(self.video_preview_label, 'image')
            
            if hasattr(self, 'video_result_label'):
                self.video_result_label.configure(
                    image="", 
                    text="Scan result\\n(Will appear after scanning)"
                )
                if hasattr(self.video_result_label, 'image'):
                    delattr(self.video_result_label, 'image')
            
            # Reset camera displays if in camera mode
            if self.source_var.get() == "camera":
                self.composite_image_label.configure(
                    image="", text="Line scan result\\n(Click 'Start Scan')"
                )
                if hasattr(self.composite_image_label, 'image'):
                    delattr(self.composite_image_label, 'image')
                
                # Reset composite image
                self.composite_image = None
                self.previous_scan_region = None
            
            # Reset button states
            self.start_button.config(state="normal")
            self.stop_scan_button.config(state="disabled")
            
            # Reset motion detection
            self.previous_frame = None
            self.frames_since_motion = 0
            self.motion_status_label.configure(text="Motion: Not Active", foreground="gray")
            
            # Reset any running scan flags
            self.scanning = False
            
            print("Ready to start a new scan!")
            
        except Exception as e:
            print(f"Error during reset: {e}")
    
    def detect_motion(self, current_frame, scan_mode=None, scan_line_x=None, width_roi=None):
        """Detect motion in the scanning region"""
        if not self.motion_enabled_var.get():
            return True
        
        # Get scanning parameters
        if scan_mode is None:
            scan_mode = self.mode_var.get()
        if scan_line_x is None:
            scan_line_x = current_frame.shape[1] // 2
        if width_roi is None:
            width_roi = int(self.width_roi_var.get())
        
        # Extract scanning region
        height = current_frame.shape[0]
        if scan_mode == "width":
            start_x = max(0, scan_line_x - width_roi // 2)
            end_x = min(current_frame.shape[1], scan_line_x + width_roi // 2)
            scan_region = current_frame[:, start_x:end_x]
        else:
            buffer = 2
            start_x = max(0, scan_line_x - buffer)
            end_x = min(current_frame.shape[1], scan_line_x + buffer + 1)
            scan_region = current_frame[:, start_x:end_x]
        
        if self.previous_frame is None:
            self.previous_frame = cv2.cvtColor(scan_region, cv2.COLOR_BGR2GRAY)
            return True
        
        # Calculate motion
        current_gray = cv2.cvtColor(scan_region, cv2.COLOR_BGR2GRAY)
        frame_diff = cv2.absdiff(self.previous_frame, current_gray)
        _, thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)
        motion_amount = cv2.countNonZero(thresh)
        
        self.previous_frame = current_gray.copy()
        
        # Check motion threshold
        threshold = int(self.motion_sensitivity_var.get())
        has_motion = motion_amount > threshold
        
        # Update status
        region_info = f"{scan_region.shape[1]}px" if scan_mode == "width" else "line"
        
        if has_motion:
            self.motion_status_label.configure(
                text=f"Motion: DETECTED ({motion_amount}) in {region_info}", 
                foreground="green"
            )
            self.frames_since_motion = 0
        else:
            self.frames_since_motion += 1
            self.motion_status_label.configure(
                text=f"Motion: No Change ({motion_amount}) in {region_info}", 
                foreground="orange"
            )
        
        return has_motion
    
    def blend_frames(self, current_region, previous_region, blend_strength):
        """Blend current scan region with previous region"""
        if previous_region is None or not self.blending_enabled_var.get():
            return current_region
        
        if current_region.shape != previous_region.shape:
            return current_region
        
        try:
            current_float = current_region.astype(np.float64)
            previous_float = previous_region.astype(np.float64)
            
            strength = float(blend_strength)
            strength = max(0.0, min(1.0, strength))
            
            blended = (1.0 - strength) * current_float + strength * previous_float
            return blended.astype(np.uint8)
        
        except Exception as e:
            print(f"Blending error: {e}")
            return current_region
    
    def show_camera_feed(self):
        """Update camera feed display"""
        if not self.camera_running or not self.camera_scanner:
            return
        
        try:
            frame = self.camera_scanner.get_frame()
            if frame is not None:
                height, width, _ = frame.shape
                scan_line_x = width // 2
                width_roi = int(self.width_roi_var.get())
                scan_mode = self.mode_var.get()
                
                # Handle scanning
                if self.scanning:
                    has_motion = self.detect_motion(frame, scan_mode, scan_line_x, width_roi)
                    
                    if has_motion:
                        if scan_mode == "width":
                            start_x = max(0, scan_line_x - width_roi // 2)
                            end_x = min(width, scan_line_x + width_roi // 2)
                            scan_region = frame[:, start_x:end_x]
                        else:
                            scan_region = frame[:, scan_line_x:scan_line_x+1]
                        
                        # Apply blending
                        if self.blending_enabled_var.get():
                            blend_strength = float(self.blend_strength_var.get())
                            scan_region = self.blend_frames(
                                scan_region, self.previous_scan_region, blend_strength
                            )
                            self.previous_scan_region = scan_region.copy()
                        
                        # Update composite image
                        if self.composite_image is None:
                            self.composite_image = scan_region
                        else:
                            self.composite_image = np.hstack((self.composite_image, scan_region))
                        
                        # Display composite
                        if self.composite_image.shape[1] > 0:
                            composite_img_tk = self.convert_frame_to_tkinter(self.composite_image)
                            if composite_img_tk:
                                self.composite_image_label.configure(image=composite_img_tk, text="")
                                self.composite_image_label.image = composite_img_tk
                
                # Draw scan visualization
                if scan_mode == "width":
                    start_x = max(0, scan_line_x - width_roi // 2)
                    end_x = min(width, scan_line_x + width_roi // 2)
                    cv2.rectangle(frame, (start_x, 0), (end_x, height), (0, 255, 0), 2)
                else:
                    cv2.line(frame, (scan_line_x, 0), (scan_line_x, height), (0, 255, 0), 2)
                
                # Display camera feed
                imgtk = self.convert_frame_to_tkinter(frame)
                if imgtk:
                    self.camera_feed_label.configure(image=imgtk, text="")
                    self.camera_feed_label.image = imgtk
                
                # Schedule next update
                self.after(33, self.show_camera_feed)  # ~30 FPS
            else:
                print("No frame received from camera")
                self.stop_camera()
                
        except Exception as e:
            print(f"Error in camera feed: {e}")
            self.stop_camera()
    
    def convert_frame_to_tkinter(self, frame):
        """Convert OpenCV frame to tkinter PhotoImage"""
        try:
            # Convert BGR to RGB
            if len(frame.shape) == 3:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = frame
            
            # Resize if needed
            height, width = rgb_image.shape[:2]
            max_width, max_height = 400, 300
            
            if width > max_width or height > max_height:
                scale = min(max_width/width, max_height/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                rgb_image = cv2.resize(rgb_image, (new_width, new_height))
            
            # Convert to PhotoImage
            img = Image.fromarray(rgb_image)
            imgtk = ImageTk.PhotoImage(image=img)
            return imgtk
            
        except Exception as e:
            print(f"Error converting frame: {e}")
            return None
    
    def stop_scan(self):
        """Stop scanning and save result"""
        self.scanning = False
        self.start_button.config(state="normal")
        self.stop_scan_button.config(state="disabled")
        
        if self.composite_image is not None:
            # Create output directory
            result_dir = os.path.join(os.getcwd(), "RESULT")
            os.makedirs(result_dir, exist_ok=True)
            
            # Save image
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"linescan_{timestamp}.jpg"
            save_path = os.path.join(result_dir, filename)
            cv2.imwrite(save_path, self.composite_image)
            print(f"Scan saved to {save_path}")
    
    def _update_config(self):
        """Update configuration with current GUI values"""
        try:
            # Update width ROI
            width_roi = int(self.width_roi_var.get())
            self.config_manager.config.set('DEFAULT', 'width_roi', str(width_roi))
            
            # Update motion detection settings
            motion_enabled = self.motion_enabled_var.get()
            self.config_manager.config.set('DEFAULT', 'motion_detection', str(motion_enabled))
            
            if hasattr(self, 'motion_sensitivity_var'):
                sensitivity = self.motion_sensitivity_var.get()
                self.config_manager.config.set('DEFAULT', 'motion_sensitivity', str(sensitivity))
            
            # Update frame blending settings  
            if hasattr(self, 'blending_enabled_var'):
                blending_enabled = self.blending_enabled_var.get()
                self.config_manager.config.set('DEFAULT', 'frame_blending', str(blending_enabled))
                
                if hasattr(self, 'blend_strength_var'):
                    blend_strength = self.blend_strength_var.get()
                    self.config_manager.config.set('DEFAULT', 'blend_strength', str(blend_strength))
                    
        except ValueError as e:
            print(f"Configuration update error: {e}")
        except Exception as e:
            print(f"Unexpected configuration error: {e}")


# Legacy compatibility
App = LineScanGUI


def main():
    """Run the GUI application"""
    app = LineScanGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
