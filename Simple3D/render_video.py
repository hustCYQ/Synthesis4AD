import open3d as o3d
import numpy as np
import cv2
import argparse
def load_point_cloud_from_txt(txt_path):
    data = np.loadtxt(txt_path)
    points = data[:, :3]
    colors = data[:, 3:] / 255.0
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    return pcd

def render_dual_view_video(pcd1, pcd2, output_video='dual_view.mp4', rotation_axis='y', n_frames=180, width=480, height=480):
    def setup_visualizer(pcd):
        vis = o3d.visualization.Visualizer()
        vis.create_window(width=width, height=height, visible=False)
        vis.add_geometry(pcd)
        opt = vis.get_render_option()
        opt.background_color = np.array([1, 1, 1])
        opt.point_size = 2.0
        return vis

    vis1 = setup_visualizer(pcd1)
    vis2 = setup_visualizer(pcd2)

    ctr1 = vis1.get_view_control()
    ctr2 = vis2.get_view_control()
    cam1 = ctr1.convert_to_pinhole_camera_parameters()
    cam2 = ctr2.convert_to_pinhole_camera_parameters()

    frames = []

    for i in range(n_frames):
        angle = (2 * np.pi / n_frames) * i

        if rotation_axis == 'y':
            R = np.array([
                [np.cos(angle), 0, np.sin(angle)],
                [0, 1, 0],
                [-np.sin(angle), 0, np.cos(angle)]
            ])
        elif rotation_axis == 'x':
            R = np.array([
                [1, 0, 0],
                [0, np.cos(angle), -np.sin(angle)],
                [0, np.sin(angle), np.cos(angle)]
            ])
        elif rotation_axis == 'z':
            R = np.array([
                [np.cos(angle), -np.sin(angle), 0],
                [np.sin(angle), np.cos(angle), 0],
                [0, 0, 1]
            ])
        else:
            raise ValueError("Invalid rotation axis")

        for cam, ctr in [(cam1, ctr1), (cam2, ctr2)]:
            extrinsic = np.asarray(cam.extrinsic).copy()
            extrinsic[:3, :3] = R
            cam.extrinsic = extrinsic
            ctr.convert_from_pinhole_camera_parameters(cam)

        vis1.poll_events()
        vis1.update_renderer()
        vis2.poll_events()
        vis2.update_renderer()

        img1 = vis1.capture_screen_float_buffer(False)
        img2 = vis2.capture_screen_float_buffer(False)

        img1 = (255 * np.asarray(img1)).astype(np.uint8)
        img2 = (255 * np.asarray(img2)).astype(np.uint8)

        combined = np.hstack([img1, img2])
        frames.append(combined)

    vis1.destroy_window()
    vis2.destroy_window()

    h, w, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(output_video, fourcc, 30, (w, h))
    for frame in frames:
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    out.release()
    print(f"save to {output_video}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vis.')
    parser.add_argument('--AS_file', type=str, default='', help='expname')
    parser.add_argument('--GT_file', type=str, default='', help='expname')
    parser.add_argument('--save_path', type=str, default='comparison.mps', help='File_Name')
   
    args = parser.parse_args()
    print(args)
    pcd1 = load_point_cloud_from_txt(args.AS_file)
    pcd2 = load_point_cloud_from_txt(args.GT_file)

    render_dual_view_video(pcd1, pcd2, output_video=args.save_path)


