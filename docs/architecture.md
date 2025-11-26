# Idea Inc - Architecture Documentation

## System Overview

Idea Inc is a distributed simulation platform built on microservices architecture, designed to model viral idea propagation across AI-driven agent populations.

## Component Details

### 1. API Gateway

**Purpose**: Central entry point for all client requests

**Responsibilities**:
- Route requests to appropriate microservices
- Handle authentication/authorization
- Rate limiting and throttling
- Request/response transformation
- GraphQL endpoint aggregation

**Tech**: FastAPI with custom middleware

**Endpoints**:
- `POST /api/v1/auth/*` → Auth Service
- `POST /api/v1/worlds/*` → Simulation Service
- `GET /api/v1/users/*` → User Service
- `POST /graphql` → GraphQL aggregator

---

### 2. Auth Service

**Purpose**: Handle all authentication and authorization

**Responsibilities**:
- OAuth2/OIDC integration (Google, GitHub, Apple)
- JWT token issuance and validation
- Passkey/WebAuthn support
- Session management
- Role-based access control (RBAC)

**Data Model**:
```python
class User:
    id: UUID
    email: str
    provider: str  # google, github, local
    provider_id: str
    roles: List[str]  # admin, researcher, player
    created_at: datetime
    last_login: datetime

class Session:
    id: UUID
    user_id: UUID
    access_token: str
    refresh_token: str
    expires_at: datetime
```

**Events Emitted**:
- `user.created`
- `user.logged_in`
- `user.logged_out`

---

### 3. Simulation Service

**Purpose**: Core simulation engine for idea propagation

**Responsibilities**:
- Manage simulation worlds
- Run agent-based simulation loops
- Calculate idea spread probabilities
- Handle idea mutations
- Generate world snapshots

**Data Models**:
```python
class World:
    id: UUID
    creator_id: UUID
    name: str
    config: WorldConfig
    status: str  # created, running, paused, completed
    agent_count: int
    network_type: str  # scale_free, small_world, random
    created_at: datetime

class WorldConfig:
    population_size: int
    network_density: float
    mutation_rate: float
    decay_rate: float
    seed_ideas: List[UUID]

class Agent:
    id: UUID
    world_id: UUID
    profile: AgentProfile
    connections: List[UUID]
    beliefs: List[UUID]  # adopted idea IDs
    state: AgentState
    memory_refs: List[str]  # vector DB references

class AgentProfile:
    age_group: str
    interests: List[str]
    trust_threshold: float  # 0-1
    openness: float  # 0-1
    influence: float  # 0-1
    region: str

class AgentState:
    mood: float
    susceptibility: float
    last_active: datetime

class Idea:
    id: UUID
    creator_id: UUID
    world_id: UUID
    text: str
    media_refs: List[str]
    tags: List[str]
    virality_score: float
    emotional_valence: float
    complexity: float
    parent_id: Optional[UUID]  # for mutations
    embedding_id: str
    created_at: datetime
```

**Spread Algorithm**:
```
For each time step:
    For each agent A with adopted ideas:
        For each connection B of A:
            For each idea I that A has but B doesn't:
                p_transmit = base_virality(I) 
                           * influence(A) 
                           * openness(B) 
                           * relevance(I, B.interests)
                           * trust_factor(A, B)
                           * context_modifier(world_state)
                
                if random() < p_transmit:
                    B.adopt(I)
                    emit event: idea_spread
                    
                    if random() < mutation_rate:
                        I' = mutate(I)
                        emit event: idea_mutated
```

**Events Emitted**:
- `world.created`
- `world.started`
- `world.paused`
- `idea.injected`
- `idea.spread`
- `idea.mutated`
- `snapshot.ready`

---

### 4. User Service

**Purpose**: Manage user profiles and game statistics

**Responsibilities**:
- Store user preferences
- Track gameplay statistics
- Manage achievements/badges
- Handle user settings

**Data Model**:
```python
class UserProfile:
    user_id: UUID
    display_name: str
    avatar_url: str
    bio: str
    preferences: Dict
    created_at: datetime

class UserStats:
    user_id: UUID
    worlds_created: int
    ideas_launched: int
    total_reach: int
    highest_virality: float
    achievements: List[str]
```

---

### 5. AI Service

**Purpose**: LLM integration for idea generation and mutation

