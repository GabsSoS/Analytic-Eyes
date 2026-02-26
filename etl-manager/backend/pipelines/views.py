from django.http import HttpResponse
from .models import Pipeline
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

def execute_pipeline(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    try:
        run = pipeline.start_execution(request.user)

        return JsonResponse({
            "pipeline_id": pipeline.id,
            "run_id": run.id,
            "status": run.status
        })

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=400
        )