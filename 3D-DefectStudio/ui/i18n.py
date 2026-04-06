# -*- coding: utf-8 -*-
"""
i18n Module — Bilingual (EN / ZH) string table
Updated: Added Simple3D config panel strings
"""

from typing import Callable

_LANG = 'en'

STRINGS: dict[str, dict[str, str]] = {
    'en': {
        # ── Window ──────────────────────────────────────
        'window_title': '3D Point Cloud Visualization 2026.v1',

        # ── Menus ───────────────────────────────────────
        'menu_file':     'File',
        'menu_edit':     'Edit',
        'menu_view':     'View',
        'menu_language': 'Language',
        'menu_help':     'Help',

        # ── File menu ───────────────────────────────────
        'action_open':      'Open Point Cloud…',
        'action_export':    'Export View…',
        'action_save_data': 'Save Dataset…',
        'action_exit':      'Exit',

        # ── Edit menu ───────────────────────────────────
        'action_clear':       'Clear Scene',
        'action_delete':      'Delete File from Disk',
        'action_select_mode': 'Selection Mode',
        'action_delete_sel':  'Delete Selection',
        'action_clear_sel':   'Clear Selection',
        'action_restore':     'Restore All',

        # ── View menu ───────────────────────────────────
        'action_reset_view': 'Reset View',
        'action_axis':       'Show Axes',
        'action_grid':       'Show Grid',
        'action_rotate':     'Auto Rotate',
        'action_bg_color':   'Background Color…',
        'action_theme':      'Toggle Theme',
        'action_zoom_in':    'Zoom In',
        'action_zoom_out':   'Zoom Out',

        # ── Language ────────────────────────────────────
        'lang_en': 'English',
        'lang_zh': '中文',

        # ── Help menu ───────────────────────────────────
        'action_help':  'Help',
        'action_about': 'About',

        # ── Docks ───────────────────────────────────────
        'dock_files':      'Files',
        'dock_properties': 'Properties',
        'dock_log':        'Log',

        # ── Properties panel ────────────────────────────
        'prop_file':        'File',
        'prop_points':      'Points',
        'prop_color_mode':  'Color Mode',
        'prop_lut':         'LUT',
        'prop_solid_color': 'Solid Color',
        'prop_point_size':  'Point Size',
        'prop_opacity':     'Opacity',
        'prop_hint':        'Left Drag=Rotate  |  Wheel=Zoom  |  Wheel Drag=Pan',

        # ── Color modes ─────────────────────────────────
        'color_auto':      'Auto',
        'color_raw_rgb':   'Raw RGB',
        'color_score_lut': 'Score LUT',
        'color_x_grad':    'X Gradient',
        'color_y_grad':    'Y Gradient',
        'color_z_grad':    'Z Gradient',
        'color_solid':     'Solid Color',

        # ── Status bar ──────────────────────────────────
        'status_ready':   'Ready',
        'status_no_file': 'No file loaded',
        'status_loading': 'Loading…',
        'status_select':  'Selection Mode',
        'status_defect':  'Defect Mode',
        'pts_label':      'pts',

        # ── Ribbon tabs ─────────────────────────────────
        'tab_home':       'Home',
        'tab_view':       'View',
        'tab_synth':      'Anomaly Gen',
        'tab_detect':     'Anomaly Det',
        'tab_help':       'Help',
        'tab_about':      'About',
        'tab_help_about': 'Help & About',

        # ── Ribbon groups ───────────────────────────────
        'grp_file':        'File',
        'grp_scene':       'Scene',
        'grp_interaction': 'Interaction',
        'grp_display':     'Display',
        'grp_tools':       'Tools',
        'grp_1d':          '1D Primitives',
        'grp_2d':          '2D Primitives',
        'grp_3d':          '3D Primitives',
        'grp_params':      'Parameters',
        'grp_actions':     'Actions',
        'grp_data':        'Data Select',
        'grp_s3d':         'Simple3D',

        # ── Ribbon buttons ──────────────────────────────
        'btn_open':       'Open',
        'btn_export':     'Export',
        'btn_save_data':  'Save Data',
        'btn_reset_view': 'Reset View',
        'btn_clear':      'Clear',
        'btn_delete':     'Delete',
        'btn_select':     'Select',
        'btn_del_sel':    'Del Sel',
        'btn_clear_sel':  'Clear Sel',
        'btn_restore':    'Restore All',
        'btn_axis':       'Axis',
        'btn_grid':       'Grid',
        'btn_zoom_in':    'Zoom In',
        'btn_zoom_out':   'Zoom Out',
        'btn_bg':         'Background',
        'btn_rotate':     'Auto Rotate',
        'btn_theme':      'Theme',
        'btn_undo':       'Undo',
        'btn_apply':      'Apply',
        'btn_exit_mode':  'Exit',
        'btn_train':      'Train Data',
        'btn_test':       'Test Data',
        'btn_help':       'Help',
        'btn_about':      'About',

        # ── Simple3D Runner ─────────────────────────────
        's3d_config':          'Configuration',
        's3d_control':         'Control',
        's3d_status':          'Status',
        's3d_dataset_type':    'Dataset:',
        's3d_train_path':      'Train:',
        's3d_test_path':       'Test:',
        's3d_train_placeholder': 'Select training data folder…',
        's3d_test_placeholder':  'Select test data folder…',
        's3d_select_folder':   'Select Folder',
        's3d_expname':         'Exp Name:',
        's3d_device':          'Device:',
        's3d_run':             '▶ Run',
        's3d_stop':            '⬛ Stop',
        's3d_clear_log':       'Clear Log',
        's3d_running':         'Running…',
        's3d_completed':       'Completed',
        's3d_failed':          'Failed',
        's3d_cancelled':       'Cancelled',
        's3d_path_error':      'Path Error',
        's3d_train_not_exist': 'Train folder does not exist:',
        's3d_test_not_exist':  'Test folder does not exist:',

        # ── Simple3D Config Panel (NEW) ─────────────────
        's3d_conda_env':       'Conda:',
        's3d_or_python':       'or Py:',
        's3d_conda_tooltip':   'Simple3D conda environment name',
        's3d_python_tooltip':  'Python interpreter full path (higher priority than Conda)',
        's3d_path':            'S3D Path:',
        's3d_path_placeholder': 'Simple3D project directory (with main.py)',
        's3d_path_tooltip':    'Simple3D project root directory (containing main.py)',
        's3d_dataset':         'Dataset:',
        's3d_experiment':      'Exp:',
        's3d_train_data_placeholder': 'Training data folder...',
        's3d_test_data_placeholder':  'Test data folder...',
        's3d_select_python':   'Select Python Interpreter',
        's3d_select_s3d_dir':  'Select Simple3D Project Directory',

        # ── Dialogs ─────────────────────────────────────
        'dlg_delete_title': 'Delete File',
        'dlg_delete_msg':   'Remove {name} from disk?',
        'dlg_open_filter':  'Point Data (*.txt *.csv *.xyz *.asc *.xyzf *.bin);;All Files (*.*)',
        'dlg_export_filter':'PNG (*.png);;TXT (*.txt)',
        'dlg_open_title':   'Open Point Cloud',
        'dlg_export_title': 'Export',
        'dlg_save_title':   'Save Dataset',
        'dlg_save_filter':  'Text Files (*.txt)',
        'dlg_bg_title':     'Select Background Color',
        'dlg_color_title':  'Select Color',
        'dlg_res_title':    'Resolution',
        'dlg_res_label':    'Value:',
        'dlg_k_title':      'Neighbors',
        'dlg_k_label':      'Value:',
        'warn_no_file':     'Please open a point cloud first',
    },

    'zh': {
        # ── Window ──────────────────────────────────────
        'window_title': '三维点云可视化 2026.v1',

        # ── Menus ───────────────────────────────────────
        'menu_file':     '文件',
        'menu_edit':     '编辑',
        'menu_view':     '视图',
        'menu_language': '语言',
        'menu_help':     '帮助',

        # ── File menu ───────────────────────────────────
        'action_open':      '打开点云文件…',
        'action_export':    '导出视图…',
        'action_save_data': '保存数据集…',
        'action_exit':      '退出',

        # ── Edit menu ───────────────────────────────────
        'action_clear':       '清空场景',
        'action_delete':      '从磁盘删除文件',
        'action_select_mode': '选择模式',
        'action_delete_sel':  '删除选区',
        'action_clear_sel':   '取消选择',
        'action_restore':     '恢复全部',

        # ── View menu ───────────────────────────────────
        'action_reset_view': '重置视角',
        'action_axis':       '显示坐标轴',
        'action_grid':       '显示网格',
        'action_rotate':     '自动旋转',
        'action_bg_color':   '背景颜色…',
        'action_theme':      '切换主题',
        'action_zoom_in':    '放大',
        'action_zoom_out':   '缩小',

        # ── Language ────────────────────────────────────
        'lang_en': 'English',
        'lang_zh': '中文',

        # ── Help menu ───────────────────────────────────
        'action_help':  '使用帮助',
        'action_about': '关于',

        # ── Docks ───────────────────────────────────────
        'dock_files':      '文件列表',
        'dock_properties': '属性面板',
        'dock_log':        '日志',

        # ── Properties panel ────────────────────────────
        'prop_file':        '文件名',
        'prop_points':      '点数量',
        'prop_color_mode':  '颜色模式',
        'prop_lut':         '色表',
        'prop_solid_color': '纯色',
        'prop_point_size':  '点大小',
        'prop_opacity':     '透明度',
        'prop_hint':        '左键拖拽=旋转  |  滚轮=缩放  |  滚轮拖拽=平移',

        # ── Color modes ─────────────────────────────────
        'color_auto':      '自动',
        'color_raw_rgb':   '原始RGB',
        'color_score_lut': '分数色表',
        'color_x_grad':    'X轴渐变',
        'color_y_grad':    'Y轴渐变',
        'color_z_grad':    'Z轴渐变',
        'color_solid':     '纯色',

        # ── Status bar ──────────────────────────────────
        'status_ready':   '就绪',
        'status_no_file': '未加载文件',
        'status_loading': '加载中…',
        'status_select':  '选择模式',
        'status_defect':  '缺陷模式',
        'pts_label':      '个点',

        # ── Ribbon tabs ─────────────────────────────────
        'tab_home':       '主页',
        'tab_view':       '视图',
        'tab_synth':      '异常生成',
        'tab_detect':     '异常检测',
        'tab_help':       '帮助',
        'tab_about':      '关于',
        'tab_help_about': '帮助与关于',

        # ── Ribbon groups ───────────────────────────────
        'grp_file':        '文件',
        'grp_scene':       '场景',
        'grp_interaction': '交互',
        'grp_display':     '显示',
        'grp_tools':       '工具',
        'grp_1d':          '一维原语',
        'grp_2d':          '二维原语',
        'grp_3d':          '三维原语',
        'grp_params':      '参数',
        'grp_actions':     '操作',
        'grp_data':        '数据选择',
        'grp_s3d':         'Simple3D',

        # ── Ribbon buttons ──────────────────────────────
        'btn_open':       '打开',
        'btn_export':     '导出',
        'btn_save_data':  '保存数据',
        'btn_reset_view': '重置视角',
        'btn_clear':      '清空',
        'btn_delete':     '删除',
        'btn_select':     '选择',
        'btn_del_sel':    '删除选区',
        'btn_clear_sel':  '取消选择',
        'btn_restore':    '恢复全部',
        'btn_axis':       '坐标轴',
        'btn_grid':       '网格',
        'btn_zoom_in':    '放大',
        'btn_zoom_out':   '缩小',
        'btn_bg':         '背景',
        'btn_rotate':     '自动旋转',
        'btn_theme':      '主题',
        'btn_undo':       '撤销',
        'btn_apply':      '应用',
        'btn_exit_mode':  '退出',
        'btn_train':      '训练数据',
        'btn_test':       '测试数据',
        'btn_help':       '帮助',
        'btn_about':      '关于',

        # ── Simple3D Runner ─────────────────────────────
        's3d_config':          '配置',
        's3d_control':         '控制',
        's3d_status':          '状态',
        's3d_dataset_type':    '数据集:',
        's3d_train_path':      '训练集:',
        's3d_test_path':       '测试集:',
        's3d_train_placeholder': '选择训练数据文件夹…',
        's3d_test_placeholder':  '选择测试数据文件夹…',
        's3d_select_folder':   '选择文件夹',
        's3d_expname':         '实验名:',
        's3d_device':          '设备:',
        's3d_run':             '▶ 运行',
        's3d_stop':            '⬛ 停止',
        's3d_clear_log':       '清空日志',
        's3d_running':         '运行中…',
        's3d_completed':       '完成',
        's3d_failed':          '失败',
        's3d_cancelled':       '已取消',
        's3d_path_error':      '路径错误',
        's3d_train_not_exist': 'Train 文件夹不存在:',
        's3d_test_not_exist':  'Test 文件夹不存在:',

        # ── Simple3D Config Panel (NEW) ─────────────────
        's3d_conda_env':       'Conda:',
        's3d_or_python':       '或 Py:',
        's3d_conda_tooltip':   'Simple3D的conda环境名称',
        's3d_python_tooltip':  'Python解释器完整路径（优先级高于Conda）',
        's3d_path':            'S3D路径:',
        's3d_path_placeholder': 'Simple3D项目目录 (含main.py)',
        's3d_path_tooltip':    'Simple3D项目根目录（包含main.py）',
        's3d_dataset':         '数据集:',
        's3d_experiment':      '实验:',
        's3d_train_data_placeholder': '训练数据文件夹...',
        's3d_test_data_placeholder':  '测试数据文件夹...',
        's3d_select_python':   '选择Python解释器',
        's3d_select_s3d_dir':  '选择Simple3D项目目录',

        # ── Dialogs ─────────────────────────────────────
        'dlg_delete_title': '删除文件',
        'dlg_delete_msg':   '确定要从磁盘删除 {name} 吗？',
        'dlg_open_filter':  '点云文件 (*.txt *.csv *.xyz *.asc *.xyzf *.bin);;所有文件 (*.*)',
        'dlg_export_filter':'PNG 图像 (*.png);;文本文件 (*.txt)',
        'dlg_open_title':   '打开点云',
        'dlg_export_title': '导出',
        'dlg_save_title':   '保存数据集',
        'dlg_save_filter':  '文本文件 (*.txt)',
        'dlg_bg_title':     '选择背景颜色',
        'dlg_color_title':  '选择颜色',
        'dlg_res_title':    '分辨率',
        'dlg_res_label':    '值：',
        'dlg_k_title':      '邻域数量',
        'dlg_k_label':      '值：',
        'warn_no_file':     '请先打开点云文件',
    },
}


def set_language(lang: str) -> None:
    global _LANG
    if lang in STRINGS:
        _LANG = lang


def get_language() -> str:
    return _LANG


def tr(key: str, **kwargs) -> str:
    text = STRINGS.get(_LANG, STRINGS['en']).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def make_tr() -> Callable[[str], str]:
    lang = _LANG
    def _tr(key: str, **kwargs) -> str:
        text = STRINGS.get(lang, STRINGS['en']).get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text
    return _tr