**Responsibilities**:
- Generate new ideas based on prompts
- Mutate existing ideas
- Calculate idea embeddings
- RAG-based context retrieval
- Cultural sensitivity analysis

**Mutation Pipeline**:
```
1. Receive mutation request (idea_id, mutation_type)
2. Retrieve idea from DB
3. Query vector DB for similar ideas (context)
4. Construct LLM prompt with constraints
5. Generate N variants
6. Filter for safety (toxicity check)
7. Calculate new embeddings
8. Score variants for virality
9. Return best variant
```

**Mutation Types**:
- `simplify` - Make more accessible
- `emotionalize` - Increase emotional appeal
- `localize` - Adapt for specific region
- `polarize` - Make more controversial
- `memeify` - Convert to meme format

---

### 6. Analytics Service

**Purpose**: Aggregate and compute simulation metrics

**Responsibilities**:
- Process event streams
- Calculate real-time metrics (R₀, reach, saturation)
- Generate time-series data
- Power dashboard visualizations

**Metrics Computed**:
- **R₀ (Basic Reproduction Number)**: Average secondary infections per idea
- **Reach**: Total unique agents exposed
- **Adoption Rate**: Percentage of exposed agents who adopt
- **Mutation Advantage**: Virality gain from mutations
- **Regional Heatmaps**: Geographic distribution
- **Saturation Level**: Percentage of population infected

---

### 7. Event Bus (Kafka)

**Topics**:
- `idea-events`: idea_injected, idea_spread, idea_mutated
- `agent-events`: agent_created, agent_adopted, agent_rejected
- `world-events`: world_created, world_started, snapshot_ready
- `user-events`: user_created, user_logged_in
- `analytics-events`: metrics_computed

**Consumer Groups**:
- `analytics-consumer`: Analytics Service
- `notification-consumer`: Notification Service
- `ai-consumer`: AI Service (for mutation triggers)

---

## Data Flow

### Idea Injection Flow
```
1. User submits idea via REST API
2. API Gateway validates JWT, routes to Simulation Service
3. Simulation Service:
   - Validates idea
   - Requests embedding from AI Service
   - Stores idea in DB
   - Emits `idea_injected` event
4. Simulation loop picks up idea for propagation
```

### Spread Calculation Flow
```
1. Simulation Service runs tick
2. For each spread event:
   - Calculate probability
   - Update agent state
   - Emit `idea_spread` event
3. Kafka delivers to consumers
4. Analytics Service updates metrics
5. Redis cache updated with latest snapshot
6. WebSocket pushes update to connected clients
```

---

## Security Architecture

### Authentication Flow
```
1. User initiates OAuth2 flow
2. Redirect to provider (Google/GitHub)
3. Provider returns auth code
4. Auth Service exchanges code for tokens
5. Auth Service creates/updates user
6. Issues JWT (access + refresh tokens)
7. Client stores tokens securely
```

### Authorization
- **JWT Claims**: user_id, roles, permissions
- **RBAC Roles**: admin, researcher, player, guest
- **Resource-level**: World ownership, idea ownership

### Security Measures
- HTTPS everywhere (TLS 1.3)
- mTLS between services
- JWT with short expiry (15 min access, 7 day refresh)
- Rate limiting per user/IP
- Input validation (Pydantic)
- SQL injection prevention (parameterized queries)
- XSS prevention (output encoding)

---

## Scalability Considerations

### Horizontal Scaling
- Stateless services behind load balancer
- Kafka partitioning by world_id
- Database sharding by region

### Caching Strategy
- **L1**: In-memory (per-service)
- **L2**: Redis (shared)
- **L3**: CDN (static assets, public snapshots)

### Performance Targets
- MVP: 10k agents, single world
- v1: 100k agents, 100 concurrent worlds
- v2: 1M agents, global distribution

---

## Observability

### Tracing
- OpenTelemetry SDK in all services
- Trace ID propagated via headers
- Jaeger for trace visualization

### Metrics
- Prometheus scraping `/metrics` endpoints
- Custom metrics: spread_rate, mutation_count, active_worlds
- Grafana dashboards

### Logging
- Structured JSON logs
- Correlation IDs
- Log levels: DEBUG, INFO, WARN, ERROR
- Aggregation via Loki/ELK

### Alerting
- SLA breach alerts
- Error rate spikes
- Kafka consumer lag
- Service health checks

