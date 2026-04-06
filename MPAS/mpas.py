# -*- coding: utf-8 -*-
"""
MPAS: Mesh Point cloud Anomaly Synthesis
3D point cloud anomaly synthesis library

Anomaly types:
- sphere: spherical anomaly
- scratch: scratch anomaly
- bend: bending anomaly
- crack: crack/break anomaly
- freedom: irregular anomaly
"""

import numpy as np
import math
import open3d as o3d
from scipy.spatial import cKDTree, Delaunay
from scipy.spatial.qhull import QhullError
from sklearn.decomposition import PCA
from sklearn.neighbors import KDTree
from scipy.sparse.csgraph import dijkstra
from scipy.sparse import lil_matrix
import trimesh
import os


# ==================== Utilities ====================

def get_bbox_diagonal(points):
    """Calculate bounding box diagonal length"""
    return np.linalg.norm(np.max(points, axis=0) - np.min(points, axis=0))


def normalize_points(points):
    """Normalize point cloud to origin"""
    center = np.mean(points, axis=0)
    normalized_points = points - center
    return normalized_points, center


def resample_with_sampling(points, mask_points, target_num=250000):
    """
    Mesh reconstruction + Efficient sampling pipeline:
    1. Point cloud -> Mesh reconstruction (BPA) -> Generate uniform points near target count
    2. Fine-tune point count to exact target
    3. Extract mask region coordinates
    """
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.01, max_nn=30))
    pcd.orient_normals_consistent_tangent_plane(100)

    distances = pcd.compute_nearest_neighbor_distance()
    avg_dist = np.mean(distances)
    radius = 1.5 * avg_dist
    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
        pcd, o3d.utility.DoubleVector([radius, radius * 2])
    )
    mesh.remove_degenerate_triangles()

    if len(mesh.vertices) == 0 or len(mesh.triangles) == 0:
        return points, mask_points

    sample_multiplier = 1.2
    dense_points = mesh.sample_points_uniformly(
        number_of_points=int(target_num * sample_multiplier)
    )
    raw_points = np.asarray(dense_points.points)

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
        mask_kdtree = KDTree(mask_points)
        mask_neighbor_dists = KDTree(mask_points).query(mask_points, k=5)[0][:, 1:]
        mask_avg_spacing = np.mean(mask_neighbor_dists) if mask_neighbor_dists.size > 0 else 1e-6
        dist_thresh = mask_avg_spacing * 2.0

        dists, _ = mask_kdtree.query(final_points, k=1)
        bool_mask = dists.squeeze() < dist_thresh
        new_mask_points = final_points[bool_mask]

        if len(new_mask_points) < 10 and len(mask_points) >= 10:
            fill_num = min(50, len(mask_points))
            new_mask_points = np.vstack([
                new_mask_points,
                mask_points[np.random.choice(len(mask_points), fill_num)]
            ])

    return final_points, new_mask_points


def build_knn_graph(points, k=20):
    """Build k-NN graph (sparse matrix representation)"""
    n = len(points)
    tree = cKDTree(points)
    graph = lil_matrix((n, n), dtype=np.float64)
    dists, idxs = tree.query(points, k=k + 1, workers=-1)
    for i in range(n):
        graph[i, idxs[i, 1:]] = dists[i, 1:]
    return graph.tocsr()


def rodrigues_mat(axis, angle):
    """Rodrigues rotation matrix"""
    axis = axis / np.linalg.norm(axis) if np.linalg.norm(axis) > 1e-8 else axis
    a = math.cos(angle / 2)
    b, c, d = -axis * math.sin(angle / 2)
    return np.array([
        [a**2 + b**2 - c**2 - d**2, 2*(b*c - a*d), 2*(b*d + a*c)],
        [2*(b*c + a*d), a**2 + c**2 - b**2 - d**2, 2*(c*d - a*b)],
        [2*(b*d - a*c), 2*(c*d + a*b), a**2 + d**2 - b**2 - c**2]
    ])


