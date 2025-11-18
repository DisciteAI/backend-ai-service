# AI Training Service

FastAPI microservice for AI-powered personalized training using Google Gemini 1.5 Flash.

## Overview

This service provides intelligent, context-aware training sessions that adapt to each user's level and learning history. It integrates with the .NET backend to fetch user context and track progress while managing conversations with Google's Gemini AI.

## Features

- **Structured Curriculum**: Training follows predefined courses and topics, not free-form chat
- **Personalized Learning**: AI adapts explanations based on user level and history
- **Progress Tracking**: Automatic detection of topic completion and sync with .NET backend
- **Persistent Sessions**: Full conversation history stored in PostgreSQL
- **Prompt Engineering**: Custom system prompts with course/topic context
- **Completion Criteria**: Validates understanding through progressive questions (2/3 correct to pass)

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐
│   .NET API      │◄────►│  Python FastAPI  │◄────►│  Gemini AI     │
│   (Port 8080)   │      │   (Port 8000)    │      │  (Google API)  │
└─────────────────┘      └──────────────────┘      └────────────────┘
        │                         │
        ▼                         ▼
┌─────────────────┐      ┌──────────────────┐
│  PostgreSQL     │      │  PostgreSQL      │
│  (.NET DB)      │      │  (AI Service DB) │
│  Port 5432      │      │  Port 5433       │
│                 │      │                  │
│ - Users         │      │ - ChatSessions   │
│ - Courses       │      │ - ChatMessages   │
│ - Topics        │      │ - SessionContext │
│ - Sessions      │      │                  │
│ - UserProgress  │      │                  │
└─────────────────┘      └──────────────────┘
```

### Key Architecture Principles

1. **Two separate session types:**
   - **TrainingSession (.NET)**: Tracks overall training progress and enrollment
   - **ChatSession (Python)**: Manages AI conversation for a specific topic
2. **Python AI Service** manages conversation history and AI interactions
3. **Retry logic with exponential backoff** on all .NET API calls
4. **ChatSession links to .NET** via user_id, course_id, and topic_id

## Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Docker & Docker Compose (optional, for containerized deployment)
- Google Gemini API Key ([Get one here](https://aistudio.google.com/app/apikey))

## Quick Start

### 1. Environment Setup

```bash
cd Backend.AI.Service

# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_actual_api_key_here
```

### 2. Database Setup

The service uses its own PostgreSQL database, separate from the .NET backend.

**Option A: Using Docker Compose (Recommended)**

```bash
docker-compose up -d ai-postgres
```

**Option B: Local PostgreSQL**

Create a database manually:
```sql
CREATE DATABASE aitraining;
CREATE USER aiuser WITH PASSWORD 'aipass';
GRANT ALL PRIVILEGES ON DATABASE aitraining TO aiuser;
```

### 3. Run Database Migrations

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head
```

### 4. Start the Service

**Development Mode:**
```bash
python -m uvicorn app.main:app --reload --port 8000
```

**Production Mode (Docker):**
```bash
docker-compose up -d
```

## API Endpoints

### Session Management

#### Start New Training Session
```http
POST /api/sessions/start
Content-Type: application/json

{
  "user_id": 1,
  "topic_id": 5,
  "course_id": 2
}
```

**Response:**
```json
{
  "id": 123,
  "user_id": 1,
  "topic_id": 5,
  "course_id": 2,
  "status": "active",
  "started_at": "2025-01-13T10:30:00Z",
  "completed_at": null
}
```

#### Send Message to AI
```http
POST /api/sessions/123/message
Content-Type: application/json

{
  "message": "Can you explain what variables are?"
}
```

**Response:**
```json
{
  "session_id": 123,
  "ai_message": "Great question! A variable is like a container...",
  "topic_completed": false,
  "timestamp": "2025-01-13T10:31:00Z"
}
```

When `topic_completed` is `true`, the session is automatically marked as completed and the .NET API is notified.

#### Get Session Details
```http
GET /api/sessions/123
```

**Response:**
```json
{
  "id": 123,
  "user_id": 1,
  "topic_id": 5,
  "course_id": 2,
  "status": "completed",
  "started_at": "2025-01-13T10:30:00Z",
  "completed_at": "2025-01-13T10:45:00Z",
  "context": {
    "user_level": "beginner",
    "course_title": "Introduction to Programming",
    "topic_title": "Variables and Data Types",
    "learning_objectives": "Understand variables, data types, and assignments"
  },
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Can you explain what variables are?",
      "timestamp": "2025-01-13T10:31:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Great question! A variable is...",
      "timestamp": "2025-01-13T10:31:05Z"
    }
  ]
}
```

### Health Check
```http
GET /api/health
```

## .NET API Integration

The Python service calls these .NET endpoints (all with automatic retry logic):

### Get User Context
```http
GET http://localhost:8080/api/UserProgress/{userId}/context
```

Returns user level, completed topics, and struggle areas.

### Get Topic Details
```http
GET http://localhost:8080/api/TrainingTopics/{topicId}
```

Returns topic details including prompt template and learning objectives.

