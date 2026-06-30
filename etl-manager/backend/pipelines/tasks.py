import docker
import logging
import os
import redis
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from .models import Pipeline, PipelineRun, PipelineSchedule

logger = logging.getLogger(__name__)

# Tarefas de orquestração de pipelines: enfileira execuções, dispara execuções agendadas
# e coordena a execução dentro de containers isolados.


def _resolve_etl_docker_network(client):
    """Resolve a rede Docker utilizada pelos containers das ETLs.

    Prioriza a rede configurada por ambiente. Quando ela não existir, tenta
    descobrir a rede do container atual a partir do próprio worker/container.
    """
    configured_network = os.getenv("ETL_DOCKER_NETWORK", "").strip()
    if configured_network:
        try:
            client.networks.get(configured_network)
            return configured_network
        except docker.errors.NotFound:
            logger.warning(
                "Rede Docker configurada %s não encontrada; tentando descobrir rede do container atual",
                configured_network,
            )

    container_id = os.getenv("HOSTNAME", "").strip()
    if not container_id:
        return configured_network or "bridge"

    try:
        current_container = client.containers.get(container_id)
        networks = current_container.attrs.get("NetworkSettings", {}).get("Networks", {})
        if networks:
            network_name = next(iter(networks.keys()))
            logger.info("Usando rede Docker %s do container atual %s", network_name, container_id)
            return network_name
    except Exception as exc:
        logger.warning("Não foi possível identificar a rede do container atual %s: %s", container_id, exc)

    return configured_network or "bridge"


def queue_pipeline_execution(pipeline, triggered_by):
    # Evita disparar uma nova execução se já existe uma pipeline pendente ou em execução
    if PipelineRun.objects.filter(
        pipeline=pipeline,
        status__in=[PipelineRun.Status.PENDING, PipelineRun.Status.RUNNING],
    ).exists():
        logger.info(
            "Pipeline %s ja possui execucao pendente ou em andamento; disparo ignorado",
            pipeline.id,
        )
        return None

    run = PipelineRun.objects.create(
        pipeline=pipeline,
        status=PipelineRun.Status.PENDING,
        triggered_by=triggered_by,
    )
    execute_pipeline.delay(run.id)
    return run


def _resolve_anchored_trigger_user(source_run, target_pipeline):
    # Mantém o usuário original sempre que ele tiver permissão para a pipeline ancorada.
    trigger_user = source_run.triggered_by
    if trigger_user and target_pipeline.can_execute(trigger_user):
        return trigger_user
    return target_pipeline.owner


def trigger_anchored_pipelines(source_run):
    source_pipeline = source_run.pipeline

    for target_pipeline in source_pipeline.trigger_sources.all():
        try:
            trigger_user = _resolve_anchored_trigger_user(source_run, target_pipeline)
            queued_run = queue_pipeline_execution(target_pipeline, trigger_user)

            if queued_run is None:
                continue

            logger.info(
                "Pipeline %s ancorada em %s disparada automaticamente (run %s)",
                target_pipeline.id,
                source_pipeline.id,
                queued_run.id,
            )
        except Exception:
            logger.exception(
                "Erro ao disparar pipeline ancorada %s a partir da pipeline %s",
                target_pipeline.id,
                source_pipeline.id,
            )


@shared_task
def dispatch_due_schedules():
    redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url)
    scheduler_lock = redis_client.lock(
        "pipeline-schedule-dispatch-lock",
        blocking_timeout=1,
        timeout=55,
    )

    acquired = scheduler_lock.acquire(blocking=False)
    if not acquired:
        logger.info("Despacho de schedules ignorado porque outra execucao do beat ja esta em andamento")
        return 0

    dispatched_count = 0

    try:
        now = timezone.now()
        due_schedule_ids = list(
            PipelineSchedule.objects.filter(
                enabled=True,
                next_run_at__isnull=False,
                next_run_at__lte=now,
            ).values_list("id", flat=True)
        )

        for schedule_id in due_schedule_ids:
            with transaction.atomic():
                schedule = (
                    PipelineSchedule.objects.select_related("pipeline", "created_by", "pipeline__owner")
                    .filter(id=schedule_id)
                    .first()
                )

                if (
                    schedule is None
                    or not schedule.enabled
                    or schedule.next_run_at is None
                    or schedule.next_run_at > timezone.now()
                ):
                    continue

                trigger_time = timezone.now()
                schedule.mark_triggered(trigger_time=trigger_time)

                triggered_by = schedule.created_by or schedule.pipeline.owner
                queue_pipeline_execution(schedule.pipeline, triggered_by)
                dispatched_count += 1

        return dispatched_count
    finally:
        try:
            scheduler_lock.release()
        except Exception:
            logger.exception("Erro liberando lock do scheduler de pipelines")


