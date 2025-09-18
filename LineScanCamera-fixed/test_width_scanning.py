#!/usr/bin/env python3
"""
Test width scanning functionality
"""

import sys
import os
sys.path.insert(0, os.getcwd())

print("Testing Width Scanning Functionality...")
print("=" * 50)

try:
    from main import run_scanner
    
    # Test with the included video file
    video_file = "Bowler2_FV_250fps.avi"
    
    if os.path.exists(video_file):
        print(f"✓ Found test video: {video_file}")
        
        print("\n1. Testing Column Mode...")
        try:
            run_scanner(video_file, "column")
            print("✓ Column mode completed successfully")
        except Exception as e:
            print(f"✗ Column mode failed: {e}")
        
        print("\n2. Testing Width Mode...")
        try:
            run_scanner(video_file, "width")
            print("✓ Width mode completed successfully")
        except Exception as e:
            print(f"✗ Width mode failed: {e}")
        
        # Check if results were created
        result_dir = "RESULT"
        if os.path.exists(result_dir):
            results = [f for f in os.listdir(result_dir) if f.endswith(('.jpg', '.png'))]
            print(f"\n✓ Found {len(results)} result files in RESULT directory:")
            for result in results[-4:]:  # Show last 4 files
                print(f"  - {result}")
        else:
            print("\n⚠ RESULT directory not found")
            
    else:
        print(f"✗ Test video file not found: {video_file}")
        
    print("\n" + "=" * 50)
    print("Width scanning test completed!")
    print("You can also test interactively with: python gui.py")
    
except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()
