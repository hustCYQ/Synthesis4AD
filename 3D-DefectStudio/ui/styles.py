# -*- coding: utf-8 -*-
"""
Styles Module - Centralized stylesheet management
Modern dark theme inspired by VSCode / professional IDE aesthetics
"""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QStyleFactory
from .design_tokens import DesignTokens


class ModernStylesheet:

    @staticmethod
    def get_main_stylesheet() -> str:
        t = DesignTokens
        return f"""
        * {{
            font-family: 'Segoe UI', 'SF Pro Text', 'Roboto', sans-serif;
        }}

        QMainWindow {{
            background-color: {t.DARK_BG_PRIMARY};
            font-size: {t.FONT_SIZE_MD};
        }}

        QWidget {{
            background-color: transparent;
            color: {t.DARK_TEXT_PRIMARY};
        }}

        /* ── Menu Bar ───────────────────────────────────────── */
        QMenuBar {{
            background: #0f1117;
            color: {t.DARK_TEXT_SECONDARY};
            border-bottom: 1px solid #1e2130;
            padding: 2px 4px;
            font-size: {t.FONT_SIZE_SM};
            spacing: 2px;
        }}
        QMenuBar::item {{
            background: transparent;
            padding: 5px 12px;
            border-radius: {t.RADIUS_SM}px;
            color: #8899bb;
        }}
        QMenuBar::item:selected {{
            background: rgba(79,142,247,0.12);
            color: #c5d0f0;
        }}
        QMenuBar::item:pressed {{
            background: rgba(79,142,247,0.20);
            color: #ffffff;
        }}
        QMenu {{
            background: #161926;
            color: {t.DARK_TEXT_PRIMARY};
            border: 1px solid #2a2d3e;
            border-radius: {t.RADIUS_MD}px;
            padding: 4px 0;
            font-size: {t.FONT_SIZE_SM};
        }}
        QMenu::item {{
            padding: 6px 24px 6px 32px;
            color: #9aadcc;
        }}
        QMenu::item:selected {{
            background: rgba(79,142,247,0.18);
            color: #c5d0f0;
        }}
        QMenu::item:disabled {{ color: #2e3558; }}
        QMenu::separator {{
            height: 1px; background: #252840; margin: 4px 12px;
        }}
        QMenu::indicator {{ width: 14px; height: 14px; left: 8px; }}
        QMenu::indicator:checked {{
            background: #4f8ef7; border-radius: 3px;
        }}
        QMenu::icon {{ left: 8px; }}

        /* ── Dock Widgets ───────────────────────────────────── */
        QDockWidget {{
            border: none;
            background: {t.DARK_BG_SECONDARY};
        }}
        QDockWidget::title {{
            background: #1e2130;
            color: {t.DARK_TEXT_SECONDARY};
            padding: 7px 12px;
            font-size: {t.FONT_SIZE_SM};
            font-weight: {t.FONT_WEIGHT_SEMIBOLD};
            letter-spacing: 1.2px;
            text-transform: uppercase;
            border-bottom: 1px solid #2a2d3e;
            border-top: 1px solid #2a2d3e;
        }}
        QDockWidget::close-button, QDockWidget::float-button {{
            background: transparent; border: none; padding: 2px;
        }}
        QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
            background: rgba(255,255,255,0.08); border-radius: 3px;
        }}

        /* ── Status Bar ─────────────────────────────────────── */
        QStatusBar {{
            background: #0d0f1a;
            border-top: 1px solid #1e2130;
            color: {t.DARK_TEXT_SECONDARY};
            font-size: {t.FONT_SIZE_SM};
            padding: 0 6px;
            min-height: 24px;
        }}
        QStatusBar::item {{ border: none; }}
        QStatusBar QLabel {{
            color: {t.DARK_TEXT_SECONDARY};
            padding: 0 6px;
            font-size: {t.FONT_SIZE_SM};
        }}

        /* ── Log / Text Edit ────────────────────────────────── */
        QTextEdit {{
            background: #0f1117;
            color: #a0aec0;
            border: 1px solid #2a2d3e;
            border-radius: {t.RADIUS_SM}px;
            padding: 6px 8px;
            font-family: 'Cascadia Code', 'Consolas', monospace;
            font-size: {t.FONT_SIZE_SM};
            selection-background-color: {t.ACCENT_BLUE};
        }}

        /* ── List Widget ────────────────────────────────────── */
        QListWidget {{
            background: {t.DARK_BG_PRIMARY};
            color: {t.DARK_TEXT_PRIMARY};
            border: none;
            border-right: 1px solid #2a2d3e;
            padding: 4px 0;
            outline: none;
            font-size: {t.FONT_SIZE_MD};
        }}
        QListWidget::item {{
            padding: 7px 14px;
            border-left: 3px solid transparent;
            color: {t.DARK_TEXT_SECONDARY};
        }}
        QListWidget::item:hover {{
            background: rgba(255,255,255,0.05);
            color: {t.DARK_TEXT_PRIMARY};
            border-left: 3px solid rgba(79,142,247,0.4);
        }}
        QListWidget::item:selected {{
            background: rgba(79,142,247,0.15);
            color: #7eb3ff;
            border-left: 3px solid #4f8ef7;
        }}

        /* ── Labels ─────────────────────────────────────────── */
        QLabel {{
            color: {t.DARK_TEXT_PRIMARY};
            background: transparent;
            font-size: {t.FONT_SIZE_MD};
        }}
        QFormLayout QLabel {{
            color: {t.DARK_TEXT_SECONDARY};
            font-size: {t.FONT_SIZE_SM};
            min-width: 80px;
        }}

        /* ── ComboBox ───────────────────────────────────────── */
        QComboBox {{
            background: #1a1d2e;
            color: {t.DARK_TEXT_PRIMARY};
            border: 1px solid #2e3248;
            border-radius: {t.RADIUS_SM}px;
            padding: 4px 32px 4px 10px;   /* right padding leaves room for arrow */
            min-height: 26px;
            font-size: {t.FONT_SIZE_MD};
            selection-background-color: {t.ACCENT_BLUE};
        }}
        QComboBox:hover {{
            border: 1px solid #4f8ef7;
            background: #1e2133;
        }}
        QComboBox:focus {{
            border: 1px solid #4f8ef7;
            background: #1e2133;
            outline: none;
        }}
        QComboBox:disabled {{
            background: #13151f;
            color: #2e3558;
            border-color: #1e2130;
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            border: none;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            image: none;
            width: 0;
            height: 0;
            border-style: solid;
            border-width: 5px 4px 0 4px;
            border-color: {t.DARK_TEXT_SECONDARY} transparent transparent transparent;
            margin-right: 6px;
        }}
        QComboBox::down-arrow:hover {{
            border-color: #4f8ef7 transparent transparent transparent;
        }}
        QComboBox QAbstractItemView {{
            background: #1e2133;
            color: {t.DARK_TEXT_PRIMARY};
            border: 1px solid #2e3248;
            border-radius: {t.RADIUS_SM}px;
            selection-background-color: rgba(79,142,247,0.25);
            selection-color: #7eb3ff;
            outline: none;
            padding: 2px;
        }}

        /* ── SpinBox ────────────────────────────────────────── */
        QDoubleSpinBox, QSpinBox {{
            background: #1a1d2e;
            color: {t.DARK_TEXT_PRIMARY};
            border: 1px solid #2e3248;
            border-radius: {t.RADIUS_SM}px;
            padding: 4px 6px 4px 10px;
            min-height: 26px;
            font-size: {t.FONT_SIZE_MD};
        }}
        QDoubleSpinBox:hover, QSpinBox:hover {{
            border: 1px solid #4f8ef7;
            background: #1e2133;
        }}
        QDoubleSpinBox:focus, QSpinBox:focus {{
            border: 1px solid #4f8ef7;
            background: #1e2133;
            outline: none;
        }}
        QDoubleSpinBox:disabled, QSpinBox:disabled {{
            background: #13151f;
            color: #2e3558;
            border-color: #1e2130;
        }}
        QDoubleSpinBox::up-button, QSpinBox::up-button,
        QDoubleSpinBox::down-button, QSpinBox::down-button {{
            subcontrol-origin: border;
            width: 18px;
            background: #1e2133;
            border: none;
            border-left: 1px solid #2e3248;
        }}
        QDoubleSpinBox::up-button, QSpinBox::up-button {{
            subcontrol-position: top right;
            border-bottom: 1px solid #2e3248;
            border-top-right-radius: {t.RADIUS_SM}px;
        }}
        QDoubleSpinBox::down-button, QSpinBox::down-button {{
            subcontrol-position: bottom right;
            border-bottom-right-radius: {t.RADIUS_SM}px;
        }}
        QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
        QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {{
            background: rgba(79,142,247,0.18);
        }}
        QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {{
            image: none;
            width: 0; height: 0;
            border-style: solid;
            border-width: 0 3px 4px 3px;
            border-color: transparent transparent {t.DARK_TEXT_SECONDARY} transparent;
        }}
        QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {{
            image: none;
            width: 0; height: 0;
            border-style: solid;
            border-width: 4px 3px 0 3px;
            border-color: {t.DARK_TEXT_SECONDARY} transparent transparent transparent;
        }}
        QDoubleSpinBox::up-arrow:hover, QSpinBox::up-arrow:hover {{
            border-color: transparent transparent #4f8ef7 transparent;
        }}
        QDoubleSpinBox::down-arrow:hover, QSpinBox::down-arrow:hover {{
            border-color: #4f8ef7 transparent transparent transparent;
        }}

        /* ── LineEdit ───────────────────────────────────────── */
        QLineEdit {{
            background: #1a1d2e;
            color: {t.DARK_TEXT_PRIMARY};
            border: 1px solid #2e3248;
            border-radius: {t.RADIUS_SM}px;
            padding: 4px 10px;
            min-height: 26px;
            font-size: {t.FONT_SIZE_MD};
        }}
        QLineEdit:hover {{ border: 1px solid #4f8ef7; background: #1e2133; }}
        QLineEdit:focus {{ border: 1px solid #4f8ef7; background: #1e2133; outline: none; }}
        QLineEdit:disabled {{ background: #13151f; color: #2e3558; border-color: #1e2130; }}

        /* ── Sliders ────────────────────────────────────────── */
        QSlider::groove:horizontal {{
            height: 4px; background: #2a2d3e; border-radius: 2px;
        }}
        QSlider::sub-page:horizontal {{
            background: #4f8ef7; border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            width: 14px; height: 14px;
            background: #ffffff; border: 2px solid #4f8ef7;
            border-radius: 7px; margin: -5px 0;
        }}
        QSlider::handle:horizontal:hover {{
            background: #4f8ef7; border-color: #7eb3ff;
        }}
        QSlider::handle:horizontal:pressed {{ background: #3a7ce8; }}
        QSlider:disabled {{ opacity: 0.35; }}

        /* ── Checkboxes ─────────────────────────────────────── */
        QCheckBox {{
            color: {t.DARK_TEXT_SECONDARY}; spacing: 8px; font-size: {t.FONT_SIZE_MD};
        }}
        QCheckBox:hover {{ color: {t.DARK_TEXT_PRIMARY}; }}
        QCheckBox::indicator {{
            width: 15px; height: 15px;
            border: 1.5px solid #3a3f5c; border-radius: 3px; background: #1a1d2e;
        }}
        QCheckBox::indicator:hover {{ border-color: #4f8ef7; background: #1e2133; }}
        QCheckBox::indicator:checked {{ background: #4f8ef7; border-color: #4f8ef7; }}

        /* ── Scroll Bars ────────────────────────────────────── */
        QScrollBar:vertical {{
            background: transparent; width: 8px; margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: #2e3248; border-radius: 4px; min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{ background: #4f8ef7; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{
            background: transparent; height: 8px; margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: #2e3248; border-radius: 4px; min-width: 24px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: #4f8ef7; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

        /* ── Message Boxes ──────────────────────────────────── */
        QMessageBox {{ background: #1a1d2e; }}
        QMessageBox QLabel {{ color: {t.DARK_TEXT_PRIMARY}; font-size: {t.FONT_SIZE_MD}; }}
        QMessageBox QPushButton {{
            background: #4f8ef7; color: white; border: none;
            padding: 6px 20px; border-radius: {t.RADIUS_SM}px;
            font-size: {t.FONT_SIZE_MD}; min-width: 72px;
        }}
        QMessageBox QPushButton:hover {{ background: #3a7ce8; }}

        /* ── Tool Tips ──────────────────────────────────────── */
        QToolTip {{
            background: #1e2133; color: {t.DARK_TEXT_PRIMARY};
            border: 1px solid #2e3248; border-radius: {t.RADIUS_SM}px;
            padding: 5px 9px; font-size: {t.FONT_SIZE_SM};
        }}

        /* ── Toolbar ────────────────────────────────────────── */
        QToolBar {{
            background: #141620; border: none;
            border-bottom: 1px solid #2a2d3e; spacing: 0; padding: 0;
        }}
        """

    @staticmethod
    def get_ribbon_stylesheet() -> str:
        t = DesignTokens
        return f"""
        QTabWidget {{ background: #141620; }}
        QTabWidget::pane {{
            border: none; background: #181b2a;
            border-bottom: 1px solid #2a2d3e;
        }}
        QTabBar {{ background: #141620; }}
        QTabBar::tab {{
            background: transparent; color: #5a6282;
            font-size: {t.FONT_SIZE_MD}; font-weight: {t.FONT_WEIGHT_MEDIUM};
            padding: 6px 16px; border: none;
            border-bottom: 2px solid transparent; letter-spacing: 0.3px;
        }}
        QTabBar::tab:hover {{
            color: #8899cc; background: rgba(255,255,255,0.04);
            border-bottom: 2px solid #3a4268;
        }}
        QTabBar::tab:selected {{
            color: #c5d0f0; background: #181b2a;
            border-bottom: 2px solid #4f8ef7;
            font-weight: {t.FONT_WEIGHT_SEMIBOLD};
        }}
        QWidget#RibbonPage {{ background: #181b2a; }}
        QWidget#GroupCard {{
            background: #1e2133; border: 1px solid #2a2d3e; border-radius: 7px;
        }}
        QWidget#GroupCard:hover {{ border: 1px solid #3a4268; }}
        QLabel#GroupTitle {{
            color: #44506e; font-size: 7.5pt;
            font-weight: {t.FONT_WEIGHT_SEMIBOLD};
            letter-spacing: 1px; background: transparent;
        }}
        """

    @staticmethod
    def get_button_stylesheet() -> str:
        t = DesignTokens
        return f"""
        QToolButton {{
            background: transparent; border: 1px solid transparent;
            color: #8899bb; font-size: {t.FONT_SIZE_SM};
            font-weight: {t.FONT_WEIGHT_MEDIUM};
            padding: 4px 4px 3px 4px;
            border-radius: {t.RADIUS_MD}px; min-width: 52px;
        }}
        QToolButton:hover {{
            background: rgba(79,142,247,0.10);
            border: 1px solid rgba(79,142,247,0.25); color: #c5d0f0;
        }}
        QToolButton:pressed {{
            background: rgba(79,142,247,0.20);
            border: 1px solid rgba(79,142,247,0.50); color: #ffffff;
        }}
        QToolButton:checked {{
            background: rgba(79,142,247,0.20);
            border: 1px solid #4f8ef7; color: #7eb3ff;
        }}
        QToolButton:checked:hover {{
            background: rgba(79,142,247,0.28); border: 1px solid #7eb3ff;
        }}
        QToolButton:disabled {{
            color: #2e3558; background: transparent; border: 1px solid transparent;
        }}
        """

    @staticmethod
    def get_prop_panel_stylesheet() -> str:
        t = DesignTokens
        return f"""
        QWidget#PropSection {{
            background: #1a1d2e; border: 1px solid #2a2d3e;
            border-radius: 6px; margin: 2px 0;
        }}
        QLabel#PropSectionTitle {{
            color: #44506e; font-size: 7.5pt;
            font-weight: {t.FONT_WEIGHT_SEMIBOLD};
            letter-spacing: 1px; background: transparent; padding: 4px 0 2px 0;
        }}
        QLabel#PropValue {{
            color: #7eb3ff; font-size: {t.FONT_SIZE_LG};
            font-weight: {t.FONT_WEIGHT_SEMIBOLD}; background: transparent;
        }}
        """


def apply_modern_theme(main_window: QMainWindow, ribbon_tabs: QTabWidget):
    main_window.setStyle(QStyleFactory.create("fusion"))
    main_window.setStyleSheet(
        ModernStylesheet.get_main_stylesheet() +
        ModernStylesheet.get_prop_panel_stylesheet()
    )
    ribbon_tabs.setStyleSheet(ModernStylesheet.get_ribbon_stylesheet())
