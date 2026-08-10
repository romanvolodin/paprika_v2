from http import HTTPStatus
import json

import pytest

from apps.companies.models import Company, CompanyMembership


pytestmark = pytest.mark.django_db


def _patch_json(client, path, payload):
    return client.patch(path, data=json.dumps(payload), content_type="application/json")


class TestGetCompany:
    def test_returns_the_company_for_a_member(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company = company_factory(name="Mine")
        company_membership_factory(user=auth_user, company=company)

        response = auth_client.get(f"/api/v1/companies/{company.id}/")

        assert response.status_code == 200
        assert response.json()["name"] == "Mine"

    def test_non_member_gets_a_404_not_a_403(
        self, auth_client, company_factory, company_membership_factory
    ):
        # By design, a company you don't belong to 404s exactly like one
        # that doesn't exist - membership isn't leaked to non-members.
        company = company_factory()
        company_membership_factory(company=company)  # some other user

        response = auth_client.get(f"/api/v1/companies/{company.id}/")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_unknown_id_returns_404(self, auth_client):
        response = auth_client.get("/api/v1/companies/999999/")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_requires_authentication(
        self, client, company_factory, company_membership_factory
    ):
        company = company_factory()

        response = client.get(f"/api/v1/companies/{company.id}/")

        assert response.status_code == 401


class TestUpdateCompany:
    def test_updates_the_name(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company = company_factory(name="Old Name")
        company_membership_factory(user=auth_user, company=company)

        response = _patch_json(
            auth_client, f"/api/v1/companies/{company.id}/", {"name": "New Name"}
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_partial_update_leaves_slug_untouched(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company = company_factory(name="Old Name", slug="keep-me")
        company_membership_factory(user=auth_user, company=company)

        response = _patch_json(
            auth_client, f"/api/v1/companies/{company.id}/", {"name": "New Name"}
        )

        assert response.json()["slug"] == "keep-me"

    def test_updating_to_a_taken_slug_is_rejected(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company_factory(slug="taken")
        company = company_factory(slug="mine")
        company_membership_factory(user=auth_user, company=company)

        response = _patch_json(
            auth_client, f"/api/v1/companies/{company.id}/", {"slug": "taken"}
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_empty_body_changes_nothing(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company = company_factory(name="Untouched")
        company_membership_factory(user=auth_user, company=company)

        response = _patch_json(auth_client, f"/api/v1/companies/{company.id}/", {})

        assert response.status_code == 200
        assert response.json()["name"] == "Untouched"

    def test_non_member_gets_404(
        self, auth_client, company_factory, company_membership_factory
    ):
        company = company_factory()
        company_membership_factory(company=company)

        response = _patch_json(
            auth_client, f"/api/v1/companies/{company.id}/", {"name": "Hacked"}
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_requires_authentication(self, client, company_factory):
        company = company_factory()

        response = _patch_json(
            client, f"/api/v1/companies/{company.id}/", {"name": "Hacked"}
        )

        assert response.status_code == 401


class TestDeleteCompany:
    def test_deletes_the_company(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)

        response = auth_client.delete(f"/api/v1/companies/{company.id}/")

        assert response.status_code == HTTPStatus.NO_CONTENT
        assert not Company.objects.filter(id=company.id).exists()

    def test_deleting_a_company_cascades_its_memberships(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company = company_factory()
        membership = company_membership_factory(user=auth_user, company=company)

        auth_client.delete(f"/api/v1/companies/{company.id}/")

        assert not CompanyMembership.objects.filter(id=membership.id).exists()

    def test_non_member_gets_404(
        self, auth_client, company_factory, company_membership_factory
    ):
        company = company_factory()
        company_membership_factory(company=company)

        response = auth_client.delete(f"/api/v1/companies/{company.id}/")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert Company.objects.filter(id=company.id).exists()

    def test_requires_authentication(self, client, company_factory):
        company = company_factory()

        response = client.delete(f"/api/v1/companies/{company.id}/")

        assert response.status_code == 401
        assert Company.objects.filter(id=company.id).exists()
