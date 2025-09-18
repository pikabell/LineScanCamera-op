#!/usr/bin/env python3
"""
Test motion detection functionality
"""

import cv2
import numpy as np
import os

def test_motion_detection():
    print("=== Motion Detection Test ===")
    
    # Test parameters
    height, width = 480, 640
    threshold = 1000
    
    # Create two test frames
    print("1. Creating test frames...")
    
    # Frame 1: Static pattern
    frame1 = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(frame1, (200, 150), (400, 350), (0, 255, 0), -1)  # Green rectangle
    
    # Frame 2: Same pattern (no motion)
    frame2 = frame1.copy()
    
    # Frame 3: Pattern moved (motion detected)
    frame3 = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.rectangle(frame3, (250, 200), (450, 400), (0, 255, 0), -1)  # Moved green rectangle
    
    def detect_motion_test(prev_frame, curr_frame, label):
        """Simple motion detection test"""
        if prev_frame is None:
            return True, 0
        
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY) if len(prev_frame.shape) == 3 else prev_frame
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate difference
        diff = cv2.absdiff(prev_gray, curr_gray)
        _, thresh_img = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        motion_amount = cv2.countNonZero(thresh_img)
        
        has_motion = motion_amount > threshold
        print(f"   {label}: Motion amount = {motion_amount}, Has motion = {has_motion}")
        
        return has_motion, motion_amount
    
    print("2. Testing motion detection logic...")
    
    # Test sequence
    prev_frame = None
    
    # First frame (always capture)
    has_motion, amount = detect_motion_test(prev_frame, frame1, "Frame 1 (first)")
    prev_frame = frame1
    
    # Second frame (no motion)
    has_motion, amount = detect_motion_test(prev_frame, frame2, "Frame 2 (static)")
    prev_frame = frame2
    
    # Third frame (motion detected)
    has_motion, amount = detect_motion_test(prev_frame, frame3, "Frame 3 (moved)")
    
    print("\n3. Expected behavior:")
    print("   - Frame 1: Always captured (first frame)")
    print("   - Frame 2: Should NOT be captured (no motion)")
    print("   - Frame 3: Should be captured (motion detected)")
    
    print(f"\n4. Threshold setting: {threshold}")
    print("   - Lower values = more sensitive (captures small changes)")
    print("   - Higher values = less sensitive (only captures significant changes)")
    
    print("\n5. GUI Controls:")
    print("   - Enable Motion Detection: Checkbox to turn on/off")
    print("   - Sensitivity: Number input (default 1000)")
    print("   - Motion Status: Shows real-time detection status")
    
    print("\n✓ Motion detection test completed!")

if __name__ == "__main__":
    test_motion_detection()
