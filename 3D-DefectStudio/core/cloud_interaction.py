# -*- coding: utf-8 -*-
"""
cloud_interaction.py
Visual Fix:
- Fixed: Lasso overlay looking "ugly" (removed dots from Lasso mode).
- Kept: Multi-segment Scratch (Dots enabled only here).
- Kept: Physical Distance logic (Anti-penetration).
"""

import numpy as np
from PySide6.QtCore import QRect, QSize, Qt, QPoint, QObject, QEvent, QPointF
from PySide6.QtGui import QPolygonF, QPainter, QPen, QColor, QVector3D
from PySide6.QtWidgets import QMessageBox, QRubberBand, QWidget
from .anomaly_core import AnomalyGenerator


class LassoOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.path_points = []
        self.show_points = False  # [New Flag] Controls whether to draw red dots

    def update_path(self, points, show_points=False):
        self.path_points = points
        self.show_points = show_points
        self.update()

    def paintEvent(self, event):
        if not self.path_points: return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1. Draw the Line (Always)
        pen = QPen(QColor(255, 255, 0), 2)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        if len(self.path_points) > 1:
            poly = QPolygonF()
            for p in self.path_points:
                poly.append(QPointF(p))
            painter.drawPolyline(poly)

        # 2. Draw Control Points (Only if requested, e.g., for Scratch)
        if self.show_points:
            painter.setBrush(QColor(255, 0, 0))
            painter.setPen(Qt.NoPen)
            for p in self.path_points:
                painter.drawEllipse(QPointF(p), 4, 4)


