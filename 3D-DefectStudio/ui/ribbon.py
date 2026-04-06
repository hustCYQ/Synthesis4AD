# -*- coding: utf-8 -*-
"""
Ribbon Module - Modern ribbon interface (Integrated Simple3D Runner)
VSCode/IDE-style tabbed toolbar with card-based groups
"""

from typing import List, Callable, Optional
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QToolButton,
    QLabel, QFrame, QSizePolicy, QComboBox, QSlider, QCheckBox,
    QLineEdit, QProgressBar, QSpinBox, QGridLayout, QPushButton,
    QFileDialog, QGroupBox
)
from PySide6.QtGui import QColor

from .design_tokens import DesignTokens
from .icons import SystemIconHelper, load_external_icon
from .styles import ModernStylesheet
from .i18n import tr


class ModernToolButton(QToolButton):
    def __init__(self, text='', icon=None, checkable=False, parent=None):
        super().__init__(parent)
        self.setText(text)
        if icon:
            self.setIcon(icon)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setCheckable(checkable)
        self.setIconSize(QSize(36, 36))
        self.setMinimumWidth(64)
        self.setMaximumWidth(90)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setStyleSheet(ModernStylesheet.get_button_stylesheet())


class _SectionDivider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.VLine)
        self.setFixedWidth(1)
        self.setStyleSheet(
            "QFrame{background:#232640;border:none;max-width:1px;margin:8px 4px;}"
        )


class _GroupCard(QWidget):
    """Card-style group container — title pinned to bottom."""

    def __init__(self, title: str, widgets: List[QWidget], parent=None):
        super().__init__(parent)
        self.setObjectName("GroupCard")
        self.setStyleSheet(ModernStylesheet.get_ribbon_stylesheet())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        card = QWidget()
        card.setObjectName("GroupCard")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(8, 6, 8, 4)
        cl.setSpacing(0)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(2)
        btn_row.setContentsMargins(0, 0, 0, 0)
        for w in widgets:
            btn_row.addWidget(w)

        cl.addLayout(btn_row)
        cl.addStretch(1)

        self._title_lbl = QLabel(title.upper())
        self._title_lbl.setObjectName("GroupTitle")
        self._title_lbl.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self._title_lbl.setStyleSheet(
            "QLabel{color:#44506e;font-size:7pt;font-weight:600;"
            "letter-spacing:1px;background:transparent;padding-bottom:2px;}"
        )
        cl.addWidget(self._title_lbl)
        outer.addWidget(card)

    def retranslate(self, text: str) -> None:
        self._title_lbl.setText(text.upper())


