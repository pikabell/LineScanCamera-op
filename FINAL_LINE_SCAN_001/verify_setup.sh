#!/bin/bash
echo "============================================"
echo "Line Scan Camera - Setup Verification"
echo "============================================"

echo "Checking Python..."
python --version
echo ""

echo "Testing core dependencies..."
python -c "
import sys
import traceback

def test_import(module_name, description):
    try:
        __import__(module_name)
        print(f'✓ {description}')
        return True
    except ImportError as e:
        print(f'✗ {description} - {e}')
        return False

# Test core dependencies
success = True
success &= test_import('cv2', 'OpenCV')
success &= test_import('numpy', 'NumPy')
success &= test_import('matplotlib', 'Matplotlib')
success &= test_import('PIL', 'Pillow')
success &= test_import('progressbar2', 'ProgressBar2')
success &= test_import('tkinter', 'Tkinter (GUI)')

print('')
print('Testing application modules...')
success &= test_import('src.core.line_scanner', 'Line Scanner Core')
success &= test_import('src.gui.application', 'GUI Application')
success &= test_import('src.utils.config_manager', 'Configuration Manager')

if success:
    print('')
    print('✓ All dependencies and modules loaded successfully!')
else:
    print('')
    print('✗ Some dependencies are missing. Install with:')
    print('  conda env create -f environment.yml')
    print('  or')
    print('  pip install -r requirements.txt')
"

echo ""
echo "Testing camera access..."
python -c "
import cv2
import sys

print('Available camera indices:')
found_camera = False
for i in range(3):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f'  Camera {i}: ✓ Working ({frame.shape})')
            found_camera = True
        else:
            print(f'  Camera {i}: ✗ Cannot read frames')
        cap.release()
    else:
        print(f'  Camera {i}: ✗ Cannot open')

if not found_camera:
    print('⚠ No working cameras found (this is normal if no camera is connected)')
else:
    print('✓ At least one camera is working')
"

echo ""
echo "Testing video processing..."
if [ -f "Bowler2_FV_250fps.avi" ]; then
    echo "✓ Example video file found"
    echo "  You can test video processing with:"
    echo "    python main.py column Bowler2_FV_250fps.avi"
    echo "    python main.py width Bowler2_FV_250fps.avi"
else
    echo "⚠ Example video file not found (you can use your own video files)"
fi

echo ""
echo "============================================"
echo "Setup verification complete!"
echo ""
echo "To start the application:"
echo "  python main.py"
echo ""
echo "For command line usage:"
echo "  python main.py column your_video.mp4"
echo "  python main.py width your_video.mp4"
echo "============================================"
