#!/usr/bin/env python3
"""
Line Scan Camera Application - Main Entry Point

A modular implementation of line scan camera functionality using OpenCV.
This application provides both command-line and GUI interfaces for processing
video files and live camera input to create line scan images.

Usage:
    python main.py                           # GUI mode
    python main.py <mode> <video_file>       # Command line mode
    
Examples:
    python main.py                           # Start GUI
    python main.py column video.avi          # Column scan mode
    python main.py width video.mp4           # Width scan mode

Author: ECIL Team
Version: 2.0.0
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core import run_scanner, validate_scan_mode, print_usage
from src.gui import main as gui_main


def main():
    """Main entry point for the application"""
    
    # Print application header
    print("=" * 60)
    print("Line Scan Camera v2.0")
    print("ECIL - Enhanced Computer Imaging Lab")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("-> Starting GUI mode...")
        print("")
        gui_main()
    elif len(sys.argv) == 2:
        if sys.argv[1] in ['-h', '--help', 'help']:
            print_usage()
        else:
            print("-> Error: Invalid number of arguments")
            print_usage()
            sys.exit(1)
    elif len(sys.argv) == 3:
        scan_mode = sys.argv[1].lower()
        video_file = sys.argv[2]
        
        # Validate scan mode
        if not validate_scan_mode(scan_mode):
            print(f"-> Error: Invalid scan mode '{scan_mode}'")
            print_usage()
            sys.exit(1)
        
        # Validate video file
        if not os.path.isfile(video_file):
            print(f"-> Error: Video file '{video_file}' not found")
            sys.exit(1)
        
        print(f"-> Starting command line mode...")
        print(f"-> Scan mode: {scan_mode}")
        print(f"-> Video file: {video_file}")
        print("")
        
        # Run scanner
        success = run_scanner(video_file, scan_mode)
        
        if success:
            print("")
            print("-> Processing completed successfully!")
            sys.exit(0)
        else:
            print("")
            print("-> Processing failed!")
            sys.exit(1)
    else:
        print("-> Error: Too many arguments")
        print_usage()
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n-> Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n-> Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
