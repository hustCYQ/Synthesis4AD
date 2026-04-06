# -*- coding: utf-8 -*-
"""
MPAS - Mesh Point cloud Anomaly Synthesis
3D点云异常合成库
"""

from .mpas import (
    sphere,
    scratch,
    bend,
    crack,
    freedom,
    generate,
    load_data_as_pointcloud,
    save_pointcloud,
    save_gt,
    save_mask,
    get_bbox_diagonal,
    normalize_points,
    resample_with_sampling
)

__version__ = "0.1.0"
__author__ = "MPAS Team"

__all__ = [
    'sphere',
    'scratch',
    'bend',
    'crack',
    'freedom',
    'generate',
    'load_data_as_pointcloud',
    'save_pointcloud',
    'save_gt',
    'save_mask',
    'get_bbox_diagonal',
    'normalize_points',
    'resample_with_sampling'
]