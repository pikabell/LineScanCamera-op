# Line Scan Camera - Complete Setup and Usage Guide

A real-time line scanning camera application for object inspection and analysis. This application captures video frames and processes them using line scanning techniques for quality control, measurement, and inspection applications.

## 🚀 Quick Start

**For immediate use:**
```bash
# 1. Clone/download the project
# 2. Create conda environment
conda env create -f environment.yml
conda activate stitch

# 3. Run the application
python main.py
```

## 📋 What You Get

- **Real-time line scanning** from camera or video files
- **Two scan modes**: Column scan (vertical) and Width scan (horizontal)
- **Live GUI interface** with camera preview and controls
- **Motion detection** for smart frame capture
- **Configurable parameters** through easy-to-use interface
- **Automatic image saving** with timestamps

## 🛠️ Installation Options

### Option 1: Conda Environment (Recommended)

```bash
# Install conda/miniconda if you don't have it
# Download from: https://docs.conda.io/en/latest/miniconda.html

# Create environment
conda env create -f environment.yml
conda activate stitch

# Run
python main.py
```

### Option 2: pip Installation

```bash
# Install Python 3.8+ first
pip install -r requirements.txt
python main.py
```

### Option 3: Manual Installation

```bash
pip install opencv-python==4.5.* numpy matplotlib pillow progressbar2
python main.py
```

## 📦 Required Dependencies

- **Python 3.8+**
- **OpenCV 4.5+** (computer vision)
- **NumPy** (numerical operations) 
- **Matplotlib** (plotting/display)
- **Pillow** (image processing)
- **progressbar2** (progress indication)
- **tkinter** (GUI - usually included with Python)

## 🎯 How to Use

### 1. Starting the Application

```bash
# Activate environment (if using conda)
conda activate stitch

# Launch application
python main.py
```

### 2. Camera Setup

1. **Connect your camera** (USB webcam, industrial camera, etc.)
2. **Select camera index** in the GUI (0 for first camera, 1 for second, etc.)
3. **Click "Start Camera"** to see live preview
4. **Adjust camera settings** if needed

### 3. Line Scanning

#### Column Scan Mode (Vertical Lines)
- **Use for**: Objects moving horizontally past the camera
- **Applications**: Conveyor belt inspection, moving parts analysis
- **Setup**: Position the scan line vertically where objects pass
- **Result**: Creates a time-series image showing object profiles

#### Width Scan Mode (Horizontal Lines)  
- **Use for**: Objects moving vertically or stationary scanning
- **Applications**: Sheet inspection, web scanning, document analysis
- **Setup**: Position the scan line horizontally across the area of interest
- **Result**: Creates a horizontal strip image showing width profiles

### 4. Configuration

**Through GUI:**
- Camera selection and resolution
- Scan mode selection
- Scan line position and width
- Motion detection sensitivity
- Frame blending options

**Through config file** (`config/config.ini`):
```ini
[camera]
default_camera_index = 0
frame_width = 640
frame_height = 480

[scanning]
default_scan_mode = column
column_position = 320
scan_width = 10
motion_threshold = 5000

[output]
result_directory = RESULT
image_format = jpg
```

### 5. Capturing Results

1. **Set up your scan parameters**
2. **Enable motion detection** (optional - automatically triggers capture)
3. **Click "Capture Line Scan"** to start recording
4. **Let objects move past the scan line** 
5. **Images automatically saved** to `RESULT/` folder with timestamps

## 📁 Project Structure

```
LineScanCamera-op/FINAL_LINE_SCAN_001/
├── main.py                 # Start here - main application
├── environment.yml         # Conda environment setup
├── requirements.txt        # pip requirements
├── README.md              # This guide
├── config/
│   └── config.ini         # Settings and parameters
├── src/                   # Source code
│   ├── core/              # Core scanning logic
│   │   ├── line_scanner.py    # Main scanning engine
│   │   ├── camera_scanner.py  # Camera handling
│   │   └── image_metadata.py  # Image data structures
│   ├── gui/               # User interface
│   │   └── application.py     # Main GUI application
│   └── utils/             # Utilities
│       └── config_manager.py  # Configuration handling
├── RESULT/                # Output images saved here
└── examples/              # Example usage scripts
```

## 🎮 GUI Interface Guide

### Main Window Components:

#### Camera Mode:
1. **Camera Selection**: Choose camera index (0, 1, 2...)
2. **Scan Controls**: Column or Width mode selection
3. **Parameter Controls**: Scan line position, width, motion threshold
4. **Action Buttons**: Start scanning, stop scanning, reset for new scan

#### Video Mode:
1. **Video Preview Pane**: Shows loaded video with scan line overlay
2. **Video Controls**: Play, pause, frame navigation
3. **Processing Options**: Same scan parameters as camera mode
4. **Results Display**: Preview shows scan results after processing
5. **Reset Functionality**: Clear results and prepare for new video scan

### Key Features:

