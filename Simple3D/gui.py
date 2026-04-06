"""
gui.py  ——  Simple3D PyQt5 图形界面启动器
运行方式：python gui.py
依赖：pip install PyQt5
"""

import sys
import os
import subprocess
import threading

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QFileDialog, QTextEdit,
    QGroupBox, QGridLayout, QComboBox, QCheckBox, QSpinBox,
    QFrame, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QFont, QColor, QPalette, QTextCursor, QIcon


# ══════════════════════════════════════════════════════════════════════════════
#  后台运行线程
# ══════════════════════════════════════════════════════════════════════════════
class RunnerThread(QThread):
    log_signal    = pyqtSignal(str)   # 输出日志
    finish_signal = pyqtSignal(int)   # 结束信号，携带返回码

    def __init__(self, cmd: list, env: dict):
        super().__init__()
        self.cmd = cmd
        self.env = env

    def run(self):
        try:
            proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=self.env,
                bufsize=1,
            )
            for line in proc.stdout:
                self.log_signal.emit(line.rstrip())
            proc.wait()
            self.finish_signal.emit(proc.returncode)
        except Exception as e:
            self.log_signal.emit(f"[ERROR] 启动失败: {e}")
            self.finish_signal.emit(-1)


# ══════════════════════════════════════════════════════════════════════════════
#  主窗口
# ══════════════════════════════════════════════════════════════════════════════
class Simple3DGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.runner = None
        # 提前初始化 log_box，避免 _group_buttons 引用时报 AttributeError
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setObjectName("logbox")
        self.log_box.setFont(QFont("Consolas", 10))
        self._build_ui()

    # ── UI 构建 ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle("Simple3D — 异常检测启动器")
        self.setMinimumSize(860, 680)
        self._apply_style()

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 16)

        # 标题
        title = QLabel("Simple3D  |  3D 工业点云异常检测")
        title.setObjectName("title")
        root.addWidget(title)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setObjectName("divider")
        root.addWidget(divider)

        # 主体：左侧参数 + 右侧日志
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        # ── 左侧参数面板 ──────────────────────────────────────────────────────
        left = QWidget()
        left.setMaximumWidth(400)
        lv = QVBoxLayout(left)
        lv.setSpacing(10)

        lv.addWidget(self._group_dataset())
        lv.addWidget(self._group_params())
        lv.addWidget(self._group_buttons())
        lv.addStretch()

        splitter.addWidget(left)

        # ── 右侧日志区 ────────────────────────────────────────────────────────
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(8, 0, 0, 0)

        log_label = QLabel("运行日志")
        log_label.setObjectName("section")
        rv.addWidget(log_label)

        rv.addWidget(self.log_box)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # 底部状态栏
        self.status = QLabel("就绪")
        self.status.setObjectName("status")
        root.addWidget(self.status)

    # ── 数据集组 ──────────────────────────────────────────────────────────────
    def _group_dataset(self):
        grp = QGroupBox("数据集路径")
        g = QGridLayout(grp)
        g.setSpacing(8)

        # 数据集类型选择
        g.addWidget(QLabel("数据集类型"), 0, 0)
        self.dataset_combo = QComboBox()
        self.dataset_combo.addItems([
            "custom（自定义路径）",
            "minishift",
            "real",
            "shapenet",
            "mulsen",
            "mvtec",
        ])
        self.dataset_combo.currentIndexChanged.connect(self._on_dataset_change)
        g.addWidget(self.dataset_combo, 0, 1, 1, 2)

        # Train 路径
        self.train_label = QLabel("Train 文件夹")
        g.addWidget(self.train_label, 1, 0)
        self.train_edit = QLineEdit()
        self.train_edit.setPlaceholderText("选择包含正常训练样本的文件夹…")
        g.addWidget(self.train_edit, 1, 1)
        btn_train = QPushButton("浏览")
        btn_train.setFixedWidth(56)
        btn_train.clicked.connect(lambda: self._browse(self.train_edit))
        g.addWidget(btn_train, 1, 2)

        # Test 路径
        self.test_label = QLabel("Test 文件夹")
        g.addWidget(self.test_label, 2, 0)
        self.test_edit = QLineEdit()
        self.test_edit.setPlaceholderText("选择包含测试样本的文件夹…")
        g.addWidget(self.test_edit, 2, 1)
        btn_test = QPushButton("浏览")
        btn_test.setFixedWidth(56)
        btn_test.clicked.connect(lambda: self._browse(self.test_edit))
        g.addWidget(btn_test, 2, 2)

        # 提示
        self.path_hint = QLabel(
            "结构: test/good/*.asc  和  test/defect_X/*.asc"
        )
        self.path_hint.setObjectName("hint")
        g.addWidget(self.path_hint, 3, 0, 1, 3)

        return grp

    # ── 参数组 ────────────────────────────────────────────────────────────────
    def _group_params(self):
        grp = QGroupBox("运行参数")
        g = QGridLayout(grp)
        g.setSpacing(8)

        # expname
        g.addWidget(QLabel("实验名称"), 0, 0)
        self.expname_edit = QLineEdit("my_exp")
        g.addWidget(self.expname_edit, 0, 1, 1, 2)

        # device
        g.addWidget(QLabel("设备"), 1, 0)
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cuda:0", "cuda:1", "cpu"])
        g.addWidget(self.device_combo, 1, 1, 1, 2)

        # num_group
        g.addWidget(QLabel("num_group"), 2, 0)
        self.num_group = QSpinBox()
        self.num_group.setRange(256, 8192)
        self.num_group.setSingleStep(256)
        self.num_group.setValue(4096)
        g.addWidget(self.num_group, 2, 1, 1, 2)

        # group_size
        g.addWidget(QLabel("group_size"), 3, 0)
        self.group_size = QSpinBox()
        self.group_size.setRange(32, 512)
        self.group_size.setSingleStep(32)
        self.group_size.setValue(128)
        g.addWidget(self.group_size, 3, 1, 1, 2)

        # max_nn
        g.addWidget(QLabel("max_nn"), 4, 0)
        self.max_nn = QSpinBox()
        self.max_nn.setRange(10, 200)
        self.max_nn.setSingleStep(10)
        self.max_nn.setValue(40)
        g.addWidget(self.max_nn, 4, 1, 1, 2)

        # 开关
        self.cb_msnd = QCheckBox("use_MSND")
        self.cb_msnd.setChecked(True)
        g.addWidget(self.cb_msnd, 5, 0, 1, 2)

        self.cb_lfsa = QCheckBox("use_LFSA")
        self.cb_lfsa.setChecked(True)
        g.addWidget(self.cb_lfsa, 5, 2)

        self.cb_vis = QCheckBox("vis_save（保存可视化）")
        self.cb_vis.setChecked(False)
        g.addWidget(self.cb_vis, 6, 0, 1, 3)

        # level（仅 minishift 用）
        g.addWidget(QLabel("level"), 7, 0)
        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "easy", "medium", "hard"])
        g.addWidget(self.level_combo, 7, 1, 1, 2)

        return grp

    # ── 按钮组 ────────────────────────────────────────────────────────────────
    def _group_buttons(self):
        grp = QGroupBox()
        grp.setFlat(True)
        h = QHBoxLayout(grp)

        self.btn_run = QPushButton("▶  开始运行")
        self.btn_run.setObjectName("btnRun")
        self.btn_run.setMinimumHeight(38)
        self.btn_run.clicked.connect(self._run)
        h.addWidget(self.btn_run)

        self.btn_stop = QPushButton("⬛  停止")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setMinimumHeight(38)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop)
        h.addWidget(self.btn_stop)

        btn_clear = QPushButton("清空日志")
        btn_clear.setMinimumHeight(38)
        btn_clear.clicked.connect(self.log_box.clear)
        h.addWidget(btn_clear)

        return grp

    # ── 样式 ──────────────────────────────────────────────────────────────────
    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #1e1e2e;
                color: #cdd6f4;
                font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
                font-size: 13px;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: 700;
                color: #89b4fa;
                padding: 4px 0;
            }
            QLabel#section {
                font-size: 13px;
                font-weight: 600;
                color: #a6e3a1;
            }
            QLabel#hint {
                font-size: 11px;
                color: #6c7086;
            }
            QLabel#status {
                font-size: 11px;
                color: #6c7086;
                padding: 2px 0;
            }
            QFrame#divider {
                color: #313244;
            }
            QGroupBox {
                border: 1px solid #313244;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 6px;
                font-weight: 600;
                color: #bac2de;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #89b4fa;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: #181825;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #cdd6f4;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #89b4fa;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #181825;
                selection-background-color: #313244;
            }
            QPushButton {
                background: #313244;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #cdd6f4;
            }
            QPushButton:hover { background: #45475a; }
            QPushButton#btnRun {
                background: #89b4fa;
                color: #1e1e2e;
                font-weight: 700;
                border: none;
            }
            QPushButton#btnRun:hover { background: #b4befe; }
            QPushButton#btnRun:disabled { background: #45475a; color: #6c7086; }
            QPushButton#btnStop {
                background: #f38ba8;
                color: #1e1e2e;
                font-weight: 700;
                border: none;
            }
            QPushButton#btnStop:hover { background: #eba0ac; }
            QPushButton#btnStop:disabled { background: #45475a; color: #6c7086; }
            QTextEdit#logbox {
                background: #11111b;
                border: 1px solid #313244;
                border-radius: 6px;
                color: #a6e3a1;
                selection-background-color: #313244;
            }
            QCheckBox::indicator {
                width: 14px; height: 14px;
                border: 1px solid #45475a;
                border-radius: 3px;
                background: #181825;
            }
            QCheckBox::indicator:checked {
                background: #89b4fa;
                border-color: #89b4fa;
            }
            QSplitter::handle { background: #313244; width: 1px; }
        """)

    # ── 逻辑 ──────────────────────────────────────────────────────────────────
    def _browse(self, edit: QLineEdit):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", edit.text() or os.path.expanduser("~"))
        if folder:
            edit.setText(folder)

    def _on_dataset_change(self, idx):
        is_custom = (idx == 0)
        self.train_edit.setEnabled(is_custom)
        self.test_edit.setEnabled(is_custom)
        self.train_label.setEnabled(is_custom)
        self.test_label.setEnabled(is_custom)
        self.path_hint.setVisible(is_custom)

    def _dataset_key(self) -> str:
        """返回传给 --dataset 的字符串"""
        text = self.dataset_combo.currentText()
        return text.split("（")[0].strip()   # "custom（自定义路径）" → "custom"

    def _validate(self) -> bool:
        if self._dataset_key() == "custom":
            train = self.train_edit.text().strip()
            test  = self.test_edit.text().strip()
            if not train or not os.path.isdir(train):
                QMessageBox.warning(self, "路径错误", f"Train 文件夹不存在:\n{train}")
                return False
            if not test or not os.path.isdir(test):
                QMessageBox.warning(self, "路径错误", f"Test 文件夹不存在:\n{test}")
                return False
        return True

    def _build_cmd(self) -> (list, dict):
        dataset = self._dataset_key()
        cmd = [
            sys.executable, "main.py",
            "--dataset",    dataset,
            "--expname",    self.expname_edit.text().strip() or "gui_exp",
            "--device",     self.device_combo.currentText(),
            "--num_group",  str(self.num_group.value()),
            "--group_size", str(self.group_size.value()),
            "--max_nn",     str(self.max_nn.value()),
            "--use_MSND",   str(self.cb_msnd.isChecked()),
            "--use_LFSA",   str(self.cb_lfsa.isChecked()),
            "--vis_save",   str(self.cb_vis.isChecked()),
            "--level",      self.level_combo.currentText(),
        ]

        # 把自定义路径通过环境变量传给 custom.py
        env = os.environ.copy()
        if dataset == "custom":
            env["SIMPLE3D_TRAIN_PATH"] = self.train_edit.text().strip()
            env["SIMPLE3D_TEST_PATH"]  = self.test_edit.text().strip()

        return cmd, env

    def _run(self):
        if not self._validate():
            return

        self.log_box.clear()
        cmd, env = self._build_cmd()
        self._log(f"$ {' '.join(cmd)}\n")

        self.runner = RunnerThread(cmd, env)
        self.runner.log_signal.connect(self._log)
        self.runner.finish_signal.connect(self._on_finish)
        self.runner.start()

        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status.setText("运行中…")

    def _stop(self):
        if self.runner and self.runner.isRunning():
            self.runner.terminate()
            self._log("\n[INFO] 已手动停止。")
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.status.setText("已停止")

    def _on_finish(self, code: int):
        if code == 0:
            self._log("\n✅ 运行完成！")
            self.status.setText("完成")
        else:
            self._log(f"\n❌ 运行结束，返回码: {code}")
            self.status.setText(f"错误（返回码 {code}）")
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _log(self, text: str):
        self.log_box.moveCursor(QTextCursor.End)
        self.log_box.insertPlainText(text + "\n")
        self.log_box.moveCursor(QTextCursor.End)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = Simple3DGUI()
    win.show()
    sys.exit(app.exec_())
