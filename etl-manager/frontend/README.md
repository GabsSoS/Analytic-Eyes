# Analytic Eyes — Frontend

Interface web do Analytic Eyes, construída com React 19 + Vite 8.

## Tecnologias

- React 19 + React Router DOM 7
- Vite 8 (build tool / dev server)
- Axios (cliente HTTP com interceptor de token)
- Monaco Editor (`@monaco-editor/react`) — edição de código Python
- CSS puro com variáveis e `clamp()` para responsividade

## Estrutura de pastas

```
src/
├── assets/          # Imagens e ícones
├── components/      # Header, Sidebar (globais, usados no Layout)
├── pages/
│   ├── Login/       # Tela de autenticação
│   ├── Home/        # Dashboard
│   ├── Criar/       # Criação de pipeline (Monaco + upload .py)
│   ├── Fluxos/      # Listagem de pipelines
│   ├── Details/     # Detalhes, runs, edição e remoção
│   ├── Settings/    # Perfil, senha, criar usuário, logout
│   └── Layout/      # Wrapper com Header + Sidebar + <Outlet>
└── services/
    └── api.js       # Instância Axios configurada com interceptors
```

## Autenticação

O token é armazenado em `localStorage` como `"token"` e `"username"`.  
O interceptor em `services/api.js` injeta `Authorization: Token <token>` em toda requisição.  
Em caso de resposta 401 o interceptor remove o token e redireciona para `/login` automaticamente.

## Variáveis de ambiente

Crie um arquivo `.env` em `etl-manager/frontend/`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/
```

Se a variável não for definida, o Axios usa `/api/` como padrão (proxy Vite).

## Rodando localmente

```bash
cd etl-manager/frontend
npm install
npm run dev
```

O dev server sobe em `http://localhost:5173`.

## Build de produção

```bash
npm run build
```

Os artefatos ficam em `dist/` e podem ser servidos por qualquer servidor estático (Nginx, S3+CloudFront, etc.).
