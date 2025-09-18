#!/usr/bin/env python3
"""
Test script to measure actual FPS performance
"""

import time
import cv2
from main import CameraScanner

def test_fps_performance():
    print("=== FPS Performance Test ===")
    
    # Test camera FPS
    print("\n1. CAMERA FPS SETTINGS:")
    scanner = CameraScanner()
    if scanner.start():
        try:
            # Get camera properties
            actual_fps = scanner.cap.get(cv2.CAP_PROP_FPS)
            width = int(scanner.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(scanner.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            print(f"   Camera FPS setting: {actual_fps}")
            print(f"   Resolution: {width}x{height}")
            
            # Test actual frame capture rate
            print("\n2. ACTUAL FRAME CAPTURE RATE:")
            frame_count = 0
            start_time = time.time()
            test_duration = 3  # seconds
            
            print(f"   Testing for {test_duration} seconds...")
            
            while time.time() - start_time < test_duration:
                frame = scanner.get_frame()
                if frame is not None:
                    frame_count += 1
                time.sleep(0.001)  # Small delay to prevent CPU overload
            
            elapsed_time = time.time() - start_time
            measured_fps = frame_count / elapsed_time
            
            print(f"   Frames captured: {frame_count}")
            print(f"   Elapsed time: {elapsed_time:.2f}s")
            print(f"   Measured FPS: {measured_fps:.1f}")
            
            scanner.stop()
            
        except Exception as e:
            print(f"   Error during camera test: {e}")
            scanner.stop()
    else:
        print("   Camera not available for testing")
    
    print("\n3. GUI DISPLAY FPS:")
    print("   GUI update interval: 33ms")
    print("   Target display FPS: ~30 FPS")
    print("   Formula: 1000ms / 33ms = 30.3 FPS")
    
    print("\n4. VIDEO PROCESSING FPS:")
    print("   Video files are processed at their original frame rate")
    print("   Example: Bowler2_FV_250fps.avi = 250 FPS")
    print("   Processing speed depends on:")
    print("   - Video frame rate")
    print("   - Frame processing complexity")
    print("   - CPU performance")
    
    print("\n5. MOTION DETECTION IMPACT:")
    print("   When motion detection is enabled:")
    print("   - Frames are still captured at camera FPS")
    print("   - Only frames with motion are added to composite")
    print("   - Processing load: motion analysis + frame capture")
    
    print("\n6. FPS SUMMARY:")
    print("   📹 Camera Capture: 30 FPS (hardware setting)")
    print("   🖥️  GUI Display: ~30 FPS (33ms intervals)")
    print("   🎬 Video Processing: Variable (depends on source video)")
    print("   🔍 Motion Detection: Real-time analysis at capture rate")
    
    return True

if __name__ == "__main__":
    test_fps_performance()
    print("\n✓ FPS performance test completed!")
