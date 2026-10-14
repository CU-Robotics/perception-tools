import sys
import os
import cv2
import numpy as np
from typing import Callable
from contextlib import contextmanager

SILENCE_STDERR = True


# OpenCV and matplotlib like to dump garbage to stderr, silence it
@contextmanager
def silence_stderr():
    stderr = sys.stderr.fileno()
    devnull = os.open(os.devnull, os.O_WRONLY)

    stderr_copy = os.dup(stderr)

    if SILENCE_STDERR:
        os.dup2(devnull, stderr)

    try:
        yield
    finally:
        if SILENCE_STDERR:
            os.dup2(stderr_copy, stderr)

        os.close(stderr_copy)
        os.close(devnull)


class TextBox:
    def __init__(
        self,
        frame: np.ndarray,
        font: int = cv2.FONT_HERSHEY_PLAIN,
        scale: float = 1,
        thickness: int = 1,
        margin: int = 10,
        line_spacing: int = 8,
    ):
        self.frame = frame
        self.font = font
        self.scale = scale
        self.thickness = thickness
        self.margin = margin
        self.line_spacing = line_spacing
        self.cursor_x = margin
        self.cursor_y = margin

    def write(
        self, text: str, color: tuple[int, int, int] = (255, 255, 255), end: str = "\n"
    ):
        text += end

        for i, text in enumerate(text.split("\n")):
            (text_width, text_height), _ = cv2.getTextSize(
                text, self.font, self.scale, self.thickness + 2
            )

            # newline
            if i > 0:
                self.cursor_y += text_height + self.line_spacing
                self.cursor_x = self.margin

            if len(text) == 0:
                continue

            # draw text
            cv2.putText(
                self.frame,
                text,
                org=(self.cursor_x, self.cursor_y + text_height),
                fontFace=self.font,
                fontScale=self.scale,
                color=(0, 0, 0),
                thickness=self.thickness + int(2 * self.scale),
                lineType=cv2.LINE_AA,
            )
            cv2.putText(
                self.frame,
                text,
                org=(self.cursor_x, self.cursor_y + text_height),
                fontFace=self.font,
                fontScale=self.scale,
                color=color,
                thickness=self.thickness,
                lineType=cv2.LINE_AA,
            )

            self.cursor_x += text_width

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def gallery(
    name: str, detections: "CameraDetections", f: Callable[["Detection"], np.ndarray]
) -> set[tuple[str, str]]:
    flagged = set()

    items = [*detections.items()]
    i = 0

    while True:
        frame_id, det = items[i]
        image = f(det)

        with TextBox(image) as tb:
            is_flagged = (name, frame_id) in flagged

            label = f"{name}/{frame_id}"
            if is_flagged:
                label += " (flagged)"

            tb.write("keybinds: [j] prev [k] flag [l] next")
            tb.write(
                label,
                color=(0, 0, 255) if is_flagged else (0, 255, 255),
            )

        cv2.imshow(name, image)

        match cv2.waitKey(0):
            case k if k == ord("q"):
                # done viewing
                break
            case k if k == ord("k"):
                # flag (or unflag) selected detection
                if (name, frame_id) in flagged:
                    flagged.remove((name, frame_id))
                else:
                    flagged.add((name, frame_id))
            case k if k == ord("j"):
                # next detection
                i = (i - 1) % len(items)
            case k if k == ord("l"):
                # previous detection
                i = (i + 1) % len(items)

    cv2.destroyAllWindows()
    return flagged
