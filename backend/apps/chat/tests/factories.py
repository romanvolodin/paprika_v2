from django.core.files.base import ContentFile
import factory
from factory.django import DjangoModelFactory

from apps.chat.models import Attachment, Message, Reaction


class MessageFactory(DjangoModelFactory):
    """Builds user `Message` instances for tests.

    Usage:
        message_factory()                          # saved, random shot + author
        message_factory(shot=shot, text="Привет")
        message_factory(shot=shot, created_by=user, reply_to=other)
    """

    class Meta:
        model = Message

    shot = factory.SubFactory("apps.shots.tests.factories.ShotFactory")
    type = Message.Type.USER
    text = factory.Sequence(lambda n: f"Message {n}")
    created_by = factory.SubFactory("apps.users.tests.factories.UserFactory")


class AttachmentFactory(DjangoModelFactory):
    """Builds `Attachment` instances for tests (not attached to a message).

    Usage:
        attachment_factory(shot=shot, created_by=user)
        attachment_factory(shot=shot, message=message)
    """

    class Meta:
        model = Attachment

    shot = factory.SubFactory("apps.shots.tests.factories.ShotFactory")
    filename = factory.Sequence(lambda n: f"file{n}.txt")
    file = factory.LazyAttribute(lambda o: ContentFile(b"data", name=o.filename))
    size = 4
    content_type = "text/plain"
    created_by = factory.SubFactory("apps.users.tests.factories.UserFactory")


class ReactionFactory(DjangoModelFactory):
    class Meta:
        model = Reaction

    message = factory.SubFactory(MessageFactory)
    emoji = "👍"
    created_by = factory.SubFactory("apps.users.tests.factories.UserFactory")
