#!/usr/bin/env python3
"""
Test script to demonstrate region-specific motion detection
"""

import cv2
import numpy as np

def test_region_motion_detection():
    print("=== Region-Specific Motion Detection Test ===")
    
    # Create test frames
    height, width = 480, 640
    center_x = width // 2  # 320
    width_roi = 20
    
    print(f"Frame size: {width}x{height}")
    print(f"Center line: x={center_x}")
    print(f"Width ROI: {width_roi} pixels")
    print()
    
    # Frame 1: Static background with object on the left
    frame1 = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(frame1, (50, 200), (150, 300), (255, 0, 0), -1)  # Blue object on left
    
    # Frame 2: Object moves to center (in scanning region)
    frame2 = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(frame2, (300, 200), (400, 300), (255, 0, 0), -1)  # Blue object at center
    
    # Frame 3: Object moves to right (out of scanning region)
    frame3 = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(frame3, (500, 200), (600, 300), (255, 0, 0), -1)  # Blue object on right
    
    def analyze_motion_in_region(prev_frame, curr_frame, scan_mode, label):
        """Analyze motion in specific scanning region"""
        if prev_frame is None:
            return True, 0, "First frame"
        
        # Define scanning region based on mode
        if scan_mode == "width":
            start_x = max(0, center_x - width_roi // 2)  # 310
            end_x = min(width, center_x + width_roi // 2)  # 330
            region_desc = f"width ROI ({start_x}-{end_x})"
        else:
            buffer = 2
            start_x = max(0, center_x - buffer)  # 318
            end_x = min(width, center_x + buffer + 1)  # 323
            region_desc = f"column line ({start_x}-{end_x})"
        
        # Extract scanning regions
        prev_region = prev_frame[:, start_x:end_x]
        curr_region = curr_frame[:, start_x:end_x]
        
        # Convert to grayscale
        prev_gray = cv2.cvtColor(prev_region, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_region, cv2.COLOR_BGR2GRAY)
        
        # Calculate difference
        diff = cv2.absdiff(prev_gray, curr_gray)
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        motion_amount = cv2.countNonZero(thresh)
        
        # Motion threshold
        threshold = 100  # Lower threshold for demo
        has_motion = motion_amount > threshold
        
        print(f"   {label}")
        print(f"     Region: {region_desc}")
        print(f"     Motion amount: {motion_amount}")
        print(f"     Has motion: {has_motion}")
        print()
        
        return has_motion, motion_amount, region_desc
    
    print("1. COLUMN MODE DETECTION:")
    print("   (Analyzing 5-pixel wide region around center line)")
    
    prev_frame = None
    for i, (frame, desc) in enumerate([(frame1, "Object on left"), 
                                       (frame2, "Object at center"), 
                                       (frame3, "Object on right")], 1):
        has_motion, amount, region = analyze_motion_in_region(prev_frame, frame, "column", f"Frame {i}: {desc}")
        prev_frame = frame
    
    print("2. WIDTH MODE DETECTION:")
    print(f"   (Analyzing {width_roi}-pixel wide ROI region)")
    
    prev_frame = None
    for i, (frame, desc) in enumerate([(frame1, "Object on left"), 
                                       (frame2, "Object at center"), 
                                       (frame3, "Object on right")], 1):
        has_motion, amount, region = analyze_motion_in_region(prev_frame, frame, "width", f"Frame {i}: {desc}")
        prev_frame = frame
    
    print("3. EXPECTED BEHAVIOR:")
    print("   ✓ Motion outside scanning region = NOT detected")
    print("   ✓ Motion inside scanning region = DETECTED")
    print("   ✓ More precise detection focused on actual scan area")
    print("   ✓ Reduces false positives from background movement")
    
    print("\n4. ADVANTAGES:")
    print("   📍 Precision: Only detects relevant motion")
    print("   🎯 Focus: Ignores background distractions")
    print("   ⚡ Efficiency: Analyzes smaller regions")
    print("   🎛️ Control: Different sensitivity for column vs width modes")
    
    return True

if __name__ == "__main__":
    test_region_motion_detection()
    print("\n✓ Region-specific motion detection test completed!")
