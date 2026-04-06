"""
custom.py  —— 支持自定义 train/test 路径的数据集封装
用法：通过 GUI 传入 train_path 和 test_path，无需修改 main.py 里其他数据集文件。
"""

import os
import glob
import numpy as np
import torch
import open3d as o3d
from torch.utils.data import Dataset, DataLoader

# ── 配置 ────────────────────────────────────────────────────────────────────
VOXEL_SIZE = 0.15
# ────────────────────────────────────────────────────────────────────────────


def custom_classes():
    """返回一个占位类别名，保持与其他数据集接口一致。"""
    return ["custom"]


def _get_train_path():
    """运行时获取 train 路径"""
    return os.environ.get("SIMPLE3D_TRAIN_PATH", "")


def _get_test_path():
    """运行时获取 test 路径"""
    return os.environ.get("SIMPLE3D_TEST_PATH", "")


# ── 支持的点云文件后缀 ────────────────────────────────────────────────────────
SUPPORTED_EXTS = ["*.asc", "*.txt", "*.pcd", "*.ply"]

def _glob_pcds(folder: str):
    paths = []
    for ext in SUPPORTED_EXTS:
        paths.extend(glob.glob(os.path.join(folder, ext)))
    paths.sort()
    return paths


def _load_pcd(path: str) -> np.ndarray:
    """统一加载点云，返回 (N, 3) float32 numpy array。"""
    ext = os.path.splitext(path)[-1].lower()
    if ext in (".pcd", ".ply"):
        pcd = o3d.io.read_point_cloud(path)
        return np.asarray(pcd.points, dtype=np.float32)
    else:
        # .asc / .txt: 取前三列 xyz
        data = np.loadtxt(path, dtype=np.float32)
        return data[:, :3]


def _downsample(pts: np.ndarray) -> np.ndarray:
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    pcd = pcd.voxel_down_sample(voxel_size=VOXEL_SIZE)
    return np.asarray(pcd.points, dtype=np.float32)


# ── Train Dataset ─────────────────────────────────────────────────────────────
class CustomTrain(Dataset):
    def __init__(self, class_name="custom"):
        self.train_path = _get_train_path()  # ✅ 运行时获取
        if not self.train_path:
            raise ValueError("[CustomTrain] 环境变量 SIMPLE3D_TRAIN_PATH 未设置！")
        if not os.path.isdir(self.train_path):
            raise ValueError(f"[CustomTrain] train 路径不存在: {self.train_path}")
        
        self.pcd_paths = _glob_pcds(self.train_path)
        if len(self.pcd_paths) == 0:
            raise ValueError(f"[CustomTrain] 在 {self.train_path} 下未找到点云文件（支持 asc/txt/pcd/ply）")
        
        self.labels = [0] * len(self.pcd_paths)
        print(f"[CustomTrain] 加载了 {len(self.pcd_paths)} 个训练样本")

    def __len__(self):
        return len(self.pcd_paths)

    def __getitem__(self, idx):
        path  = self.pcd_paths[idx]
        label = self.labels[idx]
        pts   = _load_pcd(path)
        pts   = _downsample(pts)
        return pts, label, label, path


# ── Test Dataset ──────────────────────────────────────────────────────────────
class CustomTest(Dataset):
    """
    期望 test 目录结构（与 Real3D / MiniShift 一致）：
        test/
          good/       ← 正常样本
          defect_A/   ← 异常样本（子目录名任意）
          defect_B/
          ...
    若 test 目录下直接放点云文件（无子目录），所有文件视为 good。
    """
    def __init__(self, class_name="custom"):
        self.test_path = _get_test_path()  # ✅ 运行时获取
        if not self.test_path:
            raise ValueError("[CustomTest] 环境变量 SIMPLE3D_TEST_PATH 未设置！")
        if not os.path.isdir(self.test_path):
            raise ValueError(f"[CustomTest] test 路径不存在: {self.test_path}")

        self.pcd_paths, self.gt_paths, self.labels = self._load()
        if len(self.pcd_paths) == 0:
            raise ValueError(f"[CustomTest] 在 {self.test_path} 下未找到点云文件")
        
        print(f"[CustomTest] 加载了 {len(self.pcd_paths)} 个测试样本")

    def _load(self):
        pcd_paths, gt_paths, labels = [], [], []

        subdirs = [d for d in os.listdir(self.test_path)
                   if os.path.isdir(os.path.join(self.test_path, d))]

        if subdirs:
            # ── 有子目录：good / defect 结构 ──────────────────────────────
            for sub in subdirs:
                folder = os.path.join(self.test_path, sub)
                paths  = _glob_pcds(folder)
                paths.sort()
                if sub.lower() == "good":
                    pcd_paths.extend(paths)
                    gt_paths.extend([0] * len(paths))
                    labels.extend([0]   * len(paths))
                else:
                    pcd_paths.extend(paths)
                    gt_paths.extend(paths)   # 无逐点 GT，用路径占位
                    labels.extend([1] * len(paths))
        else:
            # ── 无子目录：直接放文件，全部视为 good ──────────────────────
            paths = _glob_pcds(self.test_path)
            paths.sort()
            pcd_paths.extend(paths)
            gt_paths.extend([0] * len(paths))
            labels.extend([0] * len(paths))

        return pcd_paths, gt_paths, labels

    def __len__(self):
        return len(self.pcd_paths)

    def __getitem__(self, idx):
        path  = self.pcd_paths[idx]
        gt    = self.gt_paths[idx]
        label = self.labels[idx]

        pts = _load_pcd(path)
        pts = _downsample(pts)

        if gt == 0:
            gt_tensor = torch.zeros([1, pts.shape[0]])
        else:
            # 无逐点标注时，异常帧 GT 全为 1（图像级判断）
            gt_tensor = torch.ones([1, 1, pts.shape[0]])

        return pts, gt_tensor[:1], label, path


# ── DataLoader 工厂（与其他数据集保持相同接口）────────────────────────────────
def get_custom_loader(split, class_name="custom"):
    if split == "train":
        dataset = CustomTrain(class_name)
    else:
        dataset = CustomTest(class_name)

    return DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
        num_workers=1,
        drop_last=False,
        pin_memory=True,
    )