def _estimate_local_normals(points, subset_indices):
    """Estimate local normal direction"""
    target_points = points[subset_indices]
    if len(target_points) < 3:
        return np.array([0, 0, 1])
    centroid = np.mean(target_points, axis=0)
    centered = target_points - centroid
    cov = np.cov(centered.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    normal = eigvecs[:, 0]
    if normal[2] < 0:
        normal = -normal
    return normal


def calculate_original_density(points, mask):
    """Calculate original point cloud density (points per unit volume)"""
    bbox_min = np.min(points[mask], axis=0)
    bbox_max = np.max(points[mask], axis=0)
    volume = np.prod(bbox_max - bbox_min)
    return len(points[mask]) / volume if volume > 0 else 0


# ==================== Core Functions ====================

def sphere(points,
           radius_ratio=0.03,
           convex=True,
           stretch_scale=0.02,
           target_num=250000,
           normalize=True):
    """Generate spherical anomaly"""
    diagonal = get_bbox_diagonal(points)
    radius = diagonal * radius_ratio

    center_idx = np.random.choice(len(points))
    center_point = points[center_idx]

    distances = np.linalg.norm(points - center_point, axis=1)
    mask = distances < radius
    mask_points = points[mask].copy()

    if np.sum(mask) < 5:
        raise ValueError("Too few mask points, increase radius_ratio")

    avg_normal = _estimate_local_normals(points, np.where(mask)[0])
    direction_sign = 1 if convex else -1
    max_displacement = -avg_normal * direction_sign * stretch_scale * diagonal

    stretched = points.copy()
    mask_indices = np.where(mask)[0]
    mask_points_arr = points[mask_indices]

    center_of_mask = np.mean(mask_points_arr, axis=0)
    dists_to_center = np.linalg.norm(mask_points_arr - center_of_mask, axis=1)
    max_dist = np.max(dists_to_center)
    weights = 0.5 * (1 + np.cos(np.pi * dists_to_center / max_dist))

    for i, idx in enumerate(mask_indices):
        stretched[idx] += max_displacement * weights[i]

    new_points = stretched
    new_mask = mask_points

    if normalize:
        new_points, center = normalize_points(new_points)
        new_mask = new_mask - center if len(new_mask) > 0 else np.array([])
    else:
        center = None

    gt = np.zeros((len(new_points), 1), dtype=np.int32)
    if len(new_mask) > 0:
        kdtree = KDTree(new_points)
        dists, idxs = kdtree.query(new_mask, k=1)
        valid_mask = dists < 1e-4
        valid_idxs = np.array(idxs[valid_mask], dtype=np.int64).flatten()
        gt[valid_idxs] = 1

    return {
        'anomaly_points': new_points,
        'mask_points': new_mask,
        'gt': gt,
        'center': center
    }


def scratch(points,
            width_ratio=0.01,
            convex=True,
            stretch_scale=0.005,
            target_num=250000,
            normalize=True):
    """Generate scratch anomaly"""
    diagonal = get_bbox_diagonal(points)
    line_width = diagonal * width_ratio

    graph = build_knn_graph(points, k=20)
    start_idx = np.random.choice(len(points))
    end_idx = np.random.choice(len(points))

    try:
        shortest_path = dijkstra(csgraph=graph, directed=False, indices=start_idx)
        if np.isinf(shortest_path[end_idx]):
            raise ValueError("Path not found")
        path = [end_idx]
        current = end_idx
        while current != start_idx:
            neighbors = graph[current].nonzero()[1]
            prev_idx = neighbors[np.argmin(shortest_path[neighbors])]
            path.append(prev_idx)
            current = prev_idx
        path_points = points[np.array(path[::-1])]
    except:
        path_start = points[start_idx]
        path_end = points[end_idx]
        num_steps = 50
        t = np.linspace(0, 1, num_steps)
        path_points = path_start + np.outer(t, path_end - path_start)

    path_tree = cKDTree(path_points)
    dists, _ = path_tree.query(points)
    mask = dists < line_width
    mask_points = points[mask].copy()

    if np.sum(mask) < 5:
        raise ValueError("Too few mask points, increase width_ratio")

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=diagonal*0.01, max_nn=30))

    bbox = pcd.get_axis_aligned_bounding_box()
    center = bbox.get_center()
    pcd.orient_normals_towards_camera_location(center)

    normals = np.asarray(pcd.normals)
    mask_normals = normals[mask]
    avg_normal = np.mean(mask_normals, axis=0)
    avg_normal = avg_normal / np.linalg.norm(avg_normal)

    direction_sign = 1 if convex else -1
    direction = -avg_normal * direction_sign * stretch_scale * diagonal

    path_kdtree = cKDTree(path_points)
    mask_points_arr = points[mask]
    dists_to_path, _ = path_kdtree.query(mask_points_arr)
    max_dist = np.max(dists_to_path)
    normalized_dist = 1 - dists_to_path / max_dist if max_dist > 0 else np.zeros_like(dists_to_path)

    displacement_magnitude = np.linalg.norm(direction)
    stretch_factor = normalized_dist

    stretched = points.copy()
    stretch_amount = displacement_magnitude * stretch_factor[:, None]
    stretched[mask] += direction / displacement_magnitude * stretch_amount

    new_mask_points = stretched[mask].copy()

    if normalize:
        stretched, center = normalize_points(stretched)
        new_mask_points = new_mask_points - center if len(new_mask_points) > 0 else np.array([])
    else:
        center = None

    if len(stretched) > target_num:
        indices = np.random.choice(len(stretched), target_num, replace=False)
        stretched = stretched[indices]

    gt = np.zeros((len(stretched), 1), dtype=np.int32)
    if len(new_mask_points) > 0:
        kdtree = KDTree(stretched)
        dists, idxs = kdtree.query(new_mask_points, k=1)
        valid_mask = dists < 1e-4
        valid_idxs = np.array(idxs[valid_mask], dtype=np.int64).flatten()
        gt[valid_idxs] = 1

    return {
        'anomaly_points': stretched,
        'mask_points': new_mask_points,
        'gt': gt,
        'center': center
    }


