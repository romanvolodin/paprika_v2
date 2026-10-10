from django.db import IntegrityError, transaction
import pytest

from apps.chat.models import Message, Reaction


pytestmark = pytest.mark.django_db


class TestMessageConstraints:
    def test_a_user_message_cannot_have_an_event(self, shot):
        with pytest.raises(IntegrityError), transaction.atomic():
            Message.objects.create(
                shot=shot, type=Message.Type.USER, event=Message.Event.TASK_ADDED
            )

    def test_a_system_message_needs_an_event(self, shot):
        with pytest.raises(IntegrityError), transaction.atomic():
            Message.objects.create(shot=shot, type=Message.Type.SYSTEM)

    def test_a_system_message_with_an_event_is_fine(self, shot):
        message = Message.objects.create(
            shot=shot, type=Message.Type.SYSTEM, event=Message.Event.TASK_ADDED
        )

        assert message.payload == {}


class TestMessageOrdering:
    def test_messages_are_ordered_by_id(self, shot, message_factory):
        first = message_factory(shot=shot)
        second = message_factory(shot=shot)

        assert list(Message.objects.filter(shot=shot)) == [first, second]


class TestSoftDelete:
    def test_the_row_stays_with_wiped_content(self, user, message_factory):
        message = message_factory(text="secret")

        message.mark_deleted(user)

        message.refresh_from_db()
        assert message.pk is not None
        assert message.text == ""
        assert message.is_deleted
        assert message.updated_by == user


class TestReactionUniqueness:
    def test_the_same_emoji_by_the_same_user_is_unique(
        self, reaction_factory, message_factory, user
    ):
        message = message_factory()
        reaction_factory(message=message, created_by=user, emoji="👍")

        with pytest.raises(IntegrityError), transaction.atomic():
            Reaction.objects.create(message=message, created_by=user, emoji="👍")

    def test_another_emoji_or_another_user_is_fine(
        self, reaction_factory, message_factory, user, user_factory
    ):
        message = message_factory()
        reaction_factory(message=message, created_by=user, emoji="👍")

        reaction_factory(message=message, created_by=user, emoji="🔥")
        reaction_factory(message=message, created_by=user_factory(), emoji="👍")

        assert message.reactions.count() == 3
