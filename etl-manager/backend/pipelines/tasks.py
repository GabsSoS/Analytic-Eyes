from celery import shared_task
from .models import PipelineRun


@shared_task
def execute_pipeline(run_id):
    run = PipelineRun.objects.get(id=run_id)

    run.status = "running"
    run.save()

    # aqui depois vamos colocar docker
    run.status = "success"
    run.save()