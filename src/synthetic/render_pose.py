import bpy
import json
import sys
import math
import argparse
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utilities.paths import SCRATCH_DIR, project_path

"""
opencv/mrcal (right-handed system):
    X right
    Y down
    Z forward  
blender (right-handed system):
    X right
    Y up
    Z backward
"""
CV_TO_BLENDER = Matrix.Diagonal((1, -1, -1, 1))


def set_camera_pose(
    camera: bpy.types.Object, object_frame: bpy.types.Object, T_cam_obj: Matrix
):
    camera.matrix_world = (
        object_frame.matrix_world @ T_cam_obj.inverted() @ CV_TO_BLENDER
    )


def set_render_properties(config: dict, bakery: dict):
    scene = bpy.context.scene
    camera = scene.camera

    # set resolution
    width = config["render"]["width_px"]
    height = config["render"]["height_px"]
    focal_len = bakery["focal_len"]

    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1
    scene.render.pixel_aspect_y = 1

    # set intrinsics
    camera.data.type = "PERSP"
    camera.data.sensor_fit = "HORIZONTAL"
    camera.data.shift_x = 0
    camera.data.shift_y = 0

    """
    just solve the ratio to obtain the focal length in mm:
        f_mm / w_mm = f_px / w_px
    """
    camera.data.lens = focal_len * camera.data.sensor_width / width


def get_intrinsics_core():
    scene = bpy.context.scene
    camera = scene.camera

    scale = scene.render.resolution_percentage / 100
    width = scene.render.resolution_x * scale
    height = scene.render.resolution_y * scale
    f = camera.data.lens * width / camera.data.sensor_width

    return np.array([f, f, width / 2, height / 2])


def main():
    # get config
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=lambda path: Path(path))

    argv = sys.argv[sys.argv.index("--") + 1 :]
    args = parser.parse_args(argv)

    assert args.config.is_file(), "config file must exist"
    config = json.loads(args.config.read_bytes())

    run_name = config["name"]
    run_dir = project_path(SCRATCH_DIR / "synthetic" / run_name)
    assert run_dir.is_dir()
    bakery = json.loads((run_dir / "bakery.json").read_bytes())

    # configure camera
    scene = bpy.context.scene
    camera = bpy.data.objects["robot_camera"]
    scene.camera = camera

    set_render_properties(config, bakery)
    np.save(run_dir / "blender_intrinsics_core.npy", get_intrinsics_core())

    # rendering
    scene.render.image_settings.file_format = "PNG"
    object_frame = bpy.data.objects["object_frame"]
    camera_names = bakery["camera_names"]
    poses = np.load(run_dir / bakery["poses"], allow_pickle=False)
    assert poses.ndim == 4
    assert poses.shape[1:] == (len(camera_names), 4, 4)

    for j, camera_name in enumerate(camera_names):
        output_dir = run_dir / "renders" / camera_name
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, T_cam_obj in enumerate(poses[:, j]):
            set_camera_pose(camera, object_frame, Matrix(T_cam_obj))
            scene.render.filepath = str(output_dir / f"{i:06d}.png")
            bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
