import factory
from factory.django import DjangoModelFactory

from apps.projects.models import Project, ProjectMembership


class ProjectFactory(DjangoModelFactory):
    """Builds `Project` instances for tests.

    Usage:
        project_factory()                  # saved project, random company + code
        project_factory(company=company, code="PRJ")
        project_factory.build(...)         # unsaved instance (no DB hit)
    """

    class Meta:
        model = Project

    company = factory.SubFactory("apps.companies.tests.factories.CompanyFactory")
    name = factory.Sequence(lambda n: f"Project {n}")
    code = factory.Sequence(lambda n: f"PRJ{n}")


class ProjectMembershipFactory(DjangoModelFactory):
    """Builds `ProjectMembership` instances for tests.

    Usage:
        project_membership_factory()                       # random user + project
        project_membership_factory(user=user, project=project, role=Role.ADMIN)
    """

    class Meta:
        model = ProjectMembership

    user = factory.SubFactory("apps.users.tests.factories.UserFactory")
    project = factory.SubFactory(ProjectFactory)
    role = ProjectMembership.Role.EXECUTOR