class Simple3DStatusWidget(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(3)
        
        status_row = QHBoxLayout()
        status_row.setSpacing(4)
        
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet("background: #44506e; border-radius: 4px;")
        
        self.status_text = QLabel(tr('status_ready'))
        self.status_text.setStyleSheet("color: #7a8ab0; font-size: 7.5pt;")
        
        status_row.addWidget(self.status_dot)
        status_row.addWidget(self.status_text)
        status_row.addStretch()
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #2e3248; border: none; border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f8ef7, stop:1 #7eb3ff);
                border-radius: 3px;
            }
        """)
        self.progress.hide()
        
        layout.addLayout(status_row)
        layout.addWidget(self.progress)
    
    def set_status(self, status: str):
        colors = {
            'idle': '#44506e', 'running': '#4f8ef7',
            'completed': '#4caf7d', 'failed': '#e05555',
            'cancelled': '#f0903a',
        }
        names = {
            'idle': tr('status_ready'), 'running': tr('s3d_running'),
            'completed': tr('s3d_completed'), 'failed': tr('s3d_failed'),
            'cancelled': tr('s3d_cancelled'),
        }
        
        self.status_dot.setStyleSheet(
            f"background: {colors.get(status, '#44506e')}; border-radius: 4px;"
        )
        self.status_text.setText(names.get(status, status))
        
        if status == 'running':
            self.progress.setRange(0, 0)
            self.progress.show()
        else:
            self.progress.hide()


class Simple3DConfigPanel(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        layout.setVerticalSpacing(1)
        
        label_style = "color: #7a8ab0; font-size: 7pt;"
        input_style = """
            QLineEdit, QComboBox, QSpinBox {
                background: #1a1d2e; color: #c5d0f0;
                border: 1px solid #2e3248; border-radius: 2px;
                padding: 1px 3px; font-size: 7pt; min-height: 16px; max-height: 16px;
            }
            QLineEdit:hover, QComboBox:hover, QSpinBox:hover { border-color: #4f8ef7; }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus { 
                border-color: #4f8ef7; background: #1e2133; 
            }
            QComboBox::drop-down { border: none; width: 12px; }
            QComboBox::down-arrow {
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid #6677aa;
            }
        """
        btn_style = """
            QPushButton { 
                background: #2e3248; color: #8899bb; 
                border: 1px solid #3a4268; border-radius: 2px;
                padding: 0px 3px; font-size: 7pt; max-height: 16px;
            }
            QPushButton:hover { background: #4f8ef7; color: white; }
        """
        checkbox_style = """
            QCheckBox { color: #7a8ab0; font-size: 7pt; spacing: 2px; }
            QCheckBox::indicator { width: 10px; height: 10px; }
            QCheckBox::indicator:unchecked { 
                background: #1a1d2e; border: 1px solid #3a4268; border-radius: 2px; 
            }
            QCheckBox::indicator:checked { 
                background: #4f8ef7; border: 1px solid #4f8ef7; border-radius: 2px; 
            }
        """
        
        row = 0
        
        # ═══ Row 0: Conda / Python ═══
        lbl_conda = QLabel(tr('s3d_conda_env'))
        lbl_conda.setStyleSheet(label_style)
        layout.addWidget(lbl_conda, row, 0)
        
        # Conda环境下拉框 + 刷新按钮的容器
        conda_container = QWidget()
        conda_layout = QHBoxLayout(conda_container)
        conda_layout.setContentsMargins(0, 0, 0, 0)
        conda_layout.setSpacing(2)
        
        self.cmb_conda_env = QComboBox()
        self.cmb_conda_env.setEditable(True)  # 允许手动输入以防检测失败
        self.cmb_conda_env.setStyleSheet(input_style)
        self.cmb_conda_env.setFixedWidth(90)
        self.cmb_conda_env.setToolTip(tr('s3d_conda_tooltip'))
        conda_layout.addWidget(self.cmb_conda_env)
        
        self.btn_refresh_conda = QPushButton("↻")
        self.btn_refresh_conda.setFixedSize(18, 16)
        self.btn_refresh_conda.setStyleSheet(btn_style)
        self.btn_refresh_conda.setToolTip("刷新Conda环境列表")
        self.btn_refresh_conda.clicked.connect(self._refresh_conda_envs)
        conda_layout.addWidget(self.btn_refresh_conda)
        
        layout.addWidget(conda_container, row, 1)
        
        # 初始化时加载conda环境列表
        self._refresh_conda_envs()
        
        lbl_py = QLabel(tr('s3d_or_python'))
        lbl_py.setStyleSheet(label_style)
        layout.addWidget(lbl_py, row, 2)
        
        self.edit_python_path = QLineEdit()
        self.edit_python_path.setPlaceholderText("/path/to/python")
        self.edit_python_path.setStyleSheet(input_style)
        self.edit_python_path.setToolTip(tr('s3d_python_tooltip'))
        layout.addWidget(self.edit_python_path, row, 3, 1, 2)
        
        self.btn_py_browse = QPushButton("...")
        self.btn_py_browse.setFixedSize(18, 16)
        self.btn_py_browse.setStyleSheet(btn_style)
        self.btn_py_browse.clicked.connect(self._browse_python)
        layout.addWidget(self.btn_py_browse, row, 5)
        
        row += 1
        
        # ═══ Row 1: S3D Path ═══
        lbl_s3d = QLabel(tr('s3d_path'))
        lbl_s3d.setStyleSheet(label_style)
        layout.addWidget(lbl_s3d, row, 0)
        
        self.edit_s3d_path = QLineEdit()
        self.edit_s3d_path.setPlaceholderText(tr('s3d_path_placeholder'))
        self.edit_s3d_path.setStyleSheet(input_style)
        self.edit_s3d_path.setToolTip(tr('s3d_path_tooltip'))
        layout.addWidget(self.edit_s3d_path, row, 1, 1, 4)
        
        self.btn_s3d_browse = QPushButton("...")
        self.btn_s3d_browse.setFixedSize(18, 16)
        self.btn_s3d_browse.setStyleSheet(btn_style)
        self.btn_s3d_browse.clicked.connect(self._browse_s3d_path)
        layout.addWidget(self.btn_s3d_browse, row, 5)
        
        row += 1
        
        # ═══ Row 2: Dataset / Exp / Device ═══
        lbl_exp = QLabel(tr('s3d_experiment'))
        lbl_exp.setStyleSheet(label_style)
        layout.addWidget(lbl_exp, row, 0)

        self.edit_expname = QLineEdit("my_exp")
        self.edit_expname.setStyleSheet(input_style)
        self.edit_expname.setFixedWidth(120)
        layout.addWidget(self.edit_expname, row, 1)

        lbl_device = QLabel(tr('s3d_device'))
        lbl_device.setStyleSheet(label_style)
        layout.addWidget(lbl_device, row, 2)

        self.cmb_device = QComboBox()
        self.cmb_device.addItems(["cuda:0", "cuda:1", "cpu"])
        self.cmb_device.setStyleSheet(input_style)
        self.cmb_device.setFixedWidth(65)
        layout.addWidget(self.cmb_device, row, 3)

        row += 1
        
        # ═══ Row 3: Train path (custom only) ═══
        self.lbl_train = QLabel(tr('s3d_train_path'))
        self.lbl_train.setStyleSheet(label_style)
        layout.addWidget(self.lbl_train, row, 0)
        
        self.edit_train = QLineEdit()
        self.edit_train.setPlaceholderText(tr('s3d_train_data_placeholder'))
        self.edit_train.setStyleSheet(input_style)
        layout.addWidget(self.edit_train, row, 1, 1, 4)
        
        self.btn_train_browse = QPushButton("...")
        self.btn_train_browse.setFixedSize(18, 16)
        self.btn_train_browse.setStyleSheet(btn_style)
        self.btn_train_browse.clicked.connect(lambda: self._browse_folder(self.edit_train))
        layout.addWidget(self.btn_train_browse, row, 5)
        
        row += 1
        
        # ═══ Row 4: Test path (custom only) ═══
        self.lbl_test = QLabel(tr('s3d_test_path'))
        self.lbl_test.setStyleSheet(label_style)
        layout.addWidget(self.lbl_test, row, 0)
        
        self.edit_test = QLineEdit()
        self.edit_test.setPlaceholderText(tr('s3d_test_data_placeholder'))
        self.edit_test.setStyleSheet(input_style)
        layout.addWidget(self.edit_test, row, 1, 1, 4)
        
        self.btn_test_browse = QPushButton("...")
        self.btn_test_browse.setFixedSize(18, 16)
        self.btn_test_browse.setStyleSheet(btn_style)
        self.btn_test_browse.clicked.connect(lambda: self._browse_folder(self.edit_test))
        layout.addWidget(self.btn_test_browse, row, 5)
        
        row += 1
        
        # ═══ Row 5: Core params (num_grp, grp_sz, max_nn) ═══
        params_widget = QWidget()
        params_layout = QHBoxLayout(params_widget)
        params_layout.setContentsMargins(0, 0, 0, 0)
        params_layout.setSpacing(3)
        
        lbl_ng = QLabel("num_grp")
        lbl_ng.setStyleSheet(label_style)
        self.spin_num_group = QSpinBox()
        self.spin_num_group.setRange(256, 8192)
        self.spin_num_group.setSingleStep(256)
        self.spin_num_group.setValue(4096)
        self.spin_num_group.setStyleSheet(input_style)
        self.spin_num_group.setFixedWidth(50)
        
        lbl_gs = QLabel("grp_sz")
        lbl_gs.setStyleSheet(label_style)
        self.spin_group_size = QSpinBox()
        self.spin_group_size.setRange(32, 512)
        self.spin_group_size.setSingleStep(32)
        self.spin_group_size.setValue(128)
        self.spin_group_size.setStyleSheet(input_style)
        self.spin_group_size.setFixedWidth(40)
        
        lbl_nn = QLabel("max_nn")
        lbl_nn.setStyleSheet(label_style)
        self.spin_max_nn = QSpinBox()
        self.spin_max_nn.setRange(10, 200)
        self.spin_max_nn.setSingleStep(10)
        self.spin_max_nn.setValue(40)
        self.spin_max_nn.setStyleSheet(input_style)
        self.spin_max_nn.setFixedWidth(35)
        
        params_layout.addWidget(lbl_ng)
        params_layout.addWidget(self.spin_num_group)
        params_layout.addWidget(lbl_gs)
        params_layout.addWidget(self.spin_group_size)
        params_layout.addWidget(lbl_nn)
        params_layout.addWidget(self.spin_max_nn)
        params_layout.addStretch()
        
        layout.addWidget(params_widget, row, 0, 1, 6)
        
        row += 1
        
        # ═══ Row 6: Checkboxes & Level ═══
        opts_widget = QWidget()
        opts_layout = QHBoxLayout(opts_widget)
        opts_layout.setContentsMargins(0, 0, 0, 0)
        opts_layout.setSpacing(4)
        
        self.chk_msnd = QCheckBox("MSND")
        self.chk_msnd.setChecked(True)
        self.chk_msnd.setStyleSheet(checkbox_style)
        
        self.chk_lfsa = QCheckBox("LFSA")
        self.chk_lfsa.setChecked(True)
        self.chk_lfsa.setStyleSheet(checkbox_style)
        
        self.chk_vis = QCheckBox("vis")
        self.chk_vis.setChecked(False)
        self.chk_vis.setStyleSheet(checkbox_style)
        
        lbl_level = QLabel("level")
        lbl_level.setStyleSheet(label_style)
        self.cmb_level = QComboBox()
        self.cmb_level.addItems(["ALL", "easy", "medium", "hard"])
        self.cmb_level.setStyleSheet(input_style)
        self.cmb_level.setFixedWidth(50)
        
        opts_layout.addWidget(self.chk_msnd)
        opts_layout.addWidget(self.chk_lfsa)
        opts_layout.addWidget(self.chk_vis)
        opts_layout.addWidget(lbl_level)
        opts_layout.addWidget(self.cmb_level)
        opts_layout.addStretch()
        
        layout.addWidget(opts_widget, row, 0, 1, 6)
        
        self._labels = {
            'conda': lbl_conda, 'py': lbl_py, 's3d': lbl_s3d,
            'exp': lbl_exp, 'device': lbl_device,
            'train': self.lbl_train, 'test': self.lbl_test,
        }
    
    def _browse_folder(self, edit: QLineEdit):
        import os
        folder = QFileDialog.getExistingDirectory(
            self, tr('s3d_select_folder'), 
            edit.text() or os.path.expanduser("~")
        )
        if folder:
            edit.setText(folder)
    
    def _browse_python(self):
        import os
        path, _ = QFileDialog.getOpenFileName(
            self, tr('s3d_select_python'),
            os.path.expanduser("~"),
            "Python (python*);; All Files (*)"
        )
        if path:
            self.edit_python_path.setText(path)
    
    def _browse_s3d_path(self):
        import os
        folder = QFileDialog.getExistingDirectory(
            self, tr('s3d_select_s3d_dir'),
            self.edit_s3d_path.text() or os.path.expanduser("~")
        )
        if folder:
            self.edit_s3d_path.setText(folder)

    
    def _refresh_conda_envs(self):
        """自动检测系统中的conda环境列表"""
        import subprocess
        import os
        
        current_text = self.cmb_conda_env.currentText()
        self.cmb_conda_env.clear()
        
        envs = []
        try:
            # 尝试运行 conda env list
            result = subprocess.run(
                ['conda', 'env', 'list'],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue
                    # 解析环境名（第一列是名称，可能带 * 表示当前环境）
                    parts = line.split()
                    if parts:
                        env_name = parts[0].replace('*', '').strip()
                        if env_name and env_name != 'base':
                            envs.append(env_name)
                # base环境放最后
                envs.append('base')
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # conda命令不可用时，添加默认占位
            envs = ['Simple3D_env', 'base']
        
        self.cmb_conda_env.addItems(envs)
        
        # 恢复之前选择的值
        if current_text:
            idx = self.cmb_conda_env.findText(current_text)
            if idx >= 0:
                self.cmb_conda_env.setCurrentIndex(idx)
            else:
                self.cmb_conda_env.setCurrentText(current_text)
    
    def get_dataset_key(self) -> str:
        return "custom"
    
    def get_simple3d_path(self) -> str:
        return self.edit_s3d_path.text().strip()
    
    def get_config(self) -> dict:
        return {
            'dataset': self.get_dataset_key(),
            'train_path': self.edit_train.text().strip(),
            'test_path': self.edit_test.text().strip(),
            'expname': self.edit_expname.text().strip() or 'gui_exp',
            'device': self.cmb_device.currentText(),
            'num_group': self.spin_num_group.value(),
            'group_size': self.spin_group_size.value(),
            'max_nn': self.spin_max_nn.value(),
            'use_MSND': self.chk_msnd.isChecked(),
            'use_LFSA': self.chk_lfsa.isChecked(),
            'vis_save': self.chk_vis.isChecked(),
            'level': self.cmb_level.currentText(),
            'python_path': self.edit_python_path.text().strip(),
            'conda_env': self.cmb_conda_env.currentText().strip(),
            'simple3d_path': self.edit_s3d_path.text().strip(),
        }
    
    def retranslate(self):
        self._labels['conda'].setText(tr('s3d_conda_env'))
        self._labels['py'].setText(tr('s3d_or_python'))
        self._labels['s3d'].setText(tr('s3d_path'))
        self._labels['exp'].setText(tr('s3d_experiment'))
        self._labels['device'].setText(tr('s3d_device'))
        self._labels['train'].setText(tr('s3d_train_path'))
        self._labels['test'].setText(tr('s3d_test_path'))
        
        self.cmb_conda_env.setToolTip(tr('s3d_conda_tooltip'))
        self.edit_python_path.setToolTip(tr('s3d_python_tooltip'))
        self.edit_s3d_path.setPlaceholderText(tr('s3d_path_placeholder'))
        self.edit_s3d_path.setToolTip(tr('s3d_path_tooltip'))
        self.edit_train.setPlaceholderText(tr('s3d_train_data_placeholder'))
        self.edit_test.setPlaceholderText(tr('s3d_test_data_placeholder'))


class ModernRibbon(QWidget):
    """Modern ribbon — tabs: Home | Anomaly Gen | Anomaly Det | Help & About"""
    
    simple3d_run_requested = Signal(dict)
    simple3d_stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tabs = QTabWidget(self)
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)

        self.param_res = 0.01
        self.param_neighbors = 50
        self.path_train = ""
        self.path_test = ""
        self.current_defect_type = None
        self._is_running = False

        self._create_pages()

    def _page(self):
        w = QWidget()
        w.setObjectName("RibbonPage")
        h = QHBoxLayout(w)
        h.setContentsMargins(10, 6, 10, 6)
        h.setSpacing(6)
        return w, h

    def _group(self, title: str, widgets: List[QWidget]) -> _GroupCard:
        return _GroupCard(title, widgets, self)

    def _tool(self, text: str, icon_name: str = '', checkable: bool = False) -> ModernToolButton:
        icon = SystemIconHelper.get_icon(icon_name) if icon_name else None
        return ModernToolButton(text, icon, checkable, self)

    def _divider(self) -> _SectionDivider:
        return _SectionDivider(self)

    def _create_pages(self):
        pages = [
            (tr('tab_home'),      self._make_home_page),
            (tr('tab_synth'),     self._make_synth_page),
            (tr('tab_detect'),    self._make_detect_page),
            (tr('tab_help_about'),self._make_help_about_page),
        ]
        for label, factory in pages:
            self.tabs.addTab(factory(), label)

    def _make_home_page(self) -> QWidget:
        w, h = self._page()

        self.btn_open      = self._tool(tr('btn_open'),      'open')
        self.btn_save      = self._tool(tr('btn_export'),    'save')
        self.btn_save_data = self._tool(tr('btn_save_data'), 'save_data')
        self.btn_save_data.setToolTip("Save point cloud and anomaly labels")
        self.grp_file = self._group(tr('grp_file'),
                                    [self.btn_open, self.btn_save, self.btn_save_data])

        self.btn_home   = self._tool(tr('btn_reset_view'), 'home')
        self.btn_clear  = self._tool(tr('btn_clear'),      'clear')
        self.btn_delete = self._tool(tr('btn_delete'),     'delete')
        self.grp_scene = self._group(tr('grp_scene'),
                                     [self.btn_home, self.btn_clear, self.btn_delete])

        self.btn_select_mode = self._tool(tr('btn_select'),    'select',  checkable=True)
        self.btn_delete_sel  = self._tool(tr('btn_del_sel'),   'commit')
        self.btn_cancel_sel  = self._tool(tr('btn_clear_sel'), 'cancel')
        self.btn_restore_all = self._tool(tr('btn_restore'),   'restore')
        self.grp_interaction = self._group(tr('grp_interaction'), [
            self.btn_select_mode, self.btn_delete_sel,
            self.btn_cancel_sel,  self.btn_restore_all,
        ])

        self.btn_axis     = self._tool(tr('btn_axis'),     'axis',    checkable=True)
        self.btn_grid     = self._tool(tr('btn_grid'),     'grid',    checkable=True)
        self.btn_zoom_in  = self._tool(tr('btn_zoom_in'),  'zoom-in')
        self.btn_zoom_out = self._tool(tr('btn_zoom_out'), 'zoom-out')
        self.btn_bg_color = self._tool(tr('btn_bg'),       'color')
        self.grp_display  = self._group(tr('grp_display'), [
            self.btn_axis, self.btn_grid,
            self.btn_zoom_in, self.btn_zoom_out, self.btn_bg_color,
        ])

        self.btn_rotate = self._tool(tr('btn_rotate'), 'rotate', checkable=True)
        self.btn_theme  = self._tool(tr('btn_theme'),  'theme')
        self.grp_tools  = self._group(tr('grp_tools'), [self.btn_rotate, self.btn_theme])

        for widget in [
            self.grp_file, self.grp_scene, self.grp_interaction,
            self.grp_display, self.grp_tools
        ]:
            h.addWidget(widget)
            if widget != self.grp_tools:
                h.addWidget(self._divider())
        h.addStretch(1)
        return w

    def _make_synth_page(self) -> QWidget:
        w, h = self._page()

        self.btn_1d_point   = ModernToolButton('Sphere',  checkable=True)
        self.btn_1d_scratch = ModernToolButton('Scratch', checkable=True)
        self.btn_1d_point.setIcon(load_external_icon('sphere.png'))
        self.btn_1d_scratch.setIcon(load_external_icon('scratch.png'))
        self.btn_1d_point.setToolTip("1D: Spherical influence")
        self.btn_1d_scratch.setToolTip("1D: Polyline scratch")
        self.btn_1d_point.clicked.connect(lambda: self._set_defect_mode('1d_point'))
        self.btn_1d_scratch.clicked.connect(lambda: self._set_defect_mode('1d_scratch'))
        self.grp_1d = self._group(tr('grp_1d'), [self.btn_1d_point, self.btn_1d_scratch])

        self.btn_2d_bend     = ModernToolButton('Bend',  checkable=True)
        self.btn_2d_fracture = ModernToolButton('Crack', checkable=True)
        self.btn_2d_bend.setIcon(load_external_icon('bend.png'))
        self.btn_2d_fracture.setIcon(load_external_icon('crack.png'))
        self.btn_2d_bend.clicked.connect(lambda: self._set_defect_mode('2d_bend'))
        self.btn_2d_fracture.clicked.connect(lambda: self._set_defect_mode('2d_fracture'))
        self.grp_2d = self._group(tr('grp_2d'), [self.btn_2d_bend, self.btn_2d_fracture])

        self.btn_3d_areal = ModernToolButton('Lasso',  checkable=True)
        self.btn_3d_irreg = ModernToolButton('Random', checkable=True)
        self.btn_3d_areal.setIcon(load_external_icon('lasso.png'))
        self.btn_3d_irreg.setIcon(load_external_icon('random.png'))
        self.btn_3d_areal.clicked.connect(lambda: self._set_defect_mode('3d_areal'))
        self.btn_3d_irreg.clicked.connect(lambda: self._set_defect_mode('3d_irreg'))
        self.grp_3d = self._group(tr('grp_3d'), [self.btn_3d_areal, self.btn_3d_irreg])

        param_card = self._make_param_card()

        # Actions
        self.btn_undo   = self._tool(tr('btn_undo'),      'restore')
        self.btn_apply  = self._tool(tr('btn_apply'),     'commit')
        self.btn_apply.setEnabled(False)
        self.btn_cancel = self._tool(tr('btn_exit_mode'), 'cancel')
        self.btn_undo.clicked.connect(lambda: self._trigger_action('undo'))
        self.btn_apply.clicked.connect(lambda: self._trigger_action('apply'))
        self.btn_cancel.clicked.connect(lambda: self._trigger_action('cancel'))
        self.grp_actions = self._group(tr('grp_actions'),
                                       [self.btn_undo, self.btn_apply, self.btn_cancel])

        for widget in [
            self.grp_1d,    self._divider(),
            self.grp_2d,    self._divider(),
            self.grp_3d,    self._divider(),
            param_card,     self._divider(),
            self.grp_actions,
        ]:
            h.addWidget(widget)
        h.addStretch(1)
        return w

    def _make_param_card(self) -> _GroupCard:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        self.chk_auto_params = QCheckBox("Auto Parameters")
        self.chk_auto_params.setChecked(False)
        self.chk_auto_params.setFixedHeight(18)
        self.chk_auto_params.setStyleSheet("""
            QCheckBox { color: #7a8ab0; font-size: 8pt; }
            QCheckBox::indicator {
                width: 12px; height: 12px;
                border: 1.5px solid #3a4268; border-radius: 3px;
                background: #1a1d2e;
            }
            QCheckBox::indicator:checked { background: #4f8ef7; border-color: #4f8ef7; }
        """)
        self.chk_auto_params.toggled.connect(self._toggle_params_state)

        self.cmb_lasso_style = QComboBox()
        self.cmb_lasso_style.addItems(["Bump/Dent", "Noise", "Surface Fit"])
        self.cmb_lasso_style.setToolTip("Deformation style")
        self.cmb_lasso_style.setFixedHeight(22)
        self.cmb_lasso_style.setStyleSheet("""
            QComboBox {
                background: #1a1d2e; color: #8899bb;
                border: 1px solid #2e3248; border-radius: 4px;
                padding: 1px 8px; font-size: 8pt;
            }
            QComboBox:hover { border-color: #4f8ef7; }
            QComboBox::drop-down { border: none; width: 18px; }
            QComboBox::down-arrow {
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid #6677aa; margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background: #1e2133; color: #8899bb; border: 1px solid #2e3248;
                selection-background-color: rgba(79,142,247,0.2);
            }
        """)
        self.cmb_lasso_style.currentIndexChanged.connect(self._on_style_changed)

        self.txt_formula = QLineEdit("cos(3*r)")
        self.txt_formula.setPlaceholderText("Formula, e.g. cos(3*r)")
        self.txt_formula.setVisible(False)
        self.txt_formula.setFixedHeight(22)
        self.txt_formula.setStyleSheet("""
            QLineEdit {
                background: #1a1d2e; color: #7eb3ff;
                border: 1px solid #2e3248; border-radius: 4px;
                padding: 1px 8px; font-family: 'Consolas', monospace; font-size: 8pt;
            }
            QLineEdit:focus { border-color: #4f8ef7; }
        """)

        slider_ss = """
            QSlider::groove:horizontal { height: 3px; background: #252840; border-radius: 2px; }
            QSlider::sub-page:horizontal { background: #4f8ef7; border-radius: 2px; }
            QSlider::handle:horizontal {
                width: 10px; height: 10px; background: #fff;
                border: 2px solid #4f8ef7; border-radius: 5px; margin: -4px 0;
            }
        """
        lbl_ss = "QLabel{color:#5a6a90;font-size:7pt;background:transparent;margin:0;padding:0;}"

        self.lbl_strength = QLabel("Strength  0.020")
        self.lbl_strength.setStyleSheet(lbl_ss)
        self.lbl_strength.setFixedHeight(14)
        self.sl_strength = QSlider(Qt.Horizontal)
        self.sl_strength.setRange(-100, 100); self.sl_strength.setValue(20)
        self.sl_strength.setFixedHeight(16); self.sl_strength.setStyleSheet(slider_ss)
        self.sl_strength.valueChanged.connect(
            lambda v: self.lbl_strength.setText(f"Strength  {v/1000.0:+.3f}")
        )

        self.lbl_size = QLabel("Size  0.050")
        self.lbl_size.setStyleSheet(lbl_ss)
        self.lbl_size.setFixedHeight(14)
        self.sl_size = QSlider(Qt.Horizontal)
        self.sl_size.setRange(1, 200); self.sl_size.setValue(50)
        self.sl_size.setFixedHeight(16); self.sl_size.setStyleSheet(slider_ss)
        self.sl_size.valueChanged.connect(
            lambda v: self.lbl_size.setText(f"Size  {v/1000.0:.3f}")
        )

        for widget in [self.chk_auto_params, self.cmb_lasso_style, self.txt_formula,
                       self.lbl_strength, self.sl_strength, self.lbl_size, self.sl_size]:
            vbox.addWidget(widget)

        self.grp_params = self._group(tr('grp_params'), [container])
        return self.grp_params

    def _make_detect_page(self) -> QWidget:
        w, h = self._page()

        self.s3d_config = Simple3DConfigPanel()
        
        config_container = QWidget()
        config_container.setObjectName("GroupCard")
        config_container.setStyleSheet("""
            QWidget#GroupCard {
                background: #1e2133;
                border: 1px solid #2a2d3e;
                border-radius: 7px;
            }
        """)
        config_layout = QVBoxLayout(config_container)
        config_layout.setContentsMargins(4, 4, 4, 2)
        config_layout.setSpacing(0)
        config_layout.addWidget(self.s3d_config)
        
        self.config_label = QLabel(tr('s3d_config').upper())
        self.config_label.setAlignment(Qt.AlignHCenter)
        self.config_label.setStyleSheet(
            "color:#44506e;font-size:7pt;font-weight:600;"
            "letter-spacing:1px;background:transparent;padding:2px;"
        )
        config_layout.addWidget(self.config_label)

        self.btn_run = self._tool(tr('s3d_run'), 'commit')
        self.btn_run.setStyleSheet("""
            QToolButton {
                background: rgba(76, 175, 125, 0.15);
                border: 1px solid #4caf7d;
                color: #4caf7d; font-size: 8.5pt;
                font-weight: 600;
                padding: 4px 4px 3px 4px;
                border-radius: 6px; min-width: 52px;
            }
            QToolButton:hover {
                background: rgba(76, 175, 125, 0.25);
                border: 1px solid #5fc98f; color: #7effb0;
            }
            QToolButton:pressed {
                background: rgba(76, 175, 125, 0.35);
            }
            QToolButton:disabled {
                color: #2e3558; background: transparent;
                border: 1px solid #2e3558;
            }
        """)
        self.btn_run.clicked.connect(self._on_run_clicked)
        
        self.btn_stop = self._tool(tr('s3d_stop'), 'cancel')
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("""
            QToolButton {
                background: rgba(224, 85, 85, 0.15);
                border: 1px solid #e05555;
                color: #e05555; font-size: 8.5pt;
                font-weight: 600;
                padding: 4px 4px 3px 4px;
                border-radius: 6px; min-width: 52px;
            }
            QToolButton:hover {
                background: rgba(224, 85, 85, 0.25);
                border: 1px solid #ff7070; color: #ff9090;
            }
            QToolButton:disabled {
                color: #2e3558; background: transparent;
                border: 1px solid #2e3558;
            }
        """)
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        
        self.btn_clear_log = self._tool(tr('s3d_clear_log'), 'clear')
        
        self.grp_control = self._group(tr('s3d_control'), 
                                       [self.btn_run, self.btn_stop, self.btn_clear_log])

        self.s3d_status = Simple3DStatusWidget()
        
        status_container = QWidget()
        status_container.setObjectName("GroupCard")
        status_container.setStyleSheet("""
            QWidget#GroupCard {
                background: #1e2133;
                border: 1px solid #2a2d3e;
                border-radius: 7px;
            }
        """)
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(8, 6, 8, 4)
        status_layout.addWidget(self.s3d_status)
        
        self.status_label = QLabel(tr('s3d_status').upper())
        self.status_label.setAlignment(Qt.AlignHCenter)
        self.status_label.setStyleSheet(
            "color:#44506e;font-size:7pt;font-weight:600;"
            "letter-spacing:1px;background:transparent;padding:2px;"
        )
        status_layout.addWidget(self.status_label)

        h.addWidget(config_container)
        h.addWidget(self._divider())
        h.addWidget(self.grp_control)
        h.addWidget(self._divider())
        h.addWidget(status_container)
        h.addStretch(1)
        return w
    
    def _on_run_clicked(self):
        config = self.s3d_config.get_config()
        
        mw = self.window()
        s3d_path = self.s3d_config.get_simple3d_path()
        if s3d_path and hasattr(mw, 'set_simple3d_path'):
            mw.set_simple3d_path(s3d_path)
        
        self.simple3d_run_requested.emit(config)
    
    def _on_stop_clicked(self):
        self.simple3d_stop_requested.emit()
    
    def set_running_state(self, running: bool):
        self._is_running = running
        self.btn_run.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.s3d_status.set_status('running' if running else 'idle')

    def _make_help_about_page(self) -> QWidget:
        w, h = self._page()

        self.btn_help_popup  = self._tool(tr('btn_help'),  'info')
        self.btn_about_popup = self._tool(tr('btn_about'), 'info')

        self.grp_help_about = self._group(
            tr('tab_help_about'),
            [self.btn_help_popup, self.btn_about_popup]
        )

        h.addWidget(self.grp_help_about)
        h.addStretch(1)
        return w

    def retranslate(self, tr_fn: Callable[[str], str]) -> None:
        tab_keys = ['tab_home', 'tab_synth', 'tab_detect', 'tab_help_about']
        for i, key in enumerate(tab_keys):
            self.tabs.setTabText(i, tr_fn(key))

        groups = {
            'grp_file':        self.grp_file,
            'grp_scene':       self.grp_scene,
            'grp_interaction': self.grp_interaction,
            'grp_display':     self.grp_display,
            'grp_tools':       self.grp_tools,
            'grp_1d':          self.grp_1d,
            'grp_2d':          self.grp_2d,
            'grp_3d':          self.grp_3d,
            'grp_params':      self.grp_params,
            'grp_actions':     self.grp_actions,
            's3d_control':     self.grp_control,
            'tab_help_about':  self.grp_help_about,
        }
        for key, card in groups.items():
            if hasattr(card, 'retranslate'):
                card.retranslate(tr_fn(key))

        for btn, key in [
            (self.btn_open,        'btn_open'),
            (self.btn_save,        'btn_export'),
            (self.btn_save_data,   'btn_save_data'),
            (self.btn_home,        'btn_reset_view'),
            (self.btn_clear,       'btn_clear'),
            (self.btn_delete,      'btn_delete'),
            (self.btn_select_mode, 'btn_select'),
            (self.btn_delete_sel,  'btn_del_sel'),
            (self.btn_cancel_sel,  'btn_clear_sel'),
            (self.btn_restore_all, 'btn_restore'),
            (self.btn_axis,        'btn_axis'),
            (self.btn_grid,        'btn_grid'),
            (self.btn_zoom_in,     'btn_zoom_in'),
            (self.btn_zoom_out,    'btn_zoom_out'),
            (self.btn_bg_color,    'btn_bg'),
            (self.btn_rotate,      'btn_rotate'),
            (self.btn_theme,       'btn_theme'),
            (self.btn_undo,        'btn_undo'),
            (self.btn_apply,       'btn_apply'),
            (self.btn_cancel,      'btn_exit_mode'),
            (self.btn_run,         's3d_run'),
            (self.btn_stop,        's3d_stop'),
            (self.btn_clear_log,   's3d_clear_log'),
            (self.btn_help_popup,  'btn_help'),
            (self.btn_about_popup, 'btn_about'),
        ]:
            btn.setText(tr_fn(key))
        
        self.config_label.setText(tr_fn('s3d_config').upper())
        self.status_label.setText(tr_fn('s3d_status').upper())
        self.s3d_config.retranslate()

    def _on_style_changed(self, index: int):
        self.txt_formula.setVisible(index == 2)

    def _toggle_params_state(self, checked: bool):
        self.sl_strength.setEnabled(not checked)
        self.sl_size.setEnabled(not checked)
        if checked:
            self.lbl_strength.setText("Strength  Auto")
            self.lbl_size.setText("Size  Auto")
        else:
            self.lbl_strength.setText(f"Strength  {self.sl_strength.value()/1000.0:+.3f}")
            self.lbl_size.setText(f"Size  {self.sl_size.value()/1000.0:.3f}")

    def _trigger_action(self, action: str):
        mw = self.window()
        if hasattr(mw, 'interactor') and mw.interactor is not None:
            {
                'undo':   mw.interactor.undo_selection,
                'apply':  mw.interactor.apply_defect,
                'cancel': mw.interactor.exit_defect_mode,
            }.get(action, lambda: None)()
        else:
            mw.log("⚠️ Interaction module not available")

    def _set_defect_mode(self, mode: str):
        _btn_map = {
            '1d_point':   'btn_1d_point',  '1d_scratch': 'btn_1d_scratch',
            '2d_bend':    'btn_2d_bend',   '2d_fracture':'btn_2d_fracture',
            '3d_areal':   'btn_3d_areal',  '3d_irreg':   'btn_3d_irreg',
        }
        for attr in _btn_map.values():
            if hasattr(self, attr):
                getattr(self, attr).setChecked(False)
        if mode in _btn_map:
            getattr(self, _btn_map[mode]).setChecked(True)

        self.current_defect_type = mode
        val = self.sl_size.value() / 1000.0
        self.lbl_size.setText({
            '1d_scratch': f"Width  {val:.3f}",
            '3d_irreg':   f"Base Size  {val:.3f}",
            '3d_areal':   f"Frequency  {val:.3f}",
        }.get(mode, f"Size  {val:.3f}"))

        mw = self.window()
        if hasattr(mw, 'interactor') and mw.interactor is not None:
            mw.interactor.set_interaction_mode(mode)
            mw.log("Mode › {}  —  {}".format(mode, {
                '1d_point':    "Click to generate sphere anomaly",
                '1d_scratch':  "Left-click: Add points  |  Right-click: Finish",
                '2d_bend':     "Select 2 points to define bend axis",
                '2d_fracture': "Select 2 points to define crack axis",
                '3d_areal':    "Draw lasso to select region",
                '3d_irreg':    "Click to generate random ellipsoid",
            }.get(mode, '')))
            if hasattr(mw, 'set_mode_indicator'):
                mw.set_mode_indicator('defect', mode)
        else:
            mw.log(f"⚠️ Mode: {mode}  —  Interaction module not loaded")