def bend(points,
         rotate_angle=25,
         target_num=250000,
         normalize=True):
    """
    Generate bending anomaly

    Args:
        points: Input point cloud, shape=(N, 3)
        rotate_angle: Bending angle (degrees), default 25
        target_num: Target number of points, default 250000
        normalize: Whether to normalize, default True

    Returns:
        dict: {
            'anomaly_points': Deformed point cloud,
            'mask_points': Points in the anomaly region,
            'gt': GT labels (N,1), 1=anomaly,
            'center': Normalized center point (if normalize=True)
        }
    """
    pca = PCA(n_components=3)
    pca.fit(points)
    variances = pca.explained_variance_
    axes_order = np.argsort(variances)[::-1]
    long_axis_idx, width_axis_idx, thick_axis_idx = axes_order

    long_axis_vec = pca.components_[long_axis_idx]
    width_axis_vec = pca.components_[width_axis_idx]
    thick_axis_vec = pca.components_[thick_axis_idx]

    center = np.mean(points, axis=0)

    projections = np.dot(points - center, long_axis_vec)
    min_proj, max_proj = np.min(projections), np.max(projections)
    midline_start = center + min_proj * long_axis_vec
    midline_end = center + max_proj * long_axis_vec
    midpoint = (midline_start + midline_end) / 2

    rotation_axis = width_axis_vec

    points_relative = points - midpoint
    distances = np.dot(points_relative, long_axis_vec)
    rot_mask = distances > 0
    rotated_points = points[rot_mask].copy()
    fixed_points = points[~rot_mask].copy()

    long_proj = np.dot(points - center, long_axis_vec)
    width_proj = np.dot(points - center, width_axis_vec)
    thick_proj = np.dot(points - center, thick_axis_vec)
    thick_length = np.max(thick_proj) - np.min(thick_proj)
    search_radius = thick_length * 1.0

    original_mask_mask = np.abs(distances) <= search_radius
    original_mask = points[original_mask_mask].copy()

    angle_rad = math.radians(rotate_angle)
    rot_matrix = rodrigues_mat(rotation_axis, angle_rad)
    rotated_points = np.dot(rotated_points - midpoint, rot_matrix.T) + midpoint

    bent_points = np.vstack([fixed_points, rotated_points])

    bent_relative = bent_points - midpoint
    bent_distances = np.dot(bent_relative, long_axis_vec)
    bent_mask_mask = np.abs(bent_distances) <= search_radius
    mask_points = bent_points[bent_mask_mask].copy()

    new_points, new_mask = resample_with_sampling(bent_points, mask_points, target_num)

    if normalize:
        new_points, center_out = normalize_points(new_points)
        new_mask = new_mask - center_out if len(new_mask) > 0 else np.array([])
    else:
        center_out = None

    gt = np.zeros((len(new_points), 1), dtype=np.int32)
    if len(new_mask) > 0:
        kdtree = KDTree(new_points)
        dists, idxs = kdtree.query(new_mask, k=1)
        valid_mask = dists < 1e-4
        valid_idxs = np.array(idxs[valid_mask], dtype=np.int64).flatten()
        gt[valid_idxs] = 1

    return {
        'anomaly_points': new_points,
        'mask_points': new_mask,
        'gt': gt,
        'center': center_out
    }


