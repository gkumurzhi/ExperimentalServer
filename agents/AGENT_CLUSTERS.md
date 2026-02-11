# Agent Clusters

> **Generated:** 2026-01-23
> **Total Agents:** 63
> **Total Clusters:** 17

## How to Use This Document

1. **Identify your task type** - What problem are you solving?
2. **Find the matching cluster(s)** - Scan cluster names and "When to use" bullets
3. **Select the most specific agent** - Review agents within the cluster
4. **Cross-reference via Agent Index** - See which other clusters an agent belongs to

**Note:** Some agents appear in multiple clusters. This is intentional - they have cross-domain expertise.

---

## Clusters

### 1. Architecture & System Design

**When to use:**
- Designing new system architecture or evaluating scalability
- Making decisions about design patterns or technology choices
- Planning major architectural changes or refactoring structure

**Typical outcomes:**
- System design documents and architectural diagrams
- Technology recommendations with trade-off analysis
- Refactoring roadmaps for legacy systems

**Agents:**
- [`architecture-advisor.md`](architecture-advisor.md) - System architecture decisions and pattern evaluation
- [`architecture-designer.md`](architecture-designer.md) - Codebase structure and maintainability design
- [`cloud-architect.md`](cloud-architect.md) - Cloud infrastructure design for scalability
- [`orchestration-specialist.md`](orchestration-specialist.md) - Multi-domain task coordination

---

### 2. Infrastructure & DevOps

**When to use:**
- Setting up or optimizing cloud infrastructure
- Containerizing applications or managing Kubernetes
- Building CI/CD pipelines or automation workflows

**Typical outcomes:**
- Terraform modules and infrastructure-as-code
- Docker/Kubernetes configurations
- Automated deployment pipelines

**Agents:**
- [`terraform-infrastructure-architect.md`](terraform-infrastructure-architect.md) - Terraform IaC design and multi-cloud setups
- [`kubernetes-specialist.md`](kubernetes-specialist.md) - K8s deployments, Helm charts, cluster management
- [`docker-containerization-expert.md`](docker-containerization-expert.md) - Dockerfiles, multi-stage builds, compose
- [`devops-deployer.md`](devops-deployer.md) - CI/CD pipeline setup and troubleshooting
- [`cloud-cost-optimizer.md`](cloud-cost-optimizer.md) - AWS/cloud cost reduction and right-sizing
- [`automation-architect.md`](automation-architect.md) - Scheduled jobs, workflow automation, triggers
- [`workflow-orchestrator.md`](workflow-orchestrator.md) - DAG pipelines and task execution flows

---

### 3. Performance & Optimization

**When to use:**
- Application is slow or experiencing latency issues
- Database queries need optimization
- Validating scalability before launch

**Typical outcomes:**
- Optimized queries and caching strategies
- Performance profiling reports
- Load test results with bottleneck identification

**Agents:**
- [`perf-optimizer.md`](perf-optimizer.md) - Application performance and caching implementation
- [`database-optimizer.md`](database-optimizer.md) - Query optimization and schema design
- [`db-optimizer.md`](db-optimizer.md) - Database performance and indexing strategies
- [`load-test-architect.md`](load-test-architect.md) - Load/stress testing and capacity validation

---

### 4. Reliability & Operations (SRE)

**When to use:**
- Defining SLOs or implementing error budgets
- Setting up monitoring, alerting, or dashboards
- Managing production deployments and rollbacks

**Typical outcomes:**
- SLI/SLO definitions and monitoring configurations
- Alerting rules and incident response runbooks
- Zero-downtime deployment strategies

**Agents:**
- [`sre-reliability-engineer.md`](sre-reliability-engineer.md) - SLOs, error budgets, incident response
- [`observability-specialist.md`](observability-specialist.md) - Monitoring, logging, alerting setup
- [`release-manager.md`](release-manager.md) - Deployment management and feature flags

---

### 5. Security & Compliance

**When to use:**
- Reviewing code for security vulnerabilities
- Implementing authentication/authorization
- Ensuring GDPR/CCPA or other regulatory compliance

**Typical outcomes:**
- Security audit reports with remediation steps
- Secure authentication implementations
- Privacy-compliant data handling workflows

**Agents:**
- [`security-auditor.md`](security-auditor.md) - Vulnerability detection and secure coding
- [`privacy-compliance-specialist.md`](privacy-compliance-specialist.md) - GDPR/CCPA compliance and consent flows

