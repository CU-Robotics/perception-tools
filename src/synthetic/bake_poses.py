import mrcal
import json
import numpy as np
from scipy.spatial.transform import Rotation
from synthetic.common import Manifest, InlinePose, get_config
from utilities.paths import project_path

# front-facing rotation for plate
R_FRONT = np.diag([1, -1, -1])


def resolve_pose(pose: InlinePose) -> np.ndarray:
    """resolve inline pose to T_ref_obj"""
    e = pose.rotation

    R_delta = Rotation.from_euler(
        "YXZ",
        [e.yaw_deg, e.pitch_deg, e.roll_deg],
        degrees=True,
    ).as_matrix()

    T = np.eye(4)
    T[:3, :3] = R_FRONT @ R_delta
    T[:3, 3] = pose.translation_m

    return T


def extrinsics_matrix(model: mrcal.cameramodel, units_to_m=1.0) -> np.ndarray:
    Rt = model.Rt_cam_ref()

    T = np.eye(4)
    T[:3, :3] = Rt[:3, :]
    T[:3, 3] = Rt[3, :] * units_to_m

    return T


def bake_poses(config: Manifest, calibration_units_to_m=1.0):
    """return object-to-camera transforms with shape (N, C, 4, 4)"""

    camera_names = sorted(config.cameras.root.keys())

    # (C, 4, 4): ref camera -> each camera
    T_cam_ref = np.stack(
        [
            extrinsics_matrix(
                mrcal.cameramodel(str(project_path(config.cameras.root[name]))),
                units_to_m=calibration_units_to_m,
            )
            for name in camera_names
        ]
    )

    # (N, 4, 4): object -> calibration ref
    T_ref_obj = np.stack([resolve_pose(pose) for pose in config.poses.items])

    # (N, C, 4, 4): object -> camera
    poses = T_cam_ref[None] @ T_ref_obj[:, None]

    # bake
    return camera_names, poses


def fit_blender_focal(config: Manifest, sample_density=100, margin=0.95):
    models = [
        mrcal.cameramodel(str(project_path(path)))
        for path in config.cameras.root.values()
    ]
    max_xy = np.zeros(2)

    for model in models:
        w, h = model.imagersize()

        # sample calibration
        x, y = np.meshgrid(
            np.linspace(0, w - 1, sample_density), np.linspace(0, h - 1, sample_density)
        )
        q = np.stack((x, y), axis=-1)

        rays = mrcal.unproject(q, *model.intrinsics())
        if not np.isfinite(rays).all() or np.any(rays[..., 2] <= 0):
            raise ValueError("FOV cannot be represented by a single pinhole camera")

        xy = rays[..., :2] / rays[..., 2:3]
        max_xy = np.maximum(max_xy, np.max(np.abs(xy), axis=(0, 1)))

    # largest focal length covers every sampled direction
    width = config.render.width_px
    height = config.render.height_px
    focal_len = margin * min((width / 2 - 2) / max_xy[0], (height / 2 - 2) / max_xy[1])

    return focal_len


def main():
    config = get_config()
    config.ensure_run_exists()

    camera_names, poses = bake_poses(config)
    focal_len = fit_blender_focal(config)

    np.save(config.run_file("baked_poses.npy"), poses)
    config.run_file("bakery.json").write_text(
        json.dumps(
            dict(
                camera_names=camera_names,
                focal_len=focal_len,
                poses="baked_poses.npy",
            )
        )
    )


if __name__ == "__main__":
    main()