def crack(points,
          gap_width=0.01,
          depth_ratio=0.6,
          target_num=250000,
          normalize=True):
    """
    Generate crack/fracture anomaly

    Args:
        points: Input point cloud, shape=(N, 3)
        gap_width: Gap width as ratio of bounding box diagonal, default 0.01
        depth_ratio: Crack depth as ratio of bounding box diagonal, default 0.6
        target_num: Target number of points, default 250000
        normalize: Whether to normalize, default True

    Returns:
        dict: {
            'anomaly_points': Deformed point cloud,
            'mask_points': Points in the anomaly region,
            'gt': GT labels (N,1), 1=anomaly,
            'center': Normalized center point (if normalize=True)
        }
    """
    bbox_diag = get_bbox_diagonal(points)

    start_idx = np.random.choice(len(points))
    end_idx = np.random.choice(len(points))
    start_point = points[start_idx]
    end_point = points[end_idx]

    mid_point = (start_point + end_point) / 2.0
    vec_line = end_point - start_point
    len_line = np.linalg.norm(vec_line)
    if len_line < 1e-6:
        return points, np.zeros(len(points), dtype=bool), np.zeros((len(points), 1), dtype=np.int32), None
    vec_line /= len_line

    pcd_tree = cKDTree(points)
    _, indices = pcd_tree.query(mid_point, k=50)
    local_normal = _estimate_local_normals(points, indices)

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

    if np.sum(mask_to_delete) == 0:
        raise ValueError("Failed to generate valid crack mask, please adjust parameters")

    delete_points = points[mask_to_delete].copy()

    remaining_points = points[~mask_to_delete]

    if len(remaining_points) < 100:
        raise ValueError("Too many points deleted, please reduce gap_width")

    tree = cKDTree(remaining_points)
    dists, indices = tree.query(delete_points, k=5)
    indices_flat = indices.flatten()
    unique_indices = np.unique(indices_flat)
    unique_indices = unique_indices[unique_indices < len(remaining_points)]

    final_mask = np.zeros(len(remaining_points), dtype=bool)
    final_mask[unique_indices] = True
    mask_points = remaining_points[final_mask].copy()

    if normalize:
        remaining_points, center = normalize_points(remaining_points)
        mask_points = mask_points - center if len(mask_points) > 0 else np.array([])
    else:
        center = None

    new_points = remaining_points
    if len(new_points) > target_num:
        indices = np.random.choice(len(new_points), target_num, replace=False)
        new_points = new_points[indices]

    gt = np.zeros((len(new_points), 1), dtype=np.int32)
    if len(mask_points) > 0:
        kdtree = KDTree(new_points)
        dists, idxs = kdtree.query(mask_points, k=1)
        valid_mask = dists < 1e-4
        valid_idxs = np.array(idxs[valid_mask], dtype=np.int64).flatten()
        gt[valid_idxs] = 1

    return {
        'anomaly_points': new_points,
        'mask_points': mask_points,
        'gt': gt,
        'center': center
    }


