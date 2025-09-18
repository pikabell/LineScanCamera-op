#!/usr/bin/env python3
"""
Line Scanner Module

This module contains the LineScanner class which implements the core
line scan camera functionality for both column and width scan modes.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

try:
    import progressbar
except ImportError:
    import progressbar2 as progressbar

# System-specific OpenCV path handling
from sys import platform
if platform == "linux" or platform == "linux2":
    sys.path.append("/opt/opencv-4.1.2/build/lib/python3")
elif platform == "win32":
    sys.path.append("C:/Users/Daniel/Desktop/opencv/opencv-4.1.2/build/lib/python3")

import cv2

from .image_metadata import ImageMetadata
from ..utils.config_manager import get_config


class LineScanner:
    """
    Implementation of a LineScan Camera from an Area Scan Camera using OpenCV.
    
    This class provides two scan modes:
    1. Column mode: Accumulates a column of pixels from each frame
    2. Width mode: Accumulates the region of interest from each frame
    
    Attributes:
        filename (str): Input video filename
        mode (str): Scan mode (column/width)
        input_dir (str): Input directory path
        output_dir (str): Output directory path
        totalFrames (int): Number of frames in the video
        list_of_Frames (list): List of ImageMetadata objects for width mode
        config (ConfigManager): Configuration manager instance
    """
    
    def __init__(self):
        """Initialize LineScanner with default values"""
        self.filename = ""
        self.mode = ""
        self.input_dir = ""
        self.output_dir = ""
        self.totalFrames = 0
        self.list_of_Frames = []
        self.config = get_config()
    
    def __str__(self):
        """String representation of the LineScanner object"""
        return f"{self.__class__.__name__}: {self.__dict__}"
    
    def width_scan_mode(self, video_obj):
        """
        Process video in width scan mode
        
        Args:
            video_obj (cv2.VideoCapture): OpenCV video capture object
        """
        # Create progress bar
        bar = progressbar.ProgressBar(
            max_value=self.totalFrames,
            redirect_stdout=True,
            prefix='-> Processing video: '
        ).start()
        
        # Setup matplotlib figure if visualization is enabled
        fig = None
        if self.config.get_boolean('DEFAULT', 'visualize'):
            try:
                fig = plt.gcf()
                # Try to set window title - handle different backends gracefully
                if hasattr(fig.canvas, 'set_window_title'):
                    fig.canvas.set_window_title('Video')
                elif hasattr(fig.canvas, 'manager') and hasattr(fig.canvas.manager, 'set_window_title'):
                    fig.canvas.manager.set_window_title('Video')
            except Exception as e:
                print(f"Note: Could not set figure title: {e}")
                # Continue without error
        
        # Initialize centroid reference for ROI
        centroid = {'x': 0, 'y': 0}
        
        # Video reading status
        success = True
        count = 0
        
        # Main scanner loop
        while success:
            self._debug_print(f"[DEBUG] frame {count}")
            
            # Create image metadata object
            image_metadata = ImageMetadata()
            
            # Read frame from video
            success, image = video_obj.read()
            
            # Validate frame
            if not self._validate_frame(image, success, count):
                continue
            
            # Rotate image 90 degrees counterclockwise
            image_rot = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            # Get image dimensions
            rows, cols = image_rot.shape[:2]
            image_metadata.set_shape(cols, rows)
            
            # Compute centroid on first frame
            if count == 0:
                boundingBoxMetadata = self.compute_object_coordinates(image_rot)
                centroid['x'] = boundingBoxMetadata['cx']
                centroid['y'] = boundingBoxMetadata['cy']
            
            # Extract ROI based on centroid
            roi_width = self.config.get_int('DEFAULT', 'width_roi', 3)
            roi = image_rot[0:rows, int(centroid['x']):int(centroid['x'] + roi_width)].copy()
            image_metadata.set_roi(roi)
            
            # Save image metadata
            self.list_of_Frames.append(image_metadata)
            
            # Visualize if enabled
            if self.config.get_boolean('DEFAULT', 'visualize'):
                self._visualize_frame(image_rot, count, fig)
            
            count += 1
            bar.update(count)
            self._debug_print("done.")
        
        # Cleanup
        if self.config.get_boolean('DEFAULT', 'visualize'):
            plt.close('all')
        bar.finish()
    
    def column_scan_mode(self, video_obj):
        """
        Process video in column scan mode
        
        Args:
            video_obj (cv2.VideoCapture): OpenCV video capture object
        """
        # Create progress bar
        bar = progressbar.ProgressBar(
            max_value=self.totalFrames,
            redirect_stdout=True,
            prefix='-> Processing video: '
        ).start()
        
        # Setup matplotlib figure if visualization is enabled
        fig = None
        if self.config.get_boolean('DEFAULT', 'visualize'):
            try:
                fig = plt.figure()
                # Try to set window title - handle different backends gracefully
                if hasattr(fig.canvas, 'set_window_title'):
                    fig.canvas.set_window_title('Video')
                elif hasattr(fig.canvas, 'manager'):
                    fig.canvas.manager.set_window_title('Video')
            except Exception as e:
                print(f"Note: Could not set figure title: {e}")
                # Continue without visualization to avoid blocking
                self.config.set('DEFAULT', 'visualize', 'false')
        
        # Initialize centroid reference
        centroid = {'x': 0, 'y': 0}
        
        # Video reading status
        success = True
        count = 0
        
        # Get video dimensions
        video_height = int(video_obj.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video_width = int(video_obj.get(cv2.CAP_PROP_FRAME_WIDTH))
        
        # Initialize flat image for column ROI
        flatImage = np.empty((video_height, self.totalFrames, 3), np.uint8)
        
        # Main scanner loop
        while success:
            self._debug_print(f"[DEBUG] frame {count}")
            
            # Read frame from video
            success, image = video_obj.read()
            
            # Validate frame
            if not self._validate_frame(image, success, count):
                continue
            
            # Use image as-is (no rotation for column mode)
            image_rot = image
            
            # Compute centroid on first frame
            if count == 0:
                boundingBoxMetadata = self.compute_object_coordinates(image_rot)
                centroid['x'] = boundingBoxMetadata['cx']
                centroid['y'] = boundingBoxMetadata['cy']
            
            # Update video dimensions
            rows, cols = image_rot.shape[:2]
            video_height = rows
            video_width = cols
            
            # Extract column ROI
            column_roi = image_rot[:, int(centroid['x'])].copy()
            flatImage[:, count] = column_roi
            
            # Draw line on image for visualization
            if self.config.get_boolean('DEFAULT', 'visualize'):
                start_point = (int(centroid['x']), 0)
                end_point = (int(centroid['x']), video_height)
                color = (255, 0, 0)  # Blue line in BGR
                thickness = 15
                image_with_line = cv2.line(image_rot, start_point, end_point, color, thickness)
                self._visualize_frame(image_with_line, count)
            
            count += 1
            bar.update(count)
            self._debug_print("done.")
        
        # Cleanup
        cv2.destroyAllWindows()
        if self.config.get_boolean('DEFAULT', 'visualize'):
            plt.close('all')
        bar.finish()
        
        # Resize and save result
        dsize = (video_width, video_height)
        flatImage = cv2.resize(flatImage, dsize)
        
        output_path = os.path.join(self.output_dir, f"{self.filename}-ColumnROi.jpg")
        cv2.imwrite(output_path, flatImage)
        print(f"Column scan result saved to: {output_path}")
    
    def concatenate_frames(self):
        """
        Concatenate frames for width scan mode to create the final stitched image
        """
        if not self.list_of_Frames:
            print("No frames to concatenate!")
            return False
        
        # Get video dimensions from first frame
        video_height = self.list_of_Frames[0].get_shape()['height']
        video_width = self.list_of_Frames[0].get_shape()['width']
        
        # Initialize flat image for column visualization
        flatImage = np.empty((video_height, len(self.list_of_Frames), 3), np.uint8)
        
        self._debug_print("Concatenating frames...")
        
        # Create progress bar
        bar = progressbar.ProgressBar(
            max_value=len(self.list_of_Frames),
            redirect_stdout=True,
            prefix='-> Concatenating frames: '
        ).start()
        
        # Initialize result for width concatenation
        result = []
        
        # Process each frame
        for n, frame_metadata in enumerate(self.list_of_Frames):
            # Get current ROI
            image1 = frame_metadata.get_roi()
            
            # Extract column for flat image visualization
            col_roi = image1[:, int(image1.shape[1] / 2)].copy()
            flatImage[:, n] = col_roi
            
            # Concatenate ROIs horizontally
            if n + 1 < len(self.list_of_Frames):
                image2 = self.list_of_Frames[n + 1].get_roi()
                
                self._debug_print(f"[DEBUG] frame {n}-{n + 1}")
                
                if n > 0:
                    # Concatenate with existing result
                    result = np.concatenate((result, image2), axis=1)
                else:
                    # First concatenation
                    result = np.concatenate((image1, image2), axis=1)
            
            bar.update(n)
        
        bar.finish()
        
        # Resize and save result
        dsize = (video_width, video_height)
        result = cv2.resize(result, dsize)
        
        output_path = os.path.join(self.output_dir, f"{self.filename}-WidthROi.jpg")
        cv2.imwrite(output_path, result)
        
        # Visualize results if enabled
        if self.config.get_boolean('STITCH', 'visualize'):
            self._visualize_stitched_results(flatImage, result)
        
        print(f"-> Output saved in: {self.output_dir}")
        return True
    
    def compute_object_coordinates(self, image):
        """
        Calculate the image coordinates of the object in an input image
        
        Args:
            image (numpy.ndarray): Input BGR image
            
        Returns:
            dict: Dictionary containing object coordinates {x, y, w, h, cx, cy}
        """
        self._debug_print("Computing object coordinates...")
        
        # Convert to grayscale
        image_gray = self._bgr_to_gray(image)
        
        # Apply Gaussian blur to remove noise
        image_blur = cv2.GaussianBlur(image_gray, (17, 17), 0)
        
        # Apply adaptive threshold
        thresh = cv2.adaptiveThreshold(
            image_blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 7, 2
        )
        
        # Morphological operations to clean up the image
        kernel = np.ones((7, 7), np.uint8)
        thresh_open = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=20)
        thresh_close = cv2.morphologyEx(thresh_open, cv2.MORPH_CLOSE, kernel, iterations=30)
        
        # Visualize threshold process if enabled
        if self.config.get_boolean('THRESH', 'visualize'):
            self._visualize_threshold_process(image_gray, thresh, thresh_open, thresh_close)
        
        # Further morphological operations
        thresh_eroded = cv2.erode(thresh_close, kernel, iterations=6)
        thresh_dilated = cv2.dilate(thresh_eroded, None, iterations=2)
        thresh_edges = cv2.Canny(thresh_dilated, 30, 200)
        
        # Visualize morphology operations if enabled
        if self.config.get_boolean('THRESH', 'visualize'):
            self._visualize_morphology_operations(thresh_eroded, thresh_dilated, thresh_edges)
        
        # Find contours
        contours, hierarchy = cv2.findContours(thresh_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        self._debug_print(f"Total contours found: {len(contours)}")
        
        # Sort contours by area (largest first)
        contours_sorted = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
        
        # Initialize bounding box metadata
        bbox_metadata = {'x': 0, 'y': 0, 'h': 0, 'w': 0, 'cx': 0, 'cy': 0, 'angle': 0}
        
        # Process the largest contour
        for contour in contours_sorted:
            area = cv2.contourArea(contour)
            if area == 0:
                continue
            
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate centroid using moments
            moments = cv2.moments(contour)
            if moments['m00'] != 0:
                cx = int(moments['m10'] / moments['m00'])
                cy = int(moments['m01'] / moments['m00'])
            else:
                cx, cy = x + w//2, y + h//2
            
            # Update bounding box metadata
            bbox_metadata.update({
                'x': x, 'y': y, 'w': w, 'h': h, 'cx': cx, 'cy': cy
            })
            
            self._debug_print(f"Bounding box: x={x}, y={y}, w={w}, h={h}")
            self._debug_print(f"Centroid: cx={cx}, cy={cy}")
            
            break
        
        # Visualize contour detection if enabled
        if self.config.get_boolean('CONTOUR', 'visualize'):
            self._visualize_contour_detection(image, contours, bbox_metadata)
        
        return bbox_metadata
    
    def _bgr_to_gray(self, image):
        """Convert BGR image to grayscale"""
        if len(image.shape) < 3:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    def _validate_frame(self, image, success, count):
        """Validate frame quality and log issues"""
        if not success:
            self._debug_print(f"[DEBUG] bad frame at {count}!")
            return False
        
        if image is None:
            self._debug_print(f"[DEBUG] empty frame at {count}!")
            return False
        
        if np.sum(image) == 0:
            self._debug_print(f"[DEBUG] black frame at {count}!")
            return False
        
        return True
    
    def _visualize_frame(self, image, count, fig=None):
        """Visualize current frame"""
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        if count > 0 and fig is not None:
            fig.set_data(image_rgb)
            plt.title(f"frame {count}")
            plt.draw()
            plt.pause(0.001)
        else:
            fig = plt.imshow(image_rgb)
            plt.title(f"frame {count}")
            plt.draw()
            plt.pause(0.001)
    
    def _visualize_threshold_process(self, original, thresh, thresh_open, thresh_close):
        """Visualize threshold processing steps"""
        plt.figure(figsize=(16, 4))
        plt.suptitle("Binary threshold")
        
        plt.subplot(1, 4, 1)
        plt.title("Original")
        plt.imshow(original, cmap='gray')
        
        plt.subplot(1, 4, 2)
        plt.title("Threshold")
        plt.imshow(thresh, cmap='gray')
        
        plt.subplot(1, 4, 3)
        plt.title("Threshold Open")
        plt.imshow(thresh_open, cmap='gray')
        
        plt.subplot(1, 4, 4)
        plt.title("Threshold Close")
        plt.imshow(thresh_close, cmap='gray')
        
        plt.show()
    
    def _visualize_morphology_operations(self, eroded, dilated, edges):
        """Visualize morphological operations"""
        plt.figure(figsize=(12, 4))
        plt.suptitle("Morphology operations")
        
        plt.subplot(1, 3, 1)
        plt.title("Eroded")
        plt.imshow(eroded, cmap='gray')
        
        plt.subplot(1, 3, 2)
        plt.title("Dilated")
        plt.imshow(dilated, cmap='gray')
        
        plt.subplot(1, 3, 3)
        plt.title("Edges")
        plt.imshow(edges, cmap='gray')
        
        plt.show()
    
    def _visualize_contour_detection(self, image, contours, bbox_metadata):
        """Visualize contour detection results"""
        plt.figure(figsize=(12, 6))
        plt.suptitle("Detected contours")
        
        # Convert BGR to RGB for matplotlib
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Show all contours
        image_contours = image_rgb.copy()
        cv2.drawContours(image_contours, contours, -1, (0, 255, 0), 3, cv2.LINE_AA)
        
        plt.subplot(1, 2, 1)
        plt.title('All Contours')
        plt.imshow(image_contours)
        
        # Show final bounding box
        image_bbox = image_rgb.copy()
        cv2.rectangle(image_bbox, 
                     (bbox_metadata['x'], bbox_metadata['y']),
                     (bbox_metadata['x'] + bbox_metadata['w'], 
                      bbox_metadata['y'] + bbox_metadata['h']),
                     (255, 0, 0), 3)
        
        plt.subplot(1, 2, 2)
        plt.title("Final Bounding Box")
        plt.imshow(image_bbox)
        
        plt.show()
    
    def _visualize_stitched_results(self, flat_image, width_result):
        """Visualize final stitched results"""
        plt.figure(figsize=(12, 6))
        plt.suptitle("Stitched image")
        
        # Convert BGR to RGB for matplotlib
        flat_rgb = cv2.cvtColor(flat_image, cv2.COLOR_BGR2RGB)
        width_rgb = cv2.cvtColor(width_result, cv2.COLOR_BGR2RGB)
        
        plt.subplot(1, 2, 1)
        plt.title("Column ROI mode")
        plt.imshow(flat_rgb)
        
        plt.subplot(1, 2, 2)
        plt.title("Width ROI mode")
        plt.imshow(width_rgb)
        
        plt.show()
    
    def _debug_print(self, message):
        """Print debug message if debug visualization is enabled"""
        if self.config.get_boolean('DEBUG', 'visualize'):
            print(message)
