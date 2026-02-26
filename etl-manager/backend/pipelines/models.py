from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone
import time

class Pipeline(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    # Criação de Pipeline
    @classmethod
    def create_pipeline(cls, name, description, user):
        return cls.objects.create(
            name=name,
            description=description,
            owner=user
        )
    
    # Verifica se o usuário é owner ou se tem permição de edição
    def can_execute(self, user):

        # Verifica se o usuário esta logado
        if not user.is_authenticated:
            return False

        # Verifica se o usuário é dono da pipe
        if self.owner == user:
            return True

        # Verifica se o usuário mesmo não sendo dono da pipe tem permissão de execute
        return PipelinePermission.objects.filter(
            pipeline=self,
            user=user,
            permission="execute"
        ).exists()

    def pipeline_list(user):
        if not user.is_authenticated:
            return PermissionError("Usuário não authenticado realizar login")
        
        pipelines = Pipeline.objects.filter(
            Q(owner=user) |
            Q(pipelinepermission__user=user,
            pipelinepermission__permission="execute")
        ).distinct() 

        return pipelines

    # Execução de fluxo
    def start_execution(self, user):
        if not self.can_execute(user):
            raise PermissionError("Usuário não pode executar")

        if PipelineRun.objects.filter(
            pipeline=self,
            status="running"
        ).exists():
            raise Exception("Pipeline já está em execução")

        run = PipelineRun.objects.create(
            pipeline=self,
            triggered_by=user,
            status="pending"
        )

        # Início real da execução
        run.status = "running"
        run.started_at = timezone.now()
        run.save()

        try:
            # Simulação de execução
            time.sleep(3)

            run.status = "success"
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)

        run.finished_at = timezone.now()
        run.save()

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
        if PipelinePermission.objects.filter(
            pipeline=self,
            user=user,
            permission=permission
        ).exists():
            return True
        else:
            PipelinePermission.objects.update_or_create(
                pipeline=self,
                user=user,
                defaults={"permission": permission}
            )
            return False
        
class PipelineRun(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name="runs"
    )

    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    log = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Run {self.id} - {self.pipeline.name} - {self.status}"