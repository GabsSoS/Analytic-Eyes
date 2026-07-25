from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes, throttle_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.http import JsonResponse, HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
import json
import mimetypes
from .models import Pipeline, PipelinePermission, PipelineRun, PipelineSchedule, get_storage
from .tasks import queue_pipeline_execution
from django.db.models import Count, OuterRef, Subquery
from .throttling import LoginRateThrottle

# cria um serializer manual para os detalhes da pipeline, incluindo código main.py e lista de colaboradores
# Esta função monta a resposta usada nas telas de detalhes e edição de pipeline
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

    trigger_sources = [
        {
            "id": source.id,
            "name": source.name,
        }
        for source in pipeline.trigger_targets.all().order_by("name")
    ]

    trigger_targets = [
        {
            "id": target.id,
            "name": target.name,
        }
        for target in pipeline.trigger_sources.all().order_by("name")
    ]

    pipeline_name = Pipeline.normalize_pipeline_storage_name(pipeline.etl_name)
    try:
        main_code = get_storage().get_script(pipeline_name, "main.py")
    except Exception:
        # Permite pipelines sem main.py para evitar falha na serialização
        main_code = ""

    env_exists = get_storage().env_file_exists(pipeline_name)
    config_exists = get_storage().config_file_exists(pipeline_name)
    input_file_name = get_storage().get_input_file_name(pipeline_name)
    output_file_name = get_storage().get_output_file_name(pipeline_name)

    schedule = getattr(pipeline, "schedule", None)

    return {
        "id": pipeline.id,
        "name": pipeline.name,
        "description": pipeline.description,
        "owner": pipeline.owner.username,
        "etl_name": pipeline.etl_name,
        "created_at": pipeline.created_at,
        "status": latest_run.status if latest_run else "NOT_RUN",
        "collaborators": collaborators,
        "trigger_sources": trigger_sources,
        "trigger_targets": trigger_targets,
        "main_code": main_code,
        "env_exists": env_exists,
        "input_file_name": input_file_name,
        "input_file_exists": input_file_name is not None,
        "output_file_name": output_file_name,
        "output_file_exists": output_file_name is not None,
        "schedule": schedule.to_dict() if schedule else {
            "enabled": False,
            "days_of_week": [],
            "hour": 0,
            "minute": 0,
            "timezone": PipelineSchedule.default_timezone_name(),
            "next_run_at": None,
            "last_triggered_at": None,
        },
    }

# Função auxiliar para parsear o campo de colaboradores enviado no corpo da requisição. Aceita uma string JSON ou uma lista de objetos. Retorna uma lista de dicionários com objetos User e permissão.
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


def _decode_uploaded_text_file(uploaded_file, expected_extensions, form_field_name):
    if uploaded_file is None:
        return None

    filename = uploaded_file.name.lower()
    if not any(filename.endswith(ext) for ext in expected_extensions):
        raise ValueError(
            f"Arquivo '{form_field_name}' deve ser um dos tipos: {', '.join(expected_extensions)}"
        )

    # Decodifica o conteúdo do arquivo enviado como texto UTF-8
    return uploaded_file.read().decode('utf-8')


# Extensoes aceitas para o arquivo de dados processado pelo script
INPUT_FILE_ALLOWED_EXTENSIONS = [".xlsx", ".xls", ".csv", ".json"]
INPUT_FILE_MAX_SIZE = 100_000_000  # 100MB


def _read_uploaded_binary_file(uploaded_file, expected_extensions, form_field_name):
    """Valida a extensao e le o conteudo binario de um arquivo enviado, sem
    tentar decodificar como texto (planilhas .xlsx/.xls sao arquivos binarios)"""
    if uploaded_file is None:
        return None

    filename = uploaded_file.name.lower()
    if not any(filename.endswith(ext) for ext in expected_extensions):
        raise ValueError(
            f"Arquivo '{form_field_name}' deve ser um dos tipos: {', '.join(expected_extensions)}"
        )

    return uploaded_file.read()


