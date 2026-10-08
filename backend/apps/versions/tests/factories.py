import io

from django.core.files.base import ContentFile
import factory
from factory.django import DjangoModelFactory
from PIL import Image

from apps.versions.models import Version


def _jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 48), "red").save(buffer, format="JPEG")
    return buffer.getvalue()


_JPEG = _jpeg_bytes()


class VersionFactory(DjangoModelFactory):
    """Builds `Version` instances for tests (a small JPG image version).

    Files are written to the per-test temporary `MEDIA_ROOT`; no ffmpeg
    needed. Uploading real videos is covered by the API/unit tests using
    the fixtures in `apps/versions/tests/conftest.py`.

    Usage:
        version_factory()                        # saved, random shot + name
        version_factory(shot=shot, name="PRJ_0010_v01")
    """

    class Meta:
        model = Version

    shot = factory.SubFactory("apps.shots.tests.factories.ShotFactory")
    project = factory.LazyAttribute(lambda o: o.shot.project)
    name = factory.Sequence(lambda n: f"PRJ_0010_v{n:02d}")
    type = Version.Type.IMAGE
    source = factory.LazyAttribute(lambda o: ContentFile(_JPEG, name=f"{o.name}.jpg"))
    thumb = factory.LazyAttribute(
        lambda o: ContentFile(_JPEG, name=f"{o.name}_thumb.jpg")
    )
    width = 64
    height = 48
    file_size = len(_JPEG)
