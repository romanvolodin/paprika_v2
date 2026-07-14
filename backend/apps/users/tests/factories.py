import factory
from factory.django import DjangoModelFactory

from apps.users.models import User


DEFAULT_PASSWORD = "Str0ngPassw0rd!"


class UserFactory(DjangoModelFactory):
    """Builds `User` instances for tests.

    Usage:
        user_factory()                      # saved user, random unique email
        user_factory(email="a@b.com")       # saved user, given email
        user_factory.build(...)             # unsaved instance (no DB hit)
        user_factory(password="whatever")   # known raw password, for login tests

    The raw password defaults to `DEFAULT_PASSWORD` and is always hashed via
    `set_password`, matching how `User.objects.create_user` behaves - tests
    that log in should import `DEFAULT_PASSWORD` rather than guessing it.
    """

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Sequence(lambda n: f"First{n}")
    last_name = factory.Sequence(lambda n: f"Last{n}")
    is_active = True
    is_staff = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):  # noqa: FBT001
        raw_password = extracted or DEFAULT_PASSWORD
        self.set_password(raw_password)
        if create:
            self.save(update_fields=["password"])
