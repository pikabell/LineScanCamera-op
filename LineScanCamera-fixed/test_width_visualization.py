#!/usr/bin/env python3
"""
Test script to verify width mode visualization changes
"""

import cv2
import numpy as np

def test_width_visualization():
    """Test the difference between column and width mode visualization"""
    
    # Create a test frame with vertical stripes for easy visualization
    height, width = 480, 640
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create vertical stripes pattern
    for x in range(0, width, 40):
        color = (0, 255, 0) if (x // 40) % 2 == 0 else (255, 0, 0)
        frame[:, x:x+20] = color
    
    # Test center position
    scan_line_x = width // 2  # 320
    width_roi = 20  # From config default
    
    print("=== Width Mode Visualization Test ===")
    print(f"Frame size: {width}x{height}")
    print(f"Center line X: {scan_line_x}")
    print(f"Width ROI: {width_roi}")
    print()
    
    # Column mode extraction
    print("1. COLUMN MODE:")
    column_scan = frame[:, scan_line_x:scan_line_x+1]
    print(f"   Extracted region: x={scan_line_x} to {scan_line_x+1} (width: {column_scan.shape[1]})")
    print(f"   Result shape: {column_scan.shape}")
    
    # Draw column visualization
    frame_column = frame.copy()
    cv2.line(frame_column, (scan_line_x, 0), (scan_line_x, height), (0, 255, 255), 3)  # Yellow line
    
    print()
    
    # Width mode extraction
    print("2. WIDTH MODE:")
    start_x = max(0, scan_line_x - width_roi // 2)
    end_x = min(width, scan_line_x + width_roi // 2)
    width_scan = frame[:, start_x:end_x]
    print(f"   Extracted region: x={start_x} to {end_x} (width: {width_scan.shape[1]})")
    print(f"   Result shape: {width_scan.shape}")
    
    # Draw width visualization
    frame_width = frame.copy()
    cv2.rectangle(frame_width, (start_x, 0), (end_x, height), (0, 255, 255), 3)  # Yellow rectangle
    
    print()
    print("3. VISUAL DIFFERENCES:")
    print("   - Column mode: Extracts 1-pixel wide line")
    print("   - Width mode: Extracts {}-pixel wide region".format(width_roi))
    print("   - Column mode shows: Single vertical line on camera feed")
    print("   - Width mode shows: Rectangular region on camera feed")
    
    # Save test images
    cv2.imwrite("test_column_mode.jpg", frame_column)
    cv2.imwrite("test_width_mode.jpg", frame_width)
    cv2.imwrite("column_extraction.jpg", column_scan)
    cv2.imwrite("width_extraction.jpg", width_scan)
    
    print()
    print("4. TEST IMAGES SAVED:")
    print("   - test_column_mode.jpg: Shows single line visualization")
    print("   - test_width_mode.jpg: Shows width rectangle visualization")
    print("   - column_extraction.jpg: 1-pixel extracted result")
    print("   - width_extraction.jpg: {}-pixel extracted result".format(width_roi))
    
    return True

if __name__ == "__main__":
    test_width_visualization()
    print("\n✓ Width visualization test completed!")
