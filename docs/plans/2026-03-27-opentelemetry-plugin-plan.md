# OpenTelemetry Plugin Implementation Plan

> **For agentic workers:** Use subagent-driven execution (if subagents available) or ai-tooling:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an `opentelemetry` plugin with one expert agent and one knowledge-base skill (5 reference files) for OTel Python instrumentation.

**Architecture:** Single plugin directory with `agents/otel-architect.md` and `skills/opentelemetry/` containing `SKILL.md` plus 5 reference files in `references/`. Content derived from the user's comprehensive OTel Python guide (SDK v1.40.0). Registered in marketplace.json.

**Tech Stack:** Markdown files with YAML frontmatter. No code, no tests, no build step.

**Spec:** `docs/plans/2026-03-27-opentelemetry-plugin-design.md`

**Content source:** The user's OTel Python advanced guide shared at the start of the conversation covers 6 sections: (1) async context propagation, (2) instrumentation by framework, (3) exporters and backends, (4) advanced production patterns, (5) operational checklist, (6) SDK status/packages. The user also shared Jupiter architecture context describing real-world AMQP/ZMQ/Rust propagation patterns. Both inform the content.

---

## File Structure

```
plugins/opentelemetry/                          # NEW directory
  agents/
    otel-architect.md                            # NEW - expert agent (~350 lines)
  skills/
    opentelemetry/
      SKILL.md                                   # NEW - core knowledge base (~200 lines)
      references/
        async-context-propagation.md             # NEW - deep dive (~250 lines)
        instrumentation-patterns.md              # NEW - deep dive (~300 lines)
        exporters-and-backends.md                # NEW - deep dive (~300 lines)
        aws-deployment.md                        # NEW - deep dive (~250 lines)
        production-checklist.md                  # NEW - deep dive (~200 lines)

.claude-plugin/marketplace.json                  # MODIFY - add plugin entry, bump version
```

---

## Chunk 1: Plugin skeleton and agent

### Task 1: Create directory structure

**Files:**
- Create: `plugins/opentelemetry/agents/` (directory)
- Create: `plugins/opentelemetry/skills/opentelemetry/references/` (directory)

- [ ] **Step 1: Create the directory tree**

```bash
mkdir -p plugins/opentelemetry/agents
mkdir -p plugins/opentelemetry/skills/opentelemetry/references
```

- [ ] **Step 2: Verify structure**

```bash
find plugins/opentelemetry -type d
```

Expected:
```
plugins/opentelemetry
plugins/opentelemetry/agents
plugins/opentelemetry/skills
plugins/opentelemetry/skills/opentelemetry
plugins/opentelemetry/skills/opentelemetry/references
```

---

### Task 2: Write the `otel-architect` agent

**Files:**
- Create: `plugins/opentelemetry/agents/otel-architect.md`

The agent covers 5 capabilities: instrument code, audit instrumentation, design custom propagation, configure exporters/Collector, review OTel code. Body uses terse keyword-list style. Per spec reviewer feedback: add WebFetch/WebSearch tools, deduplicate ANTI-PATTERNS vs CORE KNOWLEDGE, keep description concise.

- [ ] **Step 1: Write `otel-architect.md`**

Write the full agent file. Key structural decisions:
- Frontmatter: `tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch` (added WebFetch/WebSearch per review)
- ROLE section: 2-3 lines establishing identity and SDK target
- CAPABILITIES section: bullet list of all 5 capabilities with brief descriptions
- CORE KNOWLEDGE section: condensed rules (context propagation, BatchSpanProcessor, ParentBased, Celery fork, SQLAlchemy async, error handling, PII, W3C format). Include key code patterns inline (TracedThreadPoolExecutor, worker_process_init).
- APPROACH section: structured methodology per capability (instrument, audit, design, configure, review) as numbered steps
- ANTI-PATTERNS section: always-flag list referencing CORE KNOWLEDGE rules (no duplication -- just the flag list with one-liner descriptions)
- CONSTRAINTS section: SDK target, auto vs manual preference, Collector requirement, is_recording() guard

Target: ~350 lines. Follow the terse imperative style of `rag-architect.md` and `python-architect.md`.

