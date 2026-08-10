from http import HTTPStatus
import json

import pytest

from apps.companies.models import CompanyMembership


pytestmark = pytest.mark.django_db


def _post_json(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def _patch_json(client, path, payload):
    return client.patch(path, data=json.dumps(payload), content_type="application/json")


class TestListMembers:
    def test_returns_all_members(
        self,
        auth_client,
        auth_user,
        company_factory,
        company_membership_factory,
        user_factory,
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)
        other_user = user_factory(email="other@example.com")
        company_membership_factory(user=other_user, company=company)

        response = auth_client.get(f"/api/v1/companies/{company.id}/members/")

        assert response.status_code == 200
        emails = {member["email"] for member in response.json()["items"]}
        assert emails == {auth_user.email, "other@example.com"}

    def test_non_member_gets_404(
        self, auth_client, company_factory, company_membership_factory
    ):
        company = company_factory()
        company_membership_factory(company=company)

        response = auth_client.get(f"/api/v1/companies/{company.id}/members/")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_requires_authentication(self, client, company_factory):
        company = company_factory()

        response = client.get(f"/api/v1/companies/{company.id}/members/")

        assert response.status_code == 401


class TestAddMember:
    def test_adds_an_existing_user_with_the_given_role(
        self,
        auth_client,
        auth_user,
        company_factory,
        company_membership_factory,
        user_factory,
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)
        new_member = user_factory(email="newmember@example.com")

        response = _post_json(
            auth_client,
            f"/api/v1/companies/{company.id}/members/",
            {"user_id": new_member.id, "role": "producer"},
        )

        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        assert body["email"] == "newmember@example.com"
        assert body["role"] == "producer"
        assert CompanyMembership.objects.filter(
            company=company, user=new_member, role="producer"
        ).exists()

    def test_defaults_to_executor_role(
        self,
        auth_client,
        auth_user,
        company_factory,
        company_membership_factory,
        user_factory,
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)
        new_member = user_factory()

        response = _post_json(
            auth_client,
            f"/api/v1/companies/{company.id}/members/",
            {"user_id": new_member.id},
        )

        assert response.json()["role"] == "executor"

    def test_rejects_a_user_who_is_already_a_member(
        self,
        auth_client,
        auth_user,
        company_factory,
        company_membership_factory,
        user_factory,
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)
        existing_member = user_factory()
        company_membership_factory(user=existing_member, company=company)

        response = _post_json(
            auth_client,
            f"/api/v1/companies/{company.id}/members/",
            {"user_id": existing_member.id},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_rejects_an_unknown_user_id(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)

        response = _post_json(
            auth_client,
            f"/api/v1/companies/{company.id}/members/",
            {"user_id": 999999},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_non_member_cannot_add_members(
        self,
        auth_client,
        company_factory,
        company_membership_factory,
        user_factory,
    ):
        company = company_factory()
        company_membership_factory(company=company)
        new_member = user_factory()

        response = _post_json(
            auth_client,
            f"/api/v1/companies/{company.id}/members/",
            {"user_id": new_member.id},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_requires_authentication(self, client, company_factory, user_factory):
        company = company_factory()
        new_member = user_factory()

        response = _post_json(
            client,
            f"/api/v1/companies/{company.id}/members/",
            {"user_id": new_member.id},
        )

        assert response.status_code == 401


class TestUpdateMember:
    def test_updates_the_role(
        self,
        auth_client,
        auth_user,
        company_factory,
        company_membership_factory,
        user_factory,
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)
        member = user_factory()
        company_membership_factory(
            user=member, company=company, role=CompanyMembership.Role.EXECUTOR
        )

        response = _patch_json(
            auth_client,
            f"/api/v1/companies/{company.id}/members/{member.id}/",
            {"role": "coordinator"},
        )

        assert response.status_code == 200
        assert response.json()["role"] == "coordinator"

    def test_unknown_member_returns_404(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)

        response = _patch_json(
            auth_client,
            f"/api/v1/companies/{company.id}/members/999999/",
            {"role": "coordinator"},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_non_member_gets_404(
        self,
        auth_client,
        company_factory,
        company_membership_factory,
        user_factory,
    ):
        company = company_factory()
        member = user_factory()
        company_membership_factory(user=member, company=company)

        response = _patch_json(
            auth_client,
            f"/api/v1/companies/{company.id}/members/{member.id}/",
            {"role": "coordinator"},
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_requires_authentication(
        self, client, company_factory, company_membership_factory, user_factory
    ):
        company = company_factory()
        member = user_factory()
        company_membership_factory(user=member, company=company)

        response = _patch_json(
            client,
            f"/api/v1/companies/{company.id}/members/{member.id}/",
            {"role": "coordinator"},
        )

        assert response.status_code == 401


class TestRemoveMember:
    def test_removes_the_member(
        self,
        auth_client,
        auth_user,
        company_factory,
        company_membership_factory,
        user_factory,
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)
        member = user_factory()
        company_membership_factory(user=member, company=company)

        response = auth_client.delete(
            f"/api/v1/companies/{company.id}/members/{member.id}/"
        )

        assert response.status_code == HTTPStatus.NO_CONTENT
        assert not CompanyMembership.objects.filter(
            company=company, user=member
        ).exists()

    def test_unknown_member_returns_404(
        self, auth_client, auth_user, company_factory, company_membership_factory
    ):
        company = company_factory()
        company_membership_factory(user=auth_user, company=company)

        response = auth_client.delete(f"/api/v1/companies/{company.id}/members/999999/")

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_requires_authentication(
        self, client, company_factory, company_membership_factory, user_factory
    ):
        company = company_factory()
        member = user_factory()
        company_membership_factory(user=member, company=company)

        response = client.delete(f"/api/v1/companies/{company.id}/members/{member.id}/")

        assert response.status_code == 401
