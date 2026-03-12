from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
import time
from pathlib import Path

class Pipeline(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    etl_name = models.CharField(
        max_length=255,
        help_text="Nome da ETL (pasta em /etls/)"
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    # Criação de Pipeline
    @classmethod
    def create_pipeline(cls, name, description, user, lib):
        
        script_code = '''
import os

API_VENDAS_URL = os.getenv("API_VENDAS_URL", "http://api.vendas.com")
DB_CONNECTION = os.getenv("DB_CONNECTION", "sqlite:///vendas.db")
        '''
        
        if type(lib) != list:
            raise ValueError("Lib deve ser uma lista de strings")
        
        pipeline_name = name.lower().replace(" ", "_")
        
        # Usar BASE_DIR do Django (aponta para backend), parent vai para etl-manager
        etl_dir = Path(settings.BASE_DIR).parent / "etls" / pipeline_name 
        
        # Criar a pasta
        etl_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar arquivo config.py vazio
        script_path = etl_dir / "config.py"
        if not script_path.exists():
            script_path.touch()

        # escreve config padrão em config.py
        with script_path.open("w") as f:
            f.write(script_code)

        # criação de arquivo requeriments.txt vazio
        requirements_path = etl_dir / "requirements.txt"
        if not requirements_path.exists():
            requirements_path.touch()


            
        # adiciona texto ao arquivo requirements.txt
        with requirements_path.open("w") as f:
            for i in lib:
                f.write(f"{i}\n")
            
        # criação do registro no banco de dados
        return cls.objects.create(
            name=name,
            description=description,
            etl_name=f'etls/{pipeline_name}',
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

    @classmethod
    def pipeline_list(cls, user):
        if not user.is_authenticated:
            return cls.objects.none()

        return cls.objects.filter(
            Q(owner=user) |
            Q(pipelinepermission__user=user,
            pipelinepermission__permission="execute")
        ).distinct()

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
    
    #views para histórico de execução de uma pipe específica
    @classmethod
    def history(cls, pipeline_id, user):
        runs = cls.objects.filter(pipeline_id=pipeline_id, triggered_by=user).select_related("triggered_by")
        
        data = [
            {
                "id": run.id,
                "status": run.status,
                "triggered_by": run.triggered_by.username if run.triggered_by else None,
                "started_at": run.started_at,
                "finished_at": run.finished_at
            }
            for run in runs
        ]
        
        return data