# -*- coding: utf-8 -*-
"""
Design Tokens - UI Design System Constants
Centralized design parameters for consistent theming
"""


class DesignTokens:
    """Modern design tokens for consistent theming"""
    
    # ==================== Colors ====================
    
    # Dark Theme - Background
    DARK_BG_PRIMARY = "#1a1a1a"
    DARK_BG_SECONDARY = "#252525"
    DARK_BG_TERTIARY = "#2d2d2d"
    DARK_BORDER = "#3a3a3a"
    
    # Dark Theme - Text
    DARK_TEXT_PRIMARY = "#e8e8e8"
    DARK_TEXT_SECONDARY = "#b0b0b0"
    DARK_TEXT_TERTIARY = "#808080"
    
    # Accent Colors
    ACCENT_BLUE = "#0078d4"
    ACCENT_BLUE_HOVER = "#106ebe"
    ACCENT_BLUE_PRESSED = "#005a9e"
    ACCENT_BLUE_LIGHT = "#4da6ff"
    
    # Status Colors
    SUCCESS = "#107c10"
    SUCCESS_LIGHT = "#5cb85c"
    WARNING = "#ffa500"
    WARNING_LIGHT = "#ffc14d"
    ERROR = "#d13438"
    ERROR_LIGHT = "#ff5555"
    INFO = "#0078d4"
    INFO_LIGHT = "#4da6ff"
    
    # Semantic Colors
    SELECTION = "#ffeb3b"
    SELECTION_LIGHT = "#fff176"
    ANOMALY = "#ff4444"
    ANOMALY_DARK = "#cc0000"
    
    # ==================== Spacing ====================
    
    SPACE_XXS = 2
    SPACE_XS = 4
    SPACE_SM = 8
    SPACE_MD = 12
    SPACE_LG = 16
    SPACE_XL = 24
    SPACE_XXL = 32
    
    # ==================== Border Radius ====================
    
    RADIUS_SM = 4
    RADIUS_MD = 6
    RADIUS_LG = 8
    RADIUS_XL = 12
    
    # ==================== Shadows ====================
    
    SHADOW_SM = "0 1px 3px rgba(0,0,0,0.3)"
    SHADOW_MD = "0 2px 6px rgba(0,0,0,0.4)"
    SHADOW_LG = "0 4px 12px rgba(0,0,0,0.5)"
    SHADOW_XL = "0 8px 24px rgba(0,0,0,0.6)"
    
    # ==================== Typography ====================
    
    FONT_FAMILY = "'Segoe UI', 'SF Pro Display', 'Roboto', 'Arial', sans-serif"
    FONT_SIZE_XS = "8pt"
    FONT_SIZE_SM = "8.5pt"
    FONT_SIZE_MD = "9.5pt"
    FONT_SIZE_LG = "10pt"
    FONT_SIZE_XL = "11pt"
    FONT_SIZE_XXL = "13pt"
    
    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_SEMIBOLD = 600
    FONT_WEIGHT_BOLD = 700
    
    # ==================== Animation ====================
    
    TRANSITION_FAST = "100ms"
    TRANSITION_NORMAL = "200ms"
    TRANSITION_SLOW = "300ms"
    
    # ==================== Sizes ====================
    
    BUTTON_MIN_WIDTH = 75
    BUTTON_MIN_HEIGHT = 32
    ICON_SIZE_SM = 24
    ICON_SIZE_MD = 32
    ICON_SIZE_LG = 48
    
    # ==================== Z-Index ====================
    
    Z_BACKGROUND = 0
    Z_CONTENT = 1
    Z_OVERLAY = 10
    Z_MODAL = 100
    Z_TOOLTIP = 1000


class ColorScheme:
    """Helper class for color manipulation"""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """Convert RGB to hex color"""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def lighten(hex_color: str, amount: float = 0.2) -> str:
        """Lighten a color by amount (0-1)"""
        r, g, b = ColorScheme.hex_to_rgb(hex_color)
        r = min(255, int(r + (255 - r) * amount))
        g = min(255, int(g + (255 - g) * amount))
        b = min(255, int(b + (255 - b) * amount))
        return ColorScheme.rgb_to_hex(r, g, b)
    
    @staticmethod
    def darken(hex_color: str, amount: float = 0.2) -> str:
        """Darken a color by amount (0-1)"""
        r, g, b = ColorScheme.hex_to_rgb(hex_color)
        r = max(0, int(r * (1 - amount)))
        g = max(0, int(g * (1 - amount)))
        b = max(0, int(b * (1 - amount)))
        return ColorScheme.rgb_to_hex(r, g, b)
