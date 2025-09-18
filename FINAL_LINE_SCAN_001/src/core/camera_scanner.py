#!/usr/bin/env python3
"""
Camera Scanner Module

This module contains the CameraScanner class for handling live camera input
for line scan camera operations.
"""

import cv2


class CameraScanner:
    """
    A class to handle live camera input for line scan camera operations
    
    Attributes:
        cap (cv2.VideoCapture): OpenCV video capture object
        is_running (bool): Flag to indicate if camera is running
        camera_index (int): Camera index to use
    """
    
    def __init__(self, camera_index=0):
        """
        Initialize CameraScanner with specified camera index
        
        Args:
            camera_index (int): Camera index (0 for default, 1, 2... for additional cameras)
        """
        self.cap = None
        self.is_running = False
        self.camera_index = camera_index
    
    def start(self):
        """
        Start the camera capture
        
        Returns:
            bool: True if camera started successfully, False otherwise
        """
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                print(f"Error: Could not open camera {self.camera_index}.")
                return False
            
            # Set basic camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Minimal settings to avoid color distortion
            try:
                # Enable auto exposure for natural colors
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
                print(f"Camera {self.camera_index} initialized with natural color settings")
            except Exception as e:
                print(f"Note: Using default camera settings: {e}")
            
        self.is_running = True
        
        # Capture a few frames to let camera settle
        for _ in range(3):
            ret, frame = self.cap.read()
            if ret:
                break
        
        return True
    
    def get_frame(self):
        """
        Get a single frame from the camera
        
        Returns:
            numpy.ndarray or None: Frame from camera if successful, None otherwise
        """
        if self.cap is None or not self.is_running:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            print("Error: Can't receive frame (stream end?).")
            return None
        
        return frame
    
    def stop(self):
        """Stop the camera capture and release resources"""
        self.is_running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def __del__(self):
        """Destructor to ensure camera resources are released"""
        self.stop()


def run_camera_scanner():
    """
    Legacy function for compatibility with existing code
    
    Yields:
        numpy.ndarray: Frames from the camera
    """
    scanner = CameraScanner()
    if not scanner.start():
        return
    
    try:
        while scanner.is_running:
            frame = scanner.get_frame()
            if frame is not None:
                yield frame
            else:
                break
    finally:
        scanner.stop()
