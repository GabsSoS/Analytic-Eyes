from asyncio import run
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

from .models import Pipeline, PipelineRun
from .tasks import execute_pipeline


# View para execução de pipeline (POST)
@api_view(["POST"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def trigger_pipeline(request, pipeline_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response({"error": "Sem permissão"}, status=status.HTTP_403_FORBIDDEN)

    run = PipelineRun.objects.create(
        pipeline=pipeline,
        status="pending",
        triggered_by=request.user
    )

    # Dispara o worker (assíncrono)
    execute_pipeline.delay(run.id)

    # 202 Accepted porque o processamento é assíncrono
    return Response(
        {"run_id": run.id, "status": run.status},
        status=status.HTTP_202_ACCEPTED
    )


# Listagem de pipelines que o usuário tem permissão de executar (GET)
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
                "owner": p.owner.username
            }
            for p in pipes
        ]
        return Response({"pipelines": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Detalhes de uma pipeline específica (GET)
@api_view(["GET"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def get_pipeline(request, pipeline_id):

    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response(
            {"error": "Usuário não tem permissão para acessar esta pipe"},
            status=status.HTTP_403_FORBIDDEN
        )

    data = {
        "id": pipeline.id,
        "name": pipeline.name,
        "description": pipeline.description,
        "owner": pipeline.owner.username
    }
    return Response(data, status=status.HTTP_200_OK)


# Histórico de execuções de uma pipeline específica (GET)
@api_view(["GET"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def pipeline_history(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response(
            {"error": "Usuário não tem permissão para acessar esta pipe"},
            status=status.HTTP_403_FORBIDDEN
        )

    runs = PipelineRun.history(pipeline_id, request.user)
    # Se 'runs' já é uma lista/dict serializável, pode retornar direto
    return Response({f"Pipeline {pipeline_id}": runs}, status=status.HTTP_200_OK)