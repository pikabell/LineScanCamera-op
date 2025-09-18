## Width Mode Fix Summary

### Issue Fixed
The width mode in live camera scanning was not working differently from column mode. It was only extracting a single pixel line regardless of the selected mode.

### Changes Made

#### 1. Updated GUI Logic (`gui.py`)
- **Enhanced `show_camera_feed()` method** to handle both column and width modes differently
- **Column Mode**: Extracts a single pixel line (`scan_line_x:scan_line_x+1`)
- **Width Mode**: Extracts a region based on `width_roi` config (`start_x:end_x`)

#### 2. Visual Feedback Improvements
- **Column Mode Visualization**: Shows a single green line on camera feed
- **Width Mode Visualization**: Shows a green rectangle representing the width ROI
- **Console Feedback**: Prints active scanning mode and width ROI value when starting scan

#### 3. Configuration Update
- Updated default `width_roi` from 2 to 20 pixels for more visible results
- This makes the width mode difference more apparent

### Key Technical Changes

**Live Camera Width Scanning Logic:**
```python
if scan_mode == "width":
    # Width mode: extract a width region around center line
    start_x = max(0, scan_line_x - width_roi // 2)
    end_x = min(width, scan_line_x + width_roi // 2)
    scan_region = frame[:, start_x:end_x]
else:
    # Column mode: extract single line
    scan_region = frame[:, scan_line_x:scan_line_x+1]
```

**Visual Indicator:**
```python
if scan_mode == "width":
    # Draw width ROI rectangle
    cv2.rectangle(frame, (start_x, 0), (end_x, height), (0, 255, 0), 2)
else:
    # Draw single scan line
    cv2.line(frame, (scan_line_x, 0), (scan_line_x, height), (0, 255, 0), 2)
```

### How to Test

1. **Start the application:**
   ```bash
   python gui.py
   ```

2. **Select Live Camera mode**

3. **Click "Start Camera"**

4. **Test Column Mode:**
   - Select "Column" radio button
   - Click "Start Scan"
   - Observe: Single green vertical line on camera feed
   - Result: Narrow line scan result

5. **Test Width Mode:**
   - Stop scanning
   - Select "Width" radio button  
   - Click "Start Scan"
   - Observe: Green rectangle (20 pixels wide) on camera feed
   - Result: Wider line scan result with more detail

### Expected Differences

- **Column Mode**: Fast scanning, single pixel line, minimal detail
- **Width Mode**: Higher quality scanning, 20-pixel wide region, more detail
- **Visual Indicator**: Line vs Rectangle on live camera feed
- **Result Quality**: Narrow vs Wide line scan images

### Configuration
- Adjust `width_roi` in `config/config.ini` to change the width size
- Default is now 20 pixels (was 2 pixels)
- Larger values = wider scanning region = more detail but larger files
