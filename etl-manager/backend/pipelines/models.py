from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from .storage import LocalStorage, PipelineStorage
from zoneinfo import ZoneInfo
from datetime import timedelta, timezone as dt_timezone
import time

# Inicializa o storage baseado na configuração
def get_storage():
    storage_type = getattr(settings, 'PIPELINE_STORAGE_TYPE', 'local')
    if storage_type == 'local':
        return LocalStorage()
    else:
        raise ValueError(f"Tipo de storage inválido: {storage_type}")

storage = get_storage()


SCHEDULE_WEEKDAY_CHOICES = (
    (0, "Segunda-feira"),
    (1, "Terca-feira"),
    (2, "Quarta-feira"),
    (3, "Quinta-feira"),
    (4, "Sexta-feira"),
    (5, "Sabado"),
    (6, "Domingo"),
)

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
        env_content=None,
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
            
            # Salva .env se fornecido
            if env_content:
                storage.save_env_file(pipeline_name, env_content)
            
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
        schedule=None,
        env_content=None,
    ):
        if not self.can_edit(acting_user):
            raise PermissionError("Usuario nao tem permissao para editar esta pipe")

        if owner is not None and acting_user != self.owner:
            raise PermissionError("Apenas o owner pode alterar o proprietario da pipe")

        if collaborators is not None and acting_user != self.owner:
            raise PermissionError("Apenas o owner pode alterar os colaboradores da pipe")

        if schedule is not None and acting_user != self.owner:
            raise PermissionError("Apenas o owner pode alterar o agendamento da pipe")

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

        if env_content is not None:
            storage.save_env_file(current_pipeline_name, env_content)

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

        if schedule is not None:
            PipelineSchedule.upsert_for_pipeline(
                pipeline=self,
                created_by=acting_user,
                **schedule,
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


class PipelineSchedule(models.Model):
    pipeline = models.OneToOneField(
        Pipeline,
        on_delete=models.CASCADE,
        related_name="schedule",
    )
    enabled = models.BooleanField(default=False)
    days_of_week = models.JSONField(default=list, blank=True)
    hour = models.PositiveSmallIntegerField(default=0)
    minute = models.PositiveSmallIntegerField(default=0)
    timezone_name = models.CharField(
        max_length=64,
        default=getattr(settings, "TIME_ZONE", "America/Sao_Paulo"),
    )
    next_run_at = models.DateTimeField(null=True, blank=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_pipeline_schedules",
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("pipeline_id",)

    def __str__(self):
        return f"Schedule {self.pipeline_id} - {'enabled' if self.enabled else 'disabled'}"

    @staticmethod
    def normalize_days_of_week(days_of_week):
        if days_of_week is None:
            return []

        if not isinstance(days_of_week, list):
            raise ValueError("Campo 'days_of_week' deve ser uma lista")

        normalized_days = []
        seen_days = set()

        for raw_day in days_of_week:
            try:
                day = int(raw_day)
            except (TypeError, ValueError):
                raise ValueError("Cada item de 'days_of_week' deve ser um inteiro")

            if day < 0 or day > 6:
                raise ValueError("Os dias de 'days_of_week' devem estar entre 0 e 6")

            if day in seen_days:
                continue

            seen_days.add(day)
            normalized_days.append(day)

        return sorted(normalized_days)

    @classmethod
    def default_timezone_name(cls):
        return getattr(settings, "TIME_ZONE", "America/Sao_Paulo")

    @classmethod
    def validate_timezone_name(cls, timezone_name):
        try:
            ZoneInfo(timezone_name)
        except Exception as exc:
            raise ValueError("Timezone invalida para o agendamento") from exc
        return timezone_name

    @classmethod
    def compute_next_run_at(cls, *, days_of_week, hour, minute, timezone_name, reference_time=None):
        normalized_days = cls.normalize_days_of_week(days_of_week)

        if not normalized_days:
            return None

        if hour is None or int(hour) < 0 or int(hour) > 23:
            raise ValueError("Campo 'hour' deve estar entre 0 e 23")

        if minute is None or int(minute) < 0 or int(minute) > 59:
            raise ValueError("Campo 'minute' deve estar entre 0 e 59")

        tz = ZoneInfo(cls.validate_timezone_name(timezone_name))
        base_time = reference_time or timezone.now()

        if timezone.is_naive(base_time):
            base_time = timezone.make_aware(base_time, timezone.get_current_timezone())

        local_reference = timezone.localtime(base_time, tz)

        for day_offset in range(0, 8):
            candidate_date = local_reference.date() + timedelta(days=day_offset)
            if candidate_date.weekday() not in normalized_days:
                continue

            candidate_local = local_reference.replace(
                year=candidate_date.year,
                month=candidate_date.month,
                day=candidate_date.day,
                hour=int(hour),
                minute=int(minute),
                second=0,
                microsecond=0,
            )

            if candidate_local <= local_reference:
                continue

            return candidate_local.astimezone(dt_timezone.utc)

        raise ValueError("Nao foi possivel calcular a proxima execucao do agendamento")

    def clean(self):
        self.days_of_week = self.normalize_days_of_week(self.days_of_week)

        if self.hour < 0 or self.hour > 23:
            raise ValidationError({"hour": "O horario deve estar entre 0 e 23"})

        if self.minute < 0 or self.minute > 59:
            raise ValidationError({"minute": "O minuto deve estar entre 0 e 59"})

        self.timezone_name = self.validate_timezone_name(self.timezone_name)

        if self.enabled and not self.days_of_week:
            raise ValidationError({"days_of_week": "Selecione ao menos um dia para o agendamento"})

    def save(self, *args, **kwargs):
        reference_time = kwargs.pop("reference_time", None)
        self.full_clean()

        if self.enabled:
            self.next_run_at = self.compute_next_run_at(
                days_of_week=self.days_of_week,
                hour=self.hour,
                minute=self.minute,
                timezone_name=self.timezone_name,
                reference_time=reference_time or timezone.now(),
            )
        else:
            self.next_run_at = None

        super().save(*args, **kwargs)

    def mark_triggered(self, trigger_time=None):
        trigger_time = trigger_time or timezone.now()
        self.last_triggered_at = trigger_time
        self.save(
            update_fields=["last_triggered_at", "next_run_at", "updated_at"],
            reference_time=trigger_time,
        )

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "days_of_week": self.days_of_week,
            "hour": self.hour,
            "minute": self.minute,
            "timezone": self.timezone_name,
            "next_run_at": self.next_run_at,
            "last_triggered_at": self.last_triggered_at,
        }

    @classmethod
    def upsert_for_pipeline(
        cls,
        *,
        pipeline,
        created_by,
        enabled,
        days_of_week,
        hour,
        minute,
        timezone_name=None,
    ):
        schedule, _ = cls.objects.get_or_create(
            pipeline=pipeline,
            defaults={"created_by": created_by},
        )

        if schedule.created_by is None:
            schedule.created_by = created_by

        schedule.enabled = bool(enabled)
        schedule.days_of_week = cls.normalize_days_of_week(days_of_week)
        schedule.hour = int(hour)
        schedule.minute = int(minute)
        schedule.timezone_name = timezone_name or schedule.timezone_name or cls.default_timezone_name()
        schedule.save()
        return schedule

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
