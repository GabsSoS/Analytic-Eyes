from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from .storage import LocalStorage, PipelineStorage
import time

# Inicializa o storage baseado na configuração
def get_storage():
    storage_type = getattr(settings, 'PIPELINE_STORAGE_TYPE', 'local')
    if storage_type == 'local':
        return LocalStorage()
    else:
        raise ValueError(f"Tipo de storage inválido: {storage_type}")

storage = get_storage()

class Pipeline(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    etl_name = models.CharField(
        max_length=255,
        help_text="Nome da ETL (pasta em /etls/)"
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    trigger_sources = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="trigger_targets",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @staticmethod
    def build_pipeline_name(name):
        return name.strip().lower().replace(" ", "_")

    @staticmethod
    def normalize_pipeline_storage_name(etl_name):
        normalized_name = str(etl_name or "").strip().replace("\\", "/")

        while normalized_name.startswith("/"):
            normalized_name = normalized_name[1:]

        if normalized_name.startswith("etls/"):
            normalized_name = normalized_name[len("etls/"):]

        return normalized_name.strip("/")
    
    def delete(self, *args, **kwargs):
        """Delete a pipeline e seus scripts"""
        pipeline_name = self.normalize_pipeline_storage_name(self.etl_name)
        try:
            storage.delete_pipeline(pipeline_name)
        except Exception as e:
            # Log do erro mas não impede a deleção do registro
            print(f"Erro ao deletar scripts da pipeline {pipeline_name}: {str(e)}")
        
        super().delete(*args, **kwargs)
    
    # Criação de Pipeline
    @classmethod
    def create_pipeline(
        cls,
        name,
        description,
        user,
        lib,
        main_code,
        trigger_sources=None,
    ):
        
        script_code = '''import os

API_VENDAS_URL = os.getenv("API_VENDAS_URL", "http://api.vendas.com")
DB_CONNECTION = os.getenv("DB_CONNECTION", "sqlite:///vendas.db")
'''
        if type(lib) != list:
            raise ValueError("Lib deve ser uma lista de strings")
        
        pipeline_name = cls.build_pipeline_name(name)
        
        try:
            # Salva main.py usando o storage
            storage.save_script(pipeline_name, "main.py", main_code)
            # Salva config.py usando o storage
            storage.save_script(pipeline_name, "config.py", script_code)
            
            # Salva requirements.txt usando o storage
            requirements_content = "\n".join(lib)
            storage.save_script(pipeline_name, "requirements.txt", requirements_content)
            
        except Exception as e:
            raise Exception(f"Erro ao salvar scripts da pipeline: {str(e)}")
            
        # Criação do registro no banco de dados
        pipeline = cls.objects.create(
            name=name,
            description=description,
            etl_name=f'etls/{pipeline_name}',
            owner=user
        )

        if trigger_sources is not None:
            pipeline.set_trigger_sources(trigger_sources)

        return pipeline

    def can_edit(self, user):
        if not user.is_authenticated:
            return False

        if self.owner == user:
            return True

        return PipelinePermission.objects.filter(
            pipeline=self,
            user=user,
            permission="edit"
        ).exists()

    def update_pipeline(
        self,
        *,
        acting_user,
        name=None,
        description=None,
        owner=None,
        status=None,
        collaborators=None,
        main_code=None,
        trigger_sources=None,
    ):
        if not self.can_edit(acting_user):
            raise PermissionError("Usuario nao tem permissao para editar esta pipe")

        if owner is not None and acting_user != self.owner:
            raise PermissionError("Apenas o owner pode alterar o proprietario da pipe")

        if collaborators is not None and acting_user != self.owner:
            raise PermissionError("Apenas o owner pode alterar os colaboradores da pipe")

        current_pipeline_name = self.normalize_pipeline_storage_name(self.etl_name)

        if name is not None:
            normalized_name = name.strip()
            if not normalized_name:
                raise ValueError("O nome da pipeline nao pode ser vazio")

            next_pipeline_name = self.build_pipeline_name(normalized_name)
            if next_pipeline_name != current_pipeline_name:
                storage.rename_pipeline(current_pipeline_name, next_pipeline_name)
                self.etl_name = f"etls/{next_pipeline_name}"
                current_pipeline_name = next_pipeline_name

            self.name = normalized_name

        if description is not None:
            self.description = description

        if owner is not None:
            self.owner = owner

        if main_code is not None:
            storage.save_script(current_pipeline_name, "main.py", main_code)

        self.save()

        if trigger_sources is not None:
            self.set_trigger_sources(trigger_sources)

        if collaborators is not None:
            allowed_permissions = {
                permission[0] for permission in PipelinePermission.PERMISSION_CHOICES
                if permission[0] != "owner"
            }
            desired_permissions = {}

            for collaborator in collaborators:
                user = collaborator["user"]
                permission = collaborator["permission"]

                if permission not in allowed_permissions:
                    raise ValueError(f"Permissao invalida para colaborador: {permission}")

                if user == self.owner:
                    continue

                desired_permissions[user.id] = {
                    "user": user,
                    "permission": permission,
                }

            existing_permissions = PipelinePermission.objects.filter(pipeline=self)

            for permission in existing_permissions:
                if permission.user_id not in desired_permissions:
                    permission.delete()

            for desired_permission in desired_permissions.values():
                PipelinePermission.objects.update_or_create(
                    pipeline=self,
                    user=desired_permission["user"],
                    defaults={"permission": desired_permission["permission"]},
                )

        if status is not None:
            valid_statuses = {choice[0] for choice in PipelineRun.Status.choices}
            if status not in valid_statuses:
                raise ValueError("Status invalido para atualizacao da pipeline")

            latest_run = (
                PipelineRun.objects.filter(pipeline=self)
                .order_by("-created_at")
                .first()
            )

            if latest_run is None:
                latest_run = PipelineRun.objects.create(
                    pipeline=self,
                    triggered_by=acting_user,
                    status=status,
                )

            latest_run.status = status
            if latest_run.started_at is None and status in {
                PipelineRun.Status.RUNNING,
                PipelineRun.Status.SUCCESS,
                PipelineRun.Status.FAILED,
            }:
                latest_run.started_at = timezone.now()

            if status in {PipelineRun.Status.SUCCESS, PipelineRun.Status.FAILED}:
                latest_run.finished_at = timezone.now()
            elif status in {PipelineRun.Status.PENDING, PipelineRun.Status.RUNNING}:
                latest_run.finished_at = None

            latest_run.save()

        return self

    def set_trigger_sources(self, source_pipelines):
        if source_pipelines is None:
            return

        normalized_sources = []
        seen_ids = set()

        for source_pipeline in source_pipelines:
            if source_pipeline.id in seen_ids:
                continue

            if source_pipeline.id == self.id:
                raise ValueError("Uma pipeline nao pode ser ancorada nela mesma")

            if self._would_create_trigger_cycle(source_pipeline):
                raise ValueError(
                    "A ancoragem cria um ciclo entre pipelines e nao pode ser salva"
                )

            normalized_sources.append(source_pipeline)
            seen_ids.add(source_pipeline.id)

        self.trigger_targets.set(normalized_sources)

    def _would_create_trigger_cycle(self, source_pipeline):
        pending_ids = [self.id]
        visited_ids = set()

        while pending_ids:
            pipeline_id = pending_ids.pop()
            if pipeline_id in visited_ids:
                continue

            visited_ids.add(pipeline_id)

            downstream_ids = list(
                Pipeline.objects.filter(trigger_targets__id=pipeline_id)
                .values_list("id", flat=True)
            )

            if source_pipeline.id in downstream_ids:
                return True

            pending_ids.extend(
                downstream_id
                for downstream_id in downstream_ids
                if downstream_id not in visited_ids
            )

        return False
    
    # Verifica se o usuário é owner ou se tem permição de edição ou execução
    def can_execute(self, user):

        # Verifica se o usuário esta logado
        if not user.is_authenticated:
            return False

        # Verifica se o usuário é dono da pipe
        if self.owner == user:
            return True

        # Verifica se o usuário mesmo não sendo dono da pipe tem permissão de execute ou edit
        return PipelinePermission.objects.filter(
            pipeline=self,
            user=user,
            permission__in=["execute", "edit"]
        ).exists()

    @classmethod
    def pipeline_list(cls, user):
        if not user.is_authenticated:
            return cls.objects.none()

        return cls.objects.filter(
            Q(owner=user) |
            Q(pipelinepermission__user=user,
            pipelinepermission__permission__in=["execute", "edit", "view"])
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

