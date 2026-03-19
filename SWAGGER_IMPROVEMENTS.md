# 🎯 Melhorias Futuras - Swagger

Este arquivo documenta as melhorias opcionais que você pode fazer na documentação Swagger para deixar ainda mais completa.

## 1. Usar Serializers (Recomendado)

Convertendo para Serializers, a documentação fica automática e mais precisa:

```python
# serializers.py
from rest_framework import serializers
from .models import Pipeline, PipelineRun

class PipelineSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'etl_name', 'owner_name', 'created_at']
        read_only_fields = ['id', 'owner_name', 'created_at']

class PipelineRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineRun
        fields = ['id', 'pipeline', 'status', 'triggered_by', 'created_at']
        read_only_fields = ['id', 'created_at']

class CreatePipelineSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, help_text="Nome da pipeline")
    description = serializers.CharField(required=False, help_text="Descrição da pipeline")
    lib = serializers.JSONField(default=list, help_text="Dependências como JSON array")
    main_code = serializers.CharField(required=False, help_text="Código Python da pipeline")
    script = serializers.FileField(required=False, help_text="Arquivo Python (alternativa ao main_code)")
```

## 2. Usar ViewSets (Mais Moderno)

```python
# no urls.py
from rest_framework.routers import DefaultRouter
from .views import PipelineViewSet

router = DefaultRouter()
router.register('pipelines', PipelineViewSet, basename='pipeline')

urlpatterns = [
    path('api/', include(router.urls)),
    ...
]

# no views.py
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

class PipelineViewSet(viewsets.ModelViewSet):
    \"\"\"
    API para gerenciamento de Pipelines ETL.
    
    list: Listar todas as pipelines
    create: Criar nova pipeline
    retrieve: Obter detalhes de uma pipeline
    update: Atualizar uma pipeline
    destroy: Deletar uma pipeline
    \"\"\"
    serializer_class = PipelineSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Pipeline.objects.filter(owner=self.request.user)
    
    @extend_schema(
        description='Listar todas as pipelines do usuário autenticado'
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description='Criar uma nova pipeline ETL'
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
```

## 3. Adicionar Webhooks/Callbacks

```python
from drf_spectacular.utils import extend_schema

SPECTACULAR_SETTINGS = {
    ...
    'WEBHOOKS': [
        {
            'name': 'pipeline_completed',
            'description': 'Chamado quando uma pipeline completa',
            'request_body': {
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'pipeline_id': {'type': 'integer'},
                                'run_id': {'type': 'integer'},
                                'status': {'type': 'string'},
                                'timestamp': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    }
                }
            }
        }
    ]
}
```

## 4. Adicionar Tags para Organizar Endpoints

```python
from drf_spectacular.utils import extend_schema

@extend_schema(
    tags=['Pipelines'],
    operation_id='list_pipelines',
    description='Lista todas as pipelines'
)
def list_pipelines(request):
    ...

@extend_schema(
    tags=['Usuarios'],
    operation_id='create_user',
    description='Cria novo usuário'
)
def create_user(request):
    ...
```

## 5. Adicionar Exemplos de Request/Response

```python
from drf_spectacular.utils import extend_schema, OpenApiExample

@extend_schema(
    request=CreatePipelineSerializer,
    responses=PipelineSerializer,
    examples=[
        OpenApiExample(
            'Example request',
            value={
                'name': 'Pipeline de Vendas',
                'description': 'Extrai dados de vendas',
                'lib': ['pandas', 'requests'],
                'main_code': 'import pandas as pd\ndf = pd.read_csv("data.csv")'
            }
        )
    ]
)
@api_view(['POST'])
def pipeline_create(request):
    ...
```

## 6. Adicionar Paginação

```python
# settings.py
REST_FRAMEWORK = {
    ...
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
```

## 7. Adicionar Filtros e Busca

```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

class PipelineViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
```

## 8. Versioning da API

```python
# settings.py
REST_FRAMEWORK = {
    ...
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning'
}

# urls.py
urlpatterns = [
    path('v1/', include('pipelines.urls')),
    path('v2/', include('pipelines.urls_v2')),
]
```

## 🚀 Como Implementar

1. Comece com **Serializers** - é a mudança mais impactante
2. Depois migre para **ViewSets** - deixa o código mais conciso
3. Adicione **Tags** nos decoradores para melhor organização
4. Implemente **Exemplos** nos endpoints mais importantes
5. Configure **Filtros** conforme necessário

---

Essas melhorias tornarão a documentação Swagger ainda mais profissional e útil para o time de frontend! 🎯

