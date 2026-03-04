from asyncio import run
from django.http import HttpResponse
from .models import Pipeline, PipelineRun, PipelinePermission
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .tasks import execute_pipeline



# View para execução de pipeline

def trigger_pipeline(request, pipeline_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)

    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return JsonResponse({"error": "Sem permissão"}, status=403)

    run = PipelineRun.objects.create(
        pipeline=pipeline,
        status="pending",
        triggered_by=request.user
    )

    execute_pipeline.delay(run.id)  # AQUI dispara o worker

    return JsonResponse({
        "run_id": run.id,
        "status": run.status
    })
#==================================================

# Listagem de pipes que o usuário tem permissão de executar
def pipelines(request):
    try:
        pipes = Pipeline.pipeline_list(request.user) # chama o método pipeline_list para obter as pipes que o usuário tem permissão de executar

        data = [
                    {
                        "id": p.id,
                        "name": p.name,
                        "owner": p.owner.username
                    }
                    for p in pipes
                ]

        return JsonResponse({"pipelines": data}) # retorna a lista de pipes em formato JSON, contendo id, nome e dono de cada pipe

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400) # retorna o erro caso haja algum problema, como usuário não autenticado
#==================================================

# detalhes de uma pipe específica
def get_pipeline(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id) # caso o pipe não exista, retorna 404

    if not pipeline.can_execute(request.user): # verifica se o usuário tem permissão de execução
        return JsonResponse({"error": "Usuário não tem permissão para acessar esta pipe"}, status=403) # retorna erro de permissão caso o usuário não tenha acesso

    data = {
        "id": pipeline.id,
        "name": pipeline.name,
        "description": pipeline.description,
        "owner": pipeline.owner.username
    }

    return JsonResponse(data) # retorna os detalhes da pipe em formato JSON
#==================================================

#view para histórico de execuções de uma pipe especifica
def pipeline_history(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id) # caso o pipe não exista, retorna 404

    if not pipeline.can_execute(request.user): # verifica se o usuário tem permissão de execução
        return JsonResponse({"error": "Usuário não tem permissão para acessar esta pipe"}, status=403) # retorna erro de permissão caso o usuário não tenha acesso

    runs = PipelineRun.history(pipeline_id, request.user) # chama o método history para obter as execuções da pipe

    return JsonResponse({f"Pipeline {pipeline_id}": runs}) # retorna a lista de execuções em formato JSON, contendo id da execução, status, usuário que iniciou, data de início e data de término
#==================================================

