"""Inspecting uploaded version files and generating their thumbnails.

Everything here works on a path on local disk and has no knowledge of
Django models or HTTP - the API layer decides what to do with the result.
Videos go through `ffprobe`/`ffmpeg` (must be installed - see the
backend `Dockerfile`), images through Pillow.

Problems with the *uploaded file itself* (corrupt, wrong codec, ...)
raise `MediaError` with a message that is safe to show to the user. A
missing `ffmpeg` binary is a server misconfiguration and deliberately
propagates as a normal exception instead.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import io
import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageOps, UnidentifiedImageError

from .models import Version


ALLOWED_EXTENSIONS = ("mp4", "jpg", "jpeg", "png")
ALLOWED_VIDEO_CODECS = ("h264",)

_PROBE_TIMEOUT_SECONDS = 60
_FRAME_EXTRACT_TIMEOUT_SECONDS = 120
_THUMB_JPEG_QUALITY = 85

_IMAGE_FORMAT_BY_EXTENSION = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG"}


class MediaError(Exception):
    """The uploaded file can't be accepted; the message is user-facing."""


@dataclass(frozen=True)
class MediaInfo:
    type: str
    width: int
    height: int
    # Video-only; None for images.
    duration: int | None = None  # frames
    fps: float | None = None
    codec: str = ""


@dataclass(frozen=True)
class ProcessedMedia:
    info: MediaInfo
    thumb: bytes  # JPEG


@contextmanager
def local_path(upload) -> Iterator[str]:
    """Yield a filesystem path with the contents of an uploaded file.

    Large uploads are already on disk (Django spools them to a temp
    file); small ones live in memory and get written out to one.
    """
    if hasattr(upload, "temporary_file_path"):
        yield upload.temporary_file_path()
        return

    suffix = Path(upload.name).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        for chunk in upload.chunks():
            tmp.write(chunk)
        tmp.flush()
        yield tmp.name


def process_upload(
    upload, extension: str, *, thumb_position: float, thumb_max_size: int
) -> ProcessedMedia:
    """Validate an uploaded file and build its thumbnail.

    `extension` is the lowercase extension without the dot and decides
    how the file is treated; the contents must actually match it.
    """
    with local_path(upload) as path:
        if extension in _IMAGE_FORMAT_BY_EXTENSION:
            return _process_image(path, extension, thumb_max_size)
        return _process_video(path, thumb_position, thumb_max_size)


# --- images -----------------------------------------------------------------


def _process_image(path: str, extension: str, thumb_max_size: int) -> ProcessedMedia:
    try:
        with Image.open(path) as image:
            image.load()
            expected = _IMAGE_FORMAT_BY_EXTENSION[extension]
            if image.format != expected:
                raise MediaError(
                    f"The file has a .{extension} extension but its contents "
                    f"are not a {expected} image."
                )
            image = ImageOps.exif_transpose(image)
            info = MediaInfo(
                type=Version.Type.IMAGE, width=image.width, height=image.height
            )
            return ProcessedMedia(info, _jpeg_thumb(image, thumb_max_size))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise MediaError("The file is not a valid image.") from exc


def _jpeg_thumb(image: Image.Image, max_size: int) -> bytes:
    thumb = image.convert("RGB")
    thumb.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    thumb.save(buffer, format="JPEG", quality=_THUMB_JPEG_QUALITY)
    return buffer.getvalue()


# --- video ------------------------------------------------------------------


def _process_video(path: str, thumb_position: float, thumb_max_size: int):
    info = _probe_video(path)
    frame = _extract_frame(path, info, thumb_position)
    try:
        with Image.open(io.BytesIO(frame)) as image:
            thumb = _jpeg_thumb(image, thumb_max_size)
    except (UnidentifiedImageError, OSError) as exc:
        raise MediaError("Could not extract a frame from the video.") from exc
    return ProcessedMedia(info, thumb)


def _probe_video(path: str) -> MediaInfo:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                "-select_streams",
                "v:0",
                path,
            ],
            capture_output=True,
            timeout=_PROBE_TIMEOUT_SECONDS,
            check=False,
        )
        data = json.loads(result.stdout or b"{}")
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise MediaError("The file is not a valid video.") from exc

    streams = data.get("streams") or []
    format_names = (data.get("format", {}).get("format_name") or "").split(",")
    if result.returncode != 0 or not streams or "mp4" not in format_names:
        raise MediaError("The file is not a valid mp4 video.")

    stream = streams[0]
    codec = stream.get("codec_name", "")
    if codec not in ALLOWED_VIDEO_CODECS:
        allowed = ", ".join(ALLOWED_VIDEO_CODECS)
        raise MediaError(
            f"Unsupported video codec '{codec or 'unknown'}'. Accepted: {allowed}."
        )

    width, height = stream.get("width"), stream.get("height")
    if not width or not height:
        raise MediaError("Could not determine the video's resolution.")

    fps = _parse_fps(stream)
    return MediaInfo(
        type=Version.Type.VIDEO,
        width=width,
        height=height,
        duration=_frame_count(stream, data.get("format", {}), fps),
        fps=fps,
        codec=codec,
    )


def _parse_rate(value: str | None) -> float | None:
    """Parse ffprobe's `24000/1001`-style rates; None if missing or zero."""
    if not value or "/" not in value:
        return None
    numerator, _, denominator = value.partition("/")
    try:
        rate = float(numerator) / float(denominator)
    except ValueError, ZeroDivisionError:
        return None
    return rate if rate > 0 else None


def _parse_fps(stream: dict) -> float | None:
    return _parse_rate(stream.get("avg_frame_rate")) or _parse_rate(
        stream.get("r_frame_rate")
    )


def _frame_count(stream: dict, container: dict, fps: float | None) -> int | None:
    """Frames in the video: the stream's own count, else duration x fps."""
    nb_frames = stream.get("nb_frames")
    if isinstance(nb_frames, str) and nb_frames.isdigit() and int(nb_frames) > 0:
        return int(nb_frames)

    seconds = stream.get("duration") or container.get("duration")
    try:
        seconds = float(seconds)
    except TypeError, ValueError:
        return None
    if fps and seconds > 0:
        return max(1, round(seconds * fps))
    return None


def _thumb_timestamp(info: MediaInfo, position: float) -> float:
    """Seconds into the clip of the frame to use as a thumbnail.

    `position` is 0.0 (first frame) to 1.0 (last frame). Falls back to
    the very beginning when the clip's length is unknown.
    """
    if not info.duration or not info.fps:
        return 0.0
    frame_index = int((info.duration - 1) * position)
    return frame_index / info.fps


def _extract_frame(path: str, info: MediaInfo, position: float) -> bytes:
    """Return one video frame as PNG bytes."""
    for timestamp in dict.fromkeys((_thumb_timestamp(info, position), 0.0)):
        try:
            result = _run_ffmpeg_frame(path, timestamp)
        except subprocess.TimeoutExpired as exc:
            raise MediaError("Could not extract a frame from the video.") from exc
        if result.returncode == 0 and result.stdout:
            return result.stdout
    raise MediaError("Could not extract a frame from the video.")


def _run_ffmpeg_frame(path: str, timestamp: float) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            f"{timestamp:.6f}",
            "-i",
            path,
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-",
        ],
        capture_output=True,
        timeout=_FRAME_EXTRACT_TIMEOUT_SECONDS,
        check=False,
    )
