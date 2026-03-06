from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

from .models import Pipeline, PipelineRun
from .tasks import execute_pipeline


@api_view(["POST"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def trigger_pipeline(request, pipeline_id):
    if request.method != "POST":
        return JsonResponse({"error": "Metodo nao permitido"}, status=405)

    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response({"error": "Sem permissao"}, status=status.HTTP_403_FORBIDDEN)

    run = PipelineRun.objects.create(
        pipeline=pipeline,
        status=PipelineRun.Status.PENDING,
        triggered_by=request.user,
    )

    execute_pipeline.delay(run.id)

    return Response(
        {"run_id": run.id, "status": run.status},
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(["GET"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def pipelines(request):
    try:
        pipes = Pipeline.pipeline_list(request.user)
        data = [
            {
                "id": p.id,
                "name": p.name,
                "owner": p.owner.username,
            }
            for p in pipes
        ]
        return Response({"pipelines": data}, status=status.HTTP_200_OK)
    except Exception as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def get_pipeline(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response(
            {"error": "Usuario nao tem permissao para acessar esta pipe"},
            status=status.HTTP_403_FORBIDDEN,
        )

    data = {
        "id": pipeline.id,
        "name": pipeline.name,
        "description": pipeline.description,
        "owner": pipeline.owner.username,
    }
    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def pipeline_history(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response(
            {"error": "Usuario nao tem permissao para acessar esta pipe"},
            status=status.HTTP_403_FORBIDDEN,
        )

    runs = PipelineRun.history(pipeline_id, request.user)
    return Response({"pipeline_id": pipeline_id, "runs": runs}, status=status.HTTP_200_OK)
