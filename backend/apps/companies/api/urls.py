from dmr.routing import Router, path

from .views import (
    CompanyDetailController,
    CompanyListController,
    CompanyMemberDetailController,
    CompanyMemberListController,
)


router = Router(
    "",
    [
        path(
            "companies/",
            CompanyListController.as_view(),
            name="company-list",
        ),
        path(
            "companies/<int:company_id>/",
            CompanyDetailController.as_view(),
            name="company-detail",
        ),
        path(
            "companies/<int:company_id>/members/",
            CompanyMemberListController.as_view(),
            name="company-member-list",
        ),
        path(
            "companies/<int:company_id>/members/<int:user_id>/",
            CompanyMemberDetailController.as_view(),
            name="company-member-detail",
        ),
    ],
)
