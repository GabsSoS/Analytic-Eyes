# 📚 Configuração do Swagger - Analytic Eyes API

## ✅ O que foi implementado

Foi adicionada documentação interativa **Swagger (OpenAPI 3.0)** à  API usando **drf-spectacular**, que é a solução mais moderna para Django REST Framework.

### Dependências Adicionadas
- `drf-spectacular` - Gera automaticamente a documentação OpenAPI

### Arquivos Modificados
1. **requirements.txt** - Adicionado `drf-spectacular`
2. **config/settings.py** - Configurado o drf_spectacular em INSTALLED_APPS e adicionadas as configurações
3. **config/urls.py** - Adicionadas as rotas do Swagger
4. **pipelines/views.py** - Decoradores `@extend_schema` adicionados em todas as views para melhor documentação

---

## 🚀 Como usar

### 1. Instalar as dependências
```bash
pip install -r requirements.txt
```

Ou se estiver usando Docker:
```bash
docker build -t seu_projeto . --build-arg REQUIREMENTS=requirements.txt
```

### 2. Acessar a documentação

Após iniciar o servidor Django, acesse:

- **Swagger UI (Interface interativa):** http://localhost:8000/api/docs/
- **ReDoc (Documentação estática):** http://localhost:8000/api/redoc/
- **Schema JSON (Raw OpenAPI):** http://localhost:8000/api/schema/

### 3. Autenticação no Swagger

Como sua API usa **Basic Authentication**, no Swagger:
1. Clique no botão "Authorize" (cadeado no topo direito)
2. Insira suas credenciais (username e password)
3. Clique em "Authorize"

---

## 📝 Endpoints Documentados

Todos os endpoints agora aparecem no Swagger com descrições claras:

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/users/create/` | POST | Criar novo usuário (apenas staff) |
| `/api/pipelines/create/` | POST | Criar nova pipeline |
| `/api/pipelines/` | GET | Listar pipelines do usuário |
| `/api/pipelines/{id}/` | POST | Executar uma pipeline |
| `/api/pipelines/{id}/details/` | GET | Obter detalhes de uma pipeline |
| `/api/pipelines/{id}/runs/` | GET | Obter histórico de execuções |

---

## 🔧 Configurações Adicionadas

No `settings.py`, foi adicionado:

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Analytic Eyes ETL API',
    'DESCRIPTION': 'API para gerenciamento de pipelines ETL',
    'VERSION': '1.0.0',
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
    'SCHEMA_PATH_PREFIX': '/api/',
}
```

Você pode customizar:
- `TITLE` - Nome da API
- `DESCRIPTION` - Descrição da API
- `VERSION` - Versão atual
- `CONTACT` - Informações de contato (adicionar manualmente se desejar)

---

## 💡 Próximos Passos (Opcional)

### 1. Adicionar Serializers para melhor documentação
Converter suas views em ViewSets e Serializers para documentação ainda mais detalhada:

```python
from rest_framework import serializers, viewsets

class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = ['id', 'name', 'description', 'owner']

class PipelineViewSet(viewsets.ModelViewSet):
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer
    permission_classes = [IsAuthenticated]
```

### 2. Adicionar mais informações de contato/licença
No `settings.py`:

```python
SPECTACULAR_SETTINGS = {
    ...
    'CONTACT': {
        'name': 'Seu Nome',
        'email': 'seu-email@example.com',
    },
    'LICENSE': {
        'name': 'MIT',
    }
}
```

### 3. Fazer download da documentação OpenAPI
- **JSON:** http://localhost:8000/api/schema/?format=json
- **YAML:** http://localhost:8000/api/schema/?format=yaml

---

## 🐛 Troubleshooting

### Problema: "Module not found: drf_spectacular"
**Solução:** Certifique-se de ter instalado:
```bash
pip install drf-spectacular
```

### Problema: Swagger não aparece
**Solução:** Verifique se adicionou `drf_spectacular` em `INSTALLED_APPS`

### Problema: "Permission Denied" no Swagger
**Solução:** Certifique-se de estar autenticado usando o botão "Authorize"

---

## 📖 Referências

- [drf-spectacular Documentation](https://drf-spectacular.readthedocs.io/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [OpenAPI 3.0 Spec](https://spec.openapis.org/oas/v3.0.3)

