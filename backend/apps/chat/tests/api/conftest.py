import json

import pytest


def post_json(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def patch_json(client, path, payload):
    return client.patch(path, data=json.dumps(payload), content_type="application/json")


def put_json(client, path, payload):
    return client.put(path, data=json.dumps(payload), content_type="application/json")


@pytest.fixture
def member_shot(auth_user, shot, project_membership_factory):
    """A shot in a project the logged-in user belongs to (default role)."""
    project_membership_factory(user=auth_user, project=shot.project)
    return shot


@pytest.fixture
def client_shot(auth_user, shot, project_membership_factory):
    """A shot in a project where the logged-in user is a read-only `client`."""
    project_membership_factory(user=auth_user, project=shot.project, role="client")
    return shot
