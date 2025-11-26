# Idea Inc

> A playground for the 11 fundamental software skills — disguised as a memetic strategy game. Spin up AI-driven populations, drop your wildest ideas into the mix, mutate them with LLMs, and watch the world light up in real time.

## 🎯 Core Concept (In Plain English)

Imagine **Plague Inc**, but instead of germs you’re shipping jokes, conspiracy theories, brand campaigns, or social movements. Every experiment looks like this:

1. Craft an idea (text, tags, target audience, virality knobs).
2. Choose a world topology with 10k+ AI agents.
3. Launch the idea, pause/rewind/boost it, and watch live graphs, heatmaps, and leaderboards.
4. Ask the AI Service to mutate the idea mid-flight so it resonates with a new demographic.
5. Export snapshots, share scenarios, or hook into the API like a researcher.

All of that fun is the wrapper around a serious engineering exercise that checks every “fundamentals” box.

## 🧱 11 Fundamentals at a Glance

| Skill | How we hit it |
| --- | --- |
| **1. API Design** | REST for public flows, GraphQL for dashboards, gRPC between microservices. |
| **2. AuthN/AuthZ** | OAuth2/OIDC logins, JWTs, refresh tokens, passkey-ready, RBAC hooks. |
| **3. Databases** | Postgres (users/worlds), MongoDB (agent state), Redis (snapshots/limits), ClickHouse roadmap. |
| **4. Caching** | Redis hot caches, CDN/edge-ready snapshots, client-side caching via TanStack Query. |
| **5. Event-Driven** | Kafka topics (mocked locally) broadcasting idea_injected, idea_mutated, snapshot_ready. |
| **6. Concurrency** | Async FastAPI services, structured simulation loops, background workers, websockets. |
| **7. Distributed Systems** | API Gateway + microservices, eventual consistency via event bus, service mesh ready. |
| **8. Security** | HTTPS/TLS defaults, mTLS plan, rate limits, OWASP-safe inputs, Vault-ready secrets. |
| **9. Observability** | Structlog JSON logs, Prometheus metrics, OpenTelemetry instrumentation, Grafana dashboards. |
| **10. Cloud & Deployment** | Docker everywhere, Compose/K8s manifests, GitOps hooks, containerized LLM sidecars. |
| **11. AI Integration** | LLM mutation/analyze endpoints, vector store (Chroma → Milvus), RAG context per agent. |

These aren’t hypothetical — the codebase physically wires each fundamental into the gameplay loop.

## 🏗️ Architecture Overview

This is a proper microservices playground: the gateway keeps public traffic sane, the simulation engine runs hot in its own process, the AI service sits beside a vector store, and Kafka glue (mockable locally) keeps everyone in sync. Here’s the bird’s-eye view:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │
│  │  Web App    │  │  Mobile App │  │  Admin UI   │                         │
│  │  (React)    │  │  (Future)   │  │  (Internal) │                         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                         │
└─────────┼────────────────┼────────────────┼─────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY                                       │
│            REST + GraphQL + Auth Middleware + Rate Limiting                 │
└─────────────────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MICROSERVICES                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Auth Service │  │  Simulation  │  │ User Profile │  │  AI Service  │    │
│  │ OAuth2/JWT   │  │   Engine     │  │   Service    │  │  LLM + RAG   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                      │
│  │   Ingest     │  │  Analytics   │  │ Notification │                      │
│  │   Service    │  │   Service    │  │   Service    │                      │
│  └──────────────┘  └──────────────┘  └──────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVENT BUS (Kafka)                                   │
│     idea_injected | idea_spread | agent_action | mutation_created          │
└─────────────────────────────────────────────────────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  PostgreSQL  │  │   MongoDB    │  │   Redis      │  │  Vector DB   │    │
│  │  (Users,     │  │  (Agent      │  │  (Cache,     │  │  (Embeddings │    │
│  │   Worlds)    │  │   State)     │  │   Sessions)  │  │   Memory)    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐                                                          │
│  │  ClickHouse  │                                                          │
│  │  (Analytics) │                                                          │
│  └──────────────┘                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Language**: Python 3.11+ (FastAPI)
- **API**: REST + GraphQL (Strawberry) + gRPC
- **Auth**: OAuth2/OIDC (Google, GitHub), JWT, Passkeys
- **Databases**: PostgreSQL, MongoDB, Redis, ClickHouse
- **Vector DB**: ChromaDB (MVP) → Milvus/Weaviate (v1+)
- **Event Bus**: Kafka (or in-memory mock for MVP)
- **AI/LLM**: OpenAI API / Local LLM

