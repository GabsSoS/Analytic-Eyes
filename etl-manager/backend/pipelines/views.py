from django.http import HttpResponse
from .models import Pipeline
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

# View para execução de pipeline
def execute_pipeline(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id) # caso o pipe não exista, retorna 404

    try:
        run = pipeline.start_execution(request.user) # inicia a execução do pipe, passando o usuário logado para verificar permissões

        return JsonResponse({ 
            "pipeline_id": pipeline.id,
            "run_id": run.id,
            "status": run.status
        })# retorna o id do pipe, id da execução e status da execução

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=400
        )# retorna o erro caso haja algum problema, como falta de permissão ou pipe já em execução
#==================================================

# Listagem de pipes que o usuário tem permissão de executar
def list_pipes(request):
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
