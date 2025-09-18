# LineScan Camera - Fixed Version

A Python application for creating line scan images from video files or live camera feed using OpenCV and tkinter.

## Overview

This is a simple implementation of a Line Scan Camera from a video of an Area Scan Camera using OpenCV 4.x. A line scan camera uses a single line of sensor pixels (effectively one-dimensional) to build up a two-dimensional image. The second dimension results from the motion of the object being imaged.

## Features

- **Video File Processing**: Load and process video files for line scanning
- **Live Camera Feed**: Real-time camera input with live preview  
- **Line Scanning**: Extract line scans from the center of each frame
- **Two Scan Modes**: Column mode (fast) and Width mode (high quality)
- **GUI Interface**: Easy-to-use graphical interface
- **Color Preservation**: Proper color handling for natural-looking results

## Requirements

- Python 3.7+
- OpenCV 4.x
- tkinter (usually included with Python)
- PIL (Pillow)
- NumPy
- Matplotlib
- progressbar2

## Installation

1. Activate the stitch conda environment:
   ```bash
   conda activate stitch
   ```

2. All required packages should already be installed in the stitch environment.

## Usage

### Starting the Application

```bash
python gui.py
```

### Using Video Files

1. Select "Video File" radio button
2. Click "Browse" to select a video file
3. Choose scan mode (Column or Width)
4. Click "Start Scan"
5. Results will be saved in the RESULT directory

### Using Live Camera

1. Select "Live Camera" radio button
2. Click "Start Camera" to initialize camera feed
3. You should see the camera feed with a green scan line
4. Click "Start Scan" to begin line scanning
5. Move objects in front of the camera to capture line scans
6. Click "Stop Scan" to save the result

## Configuration

Edit `config/config.ini` to adjust:
- Width ROI (region of interest width)
- Visualization settings for debugging
- Debug output options

## File Structure

```
LineScanCamera-fixed/
├── main.py              # Core scanning logic and CameraScanner class
├── gui.py               # GUI implementation with tkinter
├── config/
│   └── config.ini       # Configuration settings
├── RESULT/              # Output directory for scanned images
└── README.md            # This file
```

## Troubleshooting

- **Camera not detected**: Ensure your camera is connected and not being used by another application
- **No camera feed**: Try different lighting conditions or check camera permissions
- **Color issues**: The application now uses proper BGR to RGB conversion for natural colors
- **Performance**: Reduce video resolution or adjust frame rate in config if needed

## Technical Details

- Camera resolution: 640x480 pixels
- Frame rate: 30 FPS
- Display scaling: Automatically resized to fit GUI (max 400x300)
- Line scanning: Extracts center column from each frame
- Output format: JPG images with timestamp

## Educational Resources

For more information about line scan vs area scan cameras:

-	Line Scan and Area Scan Cameras for the Inspection of Pharmaceutical Products:
https://www.youtube.com/watch?v=EzL_3BbEI20

-	Area Scan Camera vs Line Scan Camera:
https://www.youtube.com/watch?v=DkIQl06jloM


## How to use
1. Install dependencies
```
pip install -r requirements.txt
```

2. Run script
```
python3 main.py <scan_mode> <video_file>

example:

python3 main.py column C:/Users/xXx/Downloads/videos/video.mp4
```

3. Output image

You will find the output file in: ```RESULT``` folder (this folder is created automatically) with the same name as the input file.

4. Configuration file (optional)

In this folder you will find a ```config.ini``` file. You can modify the parameters to test differents width ROis in the scanning process.

## Explanation
This program uses two modes: 1. ```COLUMN MODE```: this mode generate a scanned image taking one column pixel per image sequence. This is commonly the process done by a line scan camera. 2. ```WIDTH MODE```: this mode generate a scanned image taking a region of interest (centroid) in the image sequence. This process is more time consuming, but will provide a better ouput resolution.

## State-of-the-art
There is also a C++ implementation of a line scan camera in OpenCV here: https://github.com/ppalasek/linescan. <br><br>

An example video of this is action can be found here:
https://www.youtube.com/watch?v=1X8DVp0Amh8



