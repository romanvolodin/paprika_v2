"""Sample media for the versions tests.

Videos are generated with the real `ffmpeg` (the same binary the app
uses), so tests that need them are skipped where it isn't installed.
"""

import io
from pathlib import Path
import shutil
import subprocess

from PIL import Image
import pytest


def make_png(size=(64, 48), mode="RGB") -> bytes:
    buffer = io.BytesIO()
    Image.new(mode, size, "red").save(buffer, format="PNG")
    return buffer.getvalue()


def make_jpeg(size=(64, 48)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, format="JPEG")
    return buffer.getvalue()


def _make_video(directory: Path, codec: str) -> bytes:
    """A 64x64, 10 fps, 9-frame mp4: 3 red, 3 green, then 3 blue frames."""
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        pytest.skip("ffmpeg/ffprobe are not installed")

    out = directory / f"{codec}.mp4"
    args = ["ffmpeg", "-v", "error", "-y"]
    for color in ("red", "green", "blue"):
        args += ["-f", "lavfi", "-i", f"color=c={color}:s=64x64:r=10:d=0.3"]
    args += [
        "-filter_complex",
        "[0][1][2]concat=n=3:v=1:a=0,format=yuv420p",
        "-c:v",
        codec,
        str(out),
    ]
    subprocess.run(args, check=True, capture_output=True)
    return out.read_bytes()


@pytest.fixture(scope="session")
def h264_video_bytes(tmp_path_factory) -> bytes:
    return _make_video(tmp_path_factory.mktemp("video"), "libx264")


@pytest.fixture(scope="session")
def mpeg4_video_bytes(tmp_path_factory) -> bytes:
    """An mp4 whose video codec is MPEG-4 part 2 - not accepted."""
    return _make_video(tmp_path_factory.mktemp("video"), "mpeg4")
