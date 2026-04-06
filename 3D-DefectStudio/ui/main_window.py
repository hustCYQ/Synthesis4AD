# -*- coding: utf-8 -*-
"""
Main Window Module - Application main window
Integrates all UI components and handles data management

Updated: Integrated Simple3D runner functionality
"""

import os
import time
from typing import Optional

import numpy as np
from PySide6.QtCore import Qt, QSettings, QSize
from PySide6.QtGui import QColor, QVector3D, QFont, QAction, QActionGroup
from PySide6.QtWidgets import (
    QMainWindow, QFileDialog, QDockWidget, QListWidget, QListWidgetItem,
    QWidget, QFormLayout, QLabel, QComboBox, QDoubleSpinBox, QSlider,
    QHBoxLayout, QToolButton, QColorDialog, QTextEdit, QStatusBar,
    QMessageBox, QInputDialog, QToolBar, QFrame, QSizePolicy
)

import pyqtgraph as pg

from .design_tokens import DesignTokens
from .styles import apply_modern_theme
from .ribbon import ModernRibbon
from .viewer import GLPointCloud
from .icons import SystemIconHelper
from .i18n import tr, set_language, get_language

# Import from core module
try:
    from core.training_worker import Simple3DRunner
except ImportError:
    from core import Simple3DRunner


