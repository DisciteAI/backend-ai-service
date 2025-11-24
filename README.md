# Backend AI Service - Discite Training Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791?logo=postgresql&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google-Gemini_2.5-4285F4?logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)

**Serviço de IA para conversas de treinamento personalizadas com detecção automática de conclusão de tópicos**

[Documentação Interativa](http://localhost:8000/docs) | [Arquitetura](#-arquitetura) | [Instalação](#-instalação-e-execução)

</div>

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Arquitetura](#-arquitetura)
- [Principais Funcionalidades](#-principais-funcionalidades)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Instalação e Execução](#-instalação-e-execução)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Endpoints da API](#-endpoints-da-api)
- [Configuração](#-configuração)
- [Banco de Dados](#-banco-de-dados)
- [Integração com Backend .NET](#-integração-com-backend-net)
- [Lógica de Retry](#-lógica-de-retry)
- [Desenvolvimento](#-desenvolvimento)
- [Troubleshooting](#-troubleshooting)
- [Licença](#-licença)

---

## 🚀 Sobre o Projeto

O **Backend AI Service** é um microsserviço Python desenvolvido com FastAPI que fornece conversas de treinamento personalizadas alimentadas por IA usando o Google Gemini. Ele é parte da plataforma **Discite**, responsável por:

- 🤖 **Gerenciar sessões de treinamento com IA**: Conversas adaptativas baseadas no nível do usuário
- 🎯 **Detectar conclusão automática de tópicos**: Identifica quando o usuário dominou o conteúdo
- 🔄 **Integrar com backend .NET**: Busca contexto de usuário e notifica conclusões
- 📚 **Personalizar prompts**: Utiliza templates de prompt específicos por tópico
- 💾 **Armazenar histórico completo**: Mantém registro de todas as interações

### Como Funciona

```
┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│   Cliente   │────────▶│  Backend AI      │────────▶│  Backend    │
│  (Frontend) │         │  (Python/FastAPI)│         │  (.NET)     │
└─────────────┘         └──────────────────┘         └─────────────┘
                              │     ▲                       │
                              │     │                       │
                              ▼     │                       ▼
                        ┌──────────────┐            ┌─────────────┐
                        │  Google      │            │ PostgreSQL  │
                        │  Gemini AI   │            │ (backenddb) │
                        └──────────────┘            └─────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │ PostgreSQL   │
                        │ (aitraining) │
                        └──────────────┘
```

**Fluxo de uma Sessão de Treinamento:**

1. **Início**: Cliente solicita início de sessão (user_id, topic_id, course_id)
2. **Busca de Contexto**: Python busca no .NET (com retry automático):
   - Contexto do usuário (nível, tópicos concluídos, dificuldades)
   - Detalhes do tópico (título, template de prompt, objetivos de aprendizagem)
   - Progresso no curso
3. **Construção de Prompt**: Sistema monta prompt personalizado em PT-BR
4. **Inicialização da IA**: Gemini recebe contexto e inicia conversa
5. **Troca de Mensagens**: Usuário conversa com a IA sobre o tópico
6. **Detecção de Conclusão**: Sistema identifica marcador `{TOPIC_COMPLETED}` na resposta da IA
7. **Notificação**: Python notifica .NET da conclusão (com retry)
8. **Atualização de Progresso**: .NET atualiza tabela UserProgress

---

## 🏗️ Arquitetura

### Arquitetura de Microsserviços

O sistema Discite utiliza uma arquitetura de **dois backends independentes**:

| Serviço | Porta | Tecnologia | Responsabilidade |
|---------|-------|------------|------------------|
| **Backend .NET** | 8080 | ASP.NET Core | Gerenciamento de usuários, cursos, tópicos e progresso |
| **Backend AI (Python)** | 8000 | FastAPI | Conversas com IA, detecção de conclusão |
| **DB .NET** | 5432 | PostgreSQL | Dados de usuários e estrutura de cursos |
| **DB Python** | 5433 | PostgreSQL | Histórico de conversas e contexto de sessões |

### Por Que Dois Bancos de Dados?

- **Separação de Responsabilidades**: .NET gerencia dados de negócio; Python gerencia estado de conversação
- **Escalabilidade Independente**: Cada serviço pode escalar conforme demanda
- **Isolamento de Dados**: Histórico de conversas não polui banco principal
- **Tecnologias Nativas**: Cada serviço usa seu ORM natural (EF Core vs SQLAlchemy)

---

## ✨ Principais Funcionalidades

### 🎯 Detecção Inteligente de Conclusão

O sistema utiliza o **CompletionDetector** para identificar automaticamente quando um usuário domina um tópico:

- A IA insere `{TOPIC_COMPLETED}` quando critérios são atingidos (ex: 2/3 questões corretas)
- O marcador é removido antes de enviar resposta ao usuário
- Sessão é marcada como `COMPLETED` no banco
- .NET é notificado automaticamente via API

### 🔄 Lógica de Retry com Backoff Exponencial

**Todas** as chamadas ao backend .NET utilizam retry automático para resiliência:

```python
@retry_with_backoff(max_attempts=5, base_delay=1.0)
async def get_topic_details(topic_id: int):
    # Tentativas: 1s → 2s → 4s → 8s → 16s
    ...
```

- **5 tentativas** com delays crescentes
- Protege contra falhas transitórias de rede
- Garante entrega de notificações de conclusão
- Configurável via variáveis de ambiente

### 🧠 Construção Dinâmica de Prompts

O **ContextBuilder** cria prompts personalizados em português:

- **Substituição de placeholders**: `{topic_title}`, `{user_level}`, `{completion_marker}`
- **Adaptação de dificuldade**: beginner → iniciante, intermediate → intermediário
- **Inclusão de objetivos**: Integra learning objectives do .NET
- **Instruções de conclusão**: Ensina a IA quando marcar tópico completo

### 💬 Gerenciamento de Conversação

- **Histórico completo**: Todas as mensagens armazenadas (system, user, assistant)
- **Truncamento automático**: Limita a 50 mensagens (configurável) para evitar limite de tokens
- **Prompt de sistema isolado**: Primeira mensagem (role=SYSTEM) não visível ao usuário
- **Suporte assíncrono**: Toda stack usa async/await para alta performance

---

## 🛠️ Tecnologias Utilizadas

### Core

- **[FastAPI 0.115.6](https://fastapi.tiangolo.com/)** - Framework web assíncrono de alta performance
- **[Python 3.12](https://www.python.org/)** - Linguagem de programação
- **[Uvicorn](https://www.uvicorn.org/)** - Servidor ASGI para FastAPI
- **[Pydantic 2.10](https://docs.pydantic.dev/)** - Validação de dados

### IA & HTTP

- **[Google Generative AI](https://ai.google.dev/)** - Cliente Python para Gemini 2.5 Flash
- **[HTTPX](https://www.python-httpx.org/)** - Cliente HTTP assíncrono

### Banco de Dados

- **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)** - ORM assíncrono
- **[Asyncpg](https://magicstack.github.io/asyncpg/)** - Driver PostgreSQL assíncrono
- **[Alembic](https://alembic.sqlalchemy.org/)** - Migrações de banco de dados
- **[PostgreSQL 18](https://www.postgresql.org/)** - Banco de dados relacional

### DevOps

- **[Docker](https://www.docker.com/)** - Containerização
- **[Docker Compose](https://docs.docker.com/compose/)** - Orquestração de serviços

---

## 📦 Instalação e Execução

### Pré-requisitos

- **Docker** e **Docker Compose** instalados
- **Git** para clonar repositórios
- **Chave de API do Google Gemini** ([Obter aqui](https://aistudio.google.com/app/apikey))

### Rodando Backend Completo

Siga estes passos para executar **ambos** os backends (Python + .NET) com Docker:

#### 1. Clone os Repositórios

```bash
# Clone o backend .NET
git clone https://DisciteAI@dev.azure.com/DisciteAI/backend-api/_git/backend-api

# Clone o backend AI (Python)
git clone https://github.com/DisciteAI/backend-ai-service.git
```

#### 2. Configure a Chave da API do Gemini

Crie um arquivo `.env` no mesmo diretório que contém os dois backends:

```bash
# .env
GEMINI_API_KEY=<sua_chave_api_aqui>
```

#### 3. Copie o Docker Compose

Copie o arquivo `backend-api/scripts/docker-compose.yml` para o **mesmo diretório** que contém:
- O arquivo `.env`
- A pasta `backend-api/`
- A pasta `backend-ai-service/`

Estrutura esperada:
```
seu-diretorio/
├── .env                         # Sua chave do Gemini
├── docker-compose.yml           # Copiado de backend-api/scripts/
├── backend-api/                 # Repositório .NET
└── backend-ai-service/          # Repositório Python
```

#### 4. Execute os Serviços

```bash
# Inicie todos os serviços (detached mode + build)
docker-compose up -d --build
```

#### 5. Aplique as Migrações de Banco de Dados

Em terminais separados, execute:

```bash
# Migrações .NET
docker-compose exec dotnet-backend dotnet ef database update

# Migrações Python
docker-compose exec python-backend alembic upgrade head
```

#### 6. Verifique os Serviços

```bash
# Health check do backend .NET
curl http://localhost:8080/api/health

# Health check do backend Python
curl http://localhost:8000/api/health
```

✅ Se ambos retornarem `{"status":"healthy"}`, o sistema está pronto!

### Acessando a Documentação Interativa

Com os serviços rodando, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Info do Serviço**: http://localhost:8000/

---

## 📂 Estrutura do Projeto

```
backend-ai-service/
│
├── app/
│   ├── api/                              # Roteadores da API
│   │   ├── __init__.py
│   │   └── sessions.py                   # Endpoints de sessões (/api/sessions/*)
│   │
│   ├── models/                           # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   └── chat_session.py               # ChatSession, ChatMessage, SessionContext
│   │
│   ├── schemas/                          # Schemas Pydantic
│   │   ├── __init__.py
│   │   └── session.py                    # DTOs de request/response
│   │
│   ├── services/                         # Lógica de negócio
│   │   ├── __init__.py
│   │   ├── session_manager.py            # Orquestrador principal
│   │   ├── dotnet_client.py              # Cliente HTTP para .NET (com retry)
│   │   ├── gemini_client.py              # Cliente do Google Gemini
│   │   ├── context_builder.py            # Construtor de prompts
│   │   └── completion_detector.py        # Detector de conclusão de tópico
│   │
│   ├── utils/                            # Utilitários
│   │   ├── __init__.py
│   │   └── retry.py                      # Lógica de retry com backoff exponencial
│   │
│   ├── config.py                         # Configurações da aplicação
│   ├── database.py                       # Setup do SQLAlchemy
│   └── main.py                           # Ponto de entrada do FastAPI
│
├── alembic/                              # Migrações de banco
│   ├── versions/
│   │   └── 20250113_initial_schema.py    # Schema inicial
│   ├── env.py                            # Configuração de migração
│   └── alembic.ini
│
├── requirements.txt                      # Dependências Python
├── Dockerfile                            # Build multi-stage
├── docker-compose.yml                    # Orquestração de serviços
├── .env.example                          # Exemplo de variáveis de ambiente
├── .gitignore
└── README.md                             # Este arquivo
```

---

## 🌐 Endpoints da API

### Base URL
```
http://localhost:8000
```

### Sessões de Treinamento

#### `POST /api/sessions/start`
Inicia uma nova sessão de treinamento com IA.

**Request:**
```json
{
  "user_id": 1,
  "topic_id": 5,
  "course_id": 2
}
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": 1,
  "topic_id": 5,
  "course_id": 2,
  "status": "active",
  "started_at": "2025-01-24T12:00:00Z",
  "initial_message": "Olá! Vamos começar o treinamento sobre..."
}
```

#### `POST /api/sessions/{session_id}/message`
Envia uma mensagem do usuário e recebe resposta da IA.

**Request:**
```json
{
  "content": "Como funciona a herança em Python?"
}
```

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": {
    "id": 42,
    "role": "assistant",
    "content": "A herança em Python permite...",
    "timestamp": "2025-01-24T12:05:00Z"
  },
  "status": "active",
  "completed": false
}
```

#### `GET /api/sessions/{session_id}`
Recupera detalhes de uma sessão com histórico de mensagens.

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": 1,
  "topic_id": 5,
  "status": "completed",
  "started_at": "2025-01-24T12:00:00Z",
  "completed_at": "2025-01-24T12:30:00Z",
  "messages": [
    {
      "id": 40,
      "role": "user",
      "content": "Como funciona a herança?",
      "timestamp": "2025-01-24T12:05:00Z"
    },
    {
      "id": 41,
      "role": "assistant",
      "content": "A herança em Python...",
      "timestamp": "2025-01-24T12:05:30Z"
    }
  ]
}
```

### Health Check

#### `GET /api/health`
Verifica saúde do serviço.

**Response:**
```json
{
  "status": "healthy",
  "service": "AI Training Service",
  "database": "connected"
}
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com base no `.env.example`:

```bash
# Aplicação
APP_NAME=AI Training Service
ENVIRONMENT=development
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Banco de Dados Python
DATABASE_URL=postgresql+asyncpg://aiuser:aipassword@localhost:5433/aitraining

# Google Gemini
GEMINI_API_KEY=sua_chave_api_aqui
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_OUTPUT_TOKENS=2048

# Integração com Backend .NET
DOTNET_API_URL=http://localhost:8080
DOTNET_API_TIMEOUT=30

# Retry Logic
DOTNET_API_RETRY_ATTEMPTS=5
DOTNET_API_RETRY_BASE_DELAY=1.0
DOTNET_API_RETRY_MAX_DELAY=60.0

# Conversação
MAX_CONVERSATION_HISTORY=50
COMPLETION_MARKER={TOPIC_COMPLETED}

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

### Configurações Importantes

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `GEMINI_API_KEY` | **Obrigatório**: Chave da API do Google Gemini | - |
| `DATABASE_URL` | Connection string PostgreSQL assíncrona | postgresql+asyncpg://... |
| `DOTNET_API_URL` | URL do backend .NET | http://localhost:8080 |
| `DOTNET_API_RETRY_ATTEMPTS` | Tentativas de retry ao chamar .NET | 5 |
| `MAX_CONVERSATION_HISTORY` | Máximo de mensagens no histórico | 50 |
| `COMPLETION_MARKER` | Marcador de conclusão usado pela IA | {TOPIC_COMPLETED} |

---

## 🗄️ Banco de Dados

### Schema

O serviço utiliza 3 tabelas principais:

#### `chat_sessions`
Armazena metadados de sessões de treinamento.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | UUID | Chave primária |
| user_id | Integer | ID do usuário (referência ao .NET) |
| topic_id | Integer | ID do tópico (referência ao .NET) |
| course_id | Integer | ID do curso (referência ao .NET) |
| status | Enum | active \| completed \| abandoned |
| started_at | Timestamp | Momento de início |
| completed_at | Timestamp | Momento de conclusão (nullable) |

**Índices**: id, user_id, topic_id, course_id

#### `chat_messages`
Armazena histórico completo de conversações.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | Integer | Chave primária |
| session_id | UUID | FK para chat_sessions (CASCADE) |
| role | Enum | system \| user \| assistant |
| content | Text | Conteúdo da mensagem |
| timestamp | Timestamp | Momento da mensagem |

**Índices**: id, session_id

#### `session_contexts`
Armazena cache de dados do .NET API.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | Integer | Chave primária |
| session_id | UUID | FK para chat_sessions (CASCADE, UNIQUE) |
| user_level | String | Nível do usuário |
| completed_topics_json | JSON | Tópicos concluídos |
| struggles_json | JSON | Dificuldades do usuário |
| course_title | String | Título do curso |
| topic_title | String | Título do tópico |
| learning_objectives | Text | Objetivos de aprendizagem |
| prompt_template | Text | Template do prompt |

### Migrações

```bash
# Aplicar migrações
alembic upgrade head

# Criar nova migração
alembic revision --autogenerate -m "descricao_da_mudanca"

# Reverter última migração
alembic downgrade -1

# Ver histórico de migrações
alembic history
```

---

## 🔗 Integração com Backend .NET

O serviço Python atua como **cliente** do backend .NET, consumindo os seguintes endpoints:

### Endpoints Consumidos

#### 1. `GET /api/v1/userprogress/{userId}/context`
Busca contexto global do usuário.

**Resposta do .NET:**
```json
{
  "userLevel": "intermediate",
  "completedTopicIds": [1, 2, 3],
  "struggleTopics": ["Programação Assíncrona"]
}
```

#### 2. `GET /api/v1/userprogress/{userId}/course/{courseId}`
Busca progresso específico do curso.

**Resposta do .NET:**
```json
{
  "courseId": 2,
  "completedTopics": 5,
  "totalTopics": 10,
  "progress": 50.0
}
```

#### 3. `GET /api/v1/trainingtopics/{topicId}`
Busca detalhes do tópico.

**Resposta do .NET:**
```json
{
  "id": 5,
  "title": "Herança em Python",
  "description": "Conceitos de herança...",
  "promptTemplate": "Você é um tutor...",
  "learningObjectives": "- Entender herança\n- Aplicar polimorfismo"
}
```

#### 4. `POST /api/v1/userprogress/complete-topic`
Notifica conclusão de tópico.

**Payload Python:**
```json
{
  "userId": 1,
  "topicId": 5,
  "courseId": 2,
  "completedAt": "2025-01-24T12:30:00Z",
  "sessionId": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Como o Retry Funciona

Todos os métodos do `DotNetClient` são decorados com `@retry_with_backoff`:

```python
# app/services/dotnet_client.py
@retry_with_backoff(max_attempts=5, base_delay=1.0)
async def notify_topic_completion(self, user_id, topic_id, course_id, session_id):
    # Se falhar: 1s → 2s → 4s → 8s → 16s
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
```

**Logs de Retry:**
```
WARNING: notify_topic_completion attempt 1/5 failed: Connection refused. Retrying in 1.0s...
WARNING: notify_topic_completion attempt 2/5 failed: Timeout. Retrying in 2.0s...
INFO: notify_topic_completion succeeded on attempt 3/5
```

---

## 🔄 Lógica de Retry

### Exponential Backoff Decorator

Implementado em [app/utils/retry.py](app/utils/retry.py):

```python
@retry_with_backoff(
    max_attempts=5,           # Número de tentativas
    base_delay=1.0,           # Delay inicial (segundos)
    max_delay=60.0,           # Delay máximo (segundos)
    exponential_base=2.0      # Base de crescimento
)
async def sua_funcao():
    # Tentativas: 1s → 2s → 4s → 8s → 16s
    pass
```

### Exceções Tratadas

- `httpx.HTTPError` - Erros HTTP genéricos
- `httpx.TimeoutException` - Timeout de requisição
- `ConnectionError` - Falha de conexão

### Quando Usar

✅ **Use retry para**:
- Chamadas ao backend .NET
- Chamadas a APIs externas
- Operações de rede críticas

❌ **Não use retry para**:
- Operações de banco de dados (SQLAlchemy já tem pool de conexões)
- Validações de entrada
- Erros de lógica de negócio

---

## 🛠️ Desenvolvimento

### Executar Localmente (Sem Docker)

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com sua GEMINI_API_KEY

# 3. Iniciar PostgreSQL manualmente ou via Docker
docker-compose up python-postgres

# 4. Aplicar migrações
alembic upgrade head

# 5. Iniciar servidor de desenvolvimento
python -m uvicorn app.main:app --reload --port 8000
```

### Executar com Docker

```bash
# Build e start
docker-compose up --build

# Ver logs
docker-compose logs -f ai-service

# Parar serviços
docker-compose down

# Limpar volumes e reiniciar
docker-compose down -v && docker-compose up --build
```

### Comandos Úteis

```bash
# Formatar código com black
black app/

# Executar testes (quando disponíveis)
pytest

# Entrar no container Python
docker-compose exec python-backend bash

# Verificar logs do banco
docker-compose logs python-postgres

# Resetar banco de dados
docker-compose exec python-postgres psql -U aiuser -d aitraining -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
alembic upgrade head
```

---

## 🐛 Troubleshooting

### Problema: Serviço não conecta ao .NET

**Sintomas:**
```
WARNING: get_topic_details attempt 5/5 failed: Connection refused
ERROR: Failed to fetch topic details after 5 attempts
```

**Soluções:**
1. Verifique se o backend .NET está rodando:
   ```bash
   curl http://localhost:8080/api/health
   ```
2. Confirme a variável `DOTNET_API_URL` no `.env`:
   ```bash
   docker-compose exec python-backend env | grep DOTNET_API_URL
   ```
3. Teste conectividade do container Python:
   ```bash
   docker-compose exec python-backend curl http://dotnet-backend:8080/api/health
   ```

### Problema: Erro de Banco de Dados

**Sintomas:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Soluções:**
1. Verifique se o PostgreSQL está rodando:
   ```bash
   docker-compose ps python-postgres
   ```
2. Confirme a `DATABASE_URL`:
   ```bash
   # No .env, deve ser:
   DATABASE_URL=postgresql+asyncpg://aiuser:aipassword@localhost:5433/aitraining

   # Dentro do Docker Compose, deve ser:
   DATABASE_URL=postgresql+asyncpg://aiuser:aipassword@python-postgres:5432/aitraining
   ```
3. Reaplique migrações:
   ```bash
   docker-compose exec python-backend alembic upgrade head
   ```

### Problema: Erro de API do Gemini

**Sintomas:**
```
google.generativeai.types.generation_types.StopCandidateException
```

**Soluções:**
1. Verifique se a chave API está válida:
   ```bash
   docker-compose exec python-backend env | grep GEMINI_API_KEY
   ```
2. Teste a chave manualmente:
   ```python
   import google.generativeai as genai
   genai.configure(api_key="sua_chave")
   model = genai.GenerativeModel("gemini-2.5-flash")
   response = model.generate_content("Hello")
   print(response.text)
   ```
3. Verifique limites de taxa da API: https://aistudio.google.com/app/apikey

### Problema: Conflito de Portas

**Sintomas:**
```
Error: port is already allocated
```

**Soluções:**
1. Verifique processos usando as portas:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   netstat -ano | findstr :5433

   # Linux/Mac
   lsof -i :8000
   lsof -i :5433
   ```
2. Pare serviços conflitantes ou altere portas no `docker-compose.yml`

### Problema: Migrações Falhando

**Sintomas:**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**Soluções:**
1. Verifique versão atual:
   ```bash
   alembic current
   ```
2. Force upgrade:
   ```bash
   alembic upgrade head
   ```
3. Em último caso, recrie o schema:
   ```bash
   docker-compose exec python-postgres psql -U aiuser -d aitraining -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   alembic upgrade head
   ```

---

## 👨‍💻 Autor
- [@meiranicolas](https://github.com/meiranicolas) Nicolas Gabriel Santos Meira RM:554464
- [@gustavoaraujo06](https://github.com/gustavoaraujo06) Gustavo Paz Felipe Araujo RM:555277
- [@Joaopcancian](https://github.com/Joaopcancian) João Pedro Cancian RM:555341

---
