from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
import pytest

from apps.tasks import models as task_models
from apps.tasks.models import ShotTask, Task, TaskStatus, TaskType


pytestmark = pytest.mark.django_db


class TestTaskCode:
    def test_code_is_the_type_abbreviation_plus_four_digits(
        self, project, task_type_factory
    ):
        task_type = task_type_factory(company=project.company, abbreviation="ANM")

        task = Task.objects.create(project=project, type=task_type, name="Клинап")

        assert task.code.startswith("ANM")
        assert len(task.code) == len("ANM") + 4
        assert task.code[3:].isdigit()

    def test_code_is_unique_within_a_project(self, project, task_factory):
        tasks = [task_factory(project=project) for _ in range(30)]

        codes = [t.code for t in tasks]
        assert len(set(codes)) == len(codes)

    def test_a_collision_is_resolved_by_picking_another_number(
        self, project, task_factory, mocker
    ):
        first = task_factory(project=project, type=project.company.task_types.first())
        number = int(first.code[len(first.type.abbreviation) :])
        # First attempt collides with the existing code, second doesn't.
        other = 1000 if number != 1000 else 1001
        mocker.patch.object(task_models, "_random_number", side_effect=[number, other])

        second = task_factory(project=project, type=first.type)

        assert second.code == f"{first.type.abbreviation}{other}"

    def test_gives_up_after_too_many_collisions(self, project, task_factory, mocker):
        first = task_factory(project=project)
        number = int(first.code[len(first.type.abbreviation) :])
        mocker.patch.object(task_models, "_random_number", return_value=number)

        with pytest.raises(RuntimeError, match="unique task code"):
            task_factory(project=project, type=first.type)

    def test_the_same_code_is_fine_in_another_project(
        self, task_factory, project_factory, mocker
    ):
        mocker.patch.object(task_models, "_random_number", return_value=4821)
        first = task_factory()
        other_type = first.type

        second = task_factory(project=project_factory(company=first.project.company))

        assert second.code == f"{second.type.abbreviation}4821"
        assert second.project_id != first.project_id
        assert other_type is not None

    def test_code_does_not_change_when_the_type_does(
        self, task_factory, task_type_factory
    ):
        task = task_factory()
        original = task.code
        other_type = task_type_factory(company=task.project.company)

        task.type = other_type
        task.save()
        task.refresh_from_db()

        assert task.code == original

    def test_code_does_not_change_when_the_abbreviation_is_renamed(self, task):
        original = task.code
        task.type.abbreviation = "ZZ"
        task.type.save()

        task.refresh_from_db()

        assert task.code == original


class TestTask:
    def test_str_shows_code_and_name(self, task):
        assert str(task) == f"{task.code} {task.name}"

    def test_a_task_can_be_standalone(self, task):
        assert task.shots.count() == 0

    def test_a_task_type_in_use_cannot_be_deleted(self, task):
        with pytest.raises(ProtectedError):
            task.type.delete()

    def test_deleting_a_project_deletes_its_tasks(self, task):
        task.project.delete()

        assert not Task.objects.filter(pk=task.pk).exists()

    def test_tasks_are_listed_newest_first(self, project, task_factory):
        older = task_factory(project=project)
        newer = task_factory(project=project)

        assert list(Task.objects.filter(project=project)) == [newer, older]


class TestShotTask:
    def test_a_task_can_be_on_many_shots_and_a_shot_has_many_tasks(
        self, project, shot_factory, task_factory, shot_task_factory
    ):
        shot_a, shot_b = shot_factory(project=project), shot_factory(project=project)
        sky, wires = task_factory(project=project), task_factory(project=project)
        shot_task_factory(shot=shot_a, task=sky)
        shot_task_factory(shot=shot_b, task=sky)
        shot_task_factory(shot=shot_a, task=wires)

        assert set(sky.shots.all()) == {shot_a, shot_b}
        assert set(shot_a.tasks.all()) == {sky, wires}

    def test_a_task_can_be_placed_on_a_shot_only_once(
        self, shot_task, shot_task_factory
    ):
        with pytest.raises(IntegrityError), transaction.atomic():
            shot_task_factory(shot=shot_task.shot, task=shot_task.task)

    def test_tracking_fields_are_per_shot(
        self, project, shot_factory, task_factory, shot_task_factory
    ):
        task = task_factory(project=project)
        first = shot_task_factory(
            shot=shot_factory(project=project), task=task, estimated_hours=4
        )
        second = shot_task_factory(shot=shot_factory(project=project), task=task)

        assert first.estimated_hours == Decimal("4")
        assert second.estimated_hours is None

    def test_deleting_a_task_removes_its_placements(self, shot_task):
        shot_task.task.delete()

        assert not ShotTask.objects.filter(pk=shot_task.pk).exists()
        assert shot_task.shot.__class__.objects.filter(pk=shot_task.shot_id).exists()

    def test_deleting_a_shot_removes_its_placements_but_not_the_task(self, shot_task):
        shot_task.shot.delete()

        assert not ShotTask.objects.filter(pk=shot_task.pk).exists()
        assert Task.objects.filter(pk=shot_task.task_id).exists()

    def test_a_status_in_use_cannot_be_deleted(self, shot_task):
        with pytest.raises(ProtectedError):
            shot_task.status.delete()

    def test_deleting_the_assignee_unassigns_instead_of_deleting(
        self, shot_task_factory, user
    ):
        shot_task = shot_task_factory(assignee=user)

        user.delete()
        shot_task.refresh_from_db()

        assert shot_task.assignee is None


class TestStarterSetForNewCompanies:
    def test_a_new_company_gets_task_statuses_with_one_default(self, company):
        statuses = TaskStatus.objects.filter(company=company)

        assert {s.name for s in statuses} == {
            "Не начата",
            "В работе",
            "Готова",
            "Отмена",
            "На паузе",
        }
        assert [s.name for s in statuses if s.is_default] == ["Не начата"]

    def test_side_states_have_no_order(self, company):
        side = TaskStatus.objects.filter(company=company, order__isnull=True)

        assert {s.name for s in side} == {"Отмена", "На паузе"}

    def test_a_new_company_gets_the_starter_task_types(self, company):
        types = TaskType.objects.filter(company=company)

        assert {(t.name, t.abbreviation) for t in types} == {
            ("Композ", "COMP"),
            ("Клинап", "CLN"),
            ("Трекинг", "TRK"),
            ("Ротоскоп", "ROTO"),
        }

    def test_saving_an_existing_company_does_not_seed_again(self, company):
        before = TaskStatus.objects.filter(company=company).count()

        company.save()

        assert TaskStatus.objects.filter(company=company).count() == before

    def test_each_company_gets_its_own_set(self, company_factory):
        first, second = company_factory(), company_factory()

        assert not set(first.task_types.all()) & set(second.task_types.all())
        assert first.task_types.count() == second.task_types.count() == 4
