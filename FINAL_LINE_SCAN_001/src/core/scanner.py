#!/usr/bin/env python3
"""
Scanner Function Module

This module contains the main scanner functionality that ties together
the LineScanner class with video processing.
"""

import os
import sys
import cv2

from .line_scanner import LineScanner
from ..utils.config_manager import get_config


def run_scanner(video_path, scan_mode):
    """
    Main scanner function to process video files
    
    Args:
        video_path (str): Path to the video file to process
        scan_mode (str): Scan mode to use ('column' or 'width')
        
    Returns:
        bool: True if processing completed successfully, False otherwise
    """
    # Get configuration
    config = get_config()
    
    # Create scanner instance
    scanner = LineScanner()
    scanner.mode = scan_mode
    scanner.input_dir = video_path
    
    # Validate input file
    if not os.path.isfile(scanner.input_dir):
        print(f"-> Error: File '{scanner.input_dir}' could not be found")
        return False
    
    # Setup scanner paths
    scanner.filename = os.path.basename(os.path.splitext(scanner.input_dir)[0])
    scanner.output_dir = os.path.join(os.getcwd(), "RESULT")
    
    # Create output directory if it doesn't exist
    try:
        os.makedirs(scanner.output_dir, exist_ok=True)
    except OSError as e:
        print(f"-> Error creating output directory: {e}")
        return False
    
    # Debug information
    if config.get_boolean('DEBUG', 'visualize'):
        print(f"[DEBUG] filename: {scanner.filename}")
        print(f"[DEBUG] input dir: {scanner.input_dir}")
        print(f"[DEBUG] output dir: {scanner.output_dir}")
    
    # Create video capture object
    video_obj = cv2.VideoCapture(scanner.input_dir)
    
    if not video_obj.isOpened():
        print(f"-> Error: Could not open video file '{scanner.input_dir}'")
        return False
    
    # Get video properties
    scanner.totalFrames = int(video_obj.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(video_obj.get(cv2.CAP_PROP_FPS))
    duration = round(scanner.totalFrames / fps, 2) if fps > 0 else 0
    
    # Debug video information
    if config.get_boolean('DEBUG', 'visualize'):
        print(f"[DEBUG] total frames: {scanner.totalFrames}")
        print(f"[DEBUG] frames per second: {fps}")
        print(f"[DEBUG] duration in seconds: {duration}")
        print("")
        print("============================")
        print("Processing video...")
        print("")
    
    try:
        # Process video based on scan mode
        if scanner.mode == "width":
            print("-> Starting width scan mode...")
            scanner.width_scan_mode(video_obj)
            print("-> Concatenating frames...")
            scanner.concatenate_frames()
        elif scanner.mode == "column":
            print("-> Starting column scan mode...")
            scanner.column_scan_mode(video_obj)
        else:
            print(f"-> Error: Invalid scan mode '{scanner.mode}'. Use 'column' or 'width'.")
            return False
        
        print("-> Processing completed successfully!")
        return True
        
    except Exception as e:
        print(f"-> Error during processing: {e}")
        return False
        
    finally:
        # Always release the video object
        video_obj.release()
        cv2.destroyAllWindows()


def validate_scan_mode(mode):
    """
    Validate the scan mode parameter
    
    Args:
        mode (str): Scan mode to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    valid_modes = ["column", "width"]
    return mode in valid_modes


def print_usage():
    """Print usage information"""
    print("")
    print("Line Scan Camera Usage:")
    print("-> mode: 'column' for column pixel scan")
    print("-> mode: 'width' for width ROI pixel scan")
    print(f"-> Usage: python main.py <scan_mode> <video_file>")
    print("-> Example: python main.py column video.avi")
    print("-> GUI mode: python main.py (no arguments)")
    print("")
