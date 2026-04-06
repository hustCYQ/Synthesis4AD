# -*- coding: utf-8 -*-
"""
mpas.py
Core Anomaly Generation Logic.
Updates:
- Random Mode: Integrated advanced "Delaunay/Alpha Shape" logic for irregular masks.
  (Replaces simple geometric ellipsoid with organic, irregular patches).
- Parameters: Random ellipsoid ratios are randomized internally (hardcoded ranges).
"""

import numpy as np
import math
import open3d as o3d
from scipy.spatial import cKDTree, Delaunay, QhullError
from sklearn.decomposition import PCA
from sklearn.neighbors import KDTree


class AnomalyGenerator:
    def __init__(self):
        pass

    def get_bbox_diagonal(self, points):
        if len(points) == 0: return 1.0
        return np.linalg.norm(np.max(points, axis=0) - np.min(points, axis=0))

    def _estimate_local_normals(self, points, subset_indices):
        target_points = points[subset_indices]
        if len(target_points) < 3: return np.array([0, 0, 1])
        centroid = np.mean(target_points, axis=0)
        centered = target_points - centroid
        cov = np.cov(centered.T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        normal = eigvecs[:, 0]
        if normal[2] < 0: normal = -normal
        return normal

    def _rodrigues_mat(self, axis, angle_rad):
        axis = axis / np.linalg.norm(axis)
        a = math.cos(angle_rad / 2.0)
        b, c, d = -axis * math.sin(angle_rad / 2.0)
        aa, bb, cc, dd = a * a, b * b, c * c, d * d
        bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
        return np.array([[aa + bb - cc - dd, 2 * (bc - ad), 2 * (bd + ac)],
                         [2 * (bc + ad), aa + cc - bb - dd, 2 * (cd - ab)],
                         [2 * (bd - ac), 2 * (cd + ab), aa + dd - bb - cc]])

    # -------------------------------------------------------------------------
    #  1. 1D Point / Sphere Mask
    # -------------------------------------------------------------------------
    def generate_sphere_mask(self, points, center_point, radius_ratio=0.05):
        bbox_diag = self.get_bbox_diagonal(points)
        radius = bbox_diag * radius_ratio
        diff = points - center_point
        dist_sq = np.sum(diff ** 2, axis=1)
        mask = dist_sq < (radius ** 2)
        return mask

    # -------------------------------------------------------------------------
    #  2. [ADVANCED] Random Irregular Mask (Delaunay Based)
    # -------------------------------------------------------------------------
    def generate_ellipsoid_mask_from_click(self, points, center_point, cam_pos, base_scale=0.05):
        """
        Generates an irregular, organic patch around the clicked point.
        Logic ported from user reference:
        1. Define random ellipsoid bounds.
        2. Select random hull points within bounds.
        3. Delaunay triangulation -> Extract surface triangles.
        4. Project points onto surface triangles to determine mask.
        """
        bbox_diag = self.get_bbox_diagonal(points)

        # --- 1. Randomize Ellipsoid Axis Ratios (Hardcoded Ranges) ---
        # base_scale comes from UI Size slider (e.g. 0.05)
        # We vary aspect ratios to make it irregular
        r_a = base_scale * np.random.uniform(0.8, 1.5)
        r_b = base_scale * np.random.uniform(0.8, 1.5)
        r_c = base_scale * np.random.uniform(0.5, 1.0)  # Flatter depth

        a = bbox_diag * r_a
        b = bbox_diag * r_b
        c = bbox_diag * r_c

        # --- 2. Initial Ellipsoid Filter + Backface Culling ---
        diff = points - center_point
        term_x = (diff[:, 0] / a) ** 2
        term_y = (diff[:, 1] / b) ** 2
        term_z = (diff[:, 2] / c) ** 2

        initial_mask = (term_x + term_y + term_z) < 1.0

        # Physical Distance Check (Prevent punch-through)
        dist_to_cam = np.linalg.norm(points - cam_pos, axis=1)
        center_dist = np.linalg.norm(center_point - cam_pos)
        depth_tolerance = max(a, b, c) * 1.5
        front_face_mask = dist_to_cam < (center_dist + depth_tolerance)

        # Combine
        initial_mask = initial_mask & front_face_mask
        initial_indices = np.where(initial_mask)[0]
        num_initial = len(initial_indices)

        # If too few points, just return geometric ellipsoid
        if num_initial < 10:
            return initial_mask

        # --- 3. Hull Points Selection ---
        num_hull_points = 15  # Controls complexity of the shape
        num_choose = min(num_hull_points, num_initial)
        hull_indices = np.random.choice(initial_indices, num_choose, replace=False)
        hull_points = points[hull_indices]

        # --- 4. Delaunay Triangulation & Surface Extraction ---
        try:
            tri = Delaunay(hull_points)

            # Estimate Surface Normal (using PCA of hull points)
            hull_centered = hull_points - np.mean(hull_points, axis=0)
            cov_matrix = np.cov(hull_centered.T)
            eigvals, eigenvecs = np.linalg.eigh(cov_matrix)
            # Smallest eigenvector is normal
            surface_normal = eigenvecs[:, 0]
            # Orient towards camera (simple approximation)
            view_dir = (cam_pos - center_point)
            if np.dot(surface_normal, view_dir) < 0:
                surface_normal = -surface_normal
            surface_normal /= np.linalg.norm(surface_normal)

            # Auto Alpha
            # Average distance between hull points
            # Just take a subsample for speed
            sample_diff = hull_points[:5] - np.mean(hull_points, axis=0)
            avg_dist = np.mean(np.linalg.norm(sample_diff, axis=1)) * 2.0
            alpha = avg_dist * 1.5

            surface_triangles = set()

            for tetra in tri.simplices:
                # 4 faces of tetrahedron
                faces = [
                    (tetra[0], tetra[1], tetra[2]), (tetra[0], tetra[1], tetra[3]),
                    (tetra[0], tetra[2], tetra[3]), (tetra[1], tetra[2], tetra[3])
                ]
                for face in faces:
                    p0 = hull_points[face[0]]
                    p1 = hull_points[face[1]]
                    p2 = hull_points[face[2]]

                    # Face Normal
                    fn = np.cross(p1 - p0, p2 - p0)
                    norm_fn = np.linalg.norm(fn)
                    if norm_fn < 1e-12: continue
                    fn /= norm_fn

                    # Angle Check (must face similar direction to surface normal)
                    # cos(30 deg) ~ 0.866
                    if np.dot(surface_normal, fn) < 0.5: continue

                    # Edge Length Check (Alpha Shape)
                    e1 = np.linalg.norm(p1 - p0)
                    e2 = np.linalg.norm(p2 - p1)
                    e3 = np.linalg.norm(p0 - p2)
                    if e1 > 2 * alpha or e2 > 2 * alpha or e3 > 2 * alpha: continue

                    surface_triangles.add(tuple(sorted(face)))

            alpha_edges = [list(f) for f in surface_triangles]

            if not alpha_edges:
                return initial_mask

        except (QhullError, Exception):
            return initial_mask

        # --- 5. Final Mask Generation (Projection Check) ---
        final_mask = np.zeros(len(points), dtype=bool)

        # Only check points in initial ellipsoid
        target_points = points[initial_indices]

        # Optimize: Batch processing is hard here due to triangle loop
        # We iterate points and check against any triangle
        # For speed, we can skip complex barycentric if we trust the hull

        # Simplified Check for Performance:
        # If point is close to ANY hull triangle plane AND projection is inside

        for i, p_idx in enumerate(initial_indices):
            p = target_points[i]
            is_inside = False

            for tri_face in alpha_edges:
                a = hull_points[tri_face[0]]
                b = hull_points[tri_face[1]]
                c = hull_points[tri_face[2]]

                v0 = c - a
                v1 = b - a
                v2 = p - a

                # Dist to plane
                plane_n = np.cross(v0, v1)
                norm_pn = np.linalg.norm(plane_n)
                if norm_pn < 1e-12: continue

                dist = np.abs(np.dot(plane_n, v2)) / norm_pn

                # Must be close to surface
                if dist > alpha * 0.8: continue

                # Barycentric / Projection check
                dot00 = np.dot(v0, v0)
                dot01 = np.dot(v0, v1)
                dot02 = np.dot(v0, v2)
                dot11 = np.dot(v1, v1)
                dot12 = np.dot(v1, v2)
                denom = dot00 * dot11 - dot01 * dot01
                if denom < 1e-12: continue

                u = (dot11 * dot02 - dot01 * dot12) / denom
                v = (dot00 * dot12 - dot01 * dot02) / denom

                # Relaxed barycentric bounds for organic shape
                if (u >= -0.2 and v >= -0.2 and u + v <= 1.2):
                    is_inside = True
                    break

            if is_inside:
                final_mask[p_idx] = True

        return final_mask

    # -------------------------------------------------------------------------
    #  3. Scratch Generation
    # -------------------------------------------------------------------------
    def generate_scratch_mask(self, points, control_points, width_ratio=0.01):
        if len(control_points) < 2:
            return np.zeros(len(points), dtype=bool), None

        bbox_diag = self.get_bbox_diagonal(points)
        line_width = bbox_diag * width_ratio

        all_path_points = []
        for i in range(len(control_points) - 1):
            start = control_points[i]
            end = control_points[i + 1]
            dist = np.linalg.norm(end - start)
            num_steps = max(10, int(dist / (bbox_diag * 0.005)))
            t = np.linspace(0, 1, num_steps)
            segment_points = start + np.outer(t, (end - start))
            all_path_points.append(segment_points)

        linear_path = np.vstack(all_path_points)
        pcd_tree = cKDTree(points)
        dists, indices = pcd_tree.query(linear_path, k=1)
        path_points = points[indices]

        path_tree = cKDTree(path_points)
        point_dists, _ = path_tree.query(points, k=1)
        mask = point_dists < line_width
        return mask, path_points

    def apply_scratch_deformation(self, points, mask, path_points, stretch_scale=0.005, convex=False):
        if np.sum(mask) == 0: return points
        bbox_diag = self.get_bbox_diagonal(points)
        direction_sign = 1 if convex else -1
        avg_normal = self._estimate_local_normals(points, np.where(mask)[0])
        displacement_vector = -avg_normal * direction_sign * stretch_scale * bbox_diag

        if np.linalg.norm(displacement_vector) < 1e-9: return points

        stretched = points.copy()
        mask_points = points[mask]
        path_tree = cKDTree(path_points)
        dists, _ = path_tree.query(mask_points, k=1)
        max_dist = np.max(dists)

        if max_dist < 1e-9:
            stretched[mask] += displacement_vector
            return stretched

        normalized_dists = dists / max_dist
        weights = 0.5 * (1 + np.cos(np.pi * normalized_dists))
        displacement = displacement_vector * weights[:, np.newaxis]
        stretched[mask] += displacement
        return stretched

    # -------------------------------------------------------------------------
    #  4. Deformation Application
    # -------------------------------------------------------------------------
    def apply_gradient_deformation(self, points, final_mask, stretch_scale=0.02, convex=True):
        if np.sum(final_mask) < 5: return points
        bbox_diag = self.get_bbox_diagonal(points)
        avg_normal = self._estimate_local_normals(points, np.where(final_mask)[0])
        direction_sign = 1 if convex else -1
        max_displacement = -avg_normal * direction_sign * stretch_scale * bbox_diag

        stretched = points.copy()
        mask_points = points[final_mask]
        non_mask_points = points[~final_mask]

        if len(non_mask_points) == 0:
            stretched[final_mask] += max_displacement
            return stretched

        non_mask_tree = cKDTree(non_mask_points)
        dists, _ = non_mask_tree.query(mask_points, k=1)
        max_dist = np.max(dists)
        if max_dist < 1e-6: return points

        normalized_dists = dists / max_dist
        weights = 0.5 * (1 - np.cos(np.pi * normalized_dists))
        displacement = max_displacement * weights[:, np.newaxis]
        stretched[final_mask] += displacement
        return stretched

    def apply_lasso_custom(self, points, mask, stretch_mode='noise',
                           strength=0.02, frequency=1.0,
                           custom_formula="cos(3*r)",
                           convex=True):
        bbox_diag = self.get_bbox_diagonal(points)

        avg_normal = self._estimate_local_normals(points, np.where(mask)[0])
        direction_sign = 1 if convex else -1
        direction = -avg_normal * direction_sign

        return self._advanced_stretch_core(
            points, mask, direction, bbox_diag,
            stretch_mode=stretch_mode,
            surface_scale=strength,
            wave_density=frequency * 10.0,
            custom_formula=custom_formula,
            filter_k=5,
            filter_strength=0.7
        )

    def _advanced_stretch_core(self, points, mask, direction, bbox_diag,
                               stretch_mode='noise',
                               surface_scale=0.02,
                               wave_density=2.0,
                               custom_formula="",
                               filter_k=5,
                               filter_strength=0.7):

        stretched = points.copy()
        mask_indices = np.where(mask)[0]
        mask_points = points[mask_indices]
        num_mask_points = len(mask_points)

        if num_mask_points == 0: return stretched, mask

        neighbor_radius = bbox_diag * 0.01
        real_scale = surface_scale * bbox_diag

        # --- A. NOISE MODE ---
        if stretch_mode == 'noise':
            noise_level = wave_density * 0.05
            base_disp = direction * real_scale * 0.5
            disp_mag = np.linalg.norm(base_disp)
            noise_std = disp_mag * noise_level
            gaussian_noise = np.random.normal(loc=0.0, scale=noise_std, size=(num_mask_points, 3))
            final_displacement = base_disp + gaussian_noise

        # --- B. SURFACE FIT MODE ---
        elif stretch_mode == 'surface_fit':
            pca_global = PCA(n_components=3)
            pca_global.fit(mask_points)
            normal_z = pca_global.components_[2]
            normal_z /= np.linalg.norm(normal_z)

            centroid = np.mean(mask_points, axis=0)
            centered = mask_points - centroid
            axis_x = pca_global.components_[0]
            axis_y = pca_global.components_[1]
            coord_x = np.dot(centered, axis_x)
            coord_y = np.dot(centered, axis_y)

            max_r = np.max(np.sqrt(coord_x ** 2 + coord_y ** 2)) + 1e-8
            scale_factor = wave_density * np.pi

            norm_x = (coord_x / max_r) * scale_factor
            norm_y = (coord_y / max_r) * scale_factor

            r = np.sqrt(norm_x ** 2 + norm_y ** 2)
            theta = np.arctan2(norm_y, norm_x)

            try:
                safe_dict = {
                    "sin": np.sin, "cos": np.cos, "tan": np.tan,
                    "arcsin": np.arcsin, "arccos": np.arccos, "arctan": np.arctan, "arctan2": np.arctan2,
                    "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
                    "exp": np.exp, "log": np.log, "log10": np.log10, "sqrt": np.sqrt,
                    "abs": np.abs, "absolute": np.absolute,
                    "power": np.power, "square": np.square,
                    "clip": np.clip, "min": np.minimum, "max": np.maximum,
                    "sign": np.sign, "round": np.round, "floor": np.floor, "ceil": np.ceil,
                    "pi": np.pi, "e": np.e,
                    "np": np,
                    "r": r, "theta": theta
                }
                if not custom_formula or len(custom_formula) < 1:
                    custom_formula = "cos(3*r)"
                z_fit = eval(custom_formula, {"__builtins__": None}, safe_dict)
                if isinstance(z_fit, (int, float)):
                    z_fit = np.full_like(r, z_fit)
            except Exception as e:
                print(f"Formula Error: {e}. Using Default.")
                z_fit = np.cos(3 * r)

            r_01 = np.sqrt(coord_x ** 2 + coord_y ** 2) / max_r
            decay = np.power(np.maximum(0, 1.0 - np.square(r_01)), 3.0)
            z_fit = z_fit * decay

            z_max_val = np.max(np.abs(z_fit)) + 1e-8
            z_final = (z_fit / z_max_val) * (real_scale * 0.6)

            mask_kdtree = KDTree(mask_points)
            mask_normals = np.zeros_like(mask_points)
            indices_list = mask_kdtree.query_radius(mask_points, r=neighbor_radius)
            for i, neighbors in enumerate(indices_list):
                if len(neighbors) < 3:
                    mask_normals[i] = normal_z
                else:
                    nbs = mask_points[neighbors]
                    cov = np.cov((nbs - np.mean(nbs, axis=0)).T)
                    _, evecs = np.linalg.eigh(cov)
                    n = evecs[:, 0]
                    if np.dot(n, normal_z) < 0: n = -n
                    mask_normals[i] = n

            final_displacement = mask_normals * z_final.reshape(-1, 1)

        else:
            return stretched, mask

        # --- APPLY DISPLACEMENT ---
        stretched[mask_indices] += final_displacement

        # --- FILTERING ---
        if stretch_mode == 'surface_fit' and filter_strength > 0:
            mask_point_indices = mask_indices
            mask_points_to_filter = stretched[mask_point_indices]

            filter_tree = KDTree(mask_points_to_filter)
            dists, idxs = filter_tree.query(mask_points_to_filter, k=filter_k)

            filtered_mask_points = np.zeros_like(mask_points_to_filter)

            for i in range(len(mask_points_to_filter)):
                neighbor_dists = dists[i]
                neighbor_idx = idxs[i]
                neighbor_dists[neighbor_dists < 1e-8] = 1e-8
                weights = 1.0 / neighbor_dists
                weights /= np.sum(weights)
                weighted_avg = np.sum(mask_points_to_filter[neighbor_idx] * weights.reshape(-1, 1), axis=0)
                filtered_mask_points[i] = (1 - filter_strength) * mask_points_to_filter[
                    i] + filter_strength * weighted_avg

            stretched[mask_point_indices] = filtered_mask_points

        return stretched, mask

    def apply_fracture_plane_split(self, points, start_point, end_point, gap_width=0.01, depth_ratio=0.6):
        bbox_diag = self.get_bbox_diagonal(points)
        mid_point = (start_point + end_point) / 2.0
        vec_line = end_point - start_point
        len_line = np.linalg.norm(vec_line)
        if len_line < 1e-6: return points, np.zeros(len(points), dtype=bool)
        vec_line /= len_line

        pcd_tree = cKDTree(points)
        _, indices = pcd_tree.query(mid_point, k=50)
        local_normal = self._estimate_local_normals(points, indices)

        obj_centroid = np.mean(points, axis=0)
        if np.dot(local_normal, mid_point - obj_centroid) < 0:
            local_normal = -local_normal

        plane_normal = np.cross(vec_line, local_normal)
        if np.linalg.norm(plane_normal) < 1e-6:
            plane_normal = np.cross(vec_line, np.array([0, 0, 1]))
        plane_normal /= np.linalg.norm(plane_normal)

        vec_to_points = points - mid_point
        dist_to_plane = np.abs(np.dot(vec_to_points, plane_normal))
        thickness = bbox_diag * gap_width
        mask_gap = dist_to_plane < (thickness / 2.0)

        vec_centroid_to_points = points - obj_centroid
        vec_centroid_to_mid = mid_point - obj_centroid
        norm_c2p = np.linalg.norm(vec_centroid_to_points, axis=1)
        norm_c2m = np.linalg.norm(vec_centroid_to_mid)
        valid_norms = norm_c2p > 1e-6
        cos_angles = np.zeros(len(points))
        cos_angles[valid_norms] = np.dot(vec_centroid_to_points[valid_norms], vec_centroid_to_mid) / (
                norm_c2p[valid_norms] * norm_c2m)
        topology_mask = cos_angles > 0.15

        dist_to_mid = np.linalg.norm(points - mid_point, axis=1)
        radius_mask = dist_to_mid < (bbox_diag * depth_ratio)

        mask_to_delete = mask_gap & topology_mask & radius_mask
        num_deleted = np.sum(mask_to_delete)
        if num_deleted == 0:
            return points, np.zeros(len(points), dtype=bool)

        deleted_points = points[mask_to_delete]
        remaining_points = points[~mask_to_delete]

        if len(remaining_points) == 0:
            return points, np.zeros(len(points), dtype=bool)

        tree = cKDTree(remaining_points)
        dists, indices = tree.query(deleted_points, k=5)
        indices_flat = indices.flatten()
        unique_indices = np.unique(indices_flat)
        unique_indices = unique_indices[unique_indices < len(remaining_points)]
        final_mask = np.zeros(len(remaining_points), dtype=bool)
        final_mask[unique_indices] = True

        return remaining_points, final_mask

    def apply_bend_deformation(self, points, start_point, end_point,
                               bend_angle_deg=30.0, radius_ratio=0.05, target_count=None):
        if target_count is None: target_count = len(points)
        bbox_diag = self.get_bbox_diagonal(points)
        mid_point = (start_point + end_point) / 2.0
        vec_line = end_point - start_point
        len_line = np.linalg.norm(vec_line)
        if len_line < 1e-6: return points, np.zeros(len(points), dtype=bool)
        vec_line /= len_line

        pcd_tree = cKDTree(points)
        _, indices = pcd_tree.query(mid_point, k=50)
        local_normal = self._estimate_local_normals(points, indices)
        obj_centroid = np.mean(points, axis=0)
        if np.dot(local_normal, mid_point - obj_centroid) < 0:
            local_normal = -local_normal

        plane_normal = np.cross(vec_line, local_normal)
        if np.linalg.norm(plane_normal) < 1e-6:
            plane_normal = np.cross(vec_line, np.array([0, 0, 1]))
        plane_normal /= np.linalg.norm(plane_normal)

        vec_to_points = points - mid_point
        signed_dists = np.dot(vec_to_points, plane_normal)
        mask_moving = signed_dists > 0

        if np.sum(mask_moving) == 0 or np.sum(mask_moving) == len(points):
            return points, np.zeros(len(points), dtype=bool)

        angle_rad = math.radians(bend_angle_deg)
        rot_mat = self._rodrigues_mat(vec_line, angle_rad)
        pts_move = points[mask_moving]
        pts_rotated = np.dot(pts_move - mid_point, rot_mat.T) + mid_point
        temp_points = points.copy()
        temp_points[mask_moving] = pts_rotated

        # Bend Mode STILL USES Resampling
        final_points, _ = self._resample_via_mesh_and_map_mask(temp_points, np.empty((0, 3)), target_num=target_count)

        vec_ap = final_points - start_point
        proj = np.dot(vec_ap, vec_line)
        dist_sq = np.sum(vec_ap ** 2, axis=1) - proj ** 2
        dist_sq = np.maximum(dist_sq, 0)
        dists = np.sqrt(dist_sq)
        influence_radius = bbox_diag * radius_ratio
        final_mask = dists < influence_radius

        return final_points, final_mask

    def _resample_via_mesh_and_map_mask(self, points, mask_points, target_num):
        """Kept for Bend mode use"""
        try:
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points)
            pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.01, max_nn=30))
            pcd.orient_normals_consistent_tangent_plane(k=100)

            distances = pcd.compute_nearest_neighbor_distance()
            avg_dist = np.mean(distances) if len(distances) > 0 else 0.01
            radius = 1.5 * avg_dist
            mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
                pcd, o3d.utility.DoubleVector([radius, radius * 2])
            )
            mesh.remove_degenerate_triangles()

            if len(mesh.vertices) == 0 or len(mesh.triangles) == 0:
                print("Warning: Mesh reconstruction failed.")
                return points, mask_points

            sample_multiplier = 1.2
            dense_pcd = mesh.sample_points_uniformly(
                number_of_points=int(target_num * sample_multiplier)
            )
            raw_points = np.asarray(dense_pcd.points)

            if len(raw_points) == 0: return points, mask_points

            if len(raw_points) > target_num:
                final_points = raw_points[np.random.choice(len(raw_points), target_num, replace=False)]
            elif len(raw_points) < target_num:
                fill_num = target_num - len(raw_points)
                final_points = np.vstack([
                    raw_points,
                    raw_points[np.random.choice(len(raw_points), fill_num)]
                ])
            else:
                final_points = raw_points

            new_mask_points = np.empty((0, 3))

            if len(mask_points) > 0:
                ref_tree = KDTree(mask_points)
                mask_neighbor_dists = ref_tree.query(mask_points, k=5)[0][:, 1:]
                mask_avg_spacing = np.mean(mask_neighbor_dists) if mask_neighbor_dists.size > 0 else 1e-6

                dist_thresh = mask_avg_spacing * 2.0

                dists, _ = ref_tree.query(final_points, k=1)
                bool_mask = dists.squeeze() < dist_thresh
                new_mask_points = final_points[bool_mask]

                if len(new_mask_points) < 10 and len(mask_points) >= 10:
                    fill_num = min(50, len(mask_points))
                    new_mask_points = np.vstack([
                        new_mask_points,
                        mask_points[np.random.choice(len(mask_points), fill_num)]
                    ])

            return final_points, new_mask_points

        except Exception as e:
            print(f"Resample Error: {e}")
            return points, mask_points