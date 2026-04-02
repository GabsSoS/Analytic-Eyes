from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
import json

from .models import Pipeline, PipelineRun
from .tasks import execute_pipeline

#view para realizar login
def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = IsAuthenticated(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({"message": "Login bem-sucedido"}, status=200)
        else:
            return JsonResponse({"error": "Credenciais inválidas"}, status=400)
    else:
        return JsonResponse({"error": "Método não permitido"}, status=405)



# View para criação de pipeline (POST)
@extend_schema(
    operation_id='create_pipeline',
    description='Cria uma nova pipeline ETL com código e dependências',
    request=OpenApiTypes.OBJECT,
    responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def pipeline_create(request):
   
    if request.method != "POST":
        return JsonResponse({"error": "Método não permitido"}, status=405)
    
    name = request.data.get("name")
    description = request.data.get("description", "")
    
    # Parsear lib como JSON
    lib_str = request.data.get("lib", "[]")
    try:
        lib = json.loads(lib_str)  # Converte string JSON em lista
    except json.JSONDecodeError:
        return Response(
            {"error": "Campo 'lib' deve ser um JSON válido"},
            status=400
        )
    
    main_code = request.data.get("main_code", "")
    script_file = request.FILES.get("script")

    if not name:
        return JsonResponse({"error": "O campo 'name' é obrigatório"}, status=400)
    
    try:
        # Lê o arquivo e decodifica
        main_code = script_file.read().decode('utf-8') if script_file else main_code
        
        # Validação: arquivo muito grande?
        if script_file and script_file.size > 5_000_000:  # 5MB
            return Response(
                {"error": "Arquivo maior que 5MB"},
                status=400
            )
        
        # Cria a pipeline normalmente
        pipeline = Pipeline.create_pipeline(
            name=name,
            description=description,
            user=request.user,
            lib=lib,
            main_code=main_code
        )
        
        return Response(
            {"id": pipeline.id, "name": pipeline.name},
            status=status.HTTP_201_CREATED
        )
    
    except UnicodeDecodeError:
        return Response(
            {"error": "Arquivo não é UTF-8 válido"},
            status=400
        )
    except Exception as e:
        return Response({"error": str(e)}, status=400)
    
# View para execução de pipeline (POST)
@extend_schema(
    operation_id='trigger_pipeline',
    description='Dispara a execução de uma pipeline existente de forma assíncrona',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline')
    ],
    responses={202: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
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
@extend_schema(
    operation_id='list_pipelines',
    description='Lista todas as pipelines que o usuário autenticado tem permissão de executar',
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
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
                "owner": p.owner.username
            }
            for p in pipes
        ]
        return Response({"pipelines": data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Detalhes de uma pipeline específica (GET)
@extend_schema(
    operation_id='get_pipeline_details',
    description='Retorna os detalhes de uma pipeline específica se o usuário tiver permissão',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline')
    ],
    responses={200: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
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
        "owner": pipeline.owner.username,
        "etl_name": pipeline.etl_name
    }
    return Response(data, status=status.HTTP_200_OK)

# Histórico de execuções de uma pipeline específica (GET)
@extend_schema(
    operation_id='get_pipeline_history',
    description='Retorna o histórico de execuções de uma pipeline',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline')
    ],
    responses={200: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
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

# Criação de User e autenticação básica (POST)
@extend_schema(
    operation_id='create_user',
    description='Cria um novo usuário na plataforma (apenas staff)',
    request=OpenApiTypes.OBJECT,
    responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def create_user(request):
    
    # Apenas staff pode criar usuários
    if not request.user.is_staff:
        return Response(
            {"error": "Apenas usuários staff podem criar novos usuários"},
            status=status.HTTP_403_FORBIDDEN
        )

    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Campos 'username' e 'password' são obrigatórios"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Usuário já existe"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(username=username, password=password)
    return Response(
        {"message": "Usuário criado com sucesso", "username": user.username},
        status=status.HTTP_201_CREATED
    )