---

### 6. Frontend Development

**When to use:**
- Building React, Next.js, or Vue applications
- Designing TypeScript type systems
- Implementing component architectures

**Typical outcomes:**
- Production-ready frontend components
- Type-safe application architectures
- Performance-optimized rendering patterns

**Agents:**
- [`react-specialist.md`](react-specialist.md) - React hooks, state management, optimization
- [`nextjs-expert.md`](nextjs-expert.md) - Next.js App Router, RSC, edge functions
- [`vue3-architect.md`](vue3-architect.md) - Vue 3 Composition API, Pinia, TypeScript
- [`typescript-type-architect.md`](typescript-type-architect.md) - Advanced generics and type design

---

### 7. UI/UX Design & Quality

**When to use:**
- Creating polished, premium interfaces
- Improving user experience or reducing friction
- Ensuring accessibility compliance

**Typical outcomes:**
- High-quality UI components with animations
- UX audit reports with actionable fixes
- WCAG-compliant accessible interfaces

**Agents:**
- [`premium-ui-designer.md`](premium-ui-designer.md) - High-quality visual polish and micro-interactions
- [`design-systems-architect.md`](design-systems-architect.md) - Component libraries and design tokens
- [`ux-writer.md`](ux-writer.md) - Microcopy, error messages, UI text
- [`ux-pain-point-fixer.md`](ux-pain-point-fixer.md) - UX friction analysis and conversion optimization
- [`ux-simplifier.md`](ux-simplifier.md) - UI simplification and flow reduction
- [`a11y-specialist.md`](a11y-specialist.md) - WCAG compliance and accessibility audits
- [`mobile-web-expert.md`](mobile-web-expert.md) - PWA, offline support, mobile optimization

---

### 8. Backend Frameworks

**When to use:**
- Building backend services in specific languages/frameworks
- Implementing language-specific patterns and idioms
- Optimizing framework-specific code

**Typical outcomes:**
- Idiomatic, production-ready backend code
- Framework-specific best practices applied
- Async/concurrent patterns implemented correctly

**Agents:**
- [`python-expert.md`](python-expert.md) - Python idioms, async, type hints
- [`django-expert.md`](django-expert.md) - Django ORM, DRF, admin customization
- [`laravel-specialist.md`](laravel-specialist.md) - Laravel/PHP, Eloquent, queues
- [`spring-boot-engineer.md`](spring-boot-engineer.md) - Spring Boot, Spring Security, microservices
- [`java-enterprise-architect.md`](java-enterprise-architect.md) - Enterprise Java, JVM optimization
- [`go-concurrency-expert.md`](go-concurrency-expert.md) - Go goroutines, channels, concurrency
- [`rust-systems-expert.md`](rust-systems-expert.md) - Rust ownership, lifetimes, unsafe code
- [`csharp-dotnet-architect.md`](csharp-dotnet-architect.md) - C#/.NET, Entity Framework, DI

---

### 9. API & Integration

**When to use:**
- Designing REST or GraphQL APIs
- Integrating with third-party services
- Implementing OAuth, webhooks, or API authentication

**Typical outcomes:**
- Well-documented, developer-friendly APIs
- Reliable third-party integrations with error handling
- Secure API authentication implementations

**Agents:**
- [`api-architect.md`](api-architect.md) - REST/GraphQL API design and documentation
- [`integration-specialist.md`](integration-specialist.md) - Third-party API integration and webhooks

---

### 10. Data Engineering

**When to use:**
- Building ETL pipelines or data warehouses
- Processing batch or streaming data
- Setting up data infrastructure

**Typical outcomes:**
- Scalable data pipelines with error handling
- Optimized data warehouse schemas
- Real-time or batch data processing workflows

**Agents:**
- [`data-engineer.md`](data-engineer.md) - ETL pipelines, data lakes, Spark/Kafka
- [`ml-pipeline-engineer.md`](ml-pipeline-engineer.md) - ML pipelines, model deployment, MLOps

---

### 11. AI/LLM Development

**When to use:**
- Integrating AI/LLM features into applications
- Building RAG systems or chatbots
- Optimizing prompts for better results

**Typical outcomes:**
- Streaming chat interfaces with proper state management
- RAG pipelines with vector search
- Optimized prompts with consistent outputs

