#!/usr/bin/env python3
"""
Image Metadata Module

This module contains the ImageMetadata class for handling image metadata
including region of interest (ROI) and image shape information.
"""


class ImageMetadata:
    """
    A simple image object class for the region of interest and the shape of the raw image
    
    Attributes:
        roi (numpy.ndarray): Region of interest extracted from the image
        shape (dict): Dictionary containing width and height of the raw image
    """

    def __init__(self):
        """Initialize ImageMetadata with empty roi and zero dimensions"""
        self.roi = []  # Region of interest
        self.shape = {'width': 0, 'height': 0}  # Raw image shape

    def __str__(self):
        """String representation of the ImageMetadata object"""
        return f"{self.__class__.__name__}: {self.__dict__}"
    
    def set_shape(self, width, height):
        """
        Set the shape of the image
        
        Args:
            width (int): Width of the image
            height (int): Height of the image
        """
        self.shape['width'] = width
        self.shape['height'] = height
    
    def set_roi(self, roi):
        """
        Set the region of interest
        
        Args:
            roi (numpy.ndarray): Region of interest array
        """
        self.roi = roi
    
    def get_shape(self):
        """
        Get the shape of the image
        
        Returns:
            dict: Dictionary containing width and height
        """
        return self.shape
    
    def get_roi(self):
        """
        Get the region of interest
        
        Returns:
            numpy.ndarray: Region of interest array
        """
        return self.roi
