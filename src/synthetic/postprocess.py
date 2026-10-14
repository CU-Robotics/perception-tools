import numpy as np
import mrcal
import cv2
from pydantic import BaseModel
from pathlib import Path
from utilities.paths import SCRATCH_DIR, project_path
from synthetic.common import get_config


def main():
    config = get_config()
    intrinsics_core = np.load(config.run_file("blender_intrinsics_core.npy"))

    blender_model = mrcal.cameramodel(
        intrinsics=("LENSMODEL_PINHOLE", intrinsics_core),
        imagersize=(config.render.width_px, config.render.height_px),
    )

    models = {
        name: mrcal.cameramodel(str(project_path(path)))
        for name, path in config.cameras.root.items()
    }

    for camera_name, model in models.items():
        input_dir = config.run_path() / "renders" / camera_name
        assert input_dir.is_dir()

        output_dir = config.run_path() / "warped" / camera_name
        output_dir.mkdir(parents=True, exist_ok=True)

        warp_map = mrcal.image_transformation_map(
            blender_model, model, intrinsics_only=True
        )

        for path in sorted(input_dir.glob("*.png")):
            image = cv2.imread(str(path))
            warped = mrcal.transform_image(
                image, warp_map, borderMode=cv2.BORDER_CONSTANT
            )
            cv2.imwrite(str(output_dir / path.name), warped)


if __name__ == "__main__":
    main()
