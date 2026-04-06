# -*- coding: utf-8 -*-
"""
3D Viewer Module - OpenGL point cloud visualization
"""

from typing import Optional, List
import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget
import pyqtgraph.opengl as gl


class GLPointCloud(gl.GLViewWidget):
    """Enhanced 3D point cloud viewer"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCameraPosition(distance=2)
        self.opts['fov'] = 60
        
        # Grid & Axes
        self.grid = gl.GLGridItem()
        self.grid.setSize(10, 10)
        self.grid.setSpacing(1, 1)
        self.axes = self._make_axes(size=2)
        self.addItem(self.grid)
        for ax in self.axes:
            self.addItem(ax)
        self.grid.hide()
        for ax in self.axes:
            ax.hide()
        
        # Point Cloud
        self.scatter = None
        self.selection_overlay = None
        
        # Auto Rotate
        self._auto_rotate = False
        self._rot_timer = QTimer(self)
        self._rot_timer.timeout.connect(self._spin)
        self._angle = 0
    
    def _make_axes(self, size: float = 1.0) -> List[gl.GLLinePlotItem]:
        """
        Create coordinate axes
        
        Args:
            size: Axis length
        
        Returns:
            List of axis line items
        """
        x = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [size, 0, 0]], dtype=float),
            color=(1, 0, 0, 1), 
            width=2, 
            antialias=True
        )
        y = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, size, 0]], dtype=float),
            color=(0, 1, 0, 1), 
            width=2, 
            antialias=True
        )
        z = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 0, size]], dtype=float),
            color=(0, 0, 1, 1), 
            width=2, 
            antialias=True
        )
        return [x, y, z]
    
    def set_axes_visible(self, visible: bool):
        """
        Toggle axes visibility
        
        Args:
            visible: True to show axes
        """
        for ax in self.axes:
            ax.setVisible(visible)
    
    def set_grid_visible(self, visible: bool):
        """
        Toggle grid visibility
        
        Args:
            visible: True to show grid
        """
        self.grid.setVisible(visible)
    
    def set_auto_rotate(self, enabled: bool):
        """
        Toggle auto-rotation
        
        Args:
            enabled: True to enable auto-rotation
        """
        self._auto_rotate = enabled
        if enabled:
            self._rot_timer.start(30)
        else:
            self._rot_timer.stop()
    
    def _spin(self):
        """Internal rotation update"""
        self._angle += 1
        self.orbit(1, 0)
    
    def clear_points(self):
        """Clear all point cloud data"""
        if self.scatter is not None:
            self.removeItem(self.scatter)
            self.scatter = None
        if self.selection_overlay is not None:
            try:
                self.removeItem(self.selection_overlay)
            except Exception:
                pass
            self.selection_overlay = None
    
    def set_points(self, xyz: np.ndarray, rgb01: Optional[np.ndarray] = None, size: float = 2.0):
        """
        Set point cloud data
        
        Args:
            xyz: Point coordinates (N, 3)
            rgb01: Point colors (N, 3) in 0-1 range
            size: Point size in pixels
        """
        self.clear_points()
        
        if rgb01 is None:
            rgb01 = np.ones_like(xyz) * 0.9
        
        pts = gl.GLScatterPlotItem(
            pos=xyz.astype(float),
            color=rgb01.astype(float),
            size=size,
            pxMode=True
        )
        self.scatter = pts
        self.addItem(self.scatter)
    
    def set_selection_points(self, xyz_sel: Optional[np.ndarray], size: float = 3.0):
        """
        Display selection overlay
        
        Args:
            xyz_sel: Selected point coordinates (N, 3)
            size: Point size in pixels
        """
        if self.selection_overlay is not None:
            try:
                self.removeItem(self.selection_overlay)
            except Exception:
                pass
            self.selection_overlay = None
        
        if xyz_sel is None or len(xyz_sel) == 0:
            return
        
        # Yellow selection color
        col = np.tile(np.array([1.0, 1.0, 0.0, 1.0]), (xyz_sel.shape[0], 1))
        item = gl.GLScatterPlotItem(
            pos=xyz_sel.astype(float),
            color=col,
            size=size,
            pxMode=True
        )
        self.selection_overlay = item
        self.addItem(self.selection_overlay)