def freedom(points,
           ellipse_a_ratio=0.1,
           ellipse_b_ratio=0.1,
           ellipse_c_ratio=0.1,
           convex=True,
           stretch_mode='surface_fit',
           noise_strength=0.2,
           surface_scale=0.02,
           target_num=250000,
           normalize=True):
    """
    Generate irregular/random anomaly
    """
    diagonal = get_bbox_diagonal(points)

    center_idx = np.random.choice(len(points))
    center_point = points[center_idx]

    a = diagonal * ellipse_a_ratio
    b = diagonal * ellipse_b_ratio
    c = diagonal * ellipse_c_ratio

    diff = points - center_point
    term_x = (diff[:, 0] / a) ** 2
    term_y = (diff[:, 1] / b) ** 2
    term_z = (diff[:, 2] / c) ** 2
    initial_mask = (term_x + term_y + term_z) < 1.0
    initial_indices = np.where(initial_mask)[0]

    if len(initial_indices) < 10:
        raise ValueError("Too few points in ellipsoid, please increase ellipse ratios")

    num_hull_points = 10
    num_choose = min(num_hull_points, len(initial_indices))
    hull_indices = np.random.choice(initial_indices, num_choose, replace=False)
    hull_points = points[hull_indices]

    try:
        tri = Delaunay(hull_points)
        hull_centered = hull_points - np.mean(hull_points, axis=0)
        cov_matrix = np.cov(hull_centered.T)
        eigvals, eigenvecs = np.linalg.eigh(cov_matrix)
        surface_normal = eigenvecs[:, 0]
        if surface_normal[2] < 0:
            surface_normal = -surface_normal

        all_dists = []
        for i in range(len(hull_points)):
            for j in range(i + 1, len(hull_points)):
                all_dists.append(np.linalg.norm(hull_points[i] - hull_points[j]))
        avg_dist = np.mean(all_dists)
        alpha = avg_dist * 1.2

        surface_triangles = set()
        for tetra in tri.simplices:
            faces = [
                (tetra[0], tetra[1], tetra[2]), (tetra[0], tetra[1], tetra[3]),
                (tetra[0], tetra[2], tetra[3]), (tetra[1], tetra[2], tetra[3])
            ]
            for face in faces:
                p0 = hull_points[face[0]]
                p1 = hull_points[face[1]]
                p2 = hull_points[face[2]]

                fn = np.cross(p1 - p0, p2 - p0)
                norm_fn = np.linalg.norm(fn)
                if norm_fn < 1e-12: continue
                fn /= norm_fn

                if np.dot(surface_normal, fn) < 0.5: continue

                e1 = np.linalg.norm(p1 - p0)
                e2 = np.linalg.norm(p2 - p1)
                e3 = np.linalg.norm(p0 - p2)
                if e1 > 2 * alpha or e2 > 2 * alpha or e3 > 2 * alpha: continue

                surface_triangles.add(tuple(sorted(face)))

        alpha_edges = [list(f) for f in surface_triangles]

        if not alpha_edges:
            mask = initial_mask.copy()
        else:
            mask = np.zeros(len(points), dtype=bool)
            for tri_face in alpha_edges:
                a_pts, b_pts, c_pts = hull_points[tri_face[0]], hull_points[tri_face[1]], hull_points[tri_face[2]]
                v0 = c_pts - a_pts
                v1 = b_pts - a_pts
                plane_normal = np.cross(v0, v1)
                if np.linalg.norm(plane_normal) < 1e-8: continue
                plane_normal = plane_normal / np.linalg.norm(plane_normal)

                for point_idx in initial_indices:
                    p = points[point_idx]
                    v2 = p - a_pts
                    plane_dist = np.abs(np.dot(plane_normal, v2)) / np.linalg.norm(plane_normal)
                    if plane_dist > alpha * 0.5: continue

                    dot00 = np.dot(v0, v0)
                    dot01 = np.dot(v0, v1)
                    dot02 = np.dot(v0, v2)
                    dot11 = np.dot(v1, v1)
                    dot12 = np.dot(v1, v2)
                    denom = dot00 * dot11 - dot01 * dot01
                    if denom < 1e-8: continue

                    u = (dot11 * dot02 - dot01 * dot12) / denom
                    v = (dot00 * dot12 - dot01 * dot02) / denom
                    if u >= -0.2 and v >= -0.2 and u + v <= 1.2:
                        mask[point_idx] = True
    except (QhullError, Exception):
        mask = initial_mask.copy()

    if np.sum(mask) < 5:
        raise ValueError("Generated mask points are too few")

    avg_normal = _estimate_local_normals(points, np.where(mask)[0])
    direction_sign = 1 if convex else -1

    stretched = points.copy()
    mask_indices = np.where(mask)[0]
    mask_points_arr = points[mask_indices]
    num_mask_points = len(mask_points_arr)

    if stretch_mode == 'noise':
        base_direction = -avg_normal * direction_sign * surface_scale * diagonal * 0.8
        displacement_magnitude = np.linalg.norm(base_direction)
        noise_std = displacement_magnitude * noise_strength
        gaussian_noise = np.random.normal(loc=0.0, scale=noise_std, size=(num_mask_points, 3))
        final_displacement = base_direction + gaussian_noise
    elif stretch_mode == 'surface_fit':
        pca_2d = PCA(n_components=2)
        mask_centered = mask_points_arr - np.mean(mask_points_arr, axis=0)
        mask_2d = pca_2d.fit_transform(mask_centered)
        x, y = mask_2d[:, 0], mask_2d[:, 1]

        x_max_abs = np.max(np.abs(x)) + 1e-8
        y_max_abs = np.max(np.abs(y)) + 1e-8
        x_scaled = x / x_max_abs * 0.5 * np.pi
        y_scaled = y / y_max_abs * 0.5 * np.pi

        r = np.sqrt(x_scaled ** 2 + y_scaled ** 2)
        theta = np.arctan2(y_scaled, x_scaled)

        z_fit = np.cos(4.0 * r + 1.0 * theta) * np.exp(-0.6 * r ** 2)
        z_max = np.max(np.abs(z_fit)) + 1e-8
        z_final = (z_fit / z_max) * (surface_scale * diagonal)

        neighbor_radius = diagonal * 0.01
        mask_kdtree = KDTree(mask_points_arr)
        mask_normals_arr = np.zeros_like(mask_points_arr)

        for i in range(num_mask_points):
            neighbors = mask_kdtree.query_radius(mask_points_arr[i:i + 1], r=neighbor_radius)[0]
            if len(neighbors) < 3:
                mask_normals_arr[i] = avg_normal
            else:
                neighbor_points = mask_points_arr[neighbors]
                neighbor_centered = neighbor_points - np.mean(neighbor_points, axis=0)
                cov = np.cov(neighbor_centered.T)
                eigenvals, eigenvecs = np.linalg.eigh(cov)
                local_normal = eigenvecs[:, 0]
                if np.dot(local_normal, avg_normal) < 0:
                    local_normal = -local_normal
                mask_normals_arr[i] = local_normal

        final_displacement = -mask_normals_arr * z_final.reshape(-1, 1) * direction_sign
    else:
        raise ValueError(f"Unsupported stretch mode: {stretch_mode}")

    center_of_mask = np.mean(mask_points_arr, axis=0)
    dists_to_center = np.linalg.norm(mask_points_arr - center_of_mask, axis=1)
    max_dist = np.max(dists_to_center) + 1e-8
    weights = 0.5 * (1 + np.cos(np.pi * dists_to_center / max_dist))
    final_displacement = final_displacement * weights[:, np.newaxis]

    for i, idx in enumerate(mask_indices):
        stretched[idx] += final_displacement[i]

    if normalize:
        stretched, center = normalize_points(stretched)
        new_mask = stretched[mask_indices].copy() if len(mask_indices) > 0 else np.array([])
    else:
        center = None
        new_mask = stretched[mask_indices].copy()

    new_points = stretched
    if len(new_points) > target_num:
        indices = np.random.choice(len(new_points), target_num, replace=False)
        new_points = new_points[indices]

    gt = np.zeros((len(new_points), 1), dtype=np.int32)
    if len(new_mask) > 0:
        kdtree = KDTree(new_points)
        dists, idxs = kdtree.query(new_mask, k=1)
        valid_mask = dists < 1e-4
        valid_idxs = np.array(idxs[valid_mask], dtype=np.int64).flatten()
        gt[valid_idxs] = 1

    return {
        'anomaly_points': new_points,
        'mask_points': new_mask,
        'gt': gt,
        'center': center
    }


