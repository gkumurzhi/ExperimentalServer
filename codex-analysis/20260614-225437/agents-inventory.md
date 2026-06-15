# Available Agents Inventory
_Generated: 2026-06-14 22:54:37 Europe/Moscow_

## Built-in Agents

### default
- **Description:** General-purpose fallback agent.
- **Use when:** A needed analysis area has no better specialized agent.

### worker
- **Description:** Execution-focused implementation/fix agent.
- **Use when:** Implementation feasibility, validation commands, or concrete remediation steps need review.

### explorer
- **Description:** Read-heavy codebase exploration agent.
- **Use when:** Broad repository mapping or source-level investigation is needed.

## Typed Spawn Agent Roles

The `multi_agent_v1.spawn_agent` schema was discovered and validated. It exposes a large typed catalog. Roles selected as relevant for this repository roadmap are:

| Agent type | Description | Use in this audit | Validation |
|---|---|---|---|
| `architect-reviewer` | Architecture, coupling, system boundaries, long-term maintainability. | Review whether the current `FeatureSet`, handler mixins, package split, and server lifecycle are the right base for the next product stage. | available |
| `security-auditor` | Auth flows, secrets handling, input validation, infrastructure security. | Review remaining security decisions: default `lab` profile, reverse-proxy client identity, Notepad durability, CORS/browser-origin policy. | available |
| `api-designer` | API contract design, evolution planning, compatibility review. | Shape error contracts, method/version policy, Notepad API, WebSocket message contracts, and public compatibility. | available |
| `websocket-engineer` | WebSocket lifecycle, message contracts, reconnect/failure behavior. | Validate the next WebSocket/Notepad direction after STAGE-011 closed failure semantics. | available |
| `performance-engineer` | Runtime hot paths, scalability bottlenecks, resource behavior. | Evaluate streaming upload, large listings, memory budgets, slow reader/body behavior, and benchmark priorities. | available |
| `qa-expert` | Test strategy, acceptance coverage, risk-based QA. | Convert roadmap into module-specific gates, browser/Docker smoke expansions, and acceptance criteria. | available |
| `frontend-developer` | UI behavior and production-quality frontend flows. | Review the embedded static UI as a product surface and profile-aware workspace. | available |
| `accessibility-tester` | Accessibility audit of UI interactions and components. | Check status/live regions, keyboard behavior, forms, destructive actions, and notepad flows. | available |
| `devops-engineer` | CI, release automation, environment configuration. | Review release/publish paths, docs-sync failure, Python matrix, CI cost, and provenance. | available |
| `docker-expert` | Dockerfile and container runtime review. | Review whether Docker examples should stay local/trusted-lab or become an operational distribution surface. | available |
| `dependency-manager` | Package graph, upgrades, third-party risk. | Review Python 3.14/3.15 readiness, constraints parity, Dependabot/pin refresh policy, and release dependency posture. | available |
| `documentation-engineer` | Technical docs faithful to code and operator workflows. | Resolve docs mirror drift and shape roadmap docs/ADR/API updates. | available |
| `product-manager` | Product framing and feature prioritization. | Turn technical facts into concrete future-development paths. | available |
| `project-manager` | Milestone planning and sequencing. | Convert selected roadmap into implementation stages after specialist findings. | available |

## Custom Agents

No project-scoped custom agents were found under `/home/user/PycharmProjects/ExperimentalHTTPServer/.codex/agents`.

Personal custom agents were found under `/home/user/.codex/agents`: `136` TOML files. The `name` and `description` fields were parsed; global `developer_instructions` bodies are intentionally not copied into this repository artifact. The descriptions below are used as the concise capability summaries.

