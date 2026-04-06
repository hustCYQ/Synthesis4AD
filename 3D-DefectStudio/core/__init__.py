# -*- coding: utf-8 -*-
"""
Core Package - Business logic and processing modules
"""

from .training_worker import Simple3DRunner, Simple3DConfig, find_conda_python

# Optional modules (may not be present in all installations)
try:
    from .anomaly_core import AnomalyGenerator
except ImportError:
    AnomalyGenerator = None

try:
    from .cloud_interaction import PointCloudInteractor
except ImportError:
    PointCloudInteractor = None

__all__ = [
    'Simple3DRunner',
    'Simple3DConfig',
    'find_conda_python',
    'AnomalyGenerator',
    'PointCloudInteractor',
]

__version__ = '2026.v1'