def parse_trigger_sources_payload(raw_pipeline_ids, user, current_pipeline=None):
    if raw_pipeline_ids in (None, ""):
        return None

    if isinstance(raw_pipeline_ids, str):
        try:
            raw_pipeline_ids = json.loads(raw_pipeline_ids)
        except json.JSONDecodeError:
            raise ValueError("Campo 'anchor_pipeline_ids' deve ser um JSON valido")

    if not isinstance(raw_pipeline_ids, list):
        raise ValueError("Campo 'anchor_pipeline_ids' deve ser uma lista")

    normalized_ids = []
    seen_ids = set()

    for pipeline_id in raw_pipeline_ids:
        try:
            normalized_id = int(pipeline_id)
        except (TypeError, ValueError):
            raise ValueError("Cada item de 'anchor_pipeline_ids' deve ser um inteiro")

        if current_pipeline is not None and normalized_id == current_pipeline.id:
            raise ValueError("Uma pipeline nao pode ser ancorada nela mesma")

        if normalized_id in seen_ids:
            continue

        seen_ids.add(normalized_id)
        normalized_ids.append(normalized_id)

    visible_pipelines = Pipeline.pipeline_list(user).filter(id__in=normalized_ids)
    pipelines_by_id = {pipeline.id: pipeline for pipeline in visible_pipelines}

    missing_ids = [
        pipeline_id for pipeline_id in normalized_ids
        if pipeline_id not in pipelines_by_id
    ]

    if missing_ids:
        raise ValueError(
            f"Pipelines de ancoragem nao encontradas ou sem acesso: {missing_ids}"
        )

    return [pipelines_by_id[pipeline_id] for pipeline_id in normalized_ids]


def parse_schedule_payload(raw_schedule):
    if raw_schedule in (None, ""):
        return None

    if isinstance(raw_schedule, str):
        try:
            raw_schedule = json.loads(raw_schedule)
        except json.JSONDecodeError:
            raise ValueError("Campo 'schedule' deve ser um JSON valido")

    if not isinstance(raw_schedule, dict):
        raise ValueError("Campo 'schedule' deve ser um objeto")

    enabled = bool(raw_schedule.get("enabled", False))
    days_of_week = PipelineSchedule.normalize_days_of_week(
        raw_schedule.get("days_of_week", [])
    )

    hour = raw_schedule.get("hour", 0)
    minute = raw_schedule.get("minute", 0)

    try:
        hour = int(hour)
    except (TypeError, ValueError):
        raise ValueError("Campo 'hour' deve ser um inteiro")

    try:
        minute = int(minute)
    except (TypeError, ValueError):
        raise ValueError("Campo 'minute' deve ser um inteiro")

    timezone_name = raw_schedule.get("timezone") or PipelineSchedule.default_timezone_name()
    PipelineSchedule.validate_timezone_name(timezone_name)

    if enabled and not days_of_week:
        raise ValueError("Selecione ao menos um dia para ativar o agendamento")

    if hour < 0 or hour > 23:
        raise ValueError("Campo 'hour' deve estar entre 0 e 23")

    if minute < 0 or minute > 59:
        raise ValueError("Campo 'minute' deve estar entre 0 e 59")

    return {
        "enabled": enabled,
        "days_of_week": days_of_week,
        "hour": hour,
        "minute": minute,
        "timezone_name": timezone_name,
    }

