# perception-tools
Camera calibration and perception tools for CU-Robotics' hive repository. Most tools must be run inside the `calibration-tools` docker service. Use a combination of the compose YAMLs when starting up the service:
* `compose.x11.yaml`: Accommodate X11 displays (for `imshow` and other GUIs). Open a PR if you use wayland.
* `compose.nvidia.yaml`: Mount an NVIDIA GPU for hardware acceleration. NVIDIA Container Toolkit required.

## multi-camera calibration 
The collection process for calibration images is documented in hive under the `calibrate` Cargo feature. Calibration batches should be placed under the `hive-calib` volume. Hive's `pull_batch` tool does this automatically.
```
$ python3 -m calibration_tools.calibrate -h

usage: calibrate [-h] -t TARGET [-b BATCH] -f FOCAL_ESTIMATE [-d]

process hive calibration batch

options:
  -h, --help            show this help message and exit
  -t, --target TARGET   target name
  -b, --batch BATCH     calibration batch name
  -f, --focal-estimate FOCAL_ESTIMATE
                        focal length estimate
  -d, --debug           enable debug features
```
`TARGET` must name a YAML under `hive-calib` that completely specifies the geometry of your calibration target. Generally we should opt to use `strong_checkerboard`s. `FOCAL_ESTIMATE` specifies a preliminary estimate for the focal length in pixels and is required by the optimizer. You should use an existing calibration to seed this value.

All mrcal command-line tools are available within the container, including uncertainty and cross-validation utilities.

## synthetic dataset creation
You can generate training or evaluation images of armor plates with deterministic poses using blender (installed under `/opt/blender/blender`). The synthetic dataset generation tools use mrcal camera models directly and should provide representative images of your camera rig. Blender uses a pinhole camera so renders are first remapped using your desired projection model. **Generally a larger resolution than that of your physical camera is required to avoid excessive upsampling during this conversion**, though you can modify the render resolution depending on performance needs.
```
$ ./scripts/synthesize_dataset --config <path-to-config>
```
All manifests for synthetic datasets must comply with the specifications in `src/synthetic/common.py`. An example manifest is given under `configs/synthetic/default.json`. 
