from django.core.exceptions import ValidationError
from django.db import IntegrityError
import pytest

from apps.shots.models import ShotStatus
from apps.shots.signals import DEFAULT_SHOT_STATUSES


pytestmark = pytest.mark.django_db


class TestShotStatusModel:
    def test_str_contains_company_and_name(self, shot_status_factory, company_factory):
        company = company_factory(name="Acme Studio")
        status = shot_status_factory(company=company, name="Custom Status")

        assert str(status) == "Acme Studio — Custom Status"

    def test_repr_contains_id_name_company_id_and_is_default(
        self, shot_status_factory, company
    ):
        status = shot_status_factory(
            company=company, name="Custom Status", is_default=True
        )

        text = repr(status)

        assert f"id={status.id}" in text
        assert "name=Custom Status" in text
        assert f"company_id={company.id}" in text
        assert "is_default=True" in text

    def test_name_must_be_unique_within_company(self, shot_status_factory, company):
        shot_status_factory(company=company, name="Custom Status")

        with pytest.raises(IntegrityError):
            shot_status_factory(company=company, name="Custom Status")

    def test_same_name_allowed_in_different_companies(
        self, shot_status_factory, company_factory
    ):
        company_a = company_factory()
        company_b = company_factory()
        shot_status_factory(company=company_a, name="Custom Status")

        # Should not raise.
        shot_status_factory(company=company_b, name="Custom Status")

    def test_color_must_be_a_6_digit_hex_code(self, shot_status_factory, company):
        status = shot_status_factory.build(company=company, color="not-a-color")

        with pytest.raises(ValidationError):
            status.full_clean()

    def test_color_accepts_a_valid_hex_code(self, shot_status_factory, company):
        status = shot_status_factory.build(company=company, color="#FF5733")

        # Should not raise.
        status.full_clean()

    def test_order_defaults_to_null(self, shot_status_factory):
        status = shot_status_factory()

        assert status.order is None

    def test_is_default_defaults_to_false(self, shot_status_factory):
        status = shot_status_factory()

        assert status.is_default is False

    def test_is_deleted_when_company_is_deleted(self, shot_status_factory, company):
        status = shot_status_factory(company=company)
        status_id = status.id

        company.delete()

        assert not ShotStatus.objects.filter(id=status_id).exists()


class TestDefaultShotStatusSeeding:
    def test_creating_a_company_seeds_the_full_default_set(self, company_factory):
        company = company_factory()

        names = set(company.shot_statuses.values_list("name", flat=True))

        assert names == {name for name, _color, _order in DEFAULT_SHOT_STATUSES}

    def test_exactly_one_seeded_status_is_default(self, company_factory):
        company = company_factory()

        defaults = company.shot_statuses.filter(is_default=True)

        assert defaults.count() == 1
        assert defaults.first().name == DEFAULT_SHOT_STATUSES[0][0]

    def test_seeded_colors_and_order_match_the_configured_list(self, company_factory):
        company = company_factory()

        for name, color, order in DEFAULT_SHOT_STATUSES:
            status = company.shot_statuses.get(name=name)
            assert status.color == color
            assert status.order == order

    def test_updating_an_existing_company_does_not_reseed(
        self, company_factory, shot_status_factory
    ):
        company = company_factory()
        shot_status_factory(company=company, name="Custom")

        company.name = "Renamed"
        company.save()

        # Still just the 8 seeded + the 1 custom - not doubled.
        assert company.shot_statuses.count() == len(DEFAULT_SHOT_STATUSES) + 1