**Agents:**
- [`llm-integration-specialist.md`](llm-integration-specialist.md) - AI/LLM API integration and streaming
- [`langchain-architect.md`](langchain-architect.md) - LangChain, RAG, agents, memory systems
- [`prompt-engineer.md`](prompt-engineer.md) - Prompt optimization and output formatting

---

### 12. Testing & Quality Assurance

**When to use:**
- Creating comprehensive test suites
- Setting up E2E testing infrastructure
- Debugging complex issues

**Typical outcomes:**
- Unit, integration, and E2E test coverage
- CI-integrated testing pipelines
- Root cause analysis for bugs

**Agents:**
- [`test-suite-architect.md`](test-suite-architect.md) - Test suite design and coverage strategies
- [`playwright-e2e-expert.md`](playwright-e2e-expert.md) - Playwright E2E tests, cross-browser
- [`senior-code-reviewer.md`](senior-code-reviewer.md) - Thorough code review for bugs and quality
- [`debug-detective.md`](debug-detective.md) - Error investigation and root cause analysis

---

### 13. Refactoring & Code Quality

**When to use:**
- Cleaning up technical debt
- Improving code maintainability
- Reviewing code for quality issues

**Typical outcomes:**
- Cleaner, more maintainable code
- Extracted reusable patterns
- Code quality improvements with rationale

**Agents:**
- [`refactoring-specialist.md`](refactoring-specialist.md) - Code cleanup and complexity reduction
- [`senior-code-reviewer.md`](senior-code-reviewer.md) - Quality review and best practices

---

### 14. Product & Strategy

**When to use:**
- Making product roadmap decisions
- Analyzing competitive positioning
- Evaluating build vs. kill decisions

**Typical outcomes:**
- Product feature prioritization
- Competitive analysis reports
- Strategic recommendations with trade-offs

**Agents:**
- [`product-strategy-analyst.md`](product-strategy-analyst.md) - Product roadmap and feature decisions
- [`competitive-analyst.md`](competitive-analyst.md) - Market positioning and differentiation

---

### 15. Growth & Marketing

**When to use:**
- Implementing viral/referral features
- Optimizing SEO or conversion funnels
- Building payment/subscription systems

**Typical outcomes:**
- Growth loops and referral systems
- SEO-optimized pages with schema markup
- Payment integrations and pricing tiers

**Agents:**
- [`viral-growth-engineer.md`](viral-growth-engineer.md) - Viral loops and referral mechanics
- [`seo-optimizer.md`](seo-optimizer.md) - SEO audits, meta tags, schema markup
- [`analytics-insights.md`](analytics-insights.md) - User analytics and funnel tracking
- [`monetization-architect.md`](monetization-architect.md) - Payment systems and subscriptions
- [`conversion-copywriter.md`](conversion-copywriter.md) - Landing page copy and CTAs
- [`email-campaign-architect.md`](email-campaign-architect.md) - Email flows and automation

---

### 16. Community & Support

**When to use:**
- Building community or social features
- Creating self-service support systems
- Implementing engagement mechanics

**Typical outcomes:**
- Forum/commenting systems
- Help centers and FAQ systems
- User engagement and retention features

**Agents:**
- [`community-builder.md`](community-builder.md) - Social features and engagement
- [`self-service-support-architect.md`](self-service-support-architect.md) - Help center and ticket deflection

---

### 17. Documentation & Research

**When to use:**
- Maintaining documentation accuracy
- Exploring emerging technologies
- Researching experimental solutions

**Typical outcomes:**
- Updated, accurate documentation
- Technology evaluation reports
- Proof-of-concept implementations

**Agents:**
- [`docs-maintainer.md`](docs-maintainer.md) - Documentation accuracy and staleness detection
- [`innovation-explorer.md`](innovation-explorer.md) - Emerging tech research and experimentation

---

## Agent Index

Quick reference for all 63 agents with their cluster assignments.

