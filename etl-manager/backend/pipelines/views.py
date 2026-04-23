from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
import json
from .models import Pipeline, PipelinePermission, PipelineRun, storage
from .tasks import execute_pipeline
from django.db.models import Count

# cria um serializer manual para os detalhes da pipeline, incluindo código main.py e lista de colaboradores
@extend_schema(
    operation_id='serialize_pipeline_details',
    description='Serializa os detalhes de uma pipeline',
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def serialize_pipeline_details(pipeline):
    permissions = PipelinePermission.objects.filter(
        pipeline=pipeline
    ).select_related("user")
    latest_run = (
        PipelineRun.objects.filter(pipeline=pipeline)
        .order_by("-created_at")
        .first()
    )

    collaborators = [
        {
            "id": permission.user.id,
            "username": permission.user.username,
            "permission": permission.permission,
        }
        for permission in permissions
        if permission.user_id != pipeline.owner_id
    ]

    pipeline_name = Pipeline.normalize_pipeline_storage_name(pipeline.etl_name)
    try:
        main_code = storage.get_script(pipeline_name, "main.py")
    except Exception:
        main_code = ""

    return {
        "id": pipeline.id,
        "name": pipeline.name,
        "description": pipeline.description,
        "owner": pipeline.owner.username,
        "etl_name": pipeline.etl_name,
        "created_at": pipeline.created_at,
        "status": latest_run.status if latest_run else "NOT_RUN",
        "collaborators": collaborators,
        "main_code": main_code,
    }

# Função auxiliar para parsear o campo de colaboradores enviado no corpo da requisição. Aceita uma string JSON ou uma lista de objetos. Retorna uma lista de dicionários com objetos User e permissão.
@extend_schema(
    operation_id='parse_collaborators_payload',
    description='Função auxiliar para parsear o campo de colaboradores enviado no corpo da requisição. Aceita uma string JSON ou uma lista de objetos. Retorna uma lista de dicionários com objetos User e permissão.',
    responses={200: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def parse_collaborators_payload(raw_collaborators):
    if raw_collaborators in (None, ""):
        return None

    if isinstance(raw_collaborators, str):
        try:
            raw_collaborators = json.loads(raw_collaborators)
        except json.JSONDecodeError:
            raise ValueError("Campo 'collaborators' deve ser um JSON valido")

    if not isinstance(raw_collaborators, list):
        raise ValueError("Campo 'collaborators' deve ser uma lista")

    collaborators = []
    for collaborator in raw_collaborators:
        if not isinstance(collaborator, dict):
            raise ValueError("Cada colaborador deve ser um objeto")

        username = collaborator.get("username")
        permission = collaborator.get("permission")

        if not username or not permission:
            raise ValueError("Cada colaborador precisa de 'username' e 'permission'")

        user = User.objects.filter(username=username).first()
        if user is None:
            raise ValueError(f"Usuario colaborador nao encontrado: {username}")

        collaborators.append(
            {
                "user": user,
                "permission": permission,
            }
        )

    return collaborators

#view para realizar login
@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    if request.method == "POST":
        username = request.data.get("username")
        password = request.data.get("password")
        
        if not username or not password:
            return Response(
                {"error": "Username e password são obrigatórios"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Autentica o usuário
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Obtém ou cria um token para o usuário
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "message": "Login bem-sucedido",
                    "token": token.key,
                    "username": user.username
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"error": "Credenciais inválidas"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    else:
        return Response(
            {"error": "Método não permitido"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

# View para obter informações do usuário autenticado (GET)
@extend_schema(
    operation_id='user_info',
    description='Obtém informações do usuário autenticado',
    responses={200: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def user_info(request):
    user = request.user
    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        },
        status=status.HTTP_200_OK
    )

# View para alterar senha (POST)
@extend_schema(
    operation_id='change_password',
    description='Altera a senha do usuário autenticado',
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def change_password(request):
    if request.method != "POST":
        return Response(
            {"error": "Método não permitido"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    current_password = request.data.get("current_password")
    new_password = request.data.get("new_password")
    
    if not current_password or not new_password:
        return Response(
            {"error": "Campos 'current_password' e 'new_password' são obrigatórios"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    
    # Verifica se a senha atual está correta
    if not user.check_password(current_password):
        return Response(
            {"error": "Senha atual está incorreta"},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Atualiza a senha
    user.set_password(new_password)
    user.save()
    
    return Response(
        {"message": "Senha alterada com sucesso"},
        status=status.HTTP_200_OK
    )

# View para criação de pipeline (POST)
@extend_schema(
    operation_id='create_pipeline',
    description='Cria uma nova pipeline ETL com código e dependências',
    request=OpenApiTypes.OBJECT,
    responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([TokenAuthentication])
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
        
        # Se não foi fornecido código, usar template padrão
        if not main_code.strip():
            main_code = '''import sys
import os
from datetime import datetime

if __name__ == "__main__":
    run_id = sys.argv[1] if len(sys.argv) > 1 else "local_test"
    
    print(f"[{datetime.now()}] Iniciando ETL: {os.path.basename(os.getcwd())} (Run ID: {run_id})")
    
    # TODO: Implemente sua lógica ETL aqui
    # Exemplo:
    # - Extrair dados de uma API
    # - Processar/transformar dados
    # - Salvar em banco de dados
    
    print(f"[{datetime.now()}] ETL concluída com sucesso!")
    print(f"Run ID: {run_id}")
'''
        
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
@authentication_classes([TokenAuthentication])
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def pipelines(request):
    try:
        pipes = Pipeline.pipeline_list(request.user)
        data = []
        
        for p in pipes:
            # Buscar última execução
            last_run = PipelineRun.objects.filter(pipeline=p).order_by('-created_at').first()
            
            pipeline_data = {
                "id": p.id,
                "name": p.name,
                "owner": p.owner.username
            }
            
            if last_run:
                pipeline_data["last_run"] = {
                    "status": last_run.status,
                    "started_at": last_run.started_at,
                    "finished_at": last_run.finished_at
                }
            
            data.append(pipeline_data)
        
        return Response({
            "pipelines": data,
            "current_user": request.user.username
        }, status=status.HTTP_200_OK)
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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_pipeline(request, pipeline_id):

    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not (pipeline.can_execute(request.user) or pipeline.can_edit(request.user)):
        return Response(
            {"error": "Usuário não tem permissão para acessar esta pipe"},
            status=status.HTTP_403_FORBIDDEN
        )

    return Response(serialize_pipeline_details(pipeline), status=status.HTTP_200_OK)

@extend_schema(
    operation_id='update_pipeline',
    description='Atualiza dados de uma pipeline existente, incluindo nome, status, descricao, colaboradores e codigo base',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline')
    ],
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["PUT", "PATCH"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_pipeline(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_edit(request.user):
        return Response(
            {"error": "Usuario nao tem permissao para editar esta pipe"},
            status=status.HTTP_403_FORBIDDEN
        )

    owner_username = request.data.get("owner")
    owner = None
    if owner_username is not None:
        owner = User.objects.filter(username=owner_username).first()
        if owner is None:
            return Response(
                {"error": f"Owner nao encontrado: {owner_username}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    try:
        collaborators = parse_collaborators_payload(request.data.get("collaborators"))
        script_file = request.FILES.get("script")
        main_code = request.data.get("main_code")

        if script_file is not None:
            if script_file.size > 5_000_000:
                return Response({"error": "Arquivo maior que 5MB"}, status=status.HTTP_400_BAD_REQUEST)
            main_code = script_file.read().decode("utf-8")

        next_status = request.data.get("status")
        if next_status is not None:
            next_status = str(next_status).upper()

        pipeline.update_pipeline(
            acting_user=request.user,
            name=request.data.get("name"),
            description=request.data.get("description"),
            owner=owner,
            status=next_status,
            collaborators=collaborators,
            main_code=main_code,
        )
    except UnicodeDecodeError:
        return Response(
            {"error": "Arquivo nao e UTF-8 valido"},
            status=status.HTTP_400_BAD_REQUEST
        )
    except PermissionError as error:
        return Response({"error": str(error)}, status=status.HTTP_403_FORBIDDEN)
    except ValueError as error:
        return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as error:
        return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)

    pipeline.refresh_from_db()
    return Response(serialize_pipeline_details(pipeline), status=status.HTTP_200_OK)

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
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def pipeline_history(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response(
            {"error": "Usuário não tem permissão para acessar esta pipe"},
            status=status.HTTP_403_FORBIDDEN
        )

    runs = PipelineRun.history(pipeline_id, request.user)
    return Response(
        {
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline.name,
            "runs": runs,
        },
        status=status.HTTP_200_OK,
    )
    # Se 'runs' já é uma lista/dict serializável, pode retornar direto

# Criação de User e autenticação básica (POST)
@extend_schema(
    operation_id='create_user',
    description='Cria um novo usuário na plataforma (apenas staff)',
    request=OpenApiTypes.OBJECT,
    responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
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

# Listagem de usuários (GET)
@extend_schema(
    operation_id='list_users',
    description='Lista usuários registrados na plataforma (autenticado). Usado para selecionar owners/colaboradores.',
    responses={200: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_users(request):
    # Permitir que qualquer usuário autenticado liste nomes de usuários
    # Retornamos apenas campos mínimos (id e username) para uso em seleção de colaboradores
    q = request.query_params.get("q")
    qs = User.objects.all()
    if q:
        qs = qs.filter(username__icontains=q)

    data = [{"id": u.id, "username": u.username} for u in qs.order_by("username")[:200]]
    return Response({"users": data}, status=status.HTTP_200_OK)

# Estatísticas resumidas das pipelines visíveis ao usuário (GET)
@extend_schema(
    operation_id='pipelines_stats',
    description='Retorna estatísticas resumidas das pipelines visíveis ao usuário',
    responses={200: OpenApiTypes.OBJECT, 401: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def pipelines_stats(request):
    user = request.user

    # Pipelines visíveis ao usuário
    visible_qs = Pipeline.pipeline_list(user)
    total_visible = visible_qs.count()

    # Quantas pipelines o usuário é owner
    owned_count = Pipeline.objects.filter(owner=user).count()

    # Quantas são compartilhadas (visíveis mas não owned)
    shared_count = visible_qs.exclude(owner=user).count()

    # Contagem por status da última execução
    status_counts = {"PENDING": 0, "RUNNING": 0, "SUCCESS": 0, "FAILED": 0, "NOT_RUN": 0}
    for p in visible_qs:
        last_run = PipelineRun.objects.filter(pipeline=p).order_by('-created_at').first()
        if last_run:
            st = last_run.status
        else:
            st = "NOT_RUN"

        status_counts[st] = status_counts.get(st, 0) + 1

    return Response(
        {
            "total_visible": total_visible,
            "owned_count": owned_count,
            "shared_count": shared_count,
            "status_counts": status_counts,
        },
        status=status.HTTP_200_OK,
    )

# View para deletar uma pipeline (POST ou DELETE)
@extend_schema(
    operation_id='delete_pipeline',
    description='Deleta uma pipeline. Apenas o owner pode deletar. É necessário confirmar o nome da pipeline no corpo da requisição usando o campo `confirm_name`. Aceita POST ou DELETE.',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline')
    ],
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["POST", "DELETE"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def pipeline_delete(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    # Apenas o owner pode deletar
    if pipeline.owner != request.user:
        return Response({"error": "Apenas o owner pode deletar esta pipeline"}, status=status.HTTP_403_FORBIDDEN)

    # Confirmação pelo nome
    confirm_name = None
    if request.method == "DELETE":
        # DELETE pode enviar body dependendo do cliente; DRF permite request.data
        confirm_name = request.data.get("confirm_name")
    else:
        confirm_name = request.data.get("confirm_name")

    if not confirm_name or str(confirm_name).strip() != pipeline.name:
        return Response({"error": "Confirmação inválida. Informe o nome exato da pipeline no campo 'confirm_name'."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pipeline.delete()
        return Response({"message": "Pipeline deletada com sucesso"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# metodo para ancorar uma pipelina em outra pipeline (POST)
@extend_schema(
    operation_id='link_pipeline',
    description='Linka uma pipeline a outra pipeline, permitindo que uma pipeline execute outra como sub-etapa. Aceita o ID da pipeline a ser linkada e o tipo de link (ex: "predecessor" ou "successor") no corpo da requisição.',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline que irá receber o link'),
    ],
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def link_pipeline(request, pipeline_id):
 
    pass