# ──────────────────────────────────────────────────────────────────────────────
#  Mode indicator constants
# ──────────────────────────────────────────────────────────────────────────────
_MODE_COLORS = {
    'ready':   '#44cc66',   # green
    'no_file': '#44506e',   # muted gray-blue
    'loading': '#f0c040',   # amber
    'select':  '#4f8ef7',   # blue
    'defect':  '#f07040',   # orange
}


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self._max_vis_points = 2_000_000
        self.settings = QSettings('RibbonPCD', 'ViewerModular')

        # Data management
        self._pcd_cache: dict = {}
        self._current_path: Optional[str] = None
        self._mono_color = QColor(230, 230, 230)

        # Simple3D Runner
        self._simple3d_runner: Optional[Simple3DRunner] = None
        self._simple3d_path = self.settings.value('simple3d_path', os.getcwd())

        # Build UI (order matters: menubar → ribbon → viewer → docks → statusbar)
        self._setup_menubar()
        self._setup_ribbon()
        self._setup_viewer()
        self._setup_docks()
        self._setup_statusbar()

        # Apply theme
        apply_modern_theme(self, self.ribbon.tabs)

        # Interaction module (optional core/)
        self._setup_interaction()

        # Setup Simple3D runner
        self._setup_simple3d_runner()

        # Wire up all signals
        self._connect_actions()

        # Default checked states
        self.ribbon.btn_axis.setChecked(True)
        self.ribbon.btn_grid.setChecked(True)
        self.act_axis.setChecked(True)
        self.act_grid.setChecked(True)

        # Dock sizes
        try:
            self.resizeDocks([self.file_dock, self.prop_dock], [240, 340], Qt.Horizontal)
            self.resizeDocks([self.log_dock], [220], Qt.Vertical)
        except Exception:
            pass

        # PyQtGraph config
        pg.setConfigOption('background', DesignTokens.DARK_BG_PRIMARY)
        pg.setConfigOption('foreground', DesignTokens.DARK_TEXT_PRIMARY)

        # Initial UI state (no file loaded)
        self._update_ui_state(False)
        self._retranslate_ui()
        self.setWindowTitle(tr('window_title'))

    # ══════════════════════════════════════════════════════════════════════════
    #  Setup helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_menubar(self):
        """Build the full menu bar."""
        mb = self.menuBar()

        # ── File ──────────────────────────────────────────────────────────────
        self.menu_file = mb.addMenu(tr('menu_file'))

        self.act_open = QAction(tr('action_open'), self)
        self.act_open.setShortcut('Ctrl+O')
        self.act_open.triggered.connect(self.open_files)

        self.act_export = QAction(tr('action_export'), self)
        self.act_export.setShortcut('Ctrl+E')
        self.act_export.triggered.connect(self.export_current)

        self.act_save_data = QAction(tr('action_save_data'), self)
        self.act_save_data.setShortcut('Ctrl+S')
        self.act_save_data.triggered.connect(self.save_current_data)

        self.act_exit = QAction(tr('action_exit'), self)
        self.act_exit.setShortcut('Alt+F4')
        self.act_exit.triggered.connect(self.close)

        self.menu_file.addAction(self.act_open)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_export)
        self.menu_file.addAction(self.act_save_data)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_exit)

        # ── Edit ──────────────────────────────────────────────────────────────
        self.menu_edit = mb.addMenu(tr('menu_edit'))

        self.act_clear = QAction(tr('action_clear'), self)
        self.act_clear.triggered.connect(self.clear_scene)

        self.act_delete_file = QAction(tr('action_delete'), self)
        self.act_delete_file.triggered.connect(self.delete_current_file)

        self.menu_edit.addSeparator()

        self.act_select_mode = QAction(tr('action_select_mode'), self)
        self.act_select_mode.setCheckable(True)
        self.act_select_mode.setShortcut('S')

        self.act_delete_sel = QAction(tr('action_delete_sel'), self)
        self.act_delete_sel.setShortcut('Del')

        self.act_clear_sel = QAction(tr('action_clear_sel'), self)
        self.act_clear_sel.setShortcut('Escape')

        self.act_restore = QAction(tr('action_restore'), self)

        self.menu_edit.addAction(self.act_clear)
        self.menu_edit.addAction(self.act_delete_file)
        self.menu_edit.addSeparator()
        self.menu_edit.addAction(self.act_select_mode)
        self.menu_edit.addAction(self.act_delete_sel)
        self.menu_edit.addAction(self.act_clear_sel)
        self.menu_edit.addAction(self.act_restore)

        # ── View ──────────────────────────────────────────────────────────────
        self.menu_view = mb.addMenu(tr('menu_view'))

        self.act_reset_view = QAction(tr('action_reset_view'), self)
        self.act_reset_view.setShortcut('F')
        self.act_reset_view.triggered.connect(self.reset_view)

        self.act_axis = QAction(tr('action_axis'), self)
        self.act_axis.setCheckable(True)
        self.act_axis.setShortcut('A')

        self.act_grid = QAction(tr('action_grid'), self)
        self.act_grid.setCheckable(True)
        self.act_grid.setShortcut('G')

        self.act_rotate = QAction(tr('action_rotate'), self)
        self.act_rotate.setCheckable(True)
        self.act_rotate.setShortcut('R')

        self.act_zoom_in = QAction(tr('action_zoom_in'), self)
        self.act_zoom_in.setShortcut('+')
        self.act_zoom_in.triggered.connect(lambda: self._do_zoom(0.9))

        self.act_zoom_out = QAction(tr('action_zoom_out'), self)
        self.act_zoom_out.setShortcut('-')
        self.act_zoom_out.triggered.connect(lambda: self._do_zoom(1/0.9))

        self.act_bg_color = QAction(tr('action_bg_color'), self)
        self.act_bg_color.triggered.connect(self._pick_background_color)

        self.act_theme = QAction(tr('action_theme'), self)
        self.act_theme.triggered.connect(self.toggle_theme)

        self.menu_view.addAction(self.act_reset_view)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.act_axis)
        self.menu_view.addAction(self.act_grid)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.act_rotate)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.act_zoom_in)
        self.menu_view.addAction(self.act_zoom_out)
        self.menu_view.addSeparator()
        self.menu_view.addAction(self.act_bg_color)
        self.menu_view.addAction(self.act_theme)

        # ── Language ──────────────────────────────────────────────────────────
        self.menu_lang = mb.addMenu(tr('menu_language'))
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)

        self.act_lang_en = QAction(tr('lang_en'), self)
        self.act_lang_en.setCheckable(True)
        self.act_lang_en.setChecked(get_language() == 'en')
        self.act_lang_en.triggered.connect(lambda: self._switch_language('en'))

        self.act_lang_zh = QAction(tr('lang_zh'), self)
        self.act_lang_zh.setCheckable(True)
        self.act_lang_zh.setChecked(get_language() == 'zh')
        self.act_lang_zh.triggered.connect(lambda: self._switch_language('zh'))

        lang_group.addAction(self.act_lang_en)
        lang_group.addAction(self.act_lang_zh)
        self.menu_lang.addAction(self.act_lang_en)
        self.menu_lang.addAction(self.act_lang_zh)

        # ── Help ──────────────────────────────────────────────────────────────
        self.menu_help_menu = mb.addMenu(tr('menu_help'))

        self.act_help = QAction(tr('action_help'), self)
        self.act_help.setShortcut('F1')
        self.act_help.triggered.connect(self._show_help)

        self.act_about = QAction(tr('action_about'), self)
        self.act_about.triggered.connect(self._show_about)

        self.menu_help_menu.addAction(self.act_help)
        self.menu_help_menu.addSeparator()
        self.menu_help_menu.addAction(self.act_about)

    def _setup_ribbon(self):
        """Setup ribbon toolbar."""
        self.ribbon = ModernRibbon(self)
        self.top_toolbar = QToolBar('RibbonHost', self)
        self.top_toolbar.setMovable(False)
        self.top_toolbar.setFloatable(False)
        self.top_toolbar.setAllowedAreas(Qt.TopToolBarArea)
        self.addToolBar(Qt.TopToolBarArea, self.top_toolbar)
        self.top_toolbar.addWidget(self.ribbon)

    def _setup_viewer(self):
        """Setup 3D viewer."""
        self.view3d = GLPointCloud(self)
        self.setCentralWidget(self.view3d)

    def _setup_docks(self):
        """Setup dock widgets."""
        # File list
        self.file_dock = QDockWidget(tr('dock_files'), self)
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self._file_item_clicked)
        self.file_dock.setWidget(self.file_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_dock)

        # Properties
        self.prop_dock = QDockWidget(tr('dock_properties'), self)
        self.prop_panel = self._make_prop_panel()
        self.prop_dock.setWidget(self.prop_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.prop_dock)

        # Log
        self.log_dock = QDockWidget(tr('dock_log'), self)
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_dock.setWidget(self.log_edit)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)

    def _setup_statusbar(self):
        """Setup enhanced status bar with persistent indicators."""
        self.status = QStatusBar(self)
        self.setStatusBar(self.status)
        self.status.setSizeGripEnabled(True)

        # ── Mode indicator (permanent left-ish) ──────────────────────────────
        self._mode_dot = QLabel()
        self._mode_dot.setFixedSize(8, 8)
        self._mode_dot.setStyleSheet(
            f"background: {_MODE_COLORS['no_file']}; border-radius: 4px;"
        )

        self._mode_label = QLabel(tr('status_no_file'))
        self._mode_label.setStyleSheet(
            f"color: {DesignTokens.DARK_TEXT_SECONDARY}; "
            f"font-size: {DesignTokens.FONT_SIZE_SM};"
        )
        self._mode_label.setMinimumWidth(120)

        mode_widget = QWidget()
        mode_widget.setStyleSheet("background: transparent;")
        mh = QHBoxLayout(mode_widget)
        mh.setContentsMargins(4, 0, 8, 0)
        mh.setSpacing(5)
        mh.addWidget(self._mode_dot)
        mh.addWidget(self._mode_label)

        # ── File name (permanent) ─────────────────────────────────────────────
        self._status_file = QLabel(tr('status_no_file'))
        self._status_file.setStyleSheet(
            f"color: {DesignTokens.DARK_TEXT_SECONDARY}; "
            f"font-size: {DesignTokens.FONT_SIZE_SM};"
        )
        self._status_file.setMinimumWidth(160)
        self._status_file.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # ── Separator ─────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #252840; max-width: 1px; margin: 4px 2px;")

        # ── Point count (permanent) ───────────────────────────────────────────
        self._status_points = QLabel(f"0 {tr('pts_label')}")
        self._status_points.setStyleSheet(
            f"color: #4f8ef7; "
            f"font-size: {DesignTokens.FONT_SIZE_SM}; "
            f"font-weight: 600;"
        )
        self._status_points.setMinimumWidth(80)
        self._status_points.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.status.addPermanentWidget(mode_widget)
        self.status.addPermanentWidget(self._status_file, 1)
        self.status.addPermanentWidget(sep)
        self.status.addPermanentWidget(self._status_points)

    def _setup_interaction(self):
        """Setup interaction handler (requires core modules)."""
        try:
            from core.cloud_interaction import PointCloudInteractor
            self.interactor = PointCloudInteractor(self)

            r = self.ribbon
            r.btn_select_mode.toggled.connect(self.interactor.toggle_select_mode)
            r.btn_delete_sel.clicked.connect(self.interactor.delete_selection)
            r.btn_cancel_sel.clicked.connect(self.interactor.clear_selection)
            r.btn_restore_all.clicked.connect(self.interactor.restore_all)
            self.log("✓ Interaction module loaded successfully")
        except ImportError as e:
            self.log(f"⚠️ Warning: Interaction module not found — {e}")
            self.interactor = None
            r = self.ribbon
            for btn in [r.btn_1d_point, r.btn_1d_scratch, r.btn_2d_bend,
                        r.btn_2d_fracture, r.btn_3d_areal, r.btn_3d_irreg]:
                btn.setEnabled(False)
                btn.setToolTip("Requires core modules: mpas.py & cloud_interaction.py")
        except Exception as e:
            self.log(f"⚠️ Error loading interaction module: {e}")
            self.interactor = None

    def _setup_simple3d_runner(self):
        """Setup Simple3D runner."""
        self._simple3d_runner = Simple3DRunner(self._simple3d_path, self)
        
        # Connect signals
        self._simple3d_runner.log_message.connect(self._on_simple3d_log)
        self._simple3d_runner.status_changed.connect(self._on_simple3d_status)
        self._simple3d_runner.run_finished.connect(self._on_simple3d_finished)
        
        # Connect ribbon signals
        self.ribbon.simple3d_run_requested.connect(self._run_simple3d)
        self.ribbon.simple3d_stop_requested.connect(self._stop_simple3d)
        self.ribbon.btn_clear_log.clicked.connect(self.log_edit.clear)
        
        self.log("✓ Simple3D runner initialized")

    def _make_prop_panel(self) -> QWidget:
        """Create properties panel."""
        w = QWidget()
        form = QFormLayout(w)
        form.setSpacing(10)
        form.setContentsMargins(12, 12, 12, 12)

        self.lbl_file   = QLabel('—')
        self.lbl_points = QLabel('0')
        self.lbl_points.setStyleSheet("color: #4f8ef7; font-weight: 600;")

        self.cmb_color_mode = QComboBox()
        self.cmb_color_mode.addItems([
            tr('color_auto'), tr('color_raw_rgb'), tr('color_score_lut'),
            tr('color_x_grad'), tr('color_y_grad'), tr('color_z_grad'), tr('color_solid')
        ])
        self.cmb_color_mode.currentIndexChanged.connect(self.apply_coloring)

        self.cmb_lut = QComboBox()
        self.cmb_lut.addItems(['Jet', 'Grayscale'])
        self.cmb_lut.currentIndexChanged.connect(self.apply_coloring)

        self.btn_pick_color = QToolButton()
        self.btn_pick_color.setIcon(SystemIconHelper.get_icon('color'))
        self.btn_pick_color.setToolTip('Pick solid color')
        self.btn_pick_color.clicked.connect(self._pick_mono_color)
        self._update_color_button()

        self.sp_point_size = QDoubleSpinBox()
        self.sp_point_size.setRange(0.5, 20.0)
        self.sp_point_size.setValue(2.0)
        self.sp_point_size.valueChanged.connect(self._update_point_size)

        self.sl_opacity = QSlider(Qt.Horizontal)
        self.sl_opacity.setRange(10, 100)
        self.sl_opacity.setValue(100)
        self.sl_opacity.valueChanged.connect(self._update_opacity)
        self.lbl_opacity_val = QLabel(f"{self.sl_opacity.value()}%")
        self.sl_opacity.valueChanged.connect(
            lambda v: self.lbl_opacity_val.setText(f"{v}%")
        )

        # Store form row label references for retranslation
        self._form_lbl_file        = QLabel(tr('prop_file'))
        self._form_lbl_points      = QLabel(tr('prop_points'))
        self._form_lbl_color_mode  = QLabel(tr('prop_color_mode'))
        self._form_lbl_lut         = QLabel(tr('prop_lut'))
        self._form_lbl_solid_color = QLabel(tr('prop_solid_color'))
        self._form_lbl_point_size  = QLabel(tr('prop_point_size'))
        self._form_lbl_opacity     = QLabel(tr('prop_opacity'))

        for lbl in (self._form_lbl_file, self._form_lbl_points,
                    self._form_lbl_color_mode, self._form_lbl_lut,
                    self._form_lbl_solid_color, self._form_lbl_point_size,
                    self._form_lbl_opacity):
            lbl.setStyleSheet(
                f"color: {DesignTokens.DARK_TEXT_SECONDARY}; "
                f"font-size: {DesignTokens.FONT_SIZE_SM};"
            )

        form.addRow(self._form_lbl_file,        self.lbl_file)
        form.addRow(self._form_lbl_points,       self.lbl_points)
        form.addRow(self._form_lbl_color_mode,   self.cmb_color_mode)
        form.addRow(self._form_lbl_lut,          self.cmb_lut)
        form.addRow(self._form_lbl_solid_color,  self.btn_pick_color)
        form.addRow(self._form_lbl_point_size,   self.sp_point_size)

        op_h = QHBoxLayout()
        op_h.addWidget(self.sl_opacity)
        op_h.addWidget(self.lbl_opacity_val)
        form.addRow(self._form_lbl_opacity, op_h)

        self._prop_hint = QLabel(tr('prop_hint'))
        self._prop_hint.setWordWrap(True)
        self._prop_hint.setStyleSheet(
            f"color: {DesignTokens.DARK_TEXT_TERTIARY}; "
            f"font-size: {DesignTokens.FONT_SIZE_SM};"
        )
        form.addRow(self._prop_hint)
        return w

    def _connect_actions(self):
        """Connect all ribbon buttons and menu actions."""
        r = self.ribbon

        # ── File ─────────────────────────────────────────────────────────────
        r.btn_open.clicked.connect(self.open_files)
        r.btn_save.clicked.connect(self.export_current)
        r.btn_save_data.clicked.connect(self.save_current_data)

        # ── Scene ────────────────────────────────────────────────────────────
        r.btn_home.clicked.connect(self.reset_view)
        r.btn_clear.clicked.connect(self.clear_scene)
        r.btn_delete.clicked.connect(self.delete_current_file)
        self.act_clear.triggered.connect(self.clear_scene)
        self.act_delete_file.triggered.connect(self.delete_current_file)

        # ── Axes (bidirectional sync) ─────────────────────────────────────────
        r.btn_axis.toggled.connect(self._on_axis_toggled)
        self.act_axis.toggled.connect(self._on_axis_toggled)

        r.btn_grid.toggled.connect(self._on_grid_toggled)
        self.act_grid.toggled.connect(self._on_grid_toggled)

        # ── Auto-rotate (bidirectional sync) ──────────────────────────────────
        r.btn_rotate.toggled.connect(self._on_rotate_toggled)
        self.act_rotate.toggled.connect(self._on_rotate_toggled)

        # ── Select mode (bidirectional sync) ─────────────────────────────────
        r.btn_select_mode.toggled.connect(self._on_select_mode_toggled)
        self.act_select_mode.toggled.connect(self._on_select_mode_toggled)

        # ── Edit actions ──────────────────────────────────────────────────────
        self.act_delete_sel.triggered.connect(
            lambda: self.interactor.delete_selection() if self.interactor else None
        )
        self.act_clear_sel.triggered.connect(
            lambda: self.interactor.clear_selection() if self.interactor else None
        )
        self.act_restore.triggered.connect(
            lambda: self.interactor.restore_all() if self.interactor else None
        )
        r.btn_delete_sel.clicked.connect(
            lambda: self.interactor.delete_selection() if self.interactor else None
        )
        r.btn_cancel_sel.clicked.connect(
            lambda: self.interactor.clear_selection() if self.interactor else None
        )
        r.btn_restore_all.clicked.connect(
            lambda: self.interactor.restore_all() if self.interactor else None
        )

        # ── View tools ────────────────────────────────────────────────────────
        r.btn_zoom_in.clicked.connect(lambda: self._do_zoom(0.9))
        r.btn_zoom_out.clicked.connect(lambda: self._do_zoom(1/0.9))
        r.btn_bg_color.clicked.connect(self._pick_background_color)
        r.btn_theme.clicked.connect(self.toggle_theme)

        # ── Help ──────────────────────────────────────────────────────────────
        r.btn_help_popup.clicked.connect(self._show_help)
        r.btn_about_popup.clicked.connect(self._show_about)

    # ══════════════════════════════════════════════════════════════════════════
    #  Simple3D Runner
    # ══════════════════════════════════════════════════════════════════════════

    def _run_simple3d(self, config: dict):
        """Start Simple3D run."""
        if self._simple3d_runner.is_running():
            QMessageBox.warning(self, "Warning", "Simple3D is already running!")
            return
        
        # Validate custom paths
        if config.get('dataset') == 'custom':
            train_path = config.get('train_path', '')
            test_path = config.get('test_path', '')
            
            if not train_path or not os.path.isdir(train_path):
                QMessageBox.warning(
                    self, tr('s3d_path_error'),
                    f"{tr('s3d_train_not_exist')}\n{train_path}"
                )
                return
            
            if not test_path or not os.path.isdir(test_path):
                QMessageBox.warning(
                    self, tr('s3d_path_error'),
                    f"{tr('s3d_test_not_exist')}\n{test_path}"
                )
                return
        
        self.log("━" * 50)
        self.log("🚀 Starting Simple3D...")
        
        if self._simple3d_runner.run(config):
            self.ribbon.set_running_state(True)
        else:
            self.ribbon.set_running_state(False)

    def _stop_simple3d(self):
        """Stop Simple3D run."""
        if self._simple3d_runner.is_running():
            self._simple3d_runner.stop()

    def _on_simple3d_log(self, message: str):
        """Handle Simple3D log messages."""
        self.log(message)

    def _on_simple3d_status(self, status: str):
        """Handle Simple3D status changes."""
        self.ribbon.s3d_status.set_status(status)
        
        if status == 'running':
            self.ribbon.set_running_state(True)
        else:
            self.ribbon.set_running_state(False)

    def _on_simple3d_finished(self, success: bool, return_code: int):
        """Handle Simple3D run completion."""
        self.ribbon.set_running_state(False)
        
        if success:
            self.log("━" * 50)
        else:
            self.log("━" * 50)

    def set_simple3d_path(self, path: str):
        """Set Simple3D project path."""
        self._simple3d_path = path
        self.settings.setValue('simple3d_path', path)
        if self._simple3d_runner:
            self._simple3d_runner.set_simple3d_path(path)
        self.log(f"Simple3D path: {path}")

    # ══════════════════════════════════════════════════════════════════════════
    #  Language
    # ══════════════════════════════════════════════════════════════════════════

    def _switch_language(self, lang: str) -> None:
        set_language(lang)
        self.act_lang_en.setChecked(lang == 'en')
        self.act_lang_zh.setChecked(lang == 'zh')
        self._retranslate_ui()
        self.log(f"Language → {lang}")

    def _retranslate_ui(self) -> None:
        """Update every translatable string in the main window."""
        self.setWindowTitle(tr('window_title'))

        # ── Menu titles
        self.menu_file.setTitle(tr('menu_file'))
        self.menu_edit.setTitle(tr('menu_edit'))
        self.menu_view.setTitle(tr('menu_view'))
        self.menu_lang.setTitle(tr('menu_language'))
        self.menu_help_menu.setTitle(tr('menu_help'))

        # ── File menu
        self.act_open.setText(tr('action_open'))
        self.act_export.setText(tr('action_export'))
        self.act_save_data.setText(tr('action_save_data'))
        self.act_exit.setText(tr('action_exit'))

        # ── Edit menu
        self.act_clear.setText(tr('action_clear'))
        self.act_delete_file.setText(tr('action_delete'))
        self.act_select_mode.setText(tr('action_select_mode'))
        self.act_delete_sel.setText(tr('action_delete_sel'))
        self.act_clear_sel.setText(tr('action_clear_sel'))
        self.act_restore.setText(tr('action_restore'))

        # ── View menu
        self.act_reset_view.setText(tr('action_reset_view'))
        self.act_axis.setText(tr('action_axis'))
        self.act_grid.setText(tr('action_grid'))
        self.act_rotate.setText(tr('action_rotate'))
        self.act_zoom_in.setText(tr('action_zoom_in'))
        self.act_zoom_out.setText(tr('action_zoom_out'))
        self.act_bg_color.setText(tr('action_bg_color'))
        self.act_theme.setText(tr('action_theme'))

        # ── Language menu
        self.act_lang_en.setText(tr('lang_en'))
        self.act_lang_zh.setText(tr('lang_zh'))

        # ── Help menu
        self.act_help.setText(tr('action_help'))
        self.act_about.setText(tr('action_about'))

        # ── Docks
        self.file_dock.setWindowTitle(tr('dock_files'))
        self.prop_dock.setWindowTitle(tr('dock_properties'))
        self.log_dock.setWindowTitle(tr('dock_log'))

        # ── Properties panel labels
        self._form_lbl_file.setText(tr('prop_file'))
        self._form_lbl_points.setText(tr('prop_points'))
        self._form_lbl_color_mode.setText(tr('prop_color_mode'))
        self._form_lbl_lut.setText(tr('prop_lut'))
        self._form_lbl_solid_color.setText(tr('prop_solid_color'))
        self._form_lbl_point_size.setText(tr('prop_point_size'))
        self._form_lbl_opacity.setText(tr('prop_opacity'))
        self._prop_hint.setText(tr('prop_hint'))

        # ── Color mode combo (rebuild items)
        idx = self.cmb_color_mode.currentIndex()
        self.cmb_color_mode.blockSignals(True)
        self.cmb_color_mode.clear()
        self.cmb_color_mode.addItems([
            tr('color_auto'), tr('color_raw_rgb'), tr('color_score_lut'),
            tr('color_x_grad'), tr('color_y_grad'), tr('color_z_grad'), tr('color_solid')
        ])
        self.cmb_color_mode.setCurrentIndex(idx)
        self.cmb_color_mode.blockSignals(False)

        # ── Status bar indicators
        pts_count = self.lbl_points.text() if self._current_path else '0'
        self._status_points.setText(f"{pts_count} {tr('pts_label')}")
        if not self._current_path:
            self._status_file.setText(tr('status_no_file'))
            self._mode_label.setText(tr('status_no_file'))

        # ── Ribbon
        self.ribbon.retranslate(tr)

    # ══════════════════════════════════════════════════════════════════════════
    #  UI State management
    # ══════════════════════════════════════════════════════════════════════════

    def _update_ui_state(self, has_file: bool) -> None:
        """Enable or disable controls based on whether a file is loaded."""
        r = self.ribbon

        # Ribbon buttons that need a loaded file
        file_dependent_btns = [
            r.btn_save, r.btn_save_data,
            r.btn_home, r.btn_clear, r.btn_delete,
            r.btn_select_mode, r.btn_delete_sel, r.btn_cancel_sel, r.btn_restore_all,
            r.btn_zoom_in, r.btn_zoom_out,
        ]
        for btn in file_dependent_btns:
            btn.setEnabled(has_file)

        # Menu actions
        file_dependent_acts = [
            self.act_export, self.act_save_data,
            self.act_clear, self.act_delete_file, self.act_reset_view,
            self.act_select_mode, self.act_delete_sel, self.act_clear_sel,
            self.act_restore, self.act_zoom_in, self.act_zoom_out,
        ]
        for act in file_dependent_acts:
            act.setEnabled(has_file)

        # Properties panel controls
        prop_controls = [
            self.cmb_color_mode, self.cmb_lut,
            self.btn_pick_color, self.sp_point_size, self.sl_opacity,
        ]
        for w in prop_controls:
            w.setEnabled(has_file)

        # Update status indicator
        if has_file:
            self._set_mode_indicator('ready', _MODE_COLORS['ready'])
        else:
            self._set_mode_indicator('no_file', _MODE_COLORS['no_file'])
            self._status_file.setText(tr('status_no_file'))
            self._status_points.setText(f"0 {tr('pts_label')}")

    def _set_mode_indicator(self, mode_key: str, color: str, label: str = '') -> None:
        """Update the status bar mode dot + label."""
        self._mode_dot.setStyleSheet(
            f"background: {color}; border-radius: 4px;"
        )
        self._mode_label.setText(tr(f'status_{mode_key}') if not label else label)

    def set_mode_indicator(self, mode: str, extra: str = '') -> None:
        """
        Public slot — called by ribbon / interactor to update the mode dot.
        mode: 'ready' | 'loading' | 'select' | 'defect' | 'no_file'
        """
        color = _MODE_COLORS.get(mode, _MODE_COLORS['ready'])
        label_map = {
            'ready':   tr('status_ready'),
            'no_file': tr('status_no_file'),
            'loading': tr('status_loading'),
            'select':  tr('status_select'),
            'defect':  f"{tr('status_defect')}: {extra}" if extra else tr('status_defect'),
        }
        self._mode_dot.setStyleSheet(f"background: {color}; border-radius: 4px;")
        self._mode_label.setText(label_map.get(mode, mode))

    # ══════════════════════════════════════════════════════════════════════════
    #  Synced toggle handlers (menu ↔ ribbon, no signal loops)
    # ══════════════════════════════════════════════════════════════════════════

    def _on_axis_toggled(self, checked: bool) -> None:
        self._sync_check(self.act_axis, checked)
        self._sync_check(self.ribbon.btn_axis, checked)
        self.view3d.set_axes_visible(checked)
        self.log(f"Axes: {'on' if checked else 'off'}")

    def _on_grid_toggled(self, checked: bool) -> None:
        self._sync_check(self.act_grid, checked)
        self._sync_check(self.ribbon.btn_grid, checked)
        self.view3d.set_grid_visible(checked)
        self.log(f"Grid: {'on' if checked else 'off'}")

    def _on_rotate_toggled(self, checked: bool) -> None:
        self._sync_check(self.act_rotate, checked)
        self._sync_check(self.ribbon.btn_rotate, checked)
        self.view3d.set_auto_rotate(checked)
        self.log(f"Auto Rotate: {'on' if checked else 'off'}")

    def _on_select_mode_toggled(self, checked: bool) -> None:
        self._sync_check(self.act_select_mode, checked)
        self._sync_check(self.ribbon.btn_select_mode, checked)
        if self.interactor:
            self.interactor.toggle_select_mode(checked)
        if checked:
            self.set_mode_indicator('select')
        else:
            self.set_mode_indicator('ready')

    @staticmethod
    def _sync_check(widget, checked: bool) -> None:
        """Set checked state without re-firing the toggled signal."""
        widget.blockSignals(True)
        widget.setChecked(checked)
        widget.blockSignals(False)

    # ══════════════════════════════════════════════════════════════════════════
    #  Logging
    # ══════════════════════════════════════════════════════════════════════════

    def log(self, msg: str):
        ts = time.strftime('%H:%M:%S')
        self.log_edit.append(
            f"<span style='color: {DesignTokens.DARK_TEXT_SECONDARY};'>[{ts}]</span> {msg}"
        )
        self.status.showMessage(msg, 3000)

    # ══════════════════════════════════════════════════════════════════════════
    #  View Controls
    # ══════════════════════════════════════════════════════════════════════════

    def _do_zoom(self, scale: float):
        d = float(self.view3d.opts.get('distance', 20.0)) * scale
        self.view3d.setCameraPosition(distance=d)
        self.view3d.update()

    def reset_view(self):
        if self._current_path:
            c = self._pcd_cache[self._current_path]['xyz'].mean(axis=0)
            self.view3d.setCameraPosition(
                pos=QVector3D(float(c[0]), float(c[1]), float(c[2])),
                elevation=30, azimuth=45
            )
        else:
            self.view3d.setCameraPosition(distance=10, elevation=30, azimuth=45)
        self.ribbon.btn_axis.setChecked(True)
        self.ribbon.btn_grid.setChecked(True)

    def clear_scene(self):
        self.view3d.clear_points()
        if self.interactor and hasattr(self.interactor, 'clear_selection'):
            self.interactor.clear_selection()

    def toggle_theme(self):
        if pg.getConfigOption('background') == 'k':
            pg.setConfigOption('background', 'w')
            pg.setConfigOption('foreground', 'k')
        else:
            pg.setConfigOption('background', 'k')
            pg.setConfigOption('foreground', 'w')
        self.view3d.update()

    # ══════════════════════════════════════════════════════════════════════════
    #  Color Controls
    # ══════════════════════════════════════════════════════════════════════════

    def _update_color_button(self):
        c = self._mono_color
        self.btn_pick_color.setStyleSheet(
            f'QToolButton {{ '
            f'background: rgb({c.red()},{c.green()},{c.blue()}); '
            f'border: 1px solid {DesignTokens.DARK_BORDER}; '
            f'border-radius: 4px; }}'
        )

    def _pick_mono_color(self):
        c = QColorDialog.getColor(self._mono_color, self, tr('dlg_color_title'))
        if c.isValid():
            self._mono_color = c
            self._update_color_button()
            self.apply_coloring()
            self.log(f'Solid color: RGB({c.red()},{c.green()},{c.blue()})')

    def _pick_background_color(self):
        c = QColorDialog.getColor(QColor(26, 26, 26), self, tr('dlg_bg_title'))
        if c.isValid():
            self.view3d.setBackgroundColor(c)
            self.log(f'Background: RGB({c.red()},{c.green()},{c.blue()})')

    def _update_point_size(self):
        if self.view3d.scatter:
            self.view3d.scatter.setData(size=self.sp_point_size.value())

    def _update_opacity(self):
        if self.view3d.scatter is None:
            return
        c = self.view3d.scatter.color
        if c is None or c.size == 0:
            return
        alpha = self.sl_opacity.value() / 100.0
        if c.shape[1] == 3:
            c = np.hstack([c, np.full((c.shape[0], 1), alpha)])
        else:
            c[:, 3] = alpha
        self.view3d.scatter.setData(color=c)

    # ══════════════════════════════════════════════════════════════════════════
    #  File Operations
    # ══════════════════════════════════════════════════════════════════════════

    def open_files(self):
        last_dir = self.settings.value('last_dir', os.path.expanduser('~'))
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr('dlg_open_title'), last_dir, tr('dlg_open_filter')
        )
        if not paths:
            return

        self.settings.setValue('last_dir', os.path.dirname(paths[0]))
        self.set_mode_indicator('loading')
        added = 0

        for p in paths:
            if p in self._pcd_cache:
                continue
            data = self._read_point_file(p)
            if data is None:
                continue
            n = len(data['xyz'])
            data['mask'] = np.ones(n, dtype=bool)
            data['last_color'] = None
            self._pcd_cache[p] = data

            item = QListWidgetItem(os.path.basename(p))
            item.setToolTip(p)
            item.setData(Qt.UserRole, p)
            self.file_list.addItem(item)
            added += 1

        self.log(f'Opened {added} file(s)')

        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(self.file_list.count() - max(added, 1))
            self._display_item(self.file_list.currentItem())

    def delete_current_file(self):
        if self._current_path is None:
            return
        path = self._current_path
        ret = QMessageBox.question(
            self, tr('dlg_delete_title'),
            tr('dlg_delete_msg', name=os.path.basename(path)),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return
        try:
            os.remove(path)
            self.log(f'Deleted: {path}')
        except Exception as e:
            self.log(f'Delete failed: {e}')
            return

        self._pcd_cache.pop(path, None)
        for i in range(self.file_list.count()):
            if self.file_list.item(i).data(Qt.UserRole) == path:
                self.file_list.takeItem(i)
                break

        self._current_path = None
        self.view3d.clear_points()
        self.lbl_file.setText('—')
        self.lbl_points.setText('0')

        has_remaining = self.file_list.count() > 0
        if has_remaining:
            self.file_list.setCurrentRow(0)
            self._display_item(self.file_list.currentItem())
        else:
            self._update_ui_state(False)

    def _file_item_clicked(self, item: QListWidgetItem):
        self._display_item(item)

    def _display_item(self, item: QListWidgetItem):
        self.load_point_cloud(item.data(Qt.UserRole))

    def export_current(self):
        if not self._current_path:
            return
        d = self._pcd_cache[self._current_path]
        xyz = d['xyz'][d['mask']]
        path, _ = QFileDialog.getSaveFileName(
            self, tr('dlg_export_title'), '', tr('dlg_export_filter')
        )
        if not path:
            return
        if path.endswith('.png'):
            self.view3d.readQImage().save(path)
        else:
            np.savetxt(path, xyz, fmt='%.6f')
        self.log(f'Exported: {path}')

    def save_current_data(self):
        if not self._current_path:
            QMessageBox.warning(self, 'Warning', tr('warn_no_file'))
            return
        default_name = os.path.splitext(os.path.basename(self._current_path))[0]
        path, _ = QFileDialog.getSaveFileName(
            self, tr('dlg_save_title'), default_name, tr('dlg_save_filter')
        )
        if not path:
            return
        base_path = path[:-4] if path.lower().endswith('.txt') else path
        try:
            data = self._pcd_cache[self._current_path]
            xyz = data['xyz']
            valid_mask = data.get('mask', np.ones(len(xyz), dtype=bool))
            rgb = data.get('rgb01', None)
            valid_xyz = xyz[valid_mask]
            labels = np.zeros(len(valid_xyz), dtype=int)
            if rgb is not None:
                valid_rgb = rgb[valid_mask]
                is_anomaly = (valid_rgb[:, 0] > 0.8) & (valid_rgb[:, 1] < 0.4)
                labels[is_anomaly] = 1
            np.savetxt(f"{base_path}.txt", valid_xyz, fmt='%.6f')
            np.savetxt(f"{base_path}_label.txt", labels, fmt='%d')
            self.log(f"Saved: {os.path.basename(base_path)}.txt")
            QMessageBox.information(
                self, 'Success',
                f"Dataset saved!\n\nPoints: {len(valid_xyz)}\nAnomalies: {np.sum(labels)}"
            )
        except Exception as e:
            self.log(f'Save error: {e}')
            QMessageBox.critical(self, 'Error', f'Failed to save:\n{str(e)}')

    # ══════════════════════════════════════════════════════════════════════════
    #  Data Loading
    # ══════════════════════════════════════════════════════════════════════════

    def _read_point_file(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        if ext in ('.xyzf', '.bin'):
            try:
                try:
                    mm = np.memmap(path, dtype=np.float32, mode='r')
                except Exception:
                    mm = np.fromfile(path, dtype=np.float32)
                if mm.size % 3 != 0:
                    return None
                total_pts = mm.size // 3
                step = max(1, total_pts // self._max_vis_points)
                xyz = np.reshape(mm, (-1, 3))[::step].astype(np.float32, copy=True)
                if xyz.size and np.max(np.abs(xyz)) > 10:
                    xyz /= 1000.0
                return {'xyz': xyz, 'rgb01': None, 'score': None, 'cols': 3}
            except Exception:
                return None

        data = None
        for d in (None, ' ', '\t', ','):
            try:
                data = np.loadtxt(path, dtype=float, delimiter=d)
                if data.ndim == 2 and data.shape[1] >= 3:
                    break
            except Exception:
                pass

        if data is None:
            return None

        xyz = data[:, :3].astype(np.float32, copy=False)
        if xyz.size and np.max(np.abs(xyz)) > 10:
            xyz /= 1000.0

        rgb = None
        if data.shape[1] == 6:
            rgb = data[:, 3:6]
            if np.max(rgb) > 1.0:
                rgb /= 255.0
            rgb = np.clip(rgb, 0, 1).astype(np.float32)

        score = data[:, 3].astype(np.float32) if data.shape[1] == 4 else None
        return {'xyz': xyz, 'rgb01': rgb, 'score': score, 'cols': data.shape[1]}

    def load_point_cloud(self, path: str):
        if path not in self._pcd_cache:
            d = self._read_point_file(path)
            if d is None:
                return
            d['mask'] = np.ones(len(d['xyz']), dtype=bool)
            self._pcd_cache[path] = d

        data = self._pcd_cache[path]
        self._current_path = path

        fname = os.path.basename(path)
        self.lbl_file.setText(fname)
        self._status_file.setText(fname)

        self.apply_coloring()

        n_pts = int(np.count_nonzero(data['mask']))
        self._status_points.setText(f"{n_pts:,} {tr('pts_label')}")

        if len(data['xyz']) > 0:
            c = data['xyz'].mean(axis=0)
            extent = np.linalg.norm(data['xyz'].max(0) - data['xyz'].min(0))
            self.view3d.setCameraPosition(
                pos=QVector3D(float(c[0]), float(c[1]), float(c[2])),
                distance=extent * 1.5
            )

        self._update_ui_state(True)

    # ══════════════════════════════════════════════════════════════════════════
    #  Coloring
    # ══════════════════════════════════════════════════════════════════════════

    def apply_coloring(self):
        if not self._current_path:
            return
        d = self._pcd_cache[self._current_path]
        xyz, mask = d['xyz'], d['mask']
        xyz_vis = xyz[mask]
        idx = self.cmb_color_mode.currentIndex()

        if idx == 0:
            rgb = d['rgb01'][mask] if d['rgb01'] is not None else self._axis_gradient(xyz_vis, 2)
        elif idx == 1:
            rgb = d['rgb01'][mask] if d['rgb01'] is not None else self._axis_gradient(xyz_vis, 2)
        elif idx == 2:
            rgb = self._scalar_to_rgb(d['score'][mask]) if d['score'] is not None else self._axis_gradient(xyz_vis, 2)
        elif idx == 3:
            rgb = self._axis_gradient(xyz_vis, 0)
        elif idx == 4:
            rgb = self._axis_gradient(xyz_vis, 1)
        elif idx == 5:
            rgb = self._axis_gradient(xyz_vis, 2)
        elif idx == 6:
            c = self._mono_color
            rgb = np.tile(np.array([c.red(), c.green(), c.blue()]) / 255.0, (len(xyz_vis), 1))
        else:
            rgb = self._axis_gradient(xyz_vis, 2)

        self.view3d.set_points(xyz_vis, rgb, size=self.sp_point_size.value())
        self._update_opacity()

        n = int(np.count_nonzero(mask))
        self.lbl_points.setText(str(n))
        self._status_points.setText(f"{n:,} {tr('pts_label')}")

        if self.interactor and hasattr(self.interactor, '_current_selection_idx'):
            if self.interactor._current_selection_idx is not None:
                self.interactor._set_selection(self.interactor._current_selection_idx)

    def _scalar_to_rgb(self, s):
        lut = self.cmb_lut.currentText()
        s = (s - np.min(s)) / (np.max(s) - np.min(s) + 1e-12)
        if lut == 'Grayscale':
            return np.stack([s, s, s], axis=1)
        return np.stack([
            np.clip(1.5 * s - 0.5, 0, 1),
            np.clip(1.5 - np.abs(2 * s - 1), 0, 1),
            np.clip(1.5 * (1 - s) - 0.5, 0, 1)
        ], axis=1)

    def _axis_gradient(self, xyz, ax):
        return self._scalar_to_rgb(xyz[:, ax])

    # ══════════════════════════════════════════════════════════════════════════
    #  Help dialogs
    # ══════════════════════════════════════════════════════════════════════════

    def _show_help(self):
        text = (
            '<h3>3D Point Cloud Visualization</h3>'
            '<p><b>File Operations:</b></p>'
            '<ul>'
            '<li>Open (Ctrl+O): Load point cloud files</li>'
            '<li>Export (Ctrl+E): Save view as image or data</li>'
            '<li>Save Data (Ctrl+S): Export with anomaly labels</li>'
            '</ul>'
            '<p><b>View Controls:</b></p>'
            '<ul>'
            '<li>Left Drag: Rotate view</li>'
            '<li>Wheel: Zoom in/out</li>'
            '<li>Wheel Drag: Pan view</li>'
            '<li>A: Toggle axes  |  G: Toggle grid  |  F: Reset view</li>'
            '</ul>'
            '<p><b>Anomaly Generation:</b></p>'
            '<ul>'
            '<li>1D: Point/line based defects</li>'
            '<li>2D: Bend/crack deformations</li>'
            '<li>3D: Area-based anomalies</li>'
            '</ul>'
            '<p><b>Anomaly Detection (Simple3D):</b></p>'
            '<ul>'
            '<li>Select dataset type and configure parameters</li>'
            '<li>For custom datasets, set train/test paths</li>'
            '<li>Click Run to start detection</li>'
            '</ul>'
        )
        msg = QMessageBox(self)
        msg.setWindowTitle(tr('action_help'))
        msg.setText(text)
        msg.setTextFormat(Qt.RichText)
        msg.exec()

    def _show_about(self):
        text = (
            '<h2>3D Point Cloud Visualization</h2>'
            '<p><b>Version 2026.v1</b></p>'
            '<p>Modern, modular architecture with Simple3D integration.</p>'
            '<p><b>Features:</b></p>'
            '<ul>'
            '<li>MenuBar + Ribbon interface</li>'
            '<li>Bilingual UI (EN / 中文)</li>'
            '<li>Modern dark VSCode-style theme</li>'
            '<li>Multiple defect generation modes</li>'
            '<li>Interactive editing tools</li>'
            '<li>Simple3D anomaly detection runner</li>'
            '</ul>'
            '<hr>'
            '<p><b>Copyright © 2026</b></p>'
            '<p>Huazhong University of Science and Technology<br>'
            'Operations Research and Optimization Team<br>'
            '华中科技大学 运筹与优化团队</p>'
            '<p><a href="https://github.com/hustCYQ/Synthesis4AD">'
            'https://github.com/hustCYQ/Synthesis4AD</a></p>'
        )
        msg = QMessageBox(self)
        msg.setWindowTitle(tr('action_about'))
        msg.setText(text)
        msg.setTextFormat(Qt.RichText)
        msg.exec()