- **Real-time Preview**: Both camera and video modes show scan line position
- **Debug Toggle**: Single checkbox to enable/disable visualization windows
- **Parameter Validation**: All inputs are validated before processing
- **Progress Tracking**: Visual progress bars during scan operations
- **Auto-save Results**: Processed images saved to RESULT/ directory
- **Multiple Scans**: Reset button allows processing multiple videos/scans
- **Session Management**: Clear results and start fresh with one click
- **Scrollable Interface**: Full scrolling support with mouse wheel and keyboard shortcuts

### Interface Navigation:

- **Mouse Wheel**: Scroll up/down through the interface
- **Keyboard Shortcuts**: 
  - `Arrow Up/Down`: Small scroll increments
  - `Page Up/Down`: Large scroll increments  
  - `Home`: Jump to top of interface
  - `End`: Jump to bottom of interface
- **Scrollbar**: Click and drag for precise positioning
- **Responsive Design**: Interface adapts to different window sizes

### Control Details:

- **Camera Index**: Select which camera device to use (0=default)
- **Scan Mode**: Choose between Column (vertical) or Width (horizontal) scanning
- **Scan Line Position**: Pixel position where scanning line is placed
- **Scan Width**: Thickness of the scanning region in pixels
- **Motion Threshold**: Sensitivity for motion detection (0-255)
- **Frame Blending**: Smooth transitions between frames
- **Reset / New Scan**: Clear all results and prepare for another scan

## 💡 Use Cases and Applications

### Industrial Inspection
- **Conveyor belt quality control**
- **Surface defect detection**
- **Dimension measurement**
- **Color consistency checking**

### Scientific Applications
- **Motion analysis**
- **Time-lapse documentation**
- **Particle tracking**
- **Flow visualization**

### Creative Applications
- **Artistic time-based photography**
- **Motion blur effects**
- **Dynamic texture creation**

## 🔧 Troubleshooting

### Camera Issues
```bash
# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.read()[0] else 'Camera Failed')"

# Try different camera indices if camera not found
# Common indices: 0 (built-in), 1 (USB), 2 (external)
```

### Installation Issues
```bash
# If conda environment fails
conda clean --all
conda env create -f environment.yml

# If OpenCV issues
pip uninstall opencv-python
pip install opencv-python==4.5.*

# If GUI doesn't appear (Linux)
sudo apt-get install python3-tk
```

### Performance Issues
- **Reduce camera resolution** in config (640x480 instead of 1920x1080)
- **Lower frame rate** 
- **Disable motion detection** for consistent performance
- **Use smaller scan widths** for faster processing

## 📝 Example Usage Code

### Basic Programmatic Usage
```python
# Import components
from src.core.line_scanner import LineScanner
from src.core.camera_scanner import CameraScanner  
from src.utils.config_manager import ConfigManager

# Setup
config = ConfigManager()
scanner = LineScanner(config)
camera = CameraScanner(camera_index=0)

# Capture frames
camera.start()
frames = []
for i in range(100):  # Capture 100 frames
    frame = camera.get_frame()
    frames.append(frame)
camera.stop()

# Process scan
result = scanner.column_scan_mode(frames)

# Save result
import cv2
cv2.imwrite('my_scan.jpg', result)
```

### Video File Processing
```python
import cv2
from src.core.line_scanner import LineScanner
from src.utils.config_manager import ConfigManager

# Process existing video file
config = ConfigManager()
scanner = LineScanner(config)

cap = cv2.VideoCapture('your_video.mp4')
frames = []

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frames.append(frame)

cap.release()

# Create line scan
result = scanner.column_scan_mode(frames)
cv2.imwrite('video_scan.jpg', result)
```

## 🎯 Tips for Best Results

### Camera Setup
- **Stable mounting** - minimize vibration
- **Good lighting** - even, diffuse lighting works best  
- **Proper focus** - ensure scan area is in sharp focus
- **Consistent background** - helps with motion detection

### Scan Configuration
- **Column scan**: Place line where objects pass consistently
- **Width scan**: Ensure full object width is captured
- **Motion detection**: Adjust threshold based on environment
- **Scan width**: Balance between detail and processing speed

### Output Quality  
- **Higher resolution** cameras give better detail
- **Consistent object speed** provides even scan lines
- **Multiple scans** can be combined for verification
- **Save in PNG** for lossless quality (change in config)

## 🆘 Getting Help

**Check these first:**
1. Verify camera is connected and working
2. Check conda environment is activated
3. Ensure all dependencies are installed
4. Try different camera indices
5. Check config file settings

**For issues:**
- Review the troubleshooting section above
- Test with provided example video file
- Try lower resolution settings
- Check Python and package versions

## 📈 What's Included

This package provides everything you need:
- ✅ **Complete working application**
- ✅ **Easy installation instructions** 
- ✅ **Comprehensive usage guide**
- ✅ **Example configurations**
- ✅ **Troubleshooting help**
- ✅ **Professional code structure**
- ✅ **Real-world applications**

---

## 🚀 Ready to Start?

```bash
# Three commands to get running:
conda env create -f environment.yml
conda activate stitch
python main.py
```

**That's it!** Your line scan camera application is ready to use.
