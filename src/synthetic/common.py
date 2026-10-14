import json
import argparse
from pathlib import Path
from typing import Literal
from pydantic import RootModel, BaseModel, Field
from utilities.paths import project_path


class Cameras(RootModel[dict[str, Path]]):
    pass


class RenderConfig(BaseModel):
    width_px: int = Field(gt=0)
    height_px: int = Field(gt=0)


class EulerRotation(BaseModel):
    type: Literal["euler"]
    yaw_deg: float
    pitch_deg: float
    roll_deg: float


class InlinePose(BaseModel):
    translation_m: tuple[float, float, float]
    rotation: EulerRotation


class InlinePoses(BaseModel):
    type: Literal["inline"]
    items: list[InlinePose]


class Manifest(BaseModel):
    name: str
    scene: Path
    cameras: Cameras
    render: RenderConfig
    poses: InlinePoses

    def run_path(self) -> Path:
        return project_path(Path(".scratch") / "synthetic" / self.name)

    def ensure_run_exists(self):
        self.run_path().mkdir(parents=True, exist_ok=True)

    def run_file(self, path: str | Path) -> Path:
        return self.run_path() / path


def get_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=lambda path: Path(path))

    args = parser.parse_args()

    assert args.config.is_file(), "config file must exist"
    config = Manifest.model_validate(json.loads(args.config.read_bytes()))

    return config