# ==================== Unified Interface ====================

def generate(points, defect_type, **kwargs):
    """
    Unified anomaly generation interface

    Args:
        points: Input point cloud, shape=(N, 3)
        defect_type: Anomaly type, options: 'sphere', 'scratch', 'bend', 'crack', 'freedom'
        **kwargs: Additional parameters passed to respective functions

    Returns:
        dict: Same as individual function returns
    """
    defect_type = defect_type.lower()

    if defect_type == 'sphere':
        return sphere(points, **kwargs)
    elif defect_type == 'scratch':
        return scratch(points, **kwargs)
    elif defect_type == 'bend':
        return bend(points, **kwargs)
    elif defect_type == 'crack':
        return crack(points, **kwargs)
    elif defect_type == 'freedom':
        return freedom(points, **kwargs)
    else:
        raise ValueError(f"Unsupported anomaly type: {defect_type}. Supported: sphere, scratch, bend, crack, freedom")


# ==================== File IO ====================

def load_data_as_pointcloud(path, num_points=250000):
    """Load point cloud data"""
    ext = os.path.splitext(path)[-1].lower()

    if ext in ['.stl', '.obj']:
        mesh = o3d.io.read_triangle_mesh(path)
        pcd = mesh.sample_points_uniformly(number_of_points=num_points)
        pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        return np.asarray(pcd.points)

    elif ext in ['.pcd', '.ply', '.asc', '.txt', '.xyz']:
        if ext in ['.pcd', '.ply']:
            pcd = o3d.io.read_point_cloud(path)
        else:
            data = np.loadtxt(path, comments='#')
            if data.shape[1] >= 3:
                pcd = o3d.geometry.PointCloud()
                pcd.points = o3d.utility.Vector3dVector(data[:, :3])
            else:
                raise ValueError("Data columns less than 3")

        current_num = len(pcd.points)
        if current_num > num_points:
            indices = np.random.choice(current_num, num_points, replace=False)
            pcd = pcd.select_by_index(indices)

        pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
        return np.asarray(pcd.points)

    else:
        raise ValueError(f"Unsupported file format: {ext}")


def save_pointcloud(points, path):
    """Save point cloud to file"""
    np.savetxt(path, points)


def save_gt(gt, path):
    """Save GT labels"""
    np.savetxt(path, gt, fmt='%d')


def save_mask(mask_points, path):
    """Save mask points"""
    if len(mask_points) > 0:
        np.savetxt(path, mask_points)