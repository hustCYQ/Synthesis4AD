# -*- coding: utf-8 -*-
"""
UI Package - Modern point cloud viewer UI components
Updated: Moved Simple3D runner to core module
"""

from .design_tokens import DesignTokens
from .icons import ModernIconFactory, SystemIconHelper, load_external_icon
from .styles import ModernStylesheet, apply_modern_theme
from .viewer import GLPointCloud
from .ribbon import ModernRibbon, ModernToolButton
from .main_window import MainWindow
from .i18n import tr, set_language, get_language

__all__ = [
    'DesignTokens',
    'ModernIconFactory',
    'SystemIconHelper',
    'load_external_icon',
    'ModernStylesheet',
    'apply_modern_theme',
    'GLPointCloud',
    'ModernRibbon',
    'ModernToolButton',
    'MainWindow',
    'tr',
    'set_language',
    'get_language',
]

__version__ = '2026.v1'