| Agent | Summary | Clusters |
|-------|---------|----------|
| [`a11y-specialist.md`](a11y-specialist.md) | Accessibility audits, WCAG compliance, screen reader support | UI/UX Design & Quality |
| [`analytics-insights.md`](analytics-insights.md) | User analytics, funnel tracking, event implementation | Growth & Marketing |
| [`api-architect.md`](api-architect.md) | REST/GraphQL API design, authentication, documentation | API & Integration |
| [`architecture-advisor.md`](architecture-advisor.md) | System architecture decisions, pattern evaluation | Architecture & System Design |
| [`architecture-designer.md`](architecture-designer.md) | Codebase structure, maintainability design | Architecture & System Design |
| [`automation-architect.md`](automation-architect.md) | CI/CD, scheduled jobs, workflow triggers | Infrastructure & DevOps |
| [`cloud-architect.md`](cloud-architect.md) | Cloud infrastructure design, scalability | Architecture & System Design, Infrastructure & DevOps |
| [`cloud-cost-optimizer.md`](cloud-cost-optimizer.md) | AWS/cloud cost reduction, right-sizing | Infrastructure & DevOps |
| [`community-builder.md`](community-builder.md) | Social features, forums, engagement mechanics | Community & Support |
| [`competitive-analyst.md`](competitive-analyst.md) | Market positioning, competitor analysis | Product & Strategy |
| [`conversion-copywriter.md`](conversion-copywriter.md) | Landing page copy, CTAs, value propositions | Growth & Marketing |
| [`csharp-dotnet-architect.md`](csharp-dotnet-architect.md) | C#/.NET, Entity Framework, async patterns | Backend Frameworks |
| [`data-engineer.md`](data-engineer.md) | ETL pipelines, data warehouses, Spark/Kafka | Data Engineering |
| [`database-optimizer.md`](database-optimizer.md) | Query optimization, schema design, indexing | Performance & Optimization |
| [`db-optimizer.md`](db-optimizer.md) | Database performance, slow query analysis | Performance & Optimization |
| [`debug-detective.md`](debug-detective.md) | Error investigation, root cause analysis | Testing & Quality Assurance |
| [`design-systems-architect.md`](design-systems-architect.md) | Component libraries, design tokens | UI/UX Design & Quality |
| [`devops-deployer.md`](devops-deployer.md) | CI/CD pipeline setup, GitHub Actions | Infrastructure & DevOps |
| [`django-expert.md`](django-expert.md) | Django ORM, DRF, admin, migrations | Backend Frameworks |
| [`docker-containerization-expert.md`](docker-containerization-expert.md) | Dockerfiles, compose, multi-stage builds | Infrastructure & DevOps |
| [`docs-maintainer.md`](docs-maintainer.md) | Documentation accuracy, staleness detection | Documentation & Research |
| [`email-campaign-architect.md`](email-campaign-architect.md) | Email marketing flows, automation | Growth & Marketing |
| [`go-concurrency-expert.md`](go-concurrency-expert.md) | Go goroutines, channels, worker pools | Backend Frameworks |
| [`innovation-explorer.md`](innovation-explorer.md) | Emerging tech research, experimentation | Documentation & Research |
| [`integration-specialist.md`](integration-specialist.md) | Third-party API integration, OAuth, webhooks | API & Integration |
| [`java-enterprise-architect.md`](java-enterprise-architect.md) | Enterprise Java, Spring, JVM optimization | Backend Frameworks |
| [`kubernetes-specialist.md`](kubernetes-specialist.md) | K8s deployments, Helm charts, RBAC | Infrastructure & DevOps |
| [`langchain-architect.md`](langchain-architect.md) | LangChain, RAG, agents, memory systems | AI/LLM Development |
| [`laravel-specialist.md`](laravel-specialist.md) | Laravel/PHP, Eloquent, queues, middleware | Backend Frameworks |
| [`llm-integration-specialist.md`](llm-integration-specialist.md) | AI/LLM API integration, streaming responses | AI/LLM Development |
| [`load-test-architect.md`](load-test-architect.md) | Load/stress testing, capacity validation | Performance & Optimization |
| [`ml-pipeline-engineer.md`](ml-pipeline-engineer.md) | ML pipelines, model deployment, MLOps | Data Engineering, AI/LLM Development |
| [`mobile-web-expert.md`](mobile-web-expert.md) | PWA, offline support, touch interactions | UI/UX Design & Quality |
| [`monetization-architect.md`](monetization-architect.md) | Payment systems, subscriptions, pricing | Growth & Marketing |
| [`nextjs-expert.md`](nextjs-expert.md) | Next.js App Router, RSC, edge functions | Frontend Development |
| [`observability-specialist.md`](observability-specialist.md) | Monitoring, logging, alerting, APM | Reliability & Operations |
| [`orchestration-specialist.md`](orchestration-specialist.md) | Multi-domain coordination, workflow synthesis | Architecture & System Design |
| [`perf-optimizer.md`](perf-optimizer.md) | Application performance, caching, profiling | Performance & Optimization |
| [`playwright-e2e-expert.md`](playwright-e2e-expert.md) | Playwright E2E tests, cross-browser, CI | Testing & Quality Assurance |
| [`premium-ui-designer.md`](premium-ui-designer.md) | Visual polish, animations, premium feel | UI/UX Design & Quality |
| [`privacy-compliance-specialist.md`](privacy-compliance-specialist.md) | GDPR/CCPA compliance, consent management | Security & Compliance |
| [`product-strategy-analyst.md`](product-strategy-analyst.md) | Product roadmap, feature prioritization | Product & Strategy |
| [`prompt-engineer.md`](prompt-engineer.md) | Prompt optimization, output formatting | AI/LLM Development |
| [`python-expert.md`](python-expert.md) | Python idioms, async, decorators, type hints | Backend Frameworks |
| [`react-specialist.md`](react-specialist.md) | React hooks, state management, optimization | Frontend Development |
| [`refactoring-specialist.md`](refactoring-specialist.md) | Code cleanup, complexity reduction | Refactoring & Code Quality |
| [`release-manager.md`](release-manager.md) | Deployment management, feature flags, rollbacks | Reliability & Operations |
| [`rust-systems-expert.md`](rust-systems-expert.md) | Rust ownership, lifetimes, FFI, unsafe | Backend Frameworks |
| [`security-auditor.md`](security-auditor.md) | Vulnerability detection, secure coding | Security & Compliance |
| [`self-service-support-architect.md`](self-service-support-architect.md) | Help center, FAQ, ticket deflection | Community & Support |
| [`senior-code-reviewer.md`](senior-code-reviewer.md) | Code review, quality assurance | Testing & Quality Assurance, Refactoring & Code Quality |
| [`seo-optimizer.md`](seo-optimizer.md) | SEO audits, meta tags, schema markup | Growth & Marketing |
| [`spring-boot-engineer.md`](spring-boot-engineer.md) | Spring Boot, Security, microservices | Backend Frameworks |
| [`sre-reliability-engineer.md`](sre-reliability-engineer.md) | SLOs, error budgets, incident response | Reliability & Operations |
| [`terraform-infrastructure-architect.md`](terraform-infrastructure-architect.md) | Terraform IaC, modules, state management | Infrastructure & DevOps |
| [`test-suite-architect.md`](test-suite-architect.md) | Test suite design, coverage strategies | Testing & Quality Assurance |
| [`typescript-type-architect.md`](typescript-type-architect.md) | Advanced generics, type utilities | Frontend Development |
| [`ux-pain-point-fixer.md`](ux-pain-point-fixer.md) | UX friction analysis, drop-off investigation | UI/UX Design & Quality |
| [`ux-simplifier.md`](ux-simplifier.md) | UI simplification, flow reduction | UI/UX Design & Quality |
| [`ux-writer.md`](ux-writer.md) | Microcopy, error messages, onboarding text | UI/UX Design & Quality |
| [`viral-growth-engineer.md`](viral-growth-engineer.md) | Viral loops, referral mechanics, activation | Growth & Marketing |
| [`vue3-architect.md`](vue3-architect.md) | Vue 3 Composition API, Pinia, reactivity | Frontend Development |
| [`workflow-orchestrator.md`](workflow-orchestrator.md) | DAG pipelines, task execution, retry logic | Infrastructure & DevOps |

---

## Cross-Cluster Agents

These agents appear in multiple clusters due to their cross-domain expertise:

| Agent | Clusters |
|-------|----------|
| [`cloud-architect.md`](cloud-architect.md) | Architecture & System Design, Infrastructure & DevOps |
| [`ml-pipeline-engineer.md`](ml-pipeline-engineer.md) | Data Engineering, AI/LLM Development |
| [`senior-code-reviewer.md`](senior-code-reviewer.md) | Testing & Quality Assurance, Refactoring & Code Quality |

---

## Statistics

- **Total agents:** 63
- **Total clusters:** 17
- **Agents with multiple clusters:** 3
- **Largest cluster:** Backend Frameworks (8 agents)
- **Smallest clusters:** Security & Compliance, API & Integration, Product & Strategy (2 agents each)