### Notify Topic Completion
```http
POST http://localhost:8080/api/UserProgress/complete-topic
Content-Type: application/json

{
  "UserId": 1,
  "TopicId": 5,
  "CourseId": 2,
  "CompletedAt": "2025-01-18T10:45:00Z",
  "SessionId": 123
}
```

Updates user progress tracking when topic is completed.

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | **Required** |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://aiuser:aipass@localhost:5433/aitraining` |
| `DOTNET_API_URL` | .NET backend URL | `http://localhost:8080` |
| `DOTNET_API_TIMEOUT` | .NET API request timeout (seconds) | `30` |
| `DOTNET_API_RETRY_ATTEMPTS` | Max retry attempts for .NET calls | `5` |
| `DOTNET_API_RETRY_BASE_DELAY` | Initial retry delay (seconds) | `1.0` |
| `DOTNET_API_RETRY_MAX_DELAY` | Max retry delay (seconds) | `60.0` |
| `DOTNET_API_RETRY_EXPONENTIAL_BASE` | Exponential backoff base | `2.0` |
| `GEMINI_MODEL` | Gemini model name | `gemini-1.5-flash` |
| `GEMINI_TEMPERATURE` | AI response creativity (0.0-1.0) | `0.7` |
| `MAX_CONVERSATION_HISTORY` | Max messages in context | `50` |
| `COMPLETION_MARKER` | Marker for topic completion | `{TOPIC_COMPLETED}` |

See `.env.example` for complete list.

### Retry Logic

All .NET API calls use automatic retry with exponential backoff:
- **Default**: 5 attempts with delays of 1s, 2s, 4s, 8s, 16s
- **Retries on**: Connection errors, timeouts, HTTP 5xx errors
- **Ensures**: Session consistency even during temporary network issues

## Prompt Engineering

### System Prompt Structure

The service builds structured prompts that include:

1. **Course Context**: Current course and topic information
2. **Learning Objectives**: What the student should learn
3. **User Context**: Student's level, completed topics, previous struggles
4. **Teaching Instructions**: How to explain, ask questions, and validate understanding
5. **Completion Criteria**: When to mark topic as complete

### Custom Prompt Templates

You can customize prompts by editing the `PromptTemplate` field in the .NET `TrainingTopic` model:

```python
"""You are an expert tutor in {course_title}.

Topic: {topic_title}
Description: {topic_description}

Student Level: {user_level}
{completed_topics}
{struggles}

[Your custom instructions here]

When student demonstrates understanding, include {completion_marker} in your response.
"""
```

**Available variables:**
- `{course_title}`
- `{topic_title}`
- `{topic_description}`
- `{learning_objectives}`
- `{user_level}`
- `{completed_topics}`
- `{struggles}`
- `{completion_marker}`

## Database Schema

### Tables

**chat_sessions**
- Stores active and completed AI chat sessions
- Links to .NET user, course, and topic IDs
- Tracks conversation status (active, completed, abandoned)

**chat_messages**
- Full conversation history
- Roles: `system`, `user`, `assistant`
- References local ChatSession

**session_contexts**
- User context snapshot for each chat session
- Includes level, completed topics, struggles
- Cached course/topic details

### Session Management

- **ChatSession (Python)**: Manages individual AI conversations for a topic
- **TrainingSession (.NET)**: Tracks overall training enrollment and progress
- These are separate but related - a TrainingSession can have multiple ChatSessions

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## Development

### Project Structure

```
Backend.AI.Service/
├── app/
│   ├── api/              # Route handlers
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic DTOs
│   ├── services/         # Business logic
│   ├── config.py         # Settings
│   ├── database.py       # DB connection
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container build
└── docker-compose.yml    # Docker orchestration
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (when implemented)
pytest
```

### API Documentation

When the service is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment

### Docker Deployment

The service includes a multi-stage Dockerfile for optimized builds:

```bash
# Build image
docker build -t ai-training-service .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f ai-service

# Stop services
docker-compose down
```

### Production Checklist

- [ ] Set `ENVIRONMENT=production` and `DEBUG=false`
- [ ] Use strong database passwords
- [ ] Configure `SERVICE_API_KEY` for .NET integration security
- [ ] Set up proper CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Configure monitoring and logging
- [ ] Set up database backups
- [ ] Use environment variable injection (not .env files)

## Troubleshooting

### Common Issues

**1. Gemini API Key Error**
```
Error: GEMINI_API_KEY is required
```
Solution: Add your API key to `.env` file

**2. Database Connection Failed**
```
Error: Could not connect to PostgreSQL
```
Solution: Ensure PostgreSQL is running on port 5433 or update `DATABASE_URL`

**3. .NET API Unreachable**
```
Warning: Failed to fetch user context from .NET API
```
Solution: Verify `DOTNET_API_URL` and ensure .NET service is running

**4. Topic Not Completing**
```
AI says topic is done but status stays "active"
```
Solution: Check completion marker `{TOPIC_COMPLETED}` is in AI response and .NET webhook succeeds

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [Your repo URL]
- Documentation: [Your docs URL]
