# -*- coding: utf-8 -*-
"""
3D Point Cloud Visualization 2026.v1
Main entry point for the application

Copyright © 2026 Huazhong University of Science and Technology
Operations Research and Optimization Team
https://github.com/hustCYQ/Synthesis4AD
"""

import sys
from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtGui import QFont
import pyqtgraph as pg

from ui import MainWindow, DesignTokens


def main():
    """Application entry point"""
    # Create application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle(QStyleFactory.create("fusion"))
    
    # Set application-wide font
    font = QFont(DesignTokens.FONT_FAMILY.replace("'", "").split(',')[0], 9)
    app.setFont(font)
    
    # PyQtGraph configuration
    pg.setConfigOption('background', DesignTokens.DARK_BG_PRIMARY)
    pg.setConfigOption('foreground', DesignTokens.DARK_TEXT_PRIMARY)
    pg.setConfigOption('antialias', True)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