- [ ] **Step 2: Verify frontmatter and line count**

```bash
head -20 plugins/opentelemetry/agents/otel-architect.md
wc -l plugins/opentelemetry/agents/otel-architect.md
```

Verify YAML frontmatter has `name`, `description`, `tools`, `model`, `color` fields. Target: ~350 lines.

- [ ] **Step 3: Check for em dashes**

```bash
grep -rn $'\xe2\x80\x94' plugins/opentelemetry/agents/otel-architect.md || echo "No em dashes found"
```

Expected: "No em dashes found". If any found, replace with `--`.

- [ ] **Step 4: Commit**

```bash
git add plugins/opentelemetry/agents/otel-architect.md
git commit -m "feat(opentelemetry): add otel-architect agent"
```

---

### Task 3: Write the `SKILL.md` knowledge base

**Files:**
- Create: `plugins/opentelemetry/skills/opentelemetry/SKILL.md`

The skill is the core knowledge base (~200 lines) loaded when OTel work is detected. It contains actionable patterns, decision trees, and an index of reference files.

- [ ] **Step 1: Write `SKILL.md`**

Content sections to write:
1. **Header** with frontmatter (name: `opentelemetry`, description with TRIGGER/DO NOT TRIGGER)
2. **OpenTelemetry Python** -- title and 1-line purpose
3. **When to Use** -- bullet list of scenarios (like rag-development SKILL.md pattern)
4. **Quick Start** -- recommended defaults for common patterns (like rag-development's "For 80% of use cases")
5. **Architecture Overview** -- TracerProvider -> SpanProcessor -> Exporter pipeline. Context via contextvars. API vs SDK packages.
6. **Auto vs Manual Instrumentation** -- decision matrix table. Auto for infrastructure (HTTP, DB, cache), manual for business logic. Combined pattern with `opentelemetry-instrument` wrapper + manual spans.
7. **Framework Patterns** -- condensed rules for FastAPI (lifespan shutdown, excluded_urls, request hooks), Celery (worker_process_init, never init before fork), SQLAlchemy async (.sync_engine).
8. **Custom Transport Propagation** -- TextMapPropagator interface. Carrier design. inject/extract pattern for dict-based payloads. W3C TraceContext format. Brief AMQP and ZMQ examples.
9. **Sampling** -- decision tree: ParentBased always, head-based for SDK, tail-based for Collector, hybrid at scale. Key env vars.
10. **Three Pillars** -- log-trace correlation (otelTraceID/otelSpanID). Structured JSON logging. Metrics via MeterProvider.
11. **Error Handling** -- record_exception for unexpected, add_event for business. Status transitions. HTTP mapping.
12. **Reference Materials** -- index of 5 reference files with when-to-consult descriptions (follow rag-development pattern).

- [ ] **Step 2: Verify structure**

```bash
wc -l plugins/opentelemetry/skills/opentelemetry/SKILL.md
grep -rn $'\xe2\x80\x94' plugins/opentelemetry/skills/opentelemetry/SKILL.md || echo "No em dashes"
```

Target: ~180-220 lines. No em dashes.

- [ ] **Step 3: Commit**

```bash
git add plugins/opentelemetry/skills/opentelemetry/SKILL.md
git commit -m "feat(opentelemetry): add core knowledge base skill"
```

---

## Chunk 2: Reference files

### Task 4: Write `async-context-propagation.md`

**Files:**
- Create: `plugins/opentelemetry/skills/opentelemetry/references/async-context-propagation.md`

Source content: Guide sections 1 ("How context propagation actually works in asyncio") plus thread boundary patterns.

- [ ] **Step 1: Write the reference file**

Content to cover:
- **contextvars mechanics** -- immutable snapshots, ContextVarsRuntimeContext, write-produces-new-context
- **asyncio.create_task** -- shallow copy at task creation time (not coroutine creation). Correct vs wrong ordering with code examples.
- **asyncio.TaskGroup** (3.11+) -- propagates correctly when create_task inside span scope
- **Plain await** -- no copy, runs in caller's context
- **Thread boundary trap** -- run_in_executor does NOT propagate. TracedThreadPoolExecutor pattern with full code. contextvars.copy_context() for one-off calls.
- **Python 3.12+ asyncio.to_thread** -- automatic propagation
- **opentelemetry-instrumentation-threading** -- auto-patches Thread, Timer, ThreadPoolExecutor

Target: ~250 lines with code examples.

- [ ] **Step 2: Verify line count and em dashes**

```bash
wc -l plugins/opentelemetry/skills/opentelemetry/references/async-context-propagation.md
grep -rn $'\xe2\x80\x94' plugins/opentelemetry/skills/opentelemetry/references/async-context-propagation.md || echo "No em dashes"
```

Target: ~250 lines. No em dashes (replace with `--` if found).

- [ ] **Step 3: Commit**

```bash
git add plugins/opentelemetry/skills/opentelemetry/references/async-context-propagation.md
git commit -m "feat(opentelemetry): add async context propagation reference"
```

---

### Task 5: Write `instrumentation-patterns.md`

**Files:**
- Create: `plugins/opentelemetry/skills/opentelemetry/references/instrumentation-patterns.md`

Source content: Guide section 2 ("Instrumentation best practices by framework") plus section 4 patterns (custom SpanProcessors, error handling).

- [ ] **Step 1: Write the reference file**

Content to cover:
- **Auto-instrumentation setup** -- opentelemetry-bootstrap, opentelemetry-instrument CLI, env vars for control (OTEL_PYTHON_DISABLED_INSTRUMENTATIONS, excluded URLs)
- **FastAPI production setup** -- full init pattern with lifespan, Resource, sampler, BatchSpanProcessor, instrumentor. server_request_hook/response_hook examples. excluded_urls configuration.
- **Celery** -- producer side (CeleryInstrumentor at module level), consumer side (worker_process_init signal, init AFTER fork). Task attribute enrichment (retries, task name). Trace continuity explanation.
- **SQLAlchemy async** -- .sync_engine to instrumentor, enable_commenter for SQL comment injection
- **HTTP clients** -- httpx, requests instrumentation
- **Custom decorators** -- @traced/@traced_async patterns with extract_args. TracedClass mixin using __init_subclass__. Sensitive argument redaction.
- **Error handling in spans** -- record_exception with custom attributes, add_event for business errors, Status transitions (UNSET->OK/ERROR), HTTP status code mapping (only 5xx = ERROR)

Target: ~300 lines with code examples.

- [ ] **Step 2: Verify line count and em dashes**

```bash
wc -l plugins/opentelemetry/skills/opentelemetry/references/instrumentation-patterns.md
grep -rn $'\xe2\x80\x94' plugins/opentelemetry/skills/opentelemetry/references/instrumentation-patterns.md || echo "No em dashes"
```

Target: ~300 lines. No em dashes.

- [ ] **Step 3: Commit**

```bash
git add plugins/opentelemetry/skills/opentelemetry/references/instrumentation-patterns.md
git commit -m "feat(opentelemetry): add instrumentation patterns reference"
```

---

### Task 6: Write `exporters-and-backends.md`

**Files:**
- Create: `plugins/opentelemetry/skills/opentelemetry/references/exporters-and-backends.md`

Source content: Guide section 3 ("Exporters and backend configuration") plus section 4 (custom SpanProcessors).

- [ ] **Step 1: Write the reference file**

Content to cover:
- **OTLP gRPC vs HTTP** -- comparison table (throughput, load balancing, debugging, serverless, proxy/firewall). When to use each.
- **BatchSpanProcessor** -- how it works (thread-safe deque, background thread, independent of event loop). Tuning parameters with env var names (max_queue_size, schedule_delay_millis, max_export_batch_size, export_timeout_millis). Silent drop when queue fills.
- **Propagation formats** -- W3C TraceContext (default), W3C Baggage, B3 (legacy Zipkin), AWS X-Ray. Comparison table with headers and use-when. CompositePropagator for multi-format. OTEL_PROPAGATORS env var.
- **Custom transport inject/extract** -- inject() and extract() with context.attach/detach pattern for message queues, gRPC metadata, Kafka headers.
- **Custom SpanProcessors** -- FilteringEnrichmentProcessor pattern (on_start for enrichment, on_end for filtering). Drop health-check spans. Add deployment attributes.
- **Collector pipeline** -- receivers (otlp grpc/http), processors (batch, memory_limiter, resourcedetection), exporters (awsxray, awsemf, otlp). Full YAML config example. Include multi-backend routing (sending traces to X-Ray and metrics to CloudWatch EMF via separate pipelines).

Target: ~300 lines with code examples and config.

- [ ] **Step 2: Verify line count and em dashes**

```bash
wc -l plugins/opentelemetry/skills/opentelemetry/references/exporters-and-backends.md
grep -rn $'\xe2\x80\x94' plugins/opentelemetry/skills/opentelemetry/references/exporters-and-backends.md || echo "No em dashes"
```

Target: ~300 lines. No em dashes.

- [ ] **Step 3: Commit**

```bash
git add plugins/opentelemetry/skills/opentelemetry/references/exporters-and-backends.md
git commit -m "feat(opentelemetry): add exporters and backends reference"
```

---

### Task 7: Write `aws-deployment.md`

**Files:**
- Create: `plugins/opentelemetry/skills/opentelemetry/references/aws-deployment.md`

Source content: Guide section 3 AWS subsections (ADOT, X-Ray, Lambda, ECS).

- [ ] **Step 1: Write the reference file**

Content to cover:
- **ADOT overview** -- aws-opentelemetry-distro v0.16.0, what it bundles (upstream Collector + AWS exporters + resource detectors + X-Ray propagation + remote sampling)
- **X-Ray integration** -- AwsXRayIdGenerator (timestamp in first 32 bits), AwsXRayPropagator (X-Amzn-Trace-Id header). Full init code with resource detection.
- **AWS resource detectors** -- AwsEc2ResourceDetector, AwsEcsResourceDetector, get_aggregated_resources pattern. OTEL_EXPERIMENTAL_RESOURCE_DETECTORS env var.
- **Lambda** -- ADOT Lambda Layer ARN pattern, AWS_LAMBDA_EXEC_WRAPPER, OTEL_SERVICE_NAME/OTEL_PROPAGATORS env vars. SAM template example. Cold start considerations (provisioned concurrency, selective instrumentations). Collector extension flush timing.
- **ECS sidecar** -- ADOT Collector container alongside app container. App sends to localhost:4317. SSM Parameter Store for config. Full Collector YAML config (receivers, processors with memory_limiter, exporters to X-Ray/CloudWatch EMF).
- **Collector-less direct export** -- OTEL_EXPORTER_OTLP_TRACES_ENDPOINT pointing to xray regional endpoint. When to use (simpler deployments).
- **Migration from aws-xray-sdk** -- aws-xray-sdk is maintenance mode, OTel is the recommended path. Key differences.

Target: ~250 lines with code, config, and SAM template.

- [ ] **Step 2: Verify line count and em dashes**

```bash
wc -l plugins/opentelemetry/skills/opentelemetry/references/aws-deployment.md
grep -rn $'\xe2\x80\x94' plugins/opentelemetry/skills/opentelemetry/references/aws-deployment.md || echo "No em dashes"
```

Target: ~250 lines. No em dashes.

- [ ] **Step 3: Commit**

```bash
git add plugins/opentelemetry/skills/opentelemetry/references/aws-deployment.md
git commit -m "feat(opentelemetry): add AWS deployment reference"
```

---

### Task 8: Write `production-checklist.md`

**Files:**
- Create: `plugins/opentelemetry/skills/opentelemetry/references/production-checklist.md`

Source content: Guide section 5 ("Operational checklist") plus section 6 ("SDK status, packages").

- [ ] **Step 1: Write the reference file**

Content to cover:
- **Do list** (7 items) -- set service.name, BatchSpanProcessor, ParentBased sampling, shutdown handlers (atexit + SIGTERM), OTEL_SDK_DISABLED kill switch, is_recording() guard, BSP queue sizing for spiky workloads
- **Don't list** (6 items) -- init before fork in prefork workers, spans in hot loops, PII in attributes/baggage, None attribute values, SimpleSpanProcessor in staging, skip Collector in production
- **Resource detection** -- get_aggregated_resources config, ProcessResourceDetector, OTELResourceDetector, cloud-specific detectors. Full code example.
- **SDK signal maturity** -- table: Traces (stable v1.40.0), Metrics (stable v1.40.0), Logs (experimental, _logs namespace), Baggage (stable)
- **Key packages and versions** -- table with package name, version, purpose (opentelemetry-api, sdk, exporter-otlp-proto-grpc, exporter-otlp-proto-http, instrumentation-fastapi, celery, sqlalchemy, httpx, logging, threading, propagator-aws-xray, sdk-extension-aws, aws-opentelemetry-distro)
- **Recent breaking changes** -- v1.40.0 (LoggingHandler deprecated, ConcurrentMultiSpanProcessor fork-safe, Python 3.14), v1.39.0 (LogData removed), v1.22.0 (Jaeger exporter removed)

Target: ~200 lines with tables and code.

- [ ] **Step 2: Verify line count and em dashes**

```bash
wc -l plugins/opentelemetry/skills/opentelemetry/references/production-checklist.md
grep -rn $'\xe2\x80\x94' plugins/opentelemetry/skills/opentelemetry/references/production-checklist.md || echo "No em dashes"
```

Target: ~200 lines. No em dashes.

- [ ] **Step 3: Commit**

```bash
git add plugins/opentelemetry/skills/opentelemetry/references/production-checklist.md
git commit -m "feat(opentelemetry): add production checklist reference"
```

---

## Chunk 3: Marketplace registration

### Task 9: Register plugin in marketplace.json

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Add the plugin entry to the `plugins` array**

Add at the end of the `plugins` array (after the last plugin entry):

```json
{
  "name": "opentelemetry",
  "source": "./plugins/opentelemetry",
  "description": "OpenTelemetry Python instrumentation -- distributed tracing, async context propagation, custom transport propagators, OTLP exporters, AWS ADOT/X-Ray, and production observability",
  "version": "1.0.0",
  "author": {
    "name": "Alfio"
  },
  "license": "MIT",
  "keywords": [
    "opentelemetry",
    "otel",
    "tracing",
    "distributed-tracing",
    "observability",
    "instrumentation",
    "spans",
    "context-propagation",
    "otlp",
    "aws-xray",
    "adot",
    "celery",
    "fastapi",
    "asyncio",
    "metrics"
  ],
  "category": "development",
  "strict": false,
  "agents": [
    "./agents/otel-architect.md"
  ],
  "skills": [
    "./skills/opentelemetry"
  ]
}
```

Note: description trimmed to ~150 chars per spec reviewer feedback.

- [ ] **Step 2: Bump marketplace metadata.version**

Increment `metadata.version` from `"3.13.0"` to `"3.14.0"`.

- [ ] **Step 3: Verify JSON is valid**

```bash
python -c "import json; json.load(open('.claude-plugin/marketplace.json'))"
```

Expected: no output (valid JSON).

- [ ] **Step 4: Verify plugin count**

```bash
python -c "import json; d=json.load(open('.claude-plugin/marketplace.json')); print(len(d['plugins']), 'plugins'); print([p['name'] for p in d['plugins'] if p['name']=='opentelemetry'])"
```

Expected: `37 plugins` and `['opentelemetry']`.

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat(opentelemetry): register plugin in marketplace v3.14.0"
```

---

## Summary

| Task | Creates/Modifies | ~Lines |
|------|-----------------|--------|
| 1. Directory structure | `plugins/opentelemetry/` tree | 0 |
| 2. Agent | `agents/otel-architect.md` | ~350 |
| 3. Skill | `skills/opentelemetry/SKILL.md` | ~200 |
| 4. Ref: async context | `references/async-context-propagation.md` | ~250 |
| 5. Ref: instrumentation | `references/instrumentation-patterns.md` | ~300 |
| 6. Ref: exporters | `references/exporters-and-backends.md` | ~300 |
| 7. Ref: AWS | `references/aws-deployment.md` | ~250 |
| 8. Ref: checklist | `references/production-checklist.md` | ~200 |
| 9. Marketplace | `.claude-plugin/marketplace.json` | ~30 (addition) |

**Total:** 9 tasks, 8 files created, 1 file modified, ~1850 lines of content.
**Estimated commits:** 9 (one per task).
