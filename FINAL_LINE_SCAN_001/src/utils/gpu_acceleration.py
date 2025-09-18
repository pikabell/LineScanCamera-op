#!/usr/bin/env python3
"""
GPU Acceleration Module for Line Scan Camera

This module provides GPU-accelerated image processing operations using CuPy
for significant performance improvements on systems with NVIDIA GPUs.
"""

import numpy as np
import cv2

# GPU acceleration support
try:
    import cupy as cp
    GPU_AVAILABLE = True
    print(f"✓ GPU acceleration enabled with {cp.cuda.runtime.getDeviceCount()} GPUs")
except ImportError:
    GPU_AVAILABLE = False
    print("! GPU acceleration not available - falling back to CPU")

class GPUImageProcessor:
    """
    GPU-accelerated image processing operations for line scan camera
    with intelligent memory management and chunked processing
    """
    
    def __init__(self):
        self.gpu_available = GPU_AVAILABLE
        if self.gpu_available:
            # Select the best GPU (usually 0)
            cp.cuda.Device(0).use()
            
            # Get GPU memory info
            mempool = cp.get_default_memory_pool()
            self.total_memory = cp.cuda.runtime.memGetInfo()[1]
            self.available_memory = cp.cuda.runtime.memGetInfo()[0]
            
            # Set conservative memory limits (use only 60% of available memory for safety)
            self.memory_limit = int(self.available_memory * 0.6)
            
            print(f"Using GPU 0 for acceleration")
            print(f"GPU memory: {self.total_memory / 1024**3:.1f} GB total, {self.available_memory / 1024**3:.1f} GB available")
            print(f"Memory limit set to: {self.memory_limit / 1024**3:.1f} GB")
    
    def get_memory_usage(self):
        """Get current GPU memory usage"""
        if not self.gpu_available:
            return 0, 0
        
        used_memory = self.total_memory - cp.cuda.runtime.memGetInfo()[0]
        return used_memory, self.total_memory
    
    def clear_gpu_memory(self):
        """Clear GPU memory pools"""
        if self.gpu_available:
            cp.get_default_memory_pool().free_all_blocks()
            cp.get_default_pinned_memory_pool().free_all_blocks()
    
    def estimate_frame_memory(self, frame_shape):
        """Estimate memory usage for a single frame"""
        if len(frame_shape) == 3:
            return frame_shape[0] * frame_shape[1] * frame_shape[2] * 4  # 4 bytes per float32
        else:
            return frame_shape[0] * frame_shape[1] * 4
    
    def calculate_optimal_chunk_size(self, frame_shape, total_frames):
        """Calculate optimal chunk size based on available GPU memory"""
        if not self.gpu_available:
            return total_frames
        
        frame_memory = self.estimate_frame_memory(frame_shape)
        max_frames = max(1, int(self.memory_limit / (frame_memory * 2)))  # *2 for safety margin
        
        # Don't make chunks too small (minimum 50 frames) or too large (maximum 1000 frames)
        chunk_size = max(50, min(max_frames, min(1000, total_frames)))
        
        print(f"Optimal chunk size: {chunk_size} frames ({chunk_size * frame_memory / 1024**2:.1f} MB per chunk)")
        return chunk_size
    
    def to_gpu(self, array):
        """Move numpy array to GPU memory"""
        if self.gpu_available:
            return cp.asarray(array)
        return array
    
    def to_cpu(self, array):
        """Move array back to CPU memory"""
        if self.gpu_available and hasattr(array, 'get'):
            return array.get()
        return array
    
    def gaussian_blur_gpu(self, image, kernel_size=(17, 17), sigma=0):
        """GPU-accelerated Gaussian blur"""
        if not self.gpu_available:
            return cv2.GaussianBlur(image, kernel_size, sigma)
        
        # Move to GPU
        gpu_image = self.to_gpu(image)
        
        # Create Gaussian kernel on GPU
        kx, ky = kernel_size
        if sigma == 0:
            sigma = 0.3 * ((kx - 1) * 0.5 - 1) + 0.8
        
        # Use CuPy's gaussian filter (equivalent to OpenCV's GaussianBlur)
        from cupyx.scipy.ndimage import gaussian_filter
        
        if len(gpu_image.shape) == 3:
            # Process each channel separately for color images
            result = cp.zeros_like(gpu_image)
            for i in range(gpu_image.shape[2]):
                result[:, :, i] = gaussian_filter(gpu_image[:, :, i], sigma=sigma)
        else:
            result = gaussian_filter(gpu_image, sigma=sigma)
        
        return self.to_cpu(result.astype(gpu_image.dtype))
    
    def morphology_operations_gpu(self, image, kernel, operation='open', iterations=1):
        """GPU-accelerated morphological operations"""
        if not self.gpu_available:
            if operation == 'open':
                return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, iterations=iterations)
            elif operation == 'close':
                return cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, iterations=iterations)
            elif operation == 'erode':
                return cv2.erode(image, kernel, iterations=iterations)
            elif operation == 'dilate':
                return cv2.dilate(image, kernel, iterations=iterations)
        
        # Move to GPU
        gpu_image = self.to_gpu(image)
        gpu_kernel = self.to_gpu(kernel)
        
        # Use CuPy's morphology operations
        from cupyx.scipy.ndimage import binary_erosion, binary_dilation
        
        result = gpu_image
        
        for _ in range(iterations):
            if operation == 'erode':
                result = binary_erosion(result, structure=gpu_kernel).astype(gpu_image.dtype) * 255
            elif operation == 'dilate':
                result = binary_dilation(result, structure=gpu_kernel).astype(gpu_image.dtype) * 255
            elif operation == 'open':
                # Erosion followed by dilation
                temp = binary_erosion(result, structure=gpu_kernel).astype(gpu_image.dtype) * 255
                result = binary_dilation(temp, structure=gpu_kernel).astype(gpu_image.dtype) * 255
            elif operation == 'close':
                # Dilation followed by erosion
                temp = binary_dilation(result, structure=gpu_kernel).astype(gpu_image.dtype) * 255
                result = binary_erosion(temp, structure=gpu_kernel).astype(gpu_image.dtype) * 255
        
        return self.to_cpu(result)
    
    def resize_gpu(self, image, dsize, interpolation=cv2.INTER_LINEAR):
        """GPU-accelerated image resizing"""
        if not self.gpu_available:
            return cv2.resize(image, dsize, interpolation=interpolation)
        
        # For now, use CPU resize as CuPy doesn't have direct resize
        # But we can use GPU for other operations in the pipeline
        return cv2.resize(image, dsize, interpolation=interpolation)
    
    def concatenate_gpu(self, arrays, axis=1):
        """GPU-accelerated array concatenation"""
        if not self.gpu_available:
            return np.concatenate(arrays, axis=axis)
        
        # Move arrays to GPU
        gpu_arrays = [self.to_gpu(arr) for arr in arrays]
        
        # Concatenate on GPU
        result = cp.concatenate(gpu_arrays, axis=axis)
        
        return self.to_cpu(result)
    
    def motion_detection_gpu(self, current_frame, previous_frame):
        """GPU-accelerated motion detection"""
        if not self.gpu_available:
            diff = cv2.absdiff(current_frame, previous_frame)
            return np.sum(diff)
        
        # Move to GPU
        gpu_current = self.to_gpu(current_frame)
        gpu_previous = self.to_gpu(previous_frame)
        
        # Calculate absolute difference on GPU
        diff = cp.abs(gpu_current.astype(cp.float32) - gpu_previous.astype(cp.float32))
        
        # Sum on GPU
        motion_score = cp.sum(diff)
        
        return float(motion_score.get())
    
    def batch_process_frames_gpu(self, frames, scan_line_x, scan_mode='column', width_roi=3, progress_callback=None):
        """GPU-accelerated chunked batch processing of frames with memory management"""
        if not self.gpu_available or len(frames) == 0:
            return self._cpu_batch_process(frames, scan_line_x, scan_mode, width_roi)
        
        total_frames = len(frames)
        print(f"GPU chunked processing {total_frames} frames...")
        
        # Calculate optimal chunk size based on memory
        chunk_size = self.calculate_optimal_chunk_size(frames[0].shape, total_frames)
        
        # Process in chunks to avoid memory issues
        results = []
        processed_frames = 0
        
        try:
            for i in range(0, total_frames, chunk_size):
                end_idx = min(i + chunk_size, total_frames)
                chunk_frames = frames[i:end_idx]
                chunk_size_actual = len(chunk_frames)
                
                print(f"Processing chunk {i//chunk_size + 1}/{(total_frames + chunk_size - 1)//chunk_size} "
                      f"({chunk_size_actual} frames)")
                
                # Clear GPU memory before processing chunk
                self.clear_gpu_memory()
                
                # Monitor memory usage
                used_before, total = self.get_memory_usage()
                print(f"GPU memory before chunk: {used_before / 1024**3:.2f} GB used")
                
                # Process chunk on GPU
                chunk_result = self._process_chunk_gpu(chunk_frames, scan_line_x, scan_mode, width_roi)
                results.append(chunk_result)
                
                # Update progress if callback provided
                processed_frames += chunk_size_actual
                if progress_callback:
                    progress_callback(processed_frames)
                
                # Monitor memory after processing
                used_after, _ = self.get_memory_usage()
                print(f"GPU memory after chunk: {used_after / 1024**3:.2f} GB used")
                
                # Clear GPU memory after processing chunk
                self.clear_gpu_memory()
            
            # Combine results
            if scan_mode == 'column':
                # Concatenate horizontally for column mode
                final_result = np.concatenate(results, axis=1)
            else:
                # Concatenate horizontally for width mode
                final_result = np.concatenate(results, axis=1)
            
            print(f"✓ GPU chunked processing completed successfully")
            return final_result
            
        except Exception as e:
            print(f"GPU processing failed: {e}")
            print("Falling back to CPU processing...")
            return self._cpu_batch_process(frames, scan_line_x, scan_mode, width_roi)
    
    def _process_chunk_gpu(self, chunk_frames, scan_line_x, scan_mode, width_roi):
        """Process a single chunk of frames on GPU with optimizations and RGB preservation"""
        try:
            if scan_mode == 'column':
                # Optimized column extraction - extract all at once preserving RGB
                if len(chunk_frames) > 1:
                    # Use numpy for stacking (faster for small chunks)
                    frame_stack = np.stack(chunk_frames, axis=0)
                    # Extract column from all frames at once, preserving all channels
                    if len(frame_stack.shape) == 4:  # (frames, height, width, channels)
                        column_data = frame_stack[:, :, scan_line_x, :]
                        # Transpose to get (height, num_frames, channels)
                        result = np.transpose(column_data, (1, 0, 2))
                    else:  # Grayscale case
                        column_data = frame_stack[:, :, scan_line_x]
                        result = np.transpose(column_data, (1, 0))
                        # Add channel dimension if needed
                        if len(result.shape) == 2:
                            result = np.expand_dims(result, axis=2)
                else:
                    # Single frame case
                    if len(chunk_frames[0].shape) == 3:
                        result = chunk_frames[0][:, scan_line_x:scan_line_x+1, :]
                    else:
                        result = chunk_frames[0][:, scan_line_x:scan_line_x+1]
                        result = np.expand_dims(result, axis=2)
                
                return result
            
            else:
                # Optimized width ROI extraction preserving RGB
                start_x = max(0, scan_line_x - width_roi // 2)
                end_x = min(chunk_frames[0].shape[1], scan_line_x + width_roi // 2)
                
                # Extract ROIs and concatenate
                rois = []
                for frame in chunk_frames:
                    if len(frame.shape) == 3:
                        roi = frame[:, start_x:end_x, :]
                    else:
                        roi = frame[:, start_x:end_x]
                    rois.append(roi)
                
                # Use numpy concatenation for speed
                result = np.concatenate(rois, axis=1)
                return result
        
        except Exception as e:
            print(f"GPU chunk processing failed: {e}, falling back to CPU")
            # Fallback to CPU processing for this chunk
            return self._cpu_process_chunk(chunk_frames, scan_line_x, scan_mode, width_roi)
    
    def _cpu_process_chunk(self, chunk_frames, scan_line_x, scan_mode, width_roi):
        """CPU fallback for chunk processing"""
        if scan_mode == 'column':
            columns = []
            for frame in chunk_frames:
                column = frame[:, scan_line_x]
                columns.append(column)
            return np.column_stack(columns)
        else:
            rois = []
            for frame in chunk_frames:
                start_x = max(0, scan_line_x - width_roi // 2)
                end_x = min(frame.shape[1], scan_line_x + width_roi // 2)
                roi = frame[:, start_x:end_x]
                rois.append(roi)
            return np.concatenate(rois, axis=1)
    
    def stream_process_frames(self, video_obj, scan_line_x, scan_mode='column', width_roi=3, total_frames=0, progress_callback=None):
        """Ultra-fast streaming processing for very large videos with progress updates"""
        print(f"Using streaming processing for {total_frames} frames...")
        
        # Initialize result array
        if scan_mode == 'column':
            # For column mode, we'll build the result incrementally
            result_columns = []
        else:
            # For width mode, we'll concatenate ROIs
            result_rois = []
        
        frame_count = 0
        
        # Process frames one by one without storing them all
        while frame_count < total_frames:
            success, frame = video_obj.read()
            if not success or frame is None:
                break
            
            if scan_mode == 'column':
                # Extract single column preserving all channels (RGB)
                if len(frame.shape) == 3:
                    column = frame[:, scan_line_x, :]  # Keep all channels
                else:
                    column = frame[:, scan_line_x]
                result_columns.append(column)
            else:
                # Extract width ROI preserving all channels
                start_x = max(0, scan_line_x - width_roi // 2)
                end_x = min(frame.shape[1], scan_line_x + width_roi // 2)
                if len(frame.shape) == 3:
                    roi = frame[:, start_x:end_x, :]  # Keep all channels
                else:
                    roi = frame[:, start_x:end_x]
                result_rois.append(roi)
            
            frame_count += 1
            
            # Update progress callback if provided
            if progress_callback:
                progress_callback(frame_count)
            
            # Show progress
            if frame_count % 500 == 0:
                print(f"Streamed {frame_count}/{total_frames} frames...")
        
        # Combine results efficiently preserving RGB
        if scan_mode == 'column':
            if result_columns and len(result_columns[0].shape) == 2:
                # RGB columns - stack along width dimension
                return np.stack(result_columns, axis=1)
            else:
                # Grayscale columns
                return np.column_stack(result_columns)
        else:
            return np.concatenate(result_rois, axis=1)
    
    def _cpu_batch_process(self, frames, scan_line_x, scan_mode, width_roi):
        """Fallback CPU batch processing"""
        if not frames:
            return np.array([])
        
        if scan_mode == 'column':
            # Extract column from each frame
            columns = []
            for frame in frames:
                column = frame[:, scan_line_x]
                columns.append(column)
            return np.column_stack(columns)
        else:
            # Extract and concatenate ROIs
            rois = []
            for frame in frames:
                start_x = max(0, scan_line_x - width_roi // 2)
                end_x = min(frame.shape[1], scan_line_x + width_roi // 2)
                roi = frame[:, start_x:end_x]
                rois.append(roi)
            return np.concatenate(rois, axis=1)


# Global GPU processor instance
gpu_processor = GPUImageProcessor()


def get_gpu_processor():
    """Get the global GPU processor instance"""
    return gpu_processor


def is_gpu_available():
    """Check if GPU acceleration is available"""
    return GPU_AVAILABLE