```text
accessibility-tester | ~/.codex/agents/accessibility-tester.toml | Use when a task needs an accessibility audit of UI changes, interaction flows, or component behavior.
ad-security-reviewer | ~/.codex/agents/ad-security-reviewer.toml | Use when a task needs Active Directory security review across identity boundaries, delegation, GPO exposure, or directory hardening.
agent-installer | ~/.codex/agents/agent-installer.toml | Use when a task needs help selecting, copying, or organizing custom agent files from this repository into Codex agent directories.
agent-organizer | ~/.codex/agents/agent-organizer.toml | Use when the parent agent needs help choosing subagents and dividing a larger task into clean delegated threads.
ai-engineer | ~/.codex/agents/ai-engineer.toml | Use when a task needs implementation or debugging of model-backed application features, agent flows, or evaluation hooks.
angular-architect | ~/.codex/agents/angular-architect.toml | Use when a task needs Angular-specific help for component architecture, dependency injection, routing, signals, or enterprise application structure.
api-designer | ~/.codex/agents/api-designer.toml | Use when a task needs API contract design, evolution planning, or compatibility review before implementation starts.
api-documenter | ~/.codex/agents/api-documenter.toml | Use when a task needs consumer-facing API documentation generated from the real implementation, schema, and examples.
architect-reviewer | ~/.codex/agents/architect-reviewer.toml | Use when a task needs architectural review for coupling, system boundaries, long-term maintainability, or design coherence.
azure-infra-engineer | ~/.codex/agents/azure-infra-engineer.toml | Use when a task needs Azure-specific infrastructure review or implementation across resources, networking, identity, or automation.
backend-developer | ~/.codex/agents/backend-developer.toml | Use when a task needs scoped backend implementation or backend bug fixes after the owning path is known.
blockchain-developer | ~/.codex/agents/blockchain-developer.toml | Use when a task needs blockchain or Web3 implementation and review across smart-contract integration, wallet flows, or transaction lifecycle handling.
browser-debugger | ~/.codex/agents/browser-debugger.toml | Use when a task needs browser-based reproduction, UI evidence gathering, or client-side debugging through a browser MCP server.
build-engineer | ~/.codex/agents/build-engineer.toml | Use when a task needs build-graph debugging, bundling fixes, compiler pipeline work, or CI build stabilization.
business-analyst | ~/.codex/agents/business-analyst.toml | Use when a task needs requirements clarified, scope normalized, or acceptance criteria extracted from messy inputs before engineering work starts.
chaos-engineer | ~/.codex/agents/chaos-engineer.toml | Use when a task needs resilience analysis for dependency failure, degraded modes, recovery behavior, or controlled fault-injection planning.
cli-developer | ~/.codex/agents/cli-developer.toml | Use when a task needs a command-line interface feature, UX review, argument parsing change, or shell-facing workflow improvement.
cloud-architect | ~/.codex/agents/cloud-architect.toml | Use when a task needs cloud architecture review across compute, storage, networking, reliability, or multi-service design.
code-mapper | ~/.codex/agents/code-mapper.toml | Use when the parent agent needs a high-confidence map of code paths, ownership boundaries, and execution flow before changes are made.
code-reviewer | ~/.codex/agents/code-reviewer.toml | Use when a task needs a broader code-health review covering maintainability, design clarity, and risky implementation choices in addition to correctness.
competitive-analyst | ~/.codex/agents/competitive-analyst.toml | Use when a task needs a grounded comparison of tools, products, libraries, or implementation options.
compliance-auditor | ~/.codex/agents/compliance-auditor.toml | Use when a task needs compliance-oriented review of controls, auditability, policy alignment, or evidence gaps in a regulated workflow.
content-marketer | ~/.codex/agents/content-marketer.toml | Use when a task needs product-adjacent content strategy or messaging that still has to stay grounded in real technical capabilities.
context-manager | ~/.codex/agents/context-manager.toml | Use when a task needs a compact project context summary that other subagents can rely on before deeper work begins.
cpp-pro | ~/.codex/agents/cpp-pro.toml | Use when a task needs C++ work involving performance-sensitive code, memory ownership, concurrency, or systems-level integration.
csharp-developer | ~/.codex/agents/csharp-developer.toml | Use when a task needs C# or .NET application work involving services, APIs, async flows, or application architecture.
customer-success-manager | ~/.codex/agents/customer-success-manager.toml | Use when a task needs support-pattern synthesis, adoption risk analysis, or customer-facing operational guidance from engineering context.
data-analyst | ~/.codex/agents/data-analyst.toml | Use when a task needs data interpretation, metric breakdown, trend explanation, or decision support from existing analytics outputs.
data-engineer | ~/.codex/agents/data-engineer.toml | Use when a task needs ETL, ingestion, transformation, warehouse, or data-pipeline implementation and debugging.
data-researcher | ~/.codex/agents/data-researcher.toml | Use when a task needs source gathering and synthesis around datasets, metrics, data pipelines, or evidence-backed quantitative questions.
data-scientist | ~/.codex/agents/data-scientist.toml | Use when a task needs statistical reasoning, experiment interpretation, feature analysis, or model-oriented data exploration.
database-administrator | ~/.codex/agents/database-administrator.toml | Use when a task needs operational database administration review for availability, backups, recovery, permissions, or runtime health.
database-optimizer | ~/.codex/agents/database-optimizer.toml | Use when a task needs database performance analysis for query plans, schema design, indexing, or data access patterns.
debugger | ~/.codex/agents/debugger.toml | Use when a task needs deep bug isolation across code paths, stack traces, runtime behavior, or failing tests.
dependency-manager | ~/.codex/agents/dependency-manager.toml | Use when a task needs dependency upgrades, package graph analysis, version-policy cleanup, or third-party library risk assessment.
deployment-engineer | ~/.codex/agents/deployment-engineer.toml | Use when a task needs deployment workflow changes, release strategy updates, or rollout and rollback safety analysis.
devops-engineer | ~/.codex/agents/devops-engineer.toml | Use when a task needs CI, deployment pipeline, release automation, or environment configuration work.
devops-incident-responder | ~/.codex/agents/devops-incident-responder.toml | Use when a task needs rapid operational triage across CI, deployments, infrastructure automation, and service delivery failures.
django-developer | ~/.codex/agents/django-developer.toml | Use when a task needs Django-specific work across models, views, forms, ORM behavior, or admin and middleware flows.
docker-expert | ~/.codex/agents/docker-expert.toml | Use when a task needs Dockerfile review, image optimization, multi-stage build fixes, or container runtime debugging.
docs-researcher | ~/.codex/agents/docs-researcher.toml | Use when a task needs documentation-backed verification of APIs, version-specific behavior, or framework options.
documentation-engineer | ~/.codex/agents/documentation-engineer.toml | Use when a task needs technical documentation that must stay faithful to current code, tooling, and operator workflows.
dotnet-core-expert | ~/.codex/agents/dotnet-core-expert.toml | Use when a task needs modern .NET and ASP.NET Core expertise for APIs, hosting, middleware, or cross-platform application behavior.
dotnet-framework-4.8-expert | ~/.codex/agents/dotnet-framework-4.8-expert.toml | Use when a task needs .NET Framework 4.8 expertise for legacy enterprise applications, compatibility constraints, or Windows-bound integrations.
dx-optimizer | ~/.codex/agents/dx-optimizer.toml | Use when a task needs developer-experience improvements in setup time, local workflows, feedback loops, or day-to-day tooling friction.
electron-pro | ~/.codex/agents/electron-pro.toml | Use when a task needs Electron-specific implementation or debugging across main/renderer/preload boundaries, packaging, and desktop runtime behavior.
elixir-expert | ~/.codex/agents/elixir-expert.toml | Use when a task needs Elixir and OTP expertise for processes, supervision, fault tolerance, or Phoenix application behavior.
embedded-systems | ~/.codex/agents/embedded-systems.toml | Use when a task needs embedded or hardware-adjacent work involving device constraints, firmware boundaries, timing, or low-level integration.
erlang-expert | ~/.codex/agents/erlang-expert.toml | Use when a task needs Erlang/OTP and rebar3 expertise for BEAM processes, testing, releases, upgrades, or distributed runtime behavior.
error-coordinator | ~/.codex/agents/error-coordinator.toml | Use when multiple errors or symptoms need to be grouped, prioritized, and assigned to the right debugging or review agents.
error-detective | ~/.codex/agents/error-detective.toml | Use when a task needs log, exception, or stack-trace analysis to identify the most probable failure source quickly.
fintech-engineer | ~/.codex/agents/fintech-engineer.toml | Use when a task needs financial systems engineering across ledgers, reconciliation, transfers, settlement, or compliance-sensitive transactional flows.
flutter-expert | ~/.codex/agents/flutter-expert.toml | Use when a task needs Flutter expertise for widget behavior, state management, rendering issues, or mobile cross-platform implementation.
frontend-developer | ~/.codex/agents/frontend-developer.toml | Use when a task needs scoped frontend implementation or UI bug fixes with production-level behavior and quality.
fullstack-developer | ~/.codex/agents/fullstack-developer.toml | Use when one bounded feature or bug spans frontend and backend and a single worker should own the entire path.
game-developer | ~/.codex/agents/game-developer.toml | Use when a task needs game-specific implementation or debugging involving gameplay systems, rendering loops, asset flow, or player-state behavior.
git-workflow-manager | ~/.codex/agents/git-workflow-manager.toml | Use when a task needs help with branching strategy, merge flow, release branching, or repository collaboration conventions.
golang-pro | ~/.codex/agents/golang-pro.toml | Use when a task needs Go expertise for concurrency, service implementation, interfaces, tooling, or performance-sensitive backend paths.
graphql-architect | ~/.codex/agents/graphql-architect.toml | Use when a task needs GraphQL schema evolution, resolver architecture, federation design, or distributed graph performance/security review.
incident-responder | ~/.codex/agents/incident-responder.toml | Use when a task needs broad production incident triage, containment planning, or evidence-driven root cause analysis.
iot-engineer | ~/.codex/agents/iot-engineer.toml | Use when a task needs IoT system work involving devices, telemetry, edge communication, or cloud-device coordination.
it-ops-orchestrator | ~/.codex/agents/it-ops-orchestrator.toml | Use when a task needs coordinated operational planning across infrastructure, incident response, identity, endpoint, and admin workflows.
java-architect | ~/.codex/agents/java-architect.toml | Use when a task needs Java application or service architecture help across framework boundaries, JVM behavior, or large codebase structure.
javascript-pro | ~/.codex/agents/javascript-pro.toml | Use when a task needs JavaScript-focused work for runtime behavior, browser or Node execution, or application-level code that is not TypeScript-led.
knowledge-synthesizer | ~/.codex/agents/knowledge-synthesizer.toml | Use when multiple agents have returned findings and the parent agent needs a distilled, non-redundant synthesis.
kotlin-specialist | ~/.codex/agents/kotlin-specialist.toml | Use when a task needs Kotlin expertise for JVM applications, Android code, coroutines, or modern strongly typed service logic.
kubernetes-specialist | ~/.codex/agents/kubernetes-specialist.toml | Use when a task needs Kubernetes manifest review, rollout safety analysis, or cluster workload debugging.
laravel-specialist | ~/.codex/agents/laravel-specialist.toml | Use when a task needs Laravel-specific work across routing, Eloquent, queues, validation, or application structure.
legacy-modernizer | ~/.codex/agents/legacy-modernizer.toml | Use when a task needs a modernization path for older code, frameworks, or architecture without losing behavioral safety.
legal-advisor | ~/.codex/agents/legal-advisor.toml | Use when a task needs legal-risk spotting in product or engineering behavior, especially around terms, data handling, or externally visible commitments.
llm-architect | ~/.codex/agents/llm-architect.toml | Use when a task needs architecture review for prompts, tool use, retrieval, evaluation, or multi-step LLM workflows.
m365-admin | ~/.codex/agents/m365-admin.toml | Use when a task needs Microsoft 365 administration help across Exchange Online, Teams, SharePoint, identity, or tenant-level automation.
machine-learning-engineer | ~/.codex/agents/machine-learning-engineer.toml | Use when a task needs ML system implementation work across training pipelines, feature flow, model serving, or inference integration.
market-researcher | ~/.codex/agents/market-researcher.toml | Use when a task needs market landscape, positioning, or demand-side research tied to a technical product or category.
mcp-developer | ~/.codex/agents/mcp-developer.toml | Use when a task needs work on MCP servers, MCP clients, tool wiring, or protocol-aware integrations.
microservices-architect | ~/.codex/agents/microservices-architect.toml | Use when a task needs service-boundary design, inter-service contract review, or distributed-system architecture decisions.
ml-engineer | ~/.codex/agents/ml-engineer.toml | Use when a task needs practical machine learning implementation across feature engineering, inference wiring, and model-backed application logic.
mlops-engineer | ~/.codex/agents/mlops-engineer.toml | Use when a task needs model deployment, registry, pipeline, monitoring, or environment orchestration for machine learning systems.
mobile-app-developer | ~/.codex/agents/mobile-app-developer.toml | Use when a task needs app-level mobile product work across screens, state, API integration, and release-sensitive mobile behavior.
mobile-developer | ~/.codex/agents/mobile-developer.toml | Use when a task needs mobile implementation or debugging across app lifecycle, API integration, and device/platform-specific UX constraints.
multi-agent-coordinator | ~/.codex/agents/multi-agent-coordinator.toml | Use when a task needs a concrete multi-agent plan with clear role separation, dependencies, and result integration.
network-engineer | ~/.codex/agents/network-engineer.toml | Use when a task needs network-path analysis, service connectivity debugging, load-balancer review, or infrastructure network design input.
nextjs-developer | ~/.codex/agents/nextjs-developer.toml | Use when a task needs Next.js-specific work across routing, rendering modes, server actions, data fetching, or deployment-sensitive frontend behavior.
nlp-engineer | ~/.codex/agents/nlp-engineer.toml | Use when a task needs NLP-specific implementation or analysis involving text processing, embeddings, ranking, or language-model-adjacent pipelines.
payment-integration | ~/.codex/agents/payment-integration.toml | Use when a task needs payment-flow review or implementation for checkout, idempotency, webhooks, retries, or settlement state handling.
penetration-tester | ~/.codex/agents/penetration-tester.toml | Use when a task needs adversarial review of an application path for exploitability, abuse cases, or practical attack surface analysis.
performance-engineer | ~/.codex/agents/performance-engineer.toml | Use when a task needs performance investigation for slow requests, hot paths, rendering regressions, or scalability bottlenecks.
performance-monitor | ~/.codex/agents/performance-monitor.toml | Use when a task needs ongoing performance-signal interpretation across build, runtime, or operational metrics before deeper optimization starts.
php-pro | ~/.codex/agents/php-pro.toml | Use when a task needs PHP expertise for application logic, framework integration, runtime debugging, or server-side code evolution.
platform-engineer | ~/.codex/agents/platform-engineer.toml | Use when a task needs internal platform, golden-path, or self-service infrastructure design for developers.
postgres-pro | ~/.codex/agents/postgres-pro.toml | Use when a task needs PostgreSQL-specific expertise for schema design, performance behavior, locking, or operational database features.
powershell-5.1-expert | ~/.codex/agents/powershell-5.1-expert.toml | Use when a task needs Windows PowerShell 5.1 expertise for legacy automation, full .NET Framework interop, or Windows administration scripts.
powershell-7-expert | ~/.codex/agents/powershell-7-expert.toml | Use when a task needs modern PowerShell 7 expertise for cross-platform automation, scripting, or .NET-based operational tooling.
powershell-module-architect | ~/.codex/agents/powershell-module-architect.toml | Use when a task needs PowerShell module structure, command design, packaging, or profile architecture work.
powershell-security-hardening | ~/.codex/agents/powershell-security-hardening.toml | Use when a task needs PowerShell-focused hardening across script safety, admin automation, execution controls, or Windows security posture.
powershell-ui-architect | ~/.codex/agents/powershell-ui-architect.toml | Use when a task needs PowerShell-based UI work for terminals, forms, WPF, or admin-oriented interactive tooling.
product-manager | ~/.codex/agents/product-manager.toml | Use when a task needs product framing, prioritization, or feature-shaping based on engineering reality and user impact.
project-manager | ~/.codex/agents/project-manager.toml | Use when a task needs dependency mapping, milestone planning, sequencing, or delivery-risk coordination across multiple workstreams.
prompt-engineer | ~/.codex/agents/prompt-engineer.toml | Use when a task needs prompt revision, instruction design, eval-oriented prompt comparison, or prompt-output contract tightening.
python-pro | ~/.codex/agents/python-pro.toml | Use when a task needs a Python-focused subagent for runtime behavior, packaging, typing, testing, or framework-adjacent implementation.
qa-expert | ~/.codex/agents/qa-expert.toml | Use when a task needs test strategy, acceptance coverage planning, or risk-based QA guidance for a feature or release.
quant-analyst | ~/.codex/agents/quant-analyst.toml | Use when a task needs quantitative analysis of models, strategies, simulations, or numeric decision logic.
rails-expert | ~/.codex/agents/rails-expert.toml | Use when a task needs Ruby on Rails expertise for models, controllers, jobs, callbacks, or convention-driven application changes.
react-specialist | ~/.codex/agents/react-specialist.toml | Use when a task needs a React-focused agent for component behavior, state flow, rendering bugs, or modern React patterns.
refactoring-specialist | ~/.codex/agents/refactoring-specialist.toml | Use when a task needs a low-risk structural refactor that preserves behavior while improving readability, modularity, or maintainability.
research-analyst | ~/.codex/agents/research-analyst.toml | Use when a task needs a structured investigation of a technical topic, implementation approach, or design question.
reviewer | ~/.codex/agents/reviewer.toml | Use when a task needs PR-style review focused on correctness, security, behavior regressions, and missing tests.
risk-manager | ~/.codex/agents/risk-manager.toml | Use when a task needs explicit risk analysis for product, operational, financial, or architectural decisions.
rust-engineer | ~/.codex/agents/rust-engineer.toml | Use when a task needs Rust expertise for ownership-heavy systems code, async runtime behavior, or performance-sensitive implementation.
sales-engineer | ~/.codex/agents/sales-engineer.toml | Use when a task needs technically accurate solution positioning, customer-question handling, or implementation tradeoff explanation for pre-sales contexts.
scrum-master | ~/.codex/agents/scrum-master.toml | Use when a task needs process facilitation, iteration planning, or workflow friction analysis for an engineering team.
search-specialist | ~/.codex/agents/search-specialist.toml | Use when a task needs fast, high-signal searching of the codebase or external sources before deeper analysis begins.
security-auditor | ~/.codex/agents/security-auditor.toml | Use when a task needs focused security review of code, auth flows, secrets handling, input validation, or infrastructure configuration.
security-engineer | ~/.codex/agents/security-engineer.toml | Use when a task needs infrastructure and platform security engineering across IAM, secrets, network controls, or hardening work.
seo-specialist | ~/.codex/agents/seo-specialist.toml | Use when a task needs search-focused technical review across crawlability, metadata, rendering, information architecture, or content discoverability.
slack-expert | ~/.codex/agents/slack-expert.toml | Use when a task needs Slack platform work involving bots, interactivity, events, workflows, or Slack-specific integration behavior.
spring-boot-engineer | ~/.codex/agents/spring-boot-engineer.toml | Use when a task needs Spring Boot expertise for service behavior, configuration, data access, or enterprise API implementation.
sql-pro | ~/.codex/agents/sql-pro.toml | Use when a task needs SQL query design, query review, schema-aware debugging, or database migration analysis.
sre-engineer | ~/.codex/agents/sre-engineer.toml | Use when a task needs reliability engineering work involving SLOs, alerting, error budgets, operational safety, or service resilience.
swift-expert | ~/.codex/agents/swift-expert.toml | Use when a task needs Swift expertise for iOS or macOS code, async flows, Apple platform APIs, or strongly typed application logic.
task-distributor | ~/.codex/agents/task-distributor.toml | Use when a broad task needs to be broken into concrete sub-tasks with clear boundaries for multiple agents or contributors.
technical-writer | ~/.codex/agents/technical-writer.toml | Use when a task needs release notes, migration notes, onboarding material, or developer-facing prose derived from real code changes.
terraform-engineer | ~/.codex/agents/terraform-engineer.toml | Use when a task needs Terraform module design, plan review, state-aware change analysis, or IaC refactoring.
terragrunt-expert | ~/.codex/agents/terragrunt-expert.toml | Use when a task needs Terragrunt-specific help for module orchestration, environment layering, dependency wiring, or DRY infrastructure structure.
test-automator | ~/.codex/agents/test-automator.toml | Use when a task needs implementation of automated tests, test harness improvements, or targeted regression coverage.
tooling-engineer | ~/.codex/agents/tooling-engineer.toml | Use when a task needs internal developer tooling, scripts, automation glue, or workflow support utilities.
trend-analyst | ~/.codex/agents/trend-analyst.toml | Use when a task needs trend synthesis across technology shifts, adoption patterns, or emerging implementation directions.
typescript-pro | ~/.codex/agents/typescript-pro.toml | Use when a task needs strong TypeScript help for types, interfaces, refactors, or compiler-driven fixes.
ui-designer | ~/.codex/agents/ui-designer.toml | Use when a task needs concrete UI decisions, interaction design, and implementation-ready design guidance before or during development.
ui-fixer | ~/.codex/agents/ui-fixer.toml | Use when a UI issue is already reproduced and the parent agent wants the smallest safe patch.
ux-researcher | ~/.codex/agents/ux-researcher.toml | Use when a task needs UI feedback synthesized into actionable product and implementation guidance.
vue-expert | ~/.codex/agents/vue-expert.toml | Use when a task needs Vue expertise for component behavior, Composition API patterns, routing, or state and rendering issues.
websocket-engineer | ~/.codex/agents/websocket-engineer.toml | Use when a task needs real-time transport and state work across WebSocket lifecycle, message contracts, and reconnect/failure behavior.
windows-infra-admin | ~/.codex/agents/windows-infra-admin.toml | Use when a task needs Windows infrastructure administration across Active Directory, DNS, DHCP, GPO, or Windows automation.
wordpress-master | ~/.codex/agents/wordpress-master.toml | Use when a task needs WordPress-specific implementation or debugging across themes, plugins, content architecture, or operational site behavior.
workflow-orchestrator | ~/.codex/agents/workflow-orchestrator.toml | Use when the parent agent needs an explicit Codex subagent workflow for a complex task with multiple stages.
```