class PointCloudInteractor(QObject):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main = main_window
        self.view3d = main_window.view3d
        self._pcd_cache = main_window._pcd_cache

        self._mode = 'view'
        self._current_selection_idx = None
        self._rubber = QRubberBand(QRubberBand.Rectangle, self.view3d)
        self._rubber_origin = QPoint()

        self._defect_mask_accumulated = None
        self._mask_history = []
        self._lasso_points = []
        self._geometry_history = []

        self.anomaly_worker = AnomalyGenerator()
        self._overlay = LassoOverlay(self.view3d)
        self._overlay.hide()
        self.view3d.installEventFilter(self)

        self._scratch_points_list = []
        self._scratch_start_point = None
        self._click_start_pos = None

    # =========================================================================
    #  Mode Control
    # =========================================================================
    def set_interaction_mode(self, mode: str):
        is_defect_mode = any(x in self._mode for x in ['1d', '2d', '3d', 'defect'])
        is_new_defect = any(x in mode for x in ['1d', '2d', '3d', 'defect'])

        if is_defect_mode and not is_new_defect:
            self.exit_defect_mode(clear_ui=True)

        self._mode = mode
        self._overlay.hide()
        self._rubber.hide()

        if mode == 'view':
            self.main.setCursor(Qt.ArrowCursor)
            self.main.log('Mode: View')
        elif mode == 'select':
            self.main.setCursor(Qt.CrossCursor)
            self.main.log('Mode: Rect Select')
        elif is_new_defect:
            self.main.setCursor(Qt.CrossCursor)

            if '1d_point' in mode:
                self.main.log('Mode: 1D Sphere.')
            elif '1d_scratch' in mode:
                self.main.log('Mode: Scratch - Left-Click to Add, Right-Click to Finish.')
                self._overlay.update_path([], show_points=True)  # Enable dots for scratch
                self._overlay.show()
            elif '3d_irreg' in mode:
                self.main.log('Mode: Random Irregular - Click to generate.')
            else:
                self.main.log('Mode: Defect Gen.')

            path = self.main._current_path
            if path and path in self._pcd_cache:
                n = len(self._pcd_cache[path]['xyz'])
                self._defect_mask_accumulated = np.zeros(n, dtype=bool)
                self._mask_history = []
            self._update_apply_button_state()

    def toggle_select_mode(self, on: bool):
        self.set_interaction_mode('select' if on else 'view')

    def exit_defect_mode(self, clear_ui=True):
        self._defect_mask_accumulated = None
        self._mask_history = []
        self._lasso_points = []

        self._scratch_points_list = []
        self._scratch_start_point = None
        self._current_scratch_path = None
        self._current_fracture_ends = None

        self._overlay.hide()
        self._overlay.update_path([], show_points=False)

        if hasattr(self.view3d, "set_selection_points"):
            self.view3d.set_selection_points(None)

        is_defect_mode = any(x in self._mode for x in ['1d', '2d', '3d', 'defect'])
        if is_defect_mode:
            self._mode = 'view'
            self.main.setCursor(Qt.ArrowCursor)

        if clear_ui:
            if hasattr(self.main, 'ribbon'):
                ribbon = self.main.ribbon
                btn_names = ['btn_1d_point', 'btn_1d_scratch', 'btn_2d_bend', 'btn_2d_fracture', 'btn_3d_areal',
                             'btn_3d_irreg']
                for name in btn_names:
                    if hasattr(ribbon, name): getattr(ribbon, name).setChecked(False)
                ribbon.current_defect_type = None
                if hasattr(ribbon, 'btn_apply'): ribbon.btn_apply.setEnabled(False)

    def _update_apply_button_state(self):
        # 修复：显式转换为 Python bool，避免 numpy.bool_ 类型错误
        if self._defect_mask_accumulated is not None:
            has_selection = bool(np.sum(self._defect_mask_accumulated) > 0)
        else:
            has_selection = False
        
        if hasattr(self.main, 'ribbon') and hasattr(self.main.ribbon, 'btn_apply'):
            self.main.ribbon.btn_apply.setEnabled(has_selection)
    # =========================================================================
    #  Actions
    # =========================================================================
    def delete_selection(self):
        if 'defect' in self._mode or any(x in self._mode for x in ['1d', '2d', '3d']):
            self.main.log("Please use 'Undo' in Defect Mode.")
            return

        path = self.main._current_path
        if path is None: return

        if self._current_selection_idx is None or len(self._current_selection_idx) == 0:
            QMessageBox.information(self.main, 'No Selection', 'Please select points first.')
            return

        data = self._pcd_cache[path]
        if "mask" not in data:
            n = len(data["xyz"])
            data["mask"] = np.ones(n, dtype=bool)

        mask = data['mask']
        idx = self._current_selection_idx

        valid_indices = idx[(idx >= 0) & (idx < mask.size)]
        mask[valid_indices] = False

        data['mask'] = mask
        self.main.apply_coloring()
        self.clear_selection()
        self.main.log(f'Deleted {len(valid_indices)} points.')

    def clear_selection(self):
        self._current_selection_idx = None
        if hasattr(self.view3d, "set_selection_points"):
            self.view3d.set_selection_points(None)
        self.main.log('Selection cleared')

    def restore_all(self):
        path = self.main._current_path
        if path is None: return
        data = self._pcd_cache[path]
        data['mask'] = np.ones(len(data['xyz']), dtype=bool)
        self.main.apply_coloring()
        self.clear_selection()
        self.main.log('Restored all points')

    # =========================================================================
    #  Defect Actions
    # =========================================================================
    def undo_selection(self):
        if 'view' in self._mode or 'select' in self._mode: return
        if not self._mask_history: return
        self._defect_mask_accumulated = self._mask_history.pop()
        self._update_preview()
        self._update_apply_button_state()
        self.main.log("Selection Undo successful.")

    def undo_last_defect(self):
        path = self.main._current_path
        if not path or not self._geometry_history:
            self.main.log("Nothing to undo.")
            return
        old_xyz, old_rgb, old_mask, old_mode = self._geometry_history.pop()
        data = self._pcd_cache[path]
        data['xyz'] = old_xyz
        data['rgb01'] = old_rgb

        if old_mode and hasattr(self.main.ribbon, '_set_defect_mode'):
            self.main.ribbon._set_defect_mode(old_mode)

        self._defect_mask_accumulated = old_mask
        self._mask_history = []
        self.main.apply_coloring()
        self._update_preview()
        self._update_apply_button_state()
        self.main.log("Geometry restored.")

    def apply_defect(self):
        if 'view' in self._mode or 'select' in self._mode: return
        path = self.main._current_path
        if not path: return

        mask = self._defect_mask_accumulated
        current_defect_type = getattr(self.main.ribbon, 'current_defect_type', None)

        is_two_point_op = any(t in str(current_defect_type) for t in ['fracture', 'crack', 'bend'])

        if (mask is None or np.sum(mask) < 3) and not is_two_point_op:
            QMessageBox.warning(self.main, "Apply", "No area selected!")
            return

        data = self._pcd_cache[path]
        points = data['xyz']
        old_len = len(points)

        current_rgb = data['rgb01'].copy() if data['rgb01'] is not None else None
        save_mask = mask.copy() if mask is not None else np.zeros(len(points), dtype=bool)

        if len(self._geometry_history) > 5: self._geometry_history.pop(0)
        self._geometry_history.append((points.copy(), current_rgb, save_mask, current_defect_type))

        defect_type = current_defect_type if current_defect_type else '3d_areal'
        use_auto = self.main.ribbon.chk_auto_params.isChecked()
        raw_strength = self.main.ribbon.sl_strength.value()
        r_strength = abs(raw_strength) / 1000.0
        is_convex = (raw_strength >= 0)

        # [NEW] Read Lasso Params
        r_freq = self.main.ribbon.sl_size.value() / 100.0  # Map 1-200 to 0.01-2.0
        lasso_style_idx = self.main.ribbon.cmb_lasso_style.currentIndex()
        lasso_formula = self.main.ribbon.txt_formula.text()

        self.main.log(f"Applying {defect_type}...")
        final_mask = None
        new_points = None

        # [UPDATE] Unified Logic for Lasso (Areal) and Random (Irreg)
        if '3d_areal' in defect_type or '3d_irreg' in defect_type:
            final_mask = mask
            if lasso_style_idx == 0:  # Gradient
                new_points = self.anomaly_worker.apply_gradient_deformation(
                    points, final_mask, stretch_scale=r_strength, convex=is_convex
                )
            else:  # Noise or Surface Fit
                mode_str = 'noise' if lasso_style_idx == 1 else 'surface_fit'

                # [Fix] apply_lasso_custom returns (points, mask) now
                new_points, updated_mask = self.anomaly_worker.apply_lasso_custom(
                    points, final_mask,
                    stretch_mode=mode_str,
                    strength=r_strength,
                    frequency=r_freq,
                    custom_formula=lasso_formula,
                    convex=is_convex
                )
                if mode_str == 'surface_fit':
                    final_mask = updated_mask

        elif '1d_scratch' in defect_type:
            final_mask = mask
            path_points = getattr(self, '_current_scratch_path', None)
            if path_points is not None:
                new_points = self.anomaly_worker.apply_scratch_deformation(
                    points, final_mask, path_points,
                    stretch_scale=r_strength, convex=is_convex
                )
            else:
                new_points = self.anomaly_worker.apply_gradient_deformation(points, final_mask,
                                                                            stretch_scale=r_strength, convex=is_convex)
        elif '2d_fracture' in defect_type:
            ends = getattr(self, '_current_fracture_ends', None)
            if ends is None: return
            if use_auto:
                p_gap = 0.015;
                p_depth = 0.3
            else:
                p_gap = self.main.ribbon.sl_size.value() / 2000.0
                p_depth = 0.1 + (abs(raw_strength) / 100.0) * 0.9
            new_points, final_mask = self.anomaly_worker.apply_fracture_plane_split(
                points, ends[0], ends[1], gap_width=p_gap, depth_ratio=p_depth
            )

        elif '2d_bend' in defect_type:
            ends = getattr(self, '_current_fracture_ends', None)
            if ends is None: return
            fixed_radius_ratio = 0.05
            if use_auto:
                p_angle = np.random.uniform(30, 60)
                if np.random.rand() > 0.5: p_angle = -p_angle
            else:
                p_angle = self.main.ribbon.sl_strength.value() * 0.9
            new_points, final_mask = self.anomaly_worker.apply_bend_deformation(
                points, ends[0], ends[1],
                bend_angle_deg=p_angle,
                radius_ratio=fixed_radius_ratio,
                target_count=old_len
            )
        else:
            # 这里处理 1d_point (Sphere) 以及其他未命中的情况
            final_mask = mask
            # Sphere 默认使用梯度拉伸 (Gradient)
            new_points = self.anomaly_worker.apply_gradient_deformation(
                points, final_mask, stretch_scale=r_strength, convex=is_convex
            )

        data['xyz'] = new_points
        new_len = len(new_points)

        if new_len != old_len or 'bend' in defect_type:
            new_rgb = np.ones((new_len, 3), dtype=np.float32) * 0.7
            data['rgb01'] = new_rgb
            data['mask'] = np.ones(new_len, dtype=bool)
            self._defect_mask_accumulated = np.zeros(new_len, dtype=bool)
        else:
            if data['rgb01'] is None: data['rgb01'] = np.ones_like(points) * 0.7

        if final_mask is not None and len(final_mask) == len(data['xyz']):
            data['rgb01'][final_mask] = [1.0, 0.0, 0.0]

        self.main.apply_coloring()
        self.exit_defect_mode(clear_ui=True)
        self.main.log(f"Defect applied. {np.sum(final_mask)} pts marked.")

    # =========================================================================
    #  Event Filter
    # =========================================================================
    def eventFilter(self, obj, ev):
        if obj is not self.view3d: return False
        et = ev.type()

        if et == QEvent.KeyPress:
            if ev.key() == Qt.Key_Escape:
                if 'defect' in self._mode or '1d' in self._mode or '2d' in self._mode or '3d' in self._mode:
                    self.exit_defect_mode(clear_ui=True)
                    return True
                elif self._mode == 'select':
                    self.set_interaction_mode('view')
                    if hasattr(self.main.ribbon, 'btn_select_mode'):
                        self.main.ribbon.btn_select_mode.setChecked(False)
                    return True
            if ev.key() == Qt.Key_Z and (ev.modifiers() & Qt.ControlModifier):
                if 'defect' in self._mode or '1d' in self._mode or '3d' in self._mode:
                    if self._mask_history:
                        self.undo_selection()
                    else:
                        self.undo_last_defect()
                return True

        if '1d_scratch' in self._mode and self._scratch_points_list:
            if et == QEvent.MouseMove or et == QEvent.Wheel:
                self._update_scratch_lines_overlay()

        if self._mode == 'view': return False

        if ev.type() in [QEvent.MouseButtonPress, QEvent.MouseMove]:
            if ev.modifiers() & Qt.ShiftModifier: return False

        # --- Defect Mode Handling ---
        is_defect_mode = any(x in self._mode for x in ['1d', '2d', '3d', 'defect'])
        if is_defect_mode:

            # [Case A] Single/Multi Point Click
            # Added '3d_irreg' (Random) here
            if any(m in self._mode for m in ['1d_point', '1d_scratch', '2d_fracture', '2d_bend', '3d_irreg']):
                if et == QEvent.MouseButtonPress:
                    if ev.button() == Qt.LeftButton:
                        self._click_start_pos = ev.position().toPoint()
                        return False
                    elif ev.button() == Qt.RightButton:
                        if '1d_scratch' in self._mode:
                            self._finish_scratch_selection()
                            return True

                elif et == QEvent.MouseButtonRelease and ev.button() == Qt.LeftButton:
                    start = getattr(self, '_click_start_pos', QPoint(0, 0))
                    dist = (ev.position().toPoint() - start).manhattanLength()
                    if dist < 5:
                        if '1d_point' in self._mode:
                            self._process_point_click(ev.position().toPoint())
                        elif '1d_scratch' in self._mode:
                            self._process_scratch_click(ev.position().toPoint())
                        elif '3d_irreg' in self._mode:
                            # [NEW] Call Random Ellipsoid handler
                            self._process_random_ellipsoid_click(ev.position().toPoint())
                        else:
                            self._process_two_point_click(ev.position().toPoint())
                        return True
                    return False

            # [Case B] Lasso
            else:
                if et == QEvent.MouseButtonPress and ev.button() == Qt.LeftButton:
                    self._lasso_points = [ev.position().toPoint()]
                    self._overlay.resize(self.view3d.size())
                    # [Fix] Explicitly turn off dots for Lasso
                    self._overlay.update_path(self._lasso_points, show_points=False)
                    self._overlay.show()
                    return True
                elif et == QEvent.MouseMove and ev.buttons() & Qt.LeftButton:
                    self._lasso_points.append(ev.position().toPoint())
                    # [Fix] Explicitly turn off dots for Lasso
                    self._overlay.update_path(self._lasso_points, show_points=False)
                    return True
                elif et == QEvent.MouseButtonRelease and ev.button() == Qt.LeftButton:
                    self._overlay.hide()
                    if len(self._lasso_points) > 2:
                        self._process_lasso_selection(self._lasso_points)
                    self._lasso_points = []
                    return True

        # Select Mode
        if self._mode == 'select':
            if et == QEvent.MouseButtonPress and ev.button() == Qt.LeftButton:
                self._rubber_origin = ev.position().toPoint()
                self._rubber.setGeometry(QRect(self._rubber_origin, QSize()))
                self._rubber.show()
                return True
            elif et == QEvent.MouseMove and self._rubber.isVisible():
                rect = QRect(self._rubber_origin, ev.position().toPoint()).normalized()
                self._rubber.setGeometry(rect)
                return True
            elif et == QEvent.MouseButtonRelease and ev.button() == Qt.LeftButton:
                rect = self._rubber.geometry()
                self._rubber.hide()
                idx = self._pick_points_in_rect(rect)
                self._set_selection(idx)
                return True

        return super().eventFilter(obj, ev)

    # =========================================================================
    #  Helper Functions
    # =========================================================================
    def _set_selection(self, idx):
        if idx is None or len(idx) == 0:
            self.clear_selection()
            return

        self._current_selection_idx = np.unique(idx.astype(int))
        path = self.main._current_path
        if path is None: return

        data = self._pcd_cache[path]
        mask = data.get('mask', np.ones(len(data['xyz']), dtype=bool))

        ok = (self._current_selection_idx >= 0) & (self._current_selection_idx < mask.size) & mask[
            self._current_selection_idx]
        vis_idx = self._current_selection_idx[ok]

        if hasattr(self.view3d, "set_selection_points"):
            self.view3d.set_selection_points(data['xyz'][vis_idx])

        self.main.log(f'Selected {len(vis_idx)} points')

    def _update_preview(self):
        mask = self._defect_mask_accumulated
        if hasattr(self.view3d, "set_selection_points"):
            if mask is None:
                self.view3d.set_selection_points(None)
            else:
                path = self.main._current_path
                data = self._pcd_cache[path]
                self.view3d.set_selection_points(data['xyz'][mask])
        self.view3d.update()

    def _get_camera_position(self):
        """Returns the current camera position as a numpy array."""
        cam_pos_q = self.view3d.cameraPosition()
        return np.array([cam_pos_q.x(), cam_pos_q.y(), cam_pos_q.z()])

    def _pick_points_in_rect(self, rect: QRect):
        """
        [THE PHYSICAL FIX for Clicks]
        """
        path = self.main._current_path
        if path is None: return np.array([], dtype=int)
        data = self._pcd_cache[path]
        xyz_all = data['xyz']
        if xyz_all.size == 0: return np.array([], dtype=int)

        pts_screen, _, valid_z = self._project_points_to_screen(xyz_all)
        if pts_screen is None: return np.array([], dtype=int)

        is_single_click = (rect.width() < 10 and rect.height() < 10)

        search_rect = QRect(rect)
        if is_single_click:
            center = rect.center()
            radius = 50
            search_rect = QRect(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

        xr0, yr0, xr1, yr1 = search_rect.left(), search_rect.top(), search_rect.right(), search_rect.bottom()
        if xr0 > xr1: xr0, xr1 = xr1, xr0
        if yr0 > yr1: yr0, yr1 = yr1, yr0

        x = pts_screen[:, 0]
        y = pts_screen[:, 1]

        mask = data.get('mask', np.ones(len(xyz_all), dtype=bool))
        in_rect = (x >= xr0) & (x <= xr1) & (y >= yr0) & (y <= yr1) & valid_z & mask

        candidate_indices = np.nonzero(in_rect)[0]
        if len(candidate_indices) == 0: return np.array([], dtype=int)

        if is_single_click:
            c_x, c_y = rect.center().x(), rect.center().y()
            cam_pos = self._get_camera_position()
            cand_xyz = xyz_all[candidate_indices]

            diff = cand_xyz - cam_pos
            dist_sq_to_cam = np.sum(diff ** 2, axis=1)

            min_dist_sq = np.min(dist_sq_to_cam)
            min_dist = np.sqrt(min_dist_sq)

            # Tolerance for clicks: 2%
            tolerance = min_dist * 0.02
            cutoff_sq = (min_dist + tolerance) ** 2

            is_foreground = dist_sq_to_cam <= cutoff_sq

            if not np.any(is_foreground):
                best_local = np.argmin(dist_sq_to_cam)
                return np.array([candidate_indices[best_local]], dtype=int)

            foreground_indices = candidate_indices[is_foreground]
            fg_x = x[foreground_indices]
            fg_y = y[foreground_indices]

            dist_2d_sq = (fg_x - c_x) ** 2 + (fg_y - c_y) ** 2
            best_fg_local = np.argmin(dist_2d_sq)

            return np.array([foreground_indices[best_fg_local]], dtype=int)

        return candidate_indices.astype(int)

    def _process_point_click(self, pos: QPoint):
        rect = QRect(pos.x() - 1, pos.y() - 1, 2, 2)
        indices = self._pick_points_in_rect(rect)
        if len(indices) == 0: return

        center_idx = indices[0]

        path = self.main._current_path
        data = self._pcd_cache[path]
        points = data['xyz']
        center_point = points[center_idx]

        r_size = self.main.ribbon.sl_size.value() / 1000.0
        mask = self.anomaly_worker.generate_sphere_mask(points, center_point, radius_ratio=r_size)

        count = np.sum(mask)
        if count > 0:
            if self._defect_mask_accumulated is None:
                self._defect_mask_accumulated = np.zeros(len(points), dtype=bool)
            self._mask_history.append(self._defect_mask_accumulated.copy())
            self._defect_mask_accumulated |= mask

            self._update_preview()            
            self._update_apply_button_state()
            self.main.log(f"Sphere added ({count} pts).")

    # --- [NEW] Random Ellipsoid Handler ---
    def _process_random_ellipsoid_click(self, pos: QPoint):
        """Random Mode: Generates Ellipsoid Mask from Single Click."""
        rect = QRect(pos.x() - 1, pos.y() - 1, 2, 2)
        indices = self._pick_points_in_rect(rect)
        if len(indices) == 0: return

        center_idx = indices[0]
        path = self.main._current_path
        data = self._pcd_cache[path]
        points = data['xyz']
        center_point = points[center_idx]

        # Get base scale from generic Size slider
        base_size = self.main.ribbon.sl_size.value() / 1000.0

        cam_pos = self._get_camera_position()

        # Generate Mask with internal randomization
        mask = self.anomaly_worker.generate_ellipsoid_mask_from_click(
            points, center_point, cam_pos, base_scale=base_size
        )

        count = np.sum(mask)
        if count > 0:
            if self._defect_mask_accumulated is None:
                self._defect_mask_accumulated = np.zeros(len(points), dtype=bool)

            self._mask_history.append(self._defect_mask_accumulated.copy())
            self._defect_mask_accumulated |= mask

            self._update_preview()
            self._update_apply_button_state()
            self.main.log(f"Ellipsoid added ({count} pts).")

    # --- Polyline Scratch Logic ---
    def _process_scratch_click(self, pos: QPoint):
        rect = QRect(pos.x() - 1, pos.y() - 1, 2, 2)
        indices = self._pick_points_in_rect(rect)
        if len(indices) == 0: return

        path = self.main._current_path
        data = self._pcd_cache[path]
        points = data['xyz']
        clicked_point = points[indices[0]]

        self._scratch_points_list.append(clicked_point)

        all_nodes = np.array(self._scratch_points_list)
        if hasattr(self.view3d, "set_selection_points"):
            self.view3d.set_selection_points(all_nodes)

        self._update_scratch_lines_overlay()
        self.main.log(f"Point {len(self._scratch_points_list)} added.")

    def _finish_scratch_selection(self):
        if len(self._scratch_points_list) < 2:
            self.main.log("Need at least 2 points for a scratch.")
            return

        path = self.main._current_path
        data = self._pcd_cache[path]
        points = data['xyz']

        use_auto = self.main.ribbon.chk_auto_params.isChecked()
        r_size_val = self.main.ribbon.sl_size.value() / 1000.0

        if use_auto:
            r_width = 0.012
        else:
            r_width = r_size_val

        mask, path_points = self.anomaly_worker.generate_scratch_mask(
            points, self._scratch_points_list, width_ratio=r_width
        )

        self._current_scratch_path = path_points
        count = np.sum(mask)

        if count > 0:
            if self._defect_mask_accumulated is None:
                self._defect_mask_accumulated = np.zeros(len(points), dtype=bool)
            self._mask_history.append(self._defect_mask_accumulated.copy())
            self._defect_mask_accumulated |= mask
            self._update_preview()
            self._update_apply_button_state()
            self.main.log(f"Scratch generated with {len(self._scratch_points_list)} segments.")

        self._scratch_points_list = []
        self._overlay.hide()

    def _update_scratch_lines_overlay(self):
        if not self._scratch_points_list: return

        points_3d = np.array(self._scratch_points_list)
        screen_pts, _, valid = self._project_points_to_screen(points_3d)

        if screen_pts is None: return

        qpoints = []
        for i in range(len(screen_pts)):
            if valid[i]:
                qpoints.append(QPointF(screen_pts[i][0], screen_pts[i][1]).toPoint())

        self._overlay.resize(self.view3d.size())
        # [Fix] Enable dots only for scratch lines
        self._overlay.update_path(qpoints, show_points=True)
        self._overlay.show()

    def _process_two_point_click(self, pos: QPoint):
        rect = QRect(pos.x() - 1, pos.y() - 1, 2, 2)
        indices = self._pick_points_in_rect(rect)
        if len(indices) == 0: return

        path = self.main._current_path
        data = self._pcd_cache[path]
        points = data['xyz']
        clicked_point = points[indices[0]]

        if self._scratch_start_point is None:
            self._scratch_start_point = clicked_point
            if hasattr(self.view3d, "set_selection_points"):
                self.view3d.set_selection_points(clicked_point[np.newaxis, :])
            self.main.log("Start point set. Click End point.")
        else:
            start_pt = self._scratch_start_point
            end_pt = clicked_point
            self._scratch_start_point = None

            is_crack = '2d_fracture' in self._mode
            is_bend = '2d_bend' in self._mode

            self._current_fracture_ends = (start_pt, end_pt)
            if self._defect_mask_accumulated is None:
                self._defect_mask_accumulated = np.zeros(len(points), dtype=bool)
            ends = np.vstack([start_pt, end_pt])
            if hasattr(self.view3d, "set_selection_points"):
                self.view3d.set_selection_points(ends)
            if hasattr(self.main.ribbon, 'btn_apply'):
                self.main.ribbon.btn_apply.setEnabled(True)
            op_name = "Bend" if is_bend else "Crack"
            self.main.log(f"{op_name} Plane defined. Click Apply.")

    def _process_lasso_selection(self, screen_points):
        """
        Lasso with Loose Tolerance (6%) + Coarse Grid (20px)
        """
        path = self.main._current_path
        if not path: return
        data = self._pcd_cache[path]
        xyz = data['xyz']

        pts_screen, _, valid_z = self._project_points_to_screen(xyz)
        if pts_screen is None: return

        poly = QPolygonF()
        for p in screen_points: poly.append(QPointF(p))
        brect = poly.boundingRect()

        candidates_mask = (
                (pts_screen[:, 0] >= brect.left()) &
                (pts_screen[:, 0] <= brect.right()) &
                (pts_screen[:, 1] >= brect.top()) &
                (pts_screen[:, 1] <= brect.bottom()) &
                valid_z
        )
        candidate_indices = np.where(candidates_mask)[0]
        if len(candidate_indices) == 0: return

        in_poly_indices = []
        for idx in candidate_indices:
            pt = QPointF(pts_screen[idx, 0], pts_screen[idx, 1])
            if poly.containsPoint(pt, Qt.OddEvenFill):
                in_poly_indices.append(idx)

        if not in_poly_indices: return
        in_poly_indices = np.array(in_poly_indices)

        # 1. Physical Distance Filter
        cam_pos = self._get_camera_position()
        cand_xyz = xyz[in_poly_indices]
        diff = cand_xyz - cam_pos
        dist_to_cam = np.linalg.norm(diff, axis=1)

        visible_indices_local = self._filter_occluded_points_physical(
            pts_screen[in_poly_indices], dist_to_cam, tolerance_ratio=0.06, grid_size=20
        )

        final_selected_indices = in_poly_indices[visible_indices_local]

        new_mask_local = np.zeros(len(xyz), dtype=bool)
        new_mask_local[final_selected_indices] = True

        count = np.sum(new_mask_local)
        if count > 0:
            if self._defect_mask_accumulated is None:
                self._defect_mask_accumulated = np.zeros(len(xyz), dtype=bool)
            self._mask_history.append(self._defect_mask_accumulated.copy())
            self._defect_mask_accumulated |= new_mask_local
            self._update_preview()
            self._update_apply_button_state()
            self.main.log(f"Added {count} visible points.")

    def _filter_occluded_points_physical(self, screen_coords, dist_values, tolerance_ratio=0.06, grid_size=20):
        if len(dist_values) == 0: return []

        min_x, min_y = np.min(screen_coords, axis=0)
        local_x = screen_coords[:, 0] - min_x
        local_y = screen_coords[:, 1] - min_y

        grid_x = (local_x / grid_size).astype(int)
        grid_y = (local_y / grid_size).astype(int)

        width_steps = np.max(grid_x) + 1
        cell_keys = grid_y * width_steps + grid_x

        sort_order = np.lexsort((dist_values, cell_keys))
        sorted_keys = cell_keys[sort_order]
        sorted_dist = dist_values[sort_order]

        unique_keys, unique_start_indices = np.unique(sorted_keys, return_index=True)
        min_dist_values = sorted_dist[unique_start_indices]

        counts = np.diff(np.append(unique_start_indices, len(sorted_keys)))
        min_dist_expanded = np.repeat(min_dist_values, counts)

        dynamic_tolerance = min_dist_expanded * tolerance_ratio

        is_visible_sorted = sorted_dist <= (min_dist_expanded + dynamic_tolerance)
        visible_original_indices = sort_order[is_visible_sorted]

        return visible_original_indices

    def _project_points_to_screen(self, xyz):
        try:
            w_logical = self.view3d.width()
            h_logical = self.view3d.height()
            region = (0, 0, w_logical, h_logical)
            view_matrix = self.view3d.viewMatrix()
            try:
                proj_matrix = self.view3d.projectionMatrix()
            except TypeError:
                proj_matrix = self.view3d.projectionMatrix(region, region)

            mvp_qt = proj_matrix * view_matrix
            mvp = np.array(mvp_qt.data()).reshape(4, 4)
        except:
            return None, None, None

        pts4 = np.hstack([xyz, np.ones((xyz.shape[0], 1))])
        clip = pts4 @ mvp

        w = clip[:, 3:4]
        w[np.abs(w) < 1e-12] = 1.0

        ndc = clip[:, :3] / w

        screen_xy = np.zeros((len(xyz), 2))
        screen_xy[:, 0] = (ndc[:, 0] * 0.5 + 0.5) * w_logical
        screen_xy[:, 1] = (1.0 - (ndc[:, 1] * 0.5 + 0.5)) * h_logical

        valid_z = (ndc[:, 2] >= -1.0) & (ndc[:, 2] <= 1.0)

        return screen_xy, ndc[:, 2], valid_z