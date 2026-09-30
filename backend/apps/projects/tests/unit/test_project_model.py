import datetime as dt

from django.core.exceptions import ValidationError
from django.db import IntegrityError
import pytest

from apps.projects.models import Project


pytestmark = pytest.mark.django_db


class TestProjectModel:
    def test_str_returns_code_and_name(self, project_factory):
        project = project_factory(code="PRJ", name="Acme Feature")

        assert str(project) == "PRJ — Acme Feature"

    def test_repr_contains_id_code_and_company_id(self, project_factory, company):
        project = project_factory(company=company, code="PRJ")

        assert f"id={project.id}" in repr(project)
        assert "code=PRJ" in repr(project)
        assert f"company_id={company.id}" in repr(project)

    def test_code_must_be_unique_within_company(self, project_factory, company):
        project_factory(company=company, code="PRJ")

        with pytest.raises(IntegrityError):
            project_factory(company=company, code="PRJ")

    def test_same_code_allowed_in_different_companies(
        self, project_factory, company_factory
    ):
        company_a = company_factory()
        company_b = company_factory()
        project_factory(company=company_a, code="PRJ")

        # Should not raise.
        project_factory(company=company_b, code="PRJ")

    def test_code_rejects_invalid_characters(self, project_factory, company):
        project = project_factory.build(code="PRJ 001!", company=company)

        with pytest.raises(ValidationError):
            project.full_clean()

    def test_code_accepts_letters_numbers_hyphens_underscores(
        self, project_factory, company
    ):
        project = project_factory.build(code="PRJ-001_v2", company=company)

        # Should not raise.
        project.full_clean()

    def test_ordering_is_by_company_then_name(self, project_factory, company):
        project_factory(company=company, name="C Project")
        project_factory(company=company, name="A Project")
        project_factory(company=company, name="B Project")

        names = list(
            Project.objects.filter(company=company).values_list("name", flat=True)
        )

        assert names == sorted(names)

    def test_created_by_is_set_to_null_when_creator_is_deleted(
        self, project_factory, user_factory
    ):
        creator = user_factory()
        project = project_factory(created_by=creator)

        creator.delete()
        project.refresh_from_db()

        assert project.created_by is None

    def test_deadline_before_start_date_is_allowed_at_model_level(
        self, project_factory
    ):
        # Model-level `clean()` isn't used in this codebase - the
        # deadline-after-start rule is enforced by the API schema layer
        # instead. This test documents that the model itself doesn't
        # block it.
        project = project_factory(
            start_date=dt.date(2026, 6, 1), deadline=dt.date(2026, 1, 1)
        )

        assert project.deadline < project.start_date