### Infrastructure
- **Containers**: Docker
- **Orchestration**: Kubernetes (K8s)
- **Service Mesh**: Istio/Linkerd
- **GitOps**: ArgoCD
- **Observability**: OpenTelemetry, Prometheus, Grafana, Jaeger

### Frontend (Phase 2)
- **Framework**: React 18+ with TypeScript
- **State**: Zustand / TanStack Query
- **Visualization**: D3.js / Deck.gl for world map
- **API Client**: GraphQL (Apollo) + REST

## 📁 Project Structure

```
idea-inc/
├── services/
│   ├── api_gateway/          # Central API gateway
│   ├── auth_service/         # Authentication & authorization
│   ├── simulation_service/   # Core simulation engine
│   ├── user-service/         # User profiles & stats
│   ├── ai_service/           # LLM integration & mutations
│   ├── analytics-service/    # Metrics & aggregations
│   └── notification-service/ # Webhooks & websockets
├── shared/
│   ├── schemas/              # Shared data models
│   ├── proto/                # gRPC protobuf definitions
│   └── utils/                # Common utilities
├── infra/
│   ├── docker/               # Dockerfiles
│   ├── k8s/                  # Kubernetes manifests
│   ├── helm/                 # Helm charts
│   └── terraform/            # Infrastructure as code
├── frontend/                 # React web application
├── docs/                     # Documentation
├── tests/                    # Integration & E2E tests
├── docker-compose.yml        # Local development
├── docker-compose.prod.yml   # Production-like setup
└── Makefile                  # Common commands
```

## 🎮 Core Features

### MVP (Phase 1)
- [x] User authentication (OAuth2 + JWT)
- [x] Create/join simulation worlds
- [x] Inject ideas with attributes
- [x] Basic agent-based spread simulation (10k agents)
- [x] REST API for all operations
- [x] Basic LLM mutation (deterministic fallback)
- [x] World snapshots & basic analytics
- [x] Docker deployment

### v1 (Phase 2)
- [ ] Kafka event streaming
- [ ] Vector DB + RAG for agent memory
- [ ] GraphQL API
- [ ] Redis caching & leaderboards
- [ ] ClickHouse analytics
- [ ] Full observability stack
- [ ] Role-based access control

### v2+ (Phase 3)
- [ ] Multi-region deployment
- [ ] Service mesh (mTLS)
- [ ] A/B experiments
- [ ] Marketplace for idea templates
- [ ] Monetization features

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/idea-inc.git
cd idea-inc

# (Optional) Create .env pointing to Supabase Postgres
cat <<'EOF' > .env
POSTGRES_HOST=aws-1-us-east-2.pooler.supabase.com
POSTGRES_PORT=6543
POSTGRES_USER=postgres.zukptkfqnfofkodzebec
POSTGRES_PASSWORD=Scholar@9783
POSTGRES_DB=postgres
POSTGRES_SSL=true
EOF

# Start all services (development)
docker-compose up -d

# Or run individual services
cd services/auth_service
pip install -r requirements.txt
uvicorn main:app --reload
```

## 📊 11 Fundamentals Demonstrated

Need receipts? Here’s where each skill lives in the repo:

1. **API Design** – `services/api_gateway`, `shared/proto/` for gRPC.
2. **Authentication** – `services/auth_service` (JWT flows, refresh tokens).
3. **Databases** – `shared/utils/config.py` wiring Postgres + Mongo + Redis.
4. **Caching** – `shared/utils/cache.py`, gateway rate limiter, snapshot caching in simulation service.
5. **Event-Driven** – `shared/utils/events.py`, simulation emits `idea_mutated` etc.
6. **Concurrency** – Async FastAPI apps, `simulation_service/app/engine/world.py` structured loops.
7. **Distributed Systems** – Compose/K8s manifests, API gateway fan-out, eventual consistency via event bus.
8. **Security** – `shared/utils/security.py`, rate limits, HTTPS-first configs.
9. **Observability** – `shared/utils/telemetry.py`, `infra/prometheus`, structured logging middleware.
10. **Cloud/Deployment** – Dockerfiles per service, `docker-compose.yml`, `infra/k8s/`, GitOps notes.
11. **AI Integration** – `services/ai_service` (LLM prompts, vector store, RAG helper).

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

# Virality-Engine
