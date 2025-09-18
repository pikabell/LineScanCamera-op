#!/usr/bin/env python3
"""
Demonstration of frame blending for smooth line scan results
"""

import cv2
import numpy as np

def demonstrate_blending():
    print("=== Frame Blending Demonstration ===")
    
    # Create test frames with different colors to show blending effect
    height, width = 100, 5  # Small for demonstration
    
    # Frame sequence with varying intensities
    frames = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]  # Different colors
    
    for i, color in enumerate(colors):
        frame = np.full((height, width, 3), color, dtype=np.uint8)
        frames.append(frame)
    
    def blend_frames(current, previous, strength):
        """Blend current frame with previous frame"""
        if previous is None:
            return current
        
        current_float = current.astype(np.float64)
        previous_float = previous.astype(np.float64)
        
        # Blend: result = (1-strength) * current + strength * previous
        blended = (1.0 - strength) * current_float + strength * previous_float
        return blended.astype(np.uint8)
    
    print("1. WITHOUT BLENDING (Sharp Transitions):")
    print("   Frame 1: Pure Red")
    print("   Frame 2: Pure Green")
    print("   Frame 3: Pure Blue")
    print("   Result: Hard color changes")
    
    print("\n2. WITH BLENDING (Smooth Transitions):")
    
    # Test different blend strengths
    strengths = [0.1, 0.3, 0.5, 0.7]
    
    for strength in strengths:
        print(f"\n   Blend Strength: {strength}")
        previous = None
        composite_no_blend = None
        composite_blend = None
        
        for i, frame in enumerate(frames):
            # Without blending
            if composite_no_blend is None:
                composite_no_blend = frame
            else:
                composite_no_blend = np.hstack((composite_no_blend, frame))
            
            # With blending
            if previous is None:
                blended_frame = frame
            else:
                blended_frame = blend_frames(frame, previous, strength)
            
            if composite_blend is None:
                composite_blend = blended_frame
            else:
                composite_blend = np.hstack((composite_blend, blended_frame))
            
            previous = blended_frame
        
        # Analyze the difference
        avg_no_blend = np.mean(composite_no_blend, axis=(0, 1))
        avg_blend = np.mean(composite_blend, axis=(0, 1))
        
        print(f"     No blend average: R={avg_no_blend[2]:.1f}, G={avg_no_blend[1]:.1f}, B={avg_no_blend[0]:.1f}")
        print(f"     Blended average:  R={avg_blend[2]:.1f}, G={avg_blend[1]:.1f}, B={avg_blend[0]:.1f}")
    
    print("\n3. BLENDING EFFECTS:")
    print("   📊 Strength 0.1: Subtle smoothing, maintains original colors")
    print("   📊 Strength 0.3: Balanced smoothing (recommended)")  
    print("   📊 Strength 0.5: Strong smoothing, noticeable color mixing")
    print("   📊 Strength 0.7: Very smooth, significant color change")
    
    print("\n4. REAL-WORLD BENEFITS:")
    print("   🎯 Eliminates hard edges between captured frames")
    print("   🌅 Creates seamless panoramic-style results")
    print("   📹 Reduces motion artifacts and jitter")
    print("   ✨ Produces professional, smooth-looking scans")
    
    print("\n5. USAGE RECOMMENDATIONS:")
    print("   📸 Fast motion: Use lower strength (0.1-0.2)")
    print("   🚶 Slow motion: Use medium strength (0.3-0.4)")
    print("   🔍 High detail: Use higher strength (0.4-0.6)")
    print("   🎨 Artistic effect: Use very high strength (0.6-0.8)")
    
    print("\n6. GUI CONTROLS:")
    print("   ☑️ Enable Frame Blending: Turn blending on/off")
    print("   🎛️ Blend Strength: Adjust from 0.1 (subtle) to 0.8 (strong)")
    print("   📋 Real-time feedback: See effect immediately in composite")
    
    return True

if __name__ == "__main__":
    demonstrate_blending()
    print("\n✓ Frame blending demonstration completed!")
