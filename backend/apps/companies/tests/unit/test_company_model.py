from django.db import IntegrityError
import pytest

from apps.companies.models import Company


pytestmark = pytest.mark.django_db


class TestCompanyModel:
    def test_str_returns_name(self, company_factory):
        company = company_factory(name="Acme Studio")

        assert str(company) == "Acme Studio"

    def test_repr_contains_id_and_slug(self, company_factory):
        company = company_factory(name="Acme Studio")

        assert f"id={company.id}" in repr(company)
        assert f"slug={company.slug}" in repr(company)

    def test_slug_is_auto_generated_from_name(self, company_factory):
        company = company_factory(name="Acme Studio")

        assert company.slug == "acme-studio"

    def test_slug_is_not_overwritten_if_provided(self, company_factory):
        company = company_factory(name="Acme Studio", slug="custom-slug")

        assert company.slug == "custom-slug"

    def test_slug_is_not_regenerated_on_subsequent_saves(self, company_factory):
        company = company_factory(name="Acme Studio")
        original_slug = company.slug

        company.name = "Renamed Studio"
        company.save()

        assert company.slug == original_slug

    def test_slug_supports_cyrillic_names(self, company_factory):
        company = company_factory(name="Крутая Студия")

        assert company.slug == "крутая-студия"

    def test_slug_must_be_unique(self, company_factory):
        company_factory(name="Acme Studio", slug="acme")

        with pytest.raises(IntegrityError):
            company_factory(name="Acme Studio Two", slug="acme")

    def test_ordering_is_by_name(self, company_factory):
        company_factory(name="C Studio")
        company_factory(name="A Studio")
        company_factory(name="B Studio")

        names = list(Company.objects.values_list("name", flat=True))

        assert names == sorted(names)

    def test_created_by_is_set_to_null_when_creator_is_deleted(
        self, company_factory, user_factory
    ):
        creator = user_factory()
        company = company_factory(created_by=creator)

        creator.delete()
        company.refresh_from_db()

        assert company.created_by is None