@shared_task(
    bind=True,
    acks_late=True,
    soft_time_limit=3600,
    time_limit=3700,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def execute_pipeline(self, run_id):
    """Executa a ETL em um container Docker isolado com proteção de lock Redis

    - evita execução concorrente da MESMA pipeline usando um lock Redis
    - aplica timeouts e retry automático para maior robustez
    - passa limites de recursos para o container se configurados via ENV
    """
    try:
        run = PipelineRun.objects.get(id=run_id)

        # Normaliza nome da ETL (usado também como chave do lock)
        etl_name = Pipeline.normalize_pipeline_storage_name(run.pipeline.etl_name)

        # Conecta ao Redis (usa o mesmo broker do Celery)
        redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url)

        lock_name = f"pipeline-lock:{etl_name}"
        lock = redis_client.lock(lock_name, blocking_timeout=5, timeout=3600)

        # Tenta adquirir lock; se não conseguir, re-tenta conforme política de retry
        acquired = lock.acquire(blocking=False)
        if not acquired:
            logger.warning(f"Pipeline {etl_name} já em execução — adiando run {run_id}")
            raise Exception("Pipeline already running")

        try:
            # Marca como RUNNING só após garantir o lock
            run.status = "RUNNING"
            run.started_at = timezone.now()
            run.save()

            # Conecta ao Docker
            client = docker.from_env()

            # Reaproveita o mesmo volume /etls montado no worker sempre que possivel,
            # evitando rebuild da imagem etls:latest a cada nova pipeline.
            etl_host_path = os.getenv("ETL_HOST_PATH", "").strip()
            current_container = os.getenv("HOSTNAME", "").strip()
            etl_network = _resolve_etl_docker_network(client)

            # Limites de recursos (opcionais via ENV)
            mem_limit = os.getenv("ETL_CONTAINER_MEM_LIMIT", None)
            cpuset_cpus = os.getenv("ETL_CONTAINER_CPUSET", None)

            run_kwargs = {
                "image": "etls:latest",
                "command": [etl_name, str(run_id)],
                "environment": {
                    "RUN_ID": str(run_id),
                    "DB_HOST": "postgres",
                    "REDIS_URL": redis_url,
                },
                "network": etl_network,
                "remove": True,
            }

            if etl_host_path:
                run_kwargs["volumes"] = {
                    etl_host_path: {"bind": "/etls", "mode": "rw"}
                }
            elif current_container:
                run_kwargs["volumes_from"] = [current_container]

            if mem_limit:
                run_kwargs["mem_limit"] = mem_limit
            if cpuset_cpus:
                run_kwargs["cpuset_cpus"] = cpuset_cpus

            # Executa container e coleta logs (bloco principal da execução)
            try:
                logs = client.containers.run(**run_kwargs)
                logs_text = logs.decode("utf-8") if isinstance(logs, bytes) else str(logs)

                run.log = logs_text
                run.status = "SUCCESS"
                run.finished_at = timezone.now()
                run.save()

                trigger_anchored_pipelines(run)

                logger.info(f"Pipeline {run_id} executada com sucesso")

            except docker.errors.ContainerError as e:
                run.log = e.stderr.decode("utf-8") if e.stderr else str(e)
                run.status = "FAILED"
                run.finished_at = timezone.now()
                run.save()
                logger.error(f"Pipeline {run_id} falhou: {str(e)}")
                raise

        finally:
            try:
                lock.release()
            except Exception:
                logger.exception(f"Erro liberando lock Redis para {lock_name}")

    except PipelineRun.DoesNotExist:
        logger.error(f"PipelineRun {run_id} não encontrada")
    except Exception as e:
        logger.error(f"Erro ao executar pipeline: {str(e)}")
        if "run" in locals():
            run.status = "FAILED"
            run.log = str(e)
            run.finished_at = timezone.now()
            run.save()
        raise
