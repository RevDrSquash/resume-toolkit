# Industry Signals: Senior Software & AI Engineering

Domain-specific keywords and signals that recruiters search for in senior software and AI engineering roles, regardless of whether the specific job description mentions them. Used by `extract-job-signals` (to detect implicit expectations), `build-targeted-resume` (to ensure coverage), and `review-resume` (to flag gaps).

## How to use this document

When the target role is senior software engineering, AI/ML engineering, or related infrastructure work:

- Treat the keywords in the **Universal** and **role-relevant category** sections as *expected to appear* in the resume even if not in the JD.
- Treat the **Avoid** list as items that should be removed if present — they actively harm a senior resume.
- Don't include every keyword. Include the ones the candidate genuinely has.

## Universal senior software engineering keywords

Expected for any staff/senior/principal role, regardless of stack:

| Category | Keywords |
|----------|----------|
| Architecture & System Design | System Design, Microservices Architecture, Distributed Systems, High Availability, Event-Driven Architecture, Scalability, Fault Tolerance, API Design |
| Infrastructure & DevOps | CI/CD Pipelines, Infrastructure as Code (IaC), Docker, Kubernetes, Terraform, GitOps |
| Reliability & Operations | Observability, Distributed Tracing, Latency Optimization, Performance Optimization, Incident Response, SLO/SLA Management, Post-mortems |
| Technical Leadership | Technical Strategy, Cross-Functional Collaboration, Mentoring, Architecture Decisions, Technical Roadmap, Tech Debt Reduction |

## AI / ML engineering keywords

For roles tagged as AI Engineer, ML Engineer, ML Infrastructure, Applied AI, etc.:

| Category | Keywords |
|----------|----------|
| LLMs & Core Technologies | Large Language Models (LLMs), Generative AI, Retrieval-Augmented Generation (RAG), Model Fine-Tuning, LoRA, Semantic Search, Hybrid Search |
| Orchestration & Agents | LangChain, LlamaIndex, Multi-Agent Systems, Agentic Workflows, Prompt Engineering, Function Calling, Tool Use |
| Infrastructure & Data | Vector Databases, Pinecone, pgvector, Weaviate, Custom Embeddings, Context Window Optimization |
| APIs & Evaluation | OpenAI API, Anthropic API, Model Evaluation, AI Guardrails, Hallucination Reduction |
| Serving & Performance | Model Serving, Inference Optimization, vLLM, TensorRT, GPU Resource Management, CUDA, Distributed Training |
| ML Operations | MLOps, CI/CD for ML, Model Registry, Model Drift Detection, LLM Observability |

## Cloud & distributed systems (AWS-heavy)

For cloud infrastructure or platform roles:

| Category | Keywords |
|----------|----------|
| AWS Services | Amazon Web Services (AWS), Amazon S3, DynamoDB, Amazon EMR, AWS SageMaker, AWS Bedrock, Lambda, ECS, EKS |
| Data Processing | Apache Spark, ETL Pipelines, Real-Time Data Streaming, Apache Kafka, RabbitMQ |
| Production Scale | Load Balancing, Data Replication, Concurrency, Sharding, Consistency Models, Caching Strategies |

## Bridge keywords for the C++ → AI pivot

For candidates moving from C++/systems engineering into AI/ML engineering. These signal that systems experience is the foundation for, not a distraction from, AI infrastructure work:

- High-Performance Compute (HPC)
- Latency Optimization & Throughput
- Distributed Training / Edge Computing
- Scalable Inference Architecture
- Vector Search Optimization
- Concurrency & Parallel Processing
- Memory Management (smart pointers, RAII)
- Multithreading
- Hardware Acceleration

For systems-engineering work, reframe in production-AI language where possible:

| Systems-engineering task | AI/ML resume framing |
|--------------------------|----------------------|
| Writing fast C++ execution code | Model Serving, Inference Optimization, vLLM, TensorRT |
| Managing memory & compute loads | GPU Resource Management, CUDA, Distributed Training |
| Monitoring application health | Model Drift Detection, AI Guardrails, LLM Observability |
| Automating code pushes | MLOps, CI/CD for ML, Model Registry |
| Building data pipelines | ML Data Pipelines, Feature Engineering, Vector Indexing |

## Keywords to avoid

Items that signal outdated practice, fluff, or lack of specificity at the senior level:

| Category | Avoid | Reason |
|----------|-------|--------|
| Behavioral fluff | results-driven, synergy, rockstar, ninja, guru, go-getter, team player, passionate, dynamic, innovative | Invisible to ATS; signals nothing to recruiters; consumes space |
| Outdated tech as primary skills | jQuery, Subversion (SVN), "Web 2.0", Flash, AngularJS (v1) | Signals stagnant skill set |
| Overly broad AI terms | "Machine Learning" alone, "Deep Learning" alone, "AI" alone | Use specific subdomains: RAG, LoRA fine-tuning, multi-agent systems, etc. |
| Self-evident senior skills | "Strong communication", "Problem solving", "Critical thinking" | Assumed at senior level; saying them flags as junior |

## Implicit expectations by role type

Some keywords are implicit prerequisites that recruiters search for even when not in the JD. If a role matches one of these archetypes, ensure the implicit set is covered.

**"Senior Software Engineer" or "Staff Engineer"** (generic):
- System Design, Distributed Systems, CI/CD, Cloud Computing, Mentoring, Cross-Functional Collaboration

**"AI Engineer" or "ML Engineer"**:
- LLMs, RAG, Python, Vector Databases, Model Evaluation, MLOps, Prompt Engineering

**"ML Infrastructure" or "AI Platform"**:
- Distributed Training, Model Serving, Kubernetes, GPU Resource Management, Inference Optimization, MLOps, Observability

**"Backend Engineer (Senior)"**:
- System Design, Microservices, Databases (relational + NoSQL), API Design, Distributed Systems, Caching, Load Balancing

**"DevOps / SRE / Platform Engineer"**:
- Kubernetes, Terraform, CI/CD, Observability, SLO/SLA Management, Incident Response, Infrastructure as Code
