from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Company(BaseModel):
    """
    Top-level tenant. Provides data isolation between independent
    organizations within a single installation.
    """

    name = models.CharField(_("name"), max_length=255)
    slug = models.SlugField(_("slug"), max_length=255, unique=True, blank=True)

    class Meta:
        verbose_name = _("company")
        verbose_name_plural = _("companies")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<Company id={self.id} slug={self.slug}>"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class CompanyMembership(BaseModel):
    """
    A user's role within a company.

    Acts as the default role for all of the company's projects unless
    overridden by a project-level membership.
    """

    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        PRODUCER = "producer", _("Producer")
        COORDINATOR = "coordinator", _("Coordinator")
        EXECUTOR = "executor", _("Executor")
        FREELANCER = "freelancer", _("Freelancer")
        CLIENT = "client", _("Client")

    user = models.ForeignKey(
        "users.User",
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        related_name="company_memberships",
    )
    company = models.ForeignKey(
        Company,
        verbose_name=_("company"),
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        _("role"), max_length=20, choices=Role.choices, default=Role.EXECUTOR
    )

    class Meta:
        verbose_name = _("company membership")
        verbose_name_plural = _("company memberships")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "company"], name="unique_company_membership"
            )
        ]
        ordering = ["company", "user"]

    def __str__(self):
        return f"{self.user} — {self.company} ({self.get_role_display()})"

    def __repr__(self):
        return (
            f"<CompanyMembership id={self.id} user_id={self.user_id} "
            f"company_id={self.company_id} role={self.role}>"
        )
