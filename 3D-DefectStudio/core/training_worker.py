# -*- coding: utf-8 -*-
"""
training_worker.py
Simple3D 运行模块 - 支持独立conda环境

更新说明：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 支持指定 conda 环境名称（自动查找Python路径）
- 支持直接指定 Python 解释器路径
- GUI环境与Simple3D环境完全隔离
- 使用 QProcess 管理子进程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import subprocess
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, Signal, QProcess, QProcessEnvironment


def find_conda_python(env_name: str) -> Optional[str]:
    """
    根据conda环境名称查找Python解释器路径
    
    Args:
        env_name: conda环境名称（如 'Simple3D_env'）
    
    Returns:
        Python解释器的完整路径，如果找不到则返回None
    """
    if not env_name:
        return None
    
    # 常见的conda安装位置
    home = os.path.expanduser("~")
    
    # Windows vs Unix 的 Python 可执行文件名
    if sys.platform == 'win32':
        python_name = "python.exe"
        possible_bases = [
            os.path.join(home, "anaconda3"),
            os.path.join(home, "miniconda3"),
            os.path.join(home, "Anaconda3"),
            os.path.join(home, "Miniconda3"),
            "C:\\ProgramData\\Anaconda3",
            "C:\\ProgramData\\Miniconda3",
            os.path.join(home, "AppData", "Local", "anaconda3"),
            os.path.join(home, "AppData", "Local", "miniconda3"),
        ]
    else:
        python_name = "python"
        possible_bases = [
            os.path.join(home, "anaconda3"),
            os.path.join(home, "miniconda3"),
            "/opt/anaconda3",
            "/opt/miniconda3",
            "/usr/local/anaconda3",
            "/usr/local/miniconda3",
        ]
    
    # 尝试从 CONDA_PREFIX 推断
    conda_prefix = os.environ.get("CONDA_PREFIX", "")
    if conda_prefix:
        # 如果当前在某个conda环境中，往上找base
        if "envs" in conda_prefix:
            base = conda_prefix.rsplit("envs", 1)[0].rstrip(os.sep)
            possible_bases.insert(0, base)
    
    # 遍历查找
    for base in possible_bases:
        if sys.platform == 'win32':
            candidate = os.path.join(base, "envs", env_name, python_name)
        else:
            candidate = os.path.join(base, "envs", env_name, "bin", python_name)
        
        if os.path.isfile(candidate):
            return candidate
    
    # 最后尝试使用 conda run 命令获取
    try:
        result = subprocess.run(
            ["conda", "run", "-n", env_name, "which", "python"] if sys.platform != 'win32' 
            else ["conda", "run", "-n", env_name, "where", "python"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            path = result.stdout.strip().split('\n')[0]
            if os.path.isfile(path):
                return path
    except Exception:
        pass
    
    return None


@dataclass
class Simple3DConfig:
    """Simple3D 运行配置"""
    dataset: str = "custom"
    train_path: str = ""
    test_path: str = ""
    expname: str = "my_exp"
    device: str = "cuda:0"
    num_group: int = 4096
    group_size: int = 128
    max_nn: int = 40
    use_MSND: bool = True
    use_LFSA: bool = True
    vis_save: bool = False
    level: str = "ALL"
    # 新增：环境配置
    python_path: str = ""      # 直接指定Python解释器路径
    conda_env: str = ""        # conda环境名称
    simple3d_path: str = ""    # Simple3D项目路径
    
    @classmethod
    def from_dict(cls, d: dict) -> 'Simple3DConfig':
        return cls(
            dataset=d.get('dataset', 'custom'),
            train_path=d.get('train_path', ''),
            test_path=d.get('test_path', ''),
            expname=d.get('expname', 'my_exp'),
            device=d.get('device', 'cuda:0'),
            num_group=d.get('num_group', 4096),
            group_size=d.get('group_size', 128),
            max_nn=d.get('max_nn', 40),
            use_MSND=d.get('use_MSND', True),
            use_LFSA=d.get('use_LFSA', True),
            vis_save=d.get('vis_save', False),
            level=d.get('level', 'ALL'),
            python_path=d.get('python_path', ''),
            conda_env=d.get('conda_env', ''),
            simple3d_path=d.get('simple3d_path', ''),
        )
    
    def to_args(self) -> list:
        """转换为命令行参数列表"""
        return [
            "--dataset",    self.dataset,
            "--expname",    self.expname,
            "--device",     self.device,
            "--num_group",  str(self.num_group),
            "--group_size", str(self.group_size),
            "--max_nn",     str(self.max_nn),
            "--use_MSND",   str(self.use_MSND),
            "--use_LFSA",   str(self.use_LFSA),
            "--vis_save",   str(self.vis_save),
            "--level",      self.level,
        ]


class Simple3DRunner(QObject):
    """
    Simple3D 运行器 - 支持独立conda环境
    
    信号:
        log_message: 日志消息
        status_changed: 状态变化 ('idle', 'running', 'completed', 'failed', 'cancelled')
        run_finished: 运行完成 (success: bool, return_code: int)
    """
    
    # Qt 信号
    log_message = Signal(str)
    status_changed = Signal(str)
    run_finished = Signal(bool, int)
    
    def __init__(self, simple3d_path: str = None, parent=None):
        super().__init__(parent)
        
        self.simple3d_path = simple3d_path or os.getcwd()
        self._process: Optional[QProcess] = None
        self._current_config: Optional[Simple3DConfig] = None
        self._status = 'idle'
    
    @property
    def status(self) -> str:
        return self._status
    
    @status.setter
    def status(self, value: str):
        self._status = value
        self.status_changed.emit(value)
    
    def is_running(self) -> bool:
        return self._process is not None and \
               self._process.state() == QProcess.Running
    
    def set_simple3d_path(self, path: str):
        self.simple3d_path = path
    
    def _resolve_python_path(self, config: Simple3DConfig) -> str:
        """
        解析Python解释器路径
        
        优先级:
        1. 直接指定的python_path
        2. 通过conda_env查找
        3. 默认使用sys.executable（GUI的Python，可能会失败）
        """
        # 1. 直接指定的路径
        if config.python_path and os.path.isfile(config.python_path):
            return config.python_path
        
        # 2. 通过conda环境名查找
        if config.conda_env:
            found = find_conda_python(config.conda_env)
            if found:
                return found
            else:
                self.log_message.emit(f"⚠️ 未找到conda环境 '{config.conda_env}' 的Python")
        
        # 3. 默认
        self.log_message.emit("⚠️ 使用GUI的Python（可能缺少Simple3D依赖）")
        return sys.executable
    
    def run(self, config: Dict[str, Any]) -> bool:
        """
        开始运行 Simple3D
        
        Args:
            config: 配置字典
            
        Returns:
            是否成功启动
        """
        if self.is_running():
            self.log_message.emit("⚠️ Simple3D 已在运行中")
            return False
        
        # 解析配置
        self._current_config = Simple3DConfig.from_dict(config)
        
        # 如果配置中有simple3d_path，使用它
        if self._current_config.simple3d_path:
            self.simple3d_path = self._current_config.simple3d_path
        
        # 验证custom数据集路径
        if self._current_config.dataset == "custom":
            if not self._current_config.train_path or \
               not os.path.isdir(self._current_config.train_path):
                self.log_message.emit(f"❌ Train 文件夹不存在: {self._current_config.train_path}")
                return False
            if not self._current_config.test_path or \
               not os.path.isdir(self._current_config.test_path):
                self.log_message.emit(f"❌ Test 文件夹不存在: {self._current_config.test_path}")
                return False
        
        # 查找 main.py
        main_script = self._find_main_script()
        if not main_script:
            self.log_message.emit(f"❌ 未找到 main.py，请检查 Simple3D 路径: {self.simple3d_path}")
            return False
        
        # 解析Python路径
        python_exe = self._resolve_python_path(self._current_config)
        self.log_message.emit(f"📍 Python: {python_exe}")
        self.log_message.emit(f"📍 Simple3D: {self.simple3d_path}")
        
        # 创建 QProcess
        self._process = QProcess(self)
        self._process.setWorkingDirectory(self.simple3d_path)
        
        # 设置环境变量（使用QProcessEnvironment）
        env = QProcessEnvironment.systemEnvironment()
        
        # 关键：设置conda环境的PATH和库路径
        conda_env_path = os.path.dirname(os.path.dirname(python_exe))  # 获取环境根目录
        if os.path.isdir(conda_env_path):
            # 设置 PATH
            env_bin = os.path.join(conda_env_path, "bin")
            current_path = env.value("PATH", "")
            env.insert("PATH", f"{env_bin}:{current_path}")
            
            # 设置 LD_LIBRARY_PATH (Linux) / DYLD_LIBRARY_PATH (Mac)
            env_lib = os.path.join(conda_env_path, "lib")
            if sys.platform == "darwin":
                current_ld = env.value("DYLD_LIBRARY_PATH", "")
                env.insert("DYLD_LIBRARY_PATH", f"{env_lib}:{current_ld}" if current_ld else env_lib)
            else:
                current_ld = env.value("LD_LIBRARY_PATH", "")
                env.insert("LD_LIBRARY_PATH", f"{env_lib}:{current_ld}" if current_ld else env_lib)
            
            # 设置 CONDA_PREFIX
            env.insert("CONDA_PREFIX", conda_env_path)
            
            self.log_message.emit(f"📍 Conda Env: {conda_env_path}")
        
        if self._current_config.dataset == "custom":
            env.insert("SIMPLE3D_TRAIN_PATH", self._current_config.train_path)
            env.insert("SIMPLE3D_TEST_PATH", self._current_config.test_path)
        self._process.setProcessEnvironment(env)
        
        # 连接信号
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)
        
        # 构建命令
        args = [main_script] + self._current_config.to_args()
        
        self.status = 'running'
        
        cmd_str = f"{python_exe} {' '.join(args)}"
        self.log_message.emit(f"$ {cmd_str}")
        self.log_message.emit("")
        
        # 启动进程
        self._process.start(python_exe, args)
        
        return True
    
    def stop(self):
        """停止运行"""
        if not self.is_running():
            return
        
        self.log_message.emit("")
        self.log_message.emit("⏹️ 正在停止...")
        self.status = 'cancelled'
        
        self._process.terminate()
        
        if not self._process.waitForFinished(3000):
            self._process.kill()
    
    def _find_main_script(self) -> Optional[str]:
        """查找 main.py 脚本"""
        candidates = ["main.py", "run.py", "train.py"]
        
        for name in candidates:
            path = os.path.join(self.simple3d_path, name)
            if os.path.isfile(path):
                return path
        
        return None
    
    def _on_stdout(self):
        if self._process is None:
            return
        
        data = self._process.readAllStandardOutput().data()
        try:
            text = data.decode('utf-8', errors='ignore')
        except:
            text = str(data)
        
        for line in text.rstrip().split('\n'):
            if line:
                self.log_message.emit(line)
    
    def _on_stderr(self):
        if self._process is None:
            return
        
        data = self._process.readAllStandardError().data()
        try:
            text = data.decode('utf-8', errors='ignore')
        except:
            text = str(data)
        
        for line in text.rstrip().split('\n'):
            if line:
                if any(x in line.lower() for x in ['deprecat', 'warning', 'userwarning']):
                    self.log_message.emit(f"[WARN] {line}")
                else:
                    self.log_message.emit(f"[ERR] {line}")
    
    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        success = (exit_code == 0 and exit_status == QProcess.NormalExit)
        
        self.log_message.emit("")
        
        if self.status == 'cancelled':
            self.log_message.emit("⏹️ 已手动停止")
            self.run_finished.emit(False, exit_code)
        elif success:
            self.status = 'completed'
            self.log_message.emit("✅ 运行完成！")
            self.run_finished.emit(True, exit_code)
        else:
            self.status = 'failed'
            self.log_message.emit(f"❌ 运行失败（返回码: {exit_code}）")
            self.run_finished.emit(False, exit_code)
        
        self._process = None
    
    def _on_error(self, error: QProcess.ProcessError):
        error_msgs = {
            QProcess.FailedToStart: "进程启动失败（检查Python路径是否正确）",
            QProcess.Crashed: "进程崩溃",
            QProcess.Timedout: "进程超时",
            QProcess.WriteError: "写入错误",
            QProcess.ReadError: "读取错误",
            QProcess.UnknownError: "未知错误",
        }
        
        msg = error_msgs.get(error, "未知错误")
        self.log_message.emit(f"❌ 进程错误: {msg}")
        self.status = 'failed'


# 向后兼容的别名
Simple3DTrainingWorker = Simple3DRunner
TrainingConfig = Simple3DConfig


class TrainingStatus:
    """训练状态常量（向后兼容）"""
    IDLE = "idle"
    PREPARING = "preparing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
