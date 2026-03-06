from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone
import time


class Pipeline(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    container_image = models.CharField(max_length=255, default="python:3.11-slim")
    container_command = models.TextField(blank=True, default="")
    script_path = models.CharField(max_length=500, blank=True, default="")
    container_env = models.JSONField(blank=True, default=dict)
    container_timeout_seconds = models.PositiveIntegerField(default=3600)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @classmethod
    def create_pipeline(cls, name, description, user):
        return cls.objects.create(
            name=name,
            description=description,
            owner=user,
        )

    def can_execute(self, user):
        if not user.is_authenticated:
            return False

        if self.owner == user:
            return True

        return PipelinePermission.objects.filter(
            pipeline=self,
            user=user,
            permission="execute",
        ).exists()

    @classmethod
    def pipeline_list(cls, user):
        if not user.is_authenticated:
            return cls.objects.none()

        return cls.objects.filter(
            Q(owner=user)
            | Q(
                pipelinepermission__user=user,
                pipelinepermission__permission="execute",
            )
        ).distinct()

    def start_execution(self, user):
        if not self.can_execute(user):
            raise PermissionError("Usuario nao pode executar")

        if PipelineRun.objects.filter(
            pipeline=self,
            status=PipelineRun.Status.RUNNING,
        ).exists():
            raise Exception("Pipeline ja esta em execucao")

        run = PipelineRun.objects.create(
            pipeline=self,
            triggered_by=user,
            status=PipelineRun.Status.PENDING,
        )

        run.status = PipelineRun.Status.RUNNING
        run.started_at = timezone.now()
        run.save(update_fields=["status", "started_at"])

        try:
            time.sleep(3)
            run.status = PipelineRun.Status.SUCCESS
        except Exception as exc:
            run.status = PipelineRun.Status.FAILED
            run.log = str(exc)

        run.finished_at = timezone.now()
        run.save(update_fields=["status", "finished_at", "log"])

        return run


class PipelinePermission(models.Model):
    PERMISSION_CHOICES = (
        ("owner", "Owner"),
        ("edit", "Edit"),
        ("execute", "Execute"),
        ("view", "View"),
    )

    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES)

    class Meta:
        unique_together = ("pipeline", "user")

    def permission_pipe(self, user, permission):
        PipelinePermission.objects.update_or_create(
            pipeline=self,
            user=user,
            defaults={"permission": permission},
        )
        return True


class PipelineRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name="runs",
    )

    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    log = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Run {self.id} - {self.pipeline.name} - {self.status}"

    @classmethod
    def history(cls, pipeline_id, user):
        runs = (
            cls.objects.filter(pipeline_id=pipeline_id, triggered_by=user)
            .select_related("triggered_by")
            .order_by("-started_at")
        )

        data = [
            {
                "id": run.id,
                "status": run.status,
                "triggered_by": run.triggered_by.username if run.triggered_by else None,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            }
            for run in runs
        ]

        return data
