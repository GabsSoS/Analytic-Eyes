import docker
import logging
import os
import redis
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import Pipeline, PipelineRun

logger = logging.getLogger(__name__)


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

            # Caminho das ETLs no host
            etl_path = os.getenv("ETL_PATH", "/etls")

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
                "volumes": {etl_path: {"bind": "/etls", "mode": "rw"}},
                "network": "etl-manager_default",
                "remove": True,
            }

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
