# Vortex
A brand that leads in the world of confused with clarity

---

## AUGUSTUS — Elite Software Engineering & AI Reference Guide

> **Purpose:** Operate at the highest level across software engineering, AI/ML, and data engineering — a personal reference for mastering the tools, frameworks, and practices that define world-class technical work.

---

## Table of Contents

1. [Software Engineering Foundations](#1-software-engineering-foundations)
2. [System Design & Architecture](#2-system-design--architecture)
3. [Data Engineering](#3-data-engineering)
4. [AI / Machine Learning](#4-ai--machine-learning)
5. [DevOps & Platform Engineering](#5-devops--platform-engineering)
6. [Security Engineering](#6-security-engineering)
7. [Key Languages & Ecosystems](#7-key-languages--ecosystems)
8. [Coding Patterns & Best Practices](#8-coding-patterns--best-practices)
9. [Career & Mindset](#9-career--mindset)

---

## 1. Software Engineering Foundations

### Core Principles
| Principle | Description |
|-----------|-------------|
| **SOLID** | Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion |
| **DRY** | Don't Repeat Yourself — extract shared logic into reusable abstractions |
| **KISS** | Keep It Simple, Stupid — favour clarity over cleverness |
| **YAGNI** | You Aren't Gonna Need It — don't build features before they're required |
| **Separation of Concerns** | Each module owns one well-defined responsibility |

### Design Patterns (GoF)
- **Creational:** Factory, Abstract Factory, Builder, Singleton, Prototype
- **Structural:** Adapter, Bridge, Composite, Decorator, Facade, Proxy
- **Behavioral:** Strategy, Observer, Command, Iterator, State, Template Method, Chain of Responsibility

### Testing Pyramid
```
        /\
       /E2E\          ← few, slow, high-confidence
      /------\
     /Integration\    ← moderate, test component boundaries
    /------------\
   /  Unit Tests  \   ← many, fast, isolate single units
  /________________\
```
- **Test-Driven Development (TDD):** Red → Green → Refactor
- **Behaviour-Driven Development (BDD):** Given / When / Then (Cucumber, Gherkin)
- **Property-Based Testing:** QuickCheck, Hypothesis, jqwik

### Version Control (Git) Workflows
- **GitFlow:** `main` + `develop` + `feature/*` + `release/*` + `hotfix/*`
- **Trunk-Based Development:** short-lived branches, frequent merges to `main`, feature flags
- **Conventional Commits:** `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`

---

## 2. System Design & Architecture

### Distributed Systems Fundamentals
- **CAP Theorem:** When a network partition occurs, distributed systems must trade off consistency vs availability
- **BASE vs ACID:** Eventually consistent (NoSQL) vs strictly transactional (RDBMS)
- **Consensus Algorithms:** Raft, Paxos — used in etcd, ZooKeeper, Kafka controller

### Architecture Styles
| Style | When to Use |
|-------|-------------|
| Monolith | Small teams, early-stage products, low operational overhead |
| Microservices | Independent scaling, polyglot stacks, Conway's Law alignment |
| Event-Driven | High throughput, loose coupling, audit trails (Kafka, EventBridge) |
| Serverless | Bursty workloads, low ops, cost-per-invocation model |
| CQRS + Event Sourcing | Complex domains, auditability, temporal queries |

### Key Scalability Patterns
- **Horizontal vs Vertical Scaling**
- **Load Balancing:** Round Robin, Least Connections, Consistent Hashing
- **Caching:** CDN → Reverse Proxy (Varnish/Nginx) → Application (Redis/Memcached) → Database query cache
- **Database Sharding & Read Replicas**
- **Circuit Breaker, Bulkhead, Retry with Exponential Backoff** (Resilience4j, Polly)
- **Saga Pattern** for distributed transactions

### API Design
- **REST:** Stateless, resource-oriented, HTTP verbs, OpenAPI/Swagger spec
- **GraphQL:** Client-driven queries, single endpoint, DataLoader for N+1 mitigation
- **gRPC:** Binary Protobuf, strongly typed, bi-directional streaming, ideal for internal services
- **AsyncAPI:** Describe event-driven APIs (Kafka, AMQP, WebSocket)

---

## 3. Data Engineering

### Core Concepts
- **Data Lake vs Data Warehouse vs Lakehouse**
  - Lake: raw, schema-on-read (S3, GCS, ADLS)
  - Warehouse: curated, schema-on-write (Snowflake, BigQuery, Redshift)
  - Lakehouse: best of both (Delta Lake, Apache Iceberg, Apache Hudi)
- **Batch vs Streaming Processing**
  - Batch: Spark, dbt, AWS Glue
  - Streaming: Apache Flink, Spark Structured Streaming, Kafka Streams

### Data Modelling
- **Kimball (Star/Snowflake Schema):** Facts + Dimensions, optimised for analytics
- **Data Vault 2.0:** Hubs, Links, Satellites — audit-friendly, historised
- **One Big Table (OBT):** Denormalised for BI tools, column-store engines

### Modern Data Stack
```
Ingestion        → Fivetran / Airbyte / Kafka Connect
Transformation   → dbt (SQL) / Spark (Python/Scala)
Storage          → Snowflake / BigQuery / Databricks
Orchestration    → Apache Airflow / Prefect / Dagster
Serving          → Looker / Metabase / Superset / Tableau
Quality          → Great Expectations / dbt tests / Monte Carlo
```

### Data Quality Dimensions
- **Completeness, Accuracy, Consistency, Timeliness, Uniqueness, Validity**

### Key File Formats
| Format | Best For |
|--------|----------|
| Parquet | Columnar analytics, Spark/Hive |
| Avro | Row-based, schema evolution, Kafka serialisation |
| ORC | Hive-optimised columnar |
| Delta/Iceberg | ACID transactions on data lakes |
| JSON / CSV | Interchange, debugging, small datasets |

---

## 4. AI / Machine Learning

### ML Workflow (MLOps Lifecycle)
```
Problem Definition
      ↓
Data Collection & Labelling
      ↓
Exploratory Data Analysis (EDA)
      ↓
Feature Engineering
      ↓
Model Training & Hyperparameter Tuning
      ↓
Evaluation (metrics, bias, fairness)
      ↓
Deployment (serving, A/B, shadow)
      ↓
Monitoring & Retraining
```

### Supervised Learning
- **Regression:** Linear, Ridge, Lasso, Gradient Boosted Trees (XGBoost, LightGBM)
- **Classification:** Logistic Regression, SVM, Random Forests, Neural Networks
- **Evaluation:** Accuracy, Precision, Recall, F1, AUC-ROC, Confusion Matrix, RMSE

### Unsupervised Learning
- **Clustering:** K-Means, DBSCAN, Hierarchical
- **Dimensionality Reduction:** PCA, t-SNE, UMAP
- **Anomaly Detection:** Isolation Forest, Autoencoders

### Deep Learning
- **Frameworks:** PyTorch (research-first), TensorFlow/Keras (production pipelines)
- **Architectures:**
  - CNN — image recognition, spatial features
  - RNN / LSTM / GRU — sequential data, time series
  - Transformer — attention mechanism, backbone of modern NLP & vision
  - Diffusion Models — generative image synthesis (DALL-E, Stable Diffusion)

### Large Language Models (LLMs)
- **Foundation Models:** GPT-4, Claude, Gemini, Llama, Mistral
- **Fine-Tuning:** Full fine-tune, LoRA/QLoRA, PEFT
- **Retrieval-Augmented Generation (RAG):** vector store (Pinecone, Weaviate, pgvector) + LLM
- **Prompt Engineering:** Zero-shot, Few-shot, Chain-of-Thought, ReAct
- **Evaluation:** BLEU, ROUGE, BERTScore, human evals, LLM-as-judge

### MLOps Tooling
| Category | Tools |
|----------|-------|
| Experiment Tracking | MLflow, Weights & Biases, Neptune |
| Feature Store | Feast, Tecton, Vertex AI Feature Store |
| Model Registry | MLflow, SageMaker Model Registry |
| Serving | Triton, BentoML, TorchServe, Seldon, Ray Serve |
| Pipelines | Kubeflow, SageMaker Pipelines, Vertex AI Pipelines |
| Monitoring | Evidently, Arize, WhyLabs |

---

## 5. DevOps & Platform Engineering

### CI/CD
- **Pipelines:** GitHub Actions, GitLab CI, Jenkins, CircleCI, Tekton
- **Stages:** Lint → Build → Unit Test → Integration Test → Security Scan → Deploy → Smoke Test
- **Deployment Strategies:** Rolling, Blue/Green, Canary, Feature Flags (LaunchDarkly, Flagsmith)

### Containerisation & Orchestration
- **Docker:** Multi-stage builds, minimal base images (`distroless`, `alpine`), `.dockerignore`
- **Kubernetes:** Pods, Deployments, Services, Ingress, HPA, VPA, RBAC, NetworkPolicy
- **Helm:** Kubernetes package manager, chart templating
- **Service Mesh:** Istio, Linkerd — mTLS, traffic shaping, observability

### Infrastructure as Code (IaC)
- **Terraform:** HCL, provider ecosystem, state management, modules, Terragrunt
- **Pulumi:** IaC with real programming languages (Python, TypeScript, Go)
- **AWS CDK / Bicep / CloudFormation / ARM**

### Observability (The Three Pillars)
```
Logs     → structured JSON, centralised (ELK, Loki, CloudWatch)
Metrics  → time-series (Prometheus + Grafana, Datadog, New Relic)
Traces   → distributed tracing (Jaeger, Zipkin, OpenTelemetry)
```
- **SLI / SLO / SLA / Error Budgets** — site reliability engineering (SRE) model
- **Incident Management:** PagerDuty, Opsgenie, blameless post-mortems

---

## 6. Security Engineering

### Secure Coding
- **OWASP Top 10:** Injection, Broken Access Control, Identification and Authentication Failures, Security Misconfiguration, etc.
- **Input Validation & Output Encoding** — never trust external input
- **Parameterised Queries / Prepared Statements** — prevent SQL injection
- **Secrets Management:** HashiCorp Vault, AWS Secrets Manager, never commit secrets to git

### Authentication & Authorisation
- **OAuth 2.0 / OIDC:** Authorisation Code Flow (PKCE for SPAs), Client Credentials (M2M)
- **JWT:** Stateless tokens, sign with RS256/ES256, validate `exp`, `iss`, `aud`
- **RBAC / ABAC / ReBAC:** Role-based, Attribute-based, Relationship-based access control

### Supply Chain Security
- **SBOM:** Software Bill of Materials (CycloneDX, SPDX)
- **Dependency Scanning:** Dependabot, Snyk, OWASP Dependency-Check
- **Container Scanning:** Trivy, Grype, Clair
- **SLSA Framework:** Supply chain Levels for Software Artifacts

---

## 7. Key Languages & Ecosystems

### Python
- **Standard Library:** `asyncio`, `dataclasses`, `pathlib`, `typing`, `contextlib`
- **Web:** FastAPI (async, OpenAPI), Django (batteries-included), Flask (micro)
- **Data:** Pandas, Polars (Rust-backed, faster), NumPy, Pydantic
- **Async:** `asyncio`, `aiohttp`, `httpx`, `Trio`
- **Tooling:** `uv` (fast package manager), `ruff` (linter/formatter), `mypy` (type checker), `pytest`

### Java / JVM
- **Frameworks:** Spring Boot 3 (reactive with WebFlux), Micronaut, Quarkus (GraalVM native)
- **Concurrency:** `CompletableFuture`, Project Loom (virtual threads, Java 21+)
- **Build:** Maven, Gradle
- **Testing:** JUnit 5, Mockito, AssertJ, Testcontainers

### TypeScript / JavaScript
- **Runtimes:** Node.js, Deno, Bun
- **Web Frameworks:** Next.js, Remix, Fastify, NestJS
- **Frontend:** React, Vue, Svelte; State: Zustand, Jotai, TanStack Query
- **Tooling:** `tsc`, ESLint, Prettier, Vitest, Playwright

### Go
- Idiomatic Go: small interfaces, explicit error handling, goroutines + channels
- **Frameworks:** Gin, Echo, Chi, connect-go (gRPC)
- **Tooling:** `go vet`, `golangci-lint`, `go test -race`

### Rust
- Ownership model eliminates entire classes of memory bugs
- **Web:** Axum, Actix-web
- **Use cases:** CLI tools (ripgrep, fd), WebAssembly, systems programming, performance-critical libraries

---

## 8. Coding Patterns & Best Practices

### Code Quality
- **Clean Code:** meaningful names, small functions, no magic numbers, self-documenting code
- **Code Reviews:** constructive, focus on logic & maintainability, not style (automate style)
- **Refactoring:** Strangler Fig, Extract Method, Replace Conditional with Polymorphism

### Performance Engineering
1. **Measure first** — profile before optimising (Py-Spy, async-profiler, pprof)
2. **Algorithmic complexity** — Big-O; prefer O(log n) / O(n) over O(n²)
3. **Database:** index on query predicates, avoid N+1 (use joins/eager loading/DataLoader)
4. **Caching strategy:** Cache-aside, Write-through, Write-behind, TTL tuning
5. **Async I/O** — non-blocking for I/O-bound; thread pools for CPU-bound

### Concurrency Models
| Model | Language / Tool |
|-------|-----------------|
| Threads | Java, C++, Python (GIL limits CPU parallelism) |
| Async/Await | Python `asyncio`, JavaScript, Rust `tokio` |
| Goroutines | Go (M:N scheduling, cheap) |
| Virtual Threads | Java 21+ (Project Loom) |
| Actor Model | Akka (JVM), Erlang/Elixir |
| CSP (channels) | Go, Clojure `core.async` |

### Documentation
- **Code:** docstrings / Javadoc, inline comments only for *why* not *what*
- **Architecture:** Architecture Decision Records (ADRs), C4 diagrams (Context, Container, Component, Code)
- **APIs:** OpenAPI 3.x, AsyncAPI, living docs generated from code

---

## 9. Career & Mindset

### Engineering Levels (typical progression)
| Level | Focus |
|-------|-------|
| Junior | Execute tasks, learn codebase, pair programme |
| Mid | Own features end-to-end, unblock self, write tests |
| Senior | Design systems, mentor, raise engineering standards |
| Staff | Cross-team technical leadership, strategy, org-wide impact |
| Principal / Distinguished | Industry-shaping contributions, define technical direction |

### Learning Strategies
- **Deliberate Practice:** build projects outside comfort zone, not just tutorials
- **Read Source Code:** top OSS projects (Linux kernel, CPython, Redis, Kafka)
- **Write About It:** blog posts, RFCs, ADRs — teaching cements understanding
- **System Design Practice:** Grokking the System Design Interview, Designing Data-Intensive Applications (Kleppmann)

### Key Books
| Book | Topic |
|------|-------|
| *Designing Data-Intensive Applications* — Kleppmann | Distributed systems, data |
| *The Pragmatic Programmer* — Hunt & Thomas | Craft & mindset |
| *Clean Code* — Martin | Readable, maintainable code |
| *Site Reliability Engineering* — Google | SRE practices |
| *Accelerate* — Forsgren et al. | Engineering performance metrics |
| *Hands-On Machine Learning* — Géron | ML with Scikit-Learn & TensorFlow |

### Essential Online Resources
- **System Design:** [ByteByteGo](https://bytebytego.com), [system-design-primer](https://github.com/donnemartin/system-design-primer)
- **Algorithms:** [LeetCode](https://leetcode.com), [NeetCode.io](https://neetcode.io)
- **ML/AI:** [fast.ai](https://fast.ai), [Hugging Face](https://huggingface.co), [Papers With Code](https://paperswithcode.com)
- **Data Engineering:** [DataEngineeringWiki](https://dataengineering.wiki), [dbt Learn](https://courses.getdbt.com)
- **Security:** [OWASP](https://owasp.org), [HackTheBox](https://hackthebox.com), [TryHackMe](https://tryhackme.com)

---

*"The best engineers are not those who know the most — they are those who learn the fastest, communicate clearly, and build systems others can maintain."*
