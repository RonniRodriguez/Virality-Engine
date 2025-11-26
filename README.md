# Virality Engine

Virality Engine is a social-simulation lab disguised as a game. You design AI-driven populations, craft ideas or memes, let the AI service mutate those ideas in real time, and study how they move across the network. The playful surface exists so every major engineering fundamental shows up in real code instead of bullet points on a resume.

## Core Concept

The experience resembles Plague Inc., but the “pathogen” is a marketing campaign, joke, or conspiracy. A typical run looks like this:

1. Describe the idea: text, tags, demographics, virality/emotional sliders.
2. Spin up a world with 10k+ agents, each with openness, influence, trust, mood, memory, and geography.
3. Launch the idea, pause or rewind the simulation whenever you need, and watch live graphs, heat maps, mutation feeds, and leaderboards.
4. Ask the AI service to mutate or analyze the idea so it lands with a new audience.
5. Export the snapshot or rerun everything through the REST/GraphQL/gRPC interfaces for research or automation.

## Fundamentals Snapshot

1. **API design** – FastAPI REST endpoints, GraphQL dashboard plans, gRPC contracts in `shared/proto`.
2. **Authentication / authorization** – OAuth2/OIDC providers, short-lived JWTs, refresh flows, RBAC hooks in `services/auth_service`.
3. **Databases** – Postgres for users/worlds, MongoDB for agent state, Redis for caching and rate limits, ClickHouse planned for analytics.
4. **Caching** – Redis adapters in `shared/utils/cache.py`, API Gateway rate limiting, simulation snapshot caches, CDN-friendly payloads.
5. **Event-driven flows** – Kafka abstractions in `shared/utils/events.py`; simulation emits `idea_injected`, `idea_mutated`, and `world_snapshot`.
6. **Concurrency** – Async FastAPI everywhere, structured world-stepping loops, background workers for LLM calls, gateway streaming.
7. **Distributed systems** – API Gateway fronting multiple services, eventual consistency via the event bus, K8s/mesh-ready manifests.
8. **Security** – Token helpers in `shared/utils/security.py`, HTTPS defaults, rate limits, OWASP-safe parsing, Vault-ready secret loading.
9. **Observability** – Structlog JSON logs, OpenTelemetry helper utilities, Prometheus scrape configs, Grafana dashboards.
10. **Cloud / deployment** – Dockerfiles per service, docker-compose for local, Helm/K8s/GitOps scaffolding in `infra/`.
11. **AI integration** – `services/ai_service` handles prompt templates, LLM client, vector store (Chroma now, Milvus later), and RAG helpers.

## Architecture Overview

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

## Tech Stack

### Backend
- **Language**: Python 3.11+ (FastAPI)
- **API**: REST + GraphQL (Strawberry) + gRPC
- **Auth**: OAuth2/OIDC (Google, GitHub), JWT, Passkeys
- **Databases**: PostgreSQL, MongoDB, Redis, ClickHouse
- **Vector DB**: ChromaDB (MVP) → Milvus/Weaviate (v1+)
- **Event Bus**: Kafka (or in-memory mock for MVP)
- **AI/LLM**: OpenAI API / Local LLM

### Infrastructure
- **Containers**: Docker for local dev; production services use managed cloud runtimes
- **Orchestration**: Kubernetes (K8s) if self-hosting the stack
- **Service Mesh**: Istio/Linkerd, optional once you move off managed gateways
- **GitOps**: ArgoCD (planned when deploying your own cluster)
- **Observability**: OpenTelemetry, Prometheus, Grafana, Jaeger (self-hosted or managed equivalents)

### Frontend (Phase 2)
- **Framework**: React 18+ with TypeScript
- **State**: Zustand / TanStack Query
- **Visualization**: D3.js / Deck.gl for world map
- **API Client**: GraphQL (Apollo) + REST

## Project Structure

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

## Core Features

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

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/idea-inc.git
cd idea-inc

# Copy and edit env vars (points to managed Supabase, MongoDB Atlas, Redis Cloud)
cp env.example .env
vim .env

# Install Python deps and run services (frontend is Vite-based, see README)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn services.api_gateway.main:app --host 0.0.0.0 --port 8080

# Run frontend
cd frontend
npm install
npm run dev
```

## License

MIT License – see [LICENSE](LICENSE) for details.
