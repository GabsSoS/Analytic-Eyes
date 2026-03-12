import docker
import logging
from celery import shared_task
from django.utils import timezone
from .models import PipelineRun

logger = logging.getLogger(__name__)

@shared_task
def execute_pipeline(run_id):
    """
    Executa a ETL em um container Docker isolado
    """
    try:
        run = PipelineRun.objects.get(id=run_id)
        run.status = "RUNNING"
        run.started_at = timezone.now()
        run.save()
        
        # PEGA O NOME DA ETL DO PIPELINE
        etl_name = run.pipeline.etl_name  # Ex: "etl_vendas"
        
        print(f"Iniciando Docker para ETL: {etl_name}")
        
        # Conecta ao Docker
        client = docker.from_env()
        
        # EXECUTA O CONTAINER
        try:
            logs = client.containers.run(
                image="etls:latest",  # Imagem que você vai fazer build
                command=[etl_name, str(run_id)],  # Args: etl_vendas 123
                environment={
                    "RUN_ID": str(run_id),
                    "DB_HOST": "postgres",
                    "REDIS_URL": "redis://redis:6379",
                },
                network="etl-manager_default",
                remove=True,  # Remove container após terminar
                timeout=3600  # 1 hora de timeout
            )
            
            # Converte bytes para string
            logs_text = logs.decode('utf-8') if isinstance(logs, bytes) else str(logs)
            
            run.log = logs_text
            run.status = "SUCCESS"
            run.finished_at = timezone.now()
            run.save()
            
            logger.info(f"Pipeline {run_id} executada com sucesso")
            
        except docker.errors.ContainerError as e:
            # Container retornou erro
            run.log = e.stderr.decode('utf-8') if e.stderr else str(e)
            run.status = "FAILED"
            run.finished_at = timezone.now()
            run.save()
            logger.error(f" Pipeline {run_id} falhou: {str(e)}")
            
    except PipelineRun.DoesNotExist:
        logger.error(f" PipelineRun {run_id} não encontrada")
    except Exception as e:
        logger.error(f" Erro ao executar pipeline: {str(e)}")
        if 'run' in locals():
            run.status = "FAILED"
            run.log = str(e)
            run.finished_at = timezone.now()
            run.save()