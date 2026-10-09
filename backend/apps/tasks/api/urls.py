from dmr.routing import Router, path

from .views import (
    ShotTaskDetailController,
    ShotTaskListController,
    TaskDetailController,
    TaskListController,
    TaskStatusDetailController,
    TaskStatusListController,
    TaskTypeDetailController,
    TaskTypeListController,
)


router = Router(
    "",
    [
        path(
            "companies/<int:company_id>/task-types/",
            TaskTypeListController.as_view(),
            name="task-type-list",
        ),
        path(
            "task-types/<int:task_type_id>/",
            TaskTypeDetailController.as_view(),
            name="task-type-detail",
        ),
        path(
            "companies/<int:company_id>/task-statuses/",
            TaskStatusListController.as_view(),
            name="task-status-list",
        ),
        path(
            "task-statuses/<int:task_status_id>/",
            TaskStatusDetailController.as_view(),
            name="task-status-detail",
        ),
        path(
            "projects/<int:project_id>/tasks/",
            TaskListController.as_view(),
            name="task-list",
        ),
        path(
            "tasks/<int:task_id>/",
            TaskDetailController.as_view(),
            name="task-detail",
        ),
        path(
            "shots/<int:shot_id>/tasks/",
            ShotTaskListController.as_view(),
            name="shot-task-list",
        ),
        path(
            "shot-tasks/<int:shot_task_id>/",
            ShotTaskDetailController.as_view(),
            name="shot-task-detail",
        ),
    ],
)