#view para realizar login
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
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
            Token.objects.filter(user=user).delete()
            token = Token.objects.create(user=user)
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
    
    # Atualiza a senha e invalida token atual
    user.set_password(new_password)
    user.save()
    Token.objects.filter(user=user).delete()

    return Response(
        {"message": "Senha alterada com sucesso. Faça login novamente."},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    request.auth.delete()
    return Response({"message": "Logout realizado com sucesso."}, status=status.HTTP_200_OK)

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
    env_file = request.FILES.get("env")
    config_file = request.FILES.get("config")
    trigger_sources = None
    schedule = None

    if not name:
        return JsonResponse({"error": "O campo 'name' é obrigatório"}, status=400)
    
    try:
        # Lê o arquivo script e decodifica
        main_code = script_file.read().decode('utf-8') if script_file else main_code
        
        # Lê os arquivos de configuração e decodifica apenas os formatos aceitos
        env_content = None
        config_content = None
        if env_file:
            env_content = _decode_uploaded_text_file(env_file, [".env"], "env")

        if config_file:
            config_content = _decode_uploaded_text_file(config_file, [".ini"], "config")
        
        trigger_sources = parse_trigger_sources_payload(
            request.data.get("anchor_pipeline_ids"),
            request.user,
        )
        schedule = parse_schedule_payload(request.data.get("schedule"))
        
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
        
        if env_file and env_file.size > 1_000_000:  # 1MB
            return Response(
                {"error": "Arquivo .env maior que 1MB"},
                status=400
            )

        if config_file and config_file.size > 1_000_000:  # 1MB
            return Response(
                {"error": "Arquivo config.ini maior que 1MB"},
                status=400
            )
        
        # Cria a pipeline normalmente
        pipeline = Pipeline.create_pipeline(
            name=name,
            description=description,
            user=request.user,
            lib=lib,
            main_code=main_code,
            trigger_sources=trigger_sources,
            env_content=env_content,
            config_content=config_content,
        )

        if schedule is not None:
            PipelineSchedule.upsert_for_pipeline(
                pipeline=pipeline,
                created_by=request.user,
                **schedule,
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

    # Enfileira a execução para o worker processar em segundo plano
    run = queue_pipeline_execution(pipeline, request.user)
    if run is None:
        return Response(
            {"error": "Pipeline ja possui uma execucao pendente ou em andamento"},
            status=status.HTTP_409_CONFLICT,
        )

    # Dispara o worker (assíncrono)

    # 202 Accepted porque o processamento é agendado e não finalizado na requisição
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
        
        pipes = list(pipes.select_related('owner'))
        pipeline_ids = [p.id for p in pipes]

        latest_run_id_sq = PipelineRun.objects.filter(
            pipeline=OuterRef('pk')
        ).order_by('-created_at').values('id')[:1]

        runs_map = {
            r['pipeline_id']: r
            for r in PipelineRun.objects.filter(
                id__in=Pipeline.objects.filter(id__in=pipeline_ids)
                .annotate(lr=Subquery(latest_run_id_sq))
                .values_list('lr', flat=True)
            ).values('pipeline_id', 'status', 'started_at', 'finished_at')
        }

        for p in pipes:
            pipeline_data = {
                "id": p.id,
                "name": p.name,
                "owner": p.owner.username
            }
            last_run = runs_map.get(p.id)
            if last_run:
                pipeline_data["last_run"] = {
                    "status": last_run["status"],
                    "started_at": last_run["started_at"],
                    "finished_at": last_run["finished_at"]
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
        trigger_sources = parse_trigger_sources_payload(
            request.data.get("anchor_pipeline_ids"),
            request.user,
            current_pipeline=pipeline,
        )
        schedule = parse_schedule_payload(request.data.get("schedule"))
        script_file = request.FILES.get("script")
        env_file = request.FILES.get("env")
        config_file = request.FILES.get("config")
        main_code = request.data.get("main_code")

        if script_file is not None:
            if script_file.size > 5_000_000:
                return Response({"error": "Arquivo maior que 5MB"}, status=status.HTTP_400_BAD_REQUEST)
            main_code = script_file.read().decode("utf-8")

        env_content = None
        config_content = None
        if env_file is not None:
            if env_file.size > 1_000_000:
                return Response({"error": "Arquivo .env maior que 1MB"}, status=status.HTTP_400_BAD_REQUEST)
            env_content = _decode_uploaded_text_file(env_file, [".env"], "env")

        if config_file is not None:
            if config_file.size > 1_000_000:
                return Response({"error": "Arquivo config.ini maior que 1MB"}, status=status.HTTP_400_BAD_REQUEST)
            config_content = _decode_uploaded_text_file(config_file, [".ini"], "config")

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
            trigger_sources=trigger_sources,
            schedule=schedule,
            env_content=env_content,
            config_content=config_content,
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
    is_staff = bool(request.data.get("is_staff", False))

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

    user = User.objects.create_user(username=username, password=password, is_staff=is_staff)
    return Response(
        {"message": "Usuário criado com sucesso", "username": user.username, "is_staff": user.is_staff},
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

    # Staff ve campos extras (is_staff/is_active) pra tela de gerenciamento
    # de usuarios; demais usuarios continuam recebendo so id/username
    # (usado pra selecionar colaboradores em pipelines).
    if request.user.is_staff:
        data = [
            {
                "id": u.id,
                "username": u.username,
                "is_staff": u.is_staff,
                "is_active": u.is_active,
            }
            for u in qs.order_by("username")[:200]
        ]
    else:
        data = [{"id": u.id, "username": u.username} for u in qs.order_by("username")[:200]]

    return Response({"users": data}, status=status.HTTP_200_OK)


# Promove/remove um usuário de administrador (staff) (POST)
@extend_schema(
    operation_id='toggle_user_staff',
    description='Alterna o status de administrador (is_staff) de um usuário. Apenas staff pode chamar. Remover o admin de outro admin exige superusuário. Bloqueia remover o último administrador do sistema.',
    parameters=[
        OpenApiParameter(name='user_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID do usuário')
    ],
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def toggle_user_staff(request, user_id):
    if not request.user.is_staff:
        return Response(
            {"error": "Apenas usuários administradores podem alterar permissões de administrador"},
            status=status.HTTP_403_FORBIDDEN
        )

    target = get_object_or_404(User, id=user_id)

    # So um superusuario pode mexer no status de admin de OUTRO admin -
    # sem isso, qualquer staff conseguiria remover o superusuario real
    # (basta existir um segundo staff pra burlar a checagem de "ultimo
    # admin" abaixo). Promover um usuario comum a admin continua livre
    # pra qualquer staff (e o proprio usuario pode se autodemover).
    if target.is_staff and target.id != request.user.id and not request.user.is_superuser:
        return Response(
            {"error": "Apenas um superusuário pode remover o acesso de outro administrador"},
            status=status.HTTP_403_FORBIDDEN
        )

    if target.is_staff and User.objects.filter(is_staff=True).count() <= 1:
        return Response(
            {"error": "Não é possível remover o último administrador do sistema"},
            status=status.HTTP_400_BAD_REQUEST
        )

    target.is_staff = not target.is_staff
    target.save(update_fields=["is_staff"])

    return Response(
        {"id": target.id, "username": target.username, "is_staff": target.is_staff},
        status=status.HTTP_200_OK
    )


# Ativa/desativa a conta de um usuário (POST) - usado como "excluir conta":
# desativar em vez de apagar de verdade, ja que User e FK em Pipeline.owner
# (on_delete=CASCADE) - deletar de verdade apagaria as pipelines da pessoa.
@extend_schema(
    operation_id='toggle_user_active',
    description='Ativa ou desativa a conta de um usuário. Apenas staff pode chamar. Não é possível desativar a própria conta. Desativar outro admin exige superusuário.',
    parameters=[
        OpenApiParameter(name='user_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID do usuário')
    ],
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def toggle_user_active(request, user_id):
    if not request.user.is_staff:
        return Response(
            {"error": "Apenas usuários administradores podem ativar/desativar contas"},
            status=status.HTTP_403_FORBIDDEN
        )

    target = get_object_or_404(User, id=user_id)

    if target.id == request.user.id:
        return Response(
            {"error": "Você não pode desativar sua própria conta"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # So um superusuario pode ativar/desativar OUTRO admin - sem isso,
    # qualquer staff conseguiria derrubar a sessao do superusuario real
    # (a desativacao ja apaga o token na hora, e is_active=False bloqueia
    # login de volta). Desativar usuario comum continua livre.
    if target.is_staff and not request.user.is_superuser:
        return Response(
            {"error": "Apenas um superusuário pode ativar/desativar outro administrador"},
            status=status.HTTP_403_FORBIDDEN
        )

    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])

    # Desativou: derruba a sessão da pessoa na hora, nao so no proximo login
    if not target.is_active:
        Token.objects.filter(user=target).delete()

    return Response(
        {"id": target.id, "username": target.username, "is_active": target.is_active},
        status=status.HTTP_200_OK
    )


# Admin redefine a senha de outro usuário (POST)
@extend_schema(
    operation_id='reset_user_password',
    description='Redefine a senha de outro usuário. Apenas staff pode chamar. Redefinir a senha de outro admin exige superusuário. Invalida o token de sessão atual do usuário-alvo.',
    parameters=[
        OpenApiParameter(name='user_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID do usuário')
    ],
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def reset_user_password(request, user_id):
    if not request.user.is_staff:
        return Response(
            {"error": "Apenas usuários administradores podem redefinir a senha de outros usuários"},
            status=status.HTTP_403_FORBIDDEN
        )

    target = get_object_or_404(User, id=user_id)

    # So um superusuario pode redefinir a senha de OUTRO admin - sem isso,
    # qualquer staff conseguiria assumir a conta do superusuario real
    # (descobre o id via list_users, redefine a senha, loga como ele).
    if target.is_staff and target.id != request.user.id and not request.user.is_superuser:
        return Response(
            {"error": "Apenas um superusuário pode redefinir a senha de outro administrador"},
            status=status.HTTP_403_FORBIDDEN
        )

    new_password = request.data.get("new_password")

    if not new_password or len(new_password) < 6:
        return Response(
            {"error": "A nova senha deve ter pelo menos 6 caracteres"},
            status=status.HTTP_400_BAD_REQUEST
        )

    target.set_password(new_password)
    target.save()
    Token.objects.filter(user=target).delete()

    return Response(
        {"message": f"Senha de {target.username} redefinida com sucesso"},
        status=status.HTTP_200_OK
    )


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

    pipeline_ids = list(visible_qs.values_list('id', flat=True))

    latest_run_id_sq = PipelineRun.objects.filter(
        pipeline=OuterRef('pk')
    ).order_by('-created_at').values('id')[:1]

    runs_map = {
        r['pipeline_id']: r['status']
        for r in PipelineRun.objects.filter(
            id__in=Pipeline.objects.filter(id__in=pipeline_ids)
            .annotate(lr=Subquery(latest_run_id_sq))
            .values_list('lr', flat=True)
        ).values('pipeline_id', 'status')
    }

    status_counts = {"PENDING": 0, "RUNNING": 0, "SUCCESS": 0, "FAILED": 0, "NOT_RUN": 0}
    for pid in pipeline_ids:
        st = runs_map.get(pid, "NOT_RUN")
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

    confirm_name = request.data.get("confirm_name")

    if not confirm_name or str(confirm_name).strip() != pipeline.name:
        return Response({"error": "Confirmação inválida. Informe o nome exato da pipeline no campo 'confirm_name'."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        pipeline.delete()
        return Response({"message": "Pipeline deletada com sucesso"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# View para gerenciar arquivo de configuração de uma pipeline (GET ou POST)
@extend_schema(
    operation_id='manage_pipeline_env',
    description='GET: Retorna status de configuração. POST: Faz upload de um novo arquivo .env ou config.ini (substitui o existente)',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline')
    ],
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT, 201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["GET", "POST"])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manage_pipeline_env(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if request.method == "GET":
        if not pipeline.can_execute(request.user):
            return Response(
                {"error": "Usuário não tem permissão para acessar esta pipeline"},
                status=status.HTTP_403_FORBIDDEN
            )

        pipeline_name = Pipeline.normalize_pipeline_storage_name(pipeline.etl_name)
        env_exists = get_storage().env_file_exists(pipeline_name)
        config_exists = get_storage().config_file_exists(pipeline_name)

        return Response(
            {"env_exists": env_exists, "config_exists": config_exists},
            status=status.HTTP_200_OK
        )

    elif request.method == "POST":
        if not pipeline.can_edit(request.user):
            return Response(
                {"error": "Usuário não tem permissão para editar esta pipeline"},
                status=status.HTTP_403_FORBIDDEN
            )

        env_file = request.FILES.get("env")
        config_file = request.FILES.get("config")

        if not env_file and not config_file:
            return Response(
                {"error": "Campo 'env' ou 'config' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if env_file and env_file.size > 1_000_000:  # 1MB
                return Response(
                    {"error": "Arquivo .env maior que 1MB"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if config_file and config_file.size > 1_000_000:  # 1MB
                return Response(
                    {"error": "Arquivo config.ini maior que 1MB"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            pipeline_name = Pipeline.normalize_pipeline_storage_name(pipeline.etl_name)
            message_parts = []

            if env_file:
                env_content = _decode_uploaded_text_file(env_file, [".env"], "env")
                get_storage().save_env_file(pipeline_name, env_content)
                message_parts.append(".env")

            if config_file:
                config_content = _decode_uploaded_text_file(config_file, [".ini"], "config")
                get_storage().save_config_file(pipeline_name, config_content)
                message_parts.append("config.ini")

            return Response(
                {"message": f"Arquivo(s) {' e '.join(message_parts)} atualizado(s) com sucesso"},
                status=status.HTTP_201_CREATED
            )
        except UnicodeDecodeError:
            return Response(
                {"error": "Arquivo não é UTF-8 válido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# View para gerenciar o arquivo de dados (planilha ou JSON) que o script da pipeline
# processa (GET, POST ou DELETE). Usa permissao de execucao (nao de edicao): subir os
# dados a serem processados faz parte de "rodar" a pipeline, entao qualquer colaborador
# que possa executar tambem pode trocar o arquivo de entrada.
@extend_schema(
    operation_id='manage_pipeline_input_file',
    description='GET: retorna o nome do arquivo de dados atual. POST: faz upload de um arquivo (.xlsx/.xls/.csv/.json) que o script vai processar, substituindo o anterior. DELETE: remove o arquivo de dados atual.',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline')
    ],
    request=OpenApiTypes.OBJECT,
    responses={200: OpenApiTypes.OBJECT, 201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["GET", "POST", "DELETE"])
@parser_classes([MultiPartParser, FormParser])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def manage_pipeline_input_file(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response(
            {"error": "Usuário não tem permissão para acessar esta pipeline"},
            status=status.HTTP_403_FORBIDDEN
        )

    pipeline_name = Pipeline.normalize_pipeline_storage_name(pipeline.etl_name)

    if request.method == "GET":
        input_file_name = get_storage().get_input_file_name(pipeline_name)
        return Response(
            {"input_file_name": input_file_name, "input_file_exists": input_file_name is not None},
            status=status.HTTP_200_OK
        )

    if request.method == "DELETE":
        get_storage().delete_input_file(pipeline_name)
        return Response(
            {"message": "Arquivo de dados removido com sucesso"},
            status=status.HTTP_200_OK
        )

    # POST
    input_file = request.FILES.get("input_file")

    if not input_file:
        return Response(
            {"error": "Campo 'input_file' é obrigatório"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if input_file.size > INPUT_FILE_MAX_SIZE:
        return Response(
            {"error": "Arquivo de dados maior que 100MB"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        content = _read_uploaded_binary_file(input_file, INPUT_FILE_ALLOWED_EXTENSIONS, "input_file")
        saved_name = get_storage().save_input_file(pipeline_name, input_file.name, content)

        return Response(
            {"message": f"Arquivo {saved_name} enviado com sucesso", "input_file_name": saved_name},
            status=status.HTTP_201_CREATED
        )
    except ValueError as error:
        return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# View para baixar o arquivo de saida gerado pela ultima execucao bem-sucedida da
# pipeline (o script grava esse arquivo no seu proprio diretorio de trabalho; ver
# storage.sync_output_from_local e tasks.execute_pipeline)
@extend_schema(
    operation_id='download_pipeline_output_file',
    description='Baixa o arquivo de saida gerado pela ultima execucao bem-sucedida da pipeline',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline')
    ],
    responses={200: OpenApiTypes.BINARY, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_pipeline_output_file(request, pipeline_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response(
            {"error": "Usuário não tem permissão para acessar esta pipeline"},
            status=status.HTTP_403_FORBIDDEN
        )

    pipeline_name = Pipeline.normalize_pipeline_storage_name(pipeline.etl_name)
    storage = get_storage()

    try:
        content = storage.get_output_file_bytes(pipeline_name)
        output_file_name = storage.get_output_file_name(pipeline_name)
    except FileNotFoundError:
        return Response(
            {"error": "Esta pipeline ainda não gerou nenhum arquivo de saída"},
            status=status.HTTP_404_NOT_FOUND
        )

    content_type, _ = mimetypes.guess_type(output_file_name or "")
    response = HttpResponse(content, content_type=content_type or "application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{output_file_name}"'
    return response


# View para consultar o log (stdout/stderr) de uma execucao especifica (GET)
@extend_schema(
    operation_id='get_pipeline_run_log',
    description='Retorna o log de execucao (stdout/stderr) de uma run especifica da pipeline',
    parameters=[
        OpenApiParameter(name='pipeline_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da pipeline'),
        OpenApiParameter(name='run_id', type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description='ID da execução'),
    ],
    responses={200: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
)
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def pipeline_run_log(request, pipeline_id, run_id):
    pipeline = get_object_or_404(Pipeline, id=pipeline_id)

    if not pipeline.can_execute(request.user):
        return Response(
            {"error": "Usuário não tem permissão para acessar esta pipeline"},
            status=status.HTTP_403_FORBIDDEN
        )

    run = get_object_or_404(PipelineRun, id=run_id, pipeline=pipeline)

    return Response(
        {"run_id": run.id, "status": run.status, "log": run.log},
        status=status.HTTP_200_OK
    )
