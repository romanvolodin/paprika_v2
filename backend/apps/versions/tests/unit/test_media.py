import io

from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
from PIL import Image
import pytest

from apps.versions import media
from apps.versions.media import MediaError, process_upload
from apps.versions.models import Version
from apps.versions.tests.conftest import make_jpeg, make_png


def _process(data: bytes, extension: str, *, position=0.5, max_size=320):
    upload = SimpleUploadedFile(f"sample.{extension}", data)
    return process_upload(
        upload, extension, thumb_position=position, thumb_max_size=max_size
    )


def _center_color(jpeg: bytes) -> str:
    """Name of the dominant channel of the thumbnail's centre pixel."""
    with Image.open(io.BytesIO(jpeg)) as image:
        pixel = image.convert("RGB").getpixel((image.width // 2, image.height // 2))
    return ("red", "green", "blue")[pixel.index(max(pixel))]


class TestVideo:
    def test_reads_metadata(self, h264_video_bytes):
        info = _process(h264_video_bytes, "mp4").info

        assert info.type == Version.Type.VIDEO
        assert (info.width, info.height) == (64, 64)
        assert info.duration == 9
        assert info.fps == pytest.approx(10)
        assert info.codec == "h264"

    @pytest.mark.parametrize(
        ("position", "expected"),
        [(0.0, "red"), (0.5, "green"), (1.0, "blue")],
    )
    def test_thumb_frame_follows_position(self, h264_video_bytes, position, expected):
        thumb = _process(h264_video_bytes, "mp4", position=position).thumb

        assert _center_color(thumb) == expected

    def test_thumb_is_a_jpeg(self, h264_video_bytes):
        thumb = _process(h264_video_bytes, "mp4").thumb

        with Image.open(io.BytesIO(thumb)) as image:
            assert image.format == "JPEG"

    def test_rejects_other_codecs(self, mpeg4_video_bytes):
        with pytest.raises(MediaError, match="codec"):
            _process(mpeg4_video_bytes, "mp4")

    def test_rejects_garbage_with_an_mp4_extension(self):
        with pytest.raises(MediaError):
            _process(b"definitely not a video", "mp4")

    def test_works_for_uploads_already_spooled_to_disk(self, h264_video_bytes):
        upload = TemporaryUploadedFile(
            "big.mp4", "video/mp4", len(h264_video_bytes), None
        )
        upload.write(h264_video_bytes)
        upload.flush()

        result = process_upload(upload, "mp4", thumb_position=0.5, thumb_max_size=320)

        assert result.info.codec == "h264"


class TestImage:
    def test_reads_a_jpeg(self):
        result = _process(make_jpeg((100, 80)), "jpg")

        assert result.info == media.MediaInfo(
            type=Version.Type.IMAGE, width=100, height=80
        )
        assert _center_color(result.thumb) == "red"

    def test_reads_a_png_with_alpha(self):
        result = _process(make_png((30, 20), mode="RGBA"), "png")

        assert (result.info.width, result.info.height) == (30, 20)
        with Image.open(io.BytesIO(result.thumb)) as thumb:
            assert thumb.format == "JPEG"

    def test_jpeg_extension_is_accepted_as_jpg(self):
        assert _process(make_jpeg(), "jpeg").info.type == Version.Type.IMAGE

    def test_thumb_is_scaled_down_keeping_the_aspect_ratio(self):
        thumb = _process(make_jpeg((800, 400)), "jpg", max_size=320).thumb

        with Image.open(io.BytesIO(thumb)) as image:
            assert image.size == (320, 160)

    def test_small_images_are_not_upscaled(self):
        thumb = _process(make_jpeg((64, 48)), "jpg", max_size=320).thumb

        with Image.open(io.BytesIO(thumb)) as image:
            assert image.size == (64, 48)

    def test_rejects_contents_that_do_not_match_the_extension(self):
        with pytest.raises(MediaError, match="not a JPEG"):
            _process(make_png(), "jpg")

    def test_rejects_garbage(self):
        with pytest.raises(MediaError, match="not a valid image"):
            _process(b"not an image", "png")


class TestProbeHelpers:
    def test_parse_rate_handles_ntsc_fractions(self):
        assert media._parse_rate("24000/1001") == pytest.approx(23.976, abs=1e-3)

    @pytest.mark.parametrize("value", [None, "", "0/0", "25", "abc/def"])
    def test_parse_rate_returns_none_for_unusable_values(self, value):
        assert media._parse_rate(value) is None

    def test_frame_count_prefers_the_streams_own_count(self):
        assert media._frame_count({"nb_frames": "48"}, {}, 24.0) == 48

    def test_frame_count_falls_back_to_duration_times_fps(self):
        assert media._frame_count({"duration": "2.0"}, {}, 24.0) == 48

    def test_frame_count_uses_the_container_duration_as_a_last_resort(self):
        assert media._frame_count({}, {"duration": "1.0"}, 25.0) == 25

    def test_frame_count_is_none_when_nothing_is_known(self):
        assert media._frame_count({}, {}, None) is None

    def test_thumb_timestamp_defaults_to_the_start_for_unknown_length(self):
        info = media.MediaInfo(type="video", width=1, height=1)

        assert media._thumb_timestamp(info, 0.5) == 0.0
