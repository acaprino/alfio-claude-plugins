<!-- upstream: github/awesome-copilot - skills/multi-stage-dockerfile/SKILL.md -->
---
name: multi-stage-dockerfile
description: >
  Create optimized multi-stage Dockerfiles for any language or framework.
  TRIGGER WHEN: creating Dockerfiles, optimizing container images, multi-stage builds, Docker best practices.
  DO NOT TRIGGER WHEN: the task is outside the specific scope of this component.
---

Your goal is to help me create efficient multi-stage Dockerfiles that follow best practices, resulting in smaller, more secure container images.

## Multi-Stage Structure

- Use a builder stage for compilation, dependency installation, and other build-time operations
- Use a separate runtime stage that only includes what's needed to run the application
- Copy only the necessary artifacts from the builder stage to the runtime stage
- Use meaningful stage names with the `AS` keyword (e.g., `FROM node:18 AS builder`)
- Place stages in logical order: dependencies -> build -> test -> runtime

## Base Images

- Start with official, minimal base images when possible
- Specify exact version tags to ensure reproducible builds (e.g., `python:3.11-slim` not just `python`)
- Consider distroless images for runtime stages where appropriate
- Use Alpine-based images for smaller footprints when compatible with your application
- Ensure the runtime image has the minimal necessary dependencies

## Layer Optimization

- Organize commands to maximize layer caching
- Place commands that change frequently (like code changes) after commands that change less frequently (like dependency installation)
- Use `.dockerignore` to prevent unnecessary files from being included in the build context
- Combine related RUN commands with `&&` to reduce layer count
- Consider using COPY --chown to set permissions in one step

## Security Practices

- Avoid running containers as root - use `USER` instruction to specify a non-root user
- Remove build tools and unnecessary packages from the final image
- Scan the final image for vulnerabilities
- Set restrictive file permissions
- Use multi-stage builds to avoid including build secrets in the final image

## Performance Considerations

- Use build arguments for configuration that might change between environments
- Leverage build cache efficiently by ordering layers from least to most frequently changing
- Consider parallelization in build steps when possible
- Set appropriate environment variables like NODE_ENV=production to optimize runtime behavior
- Use appropriate healthchecks for the application type with the HEALTHCHECK instruction

## Common Anti-Patterns

### Wrong: Installing dev dependencies in runtime

```dockerfile
FROM node:20
WORKDIR /app
COPY . .
RUN npm install
CMD ["node", "server.js"]
```

### Correct: Multi-stage with production-only deps

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-slim
WORKDIR /app
COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist ./dist
USER node
CMD ["node", "dist/server.js"]
```

### Wrong: Breaking layer cache

```dockerfile
COPY . .
RUN pip install -r requirements.txt
```

### Correct: Dependencies first, code second

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

### Wrong: Running as root with no healthcheck

```dockerfile
FROM python:3.12
COPY app.py .
CMD ["python", "app.py"]
```

### Correct: Non-root user + healthcheck

```dockerfile
FROM python:3.12-slim
RUN useradd --create-home appuser
WORKDIR /home/appuser
COPY --chown=appuser:appuser app.py .
USER appuser
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "app.py"]
```

## Language Templates

### Node.js (TypeScript)

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json tsconfig.json ./
RUN npm ci
COPY src/ src/
RUN npm run build && npm prune --omit=dev

FROM gcr.io/distroless/nodejs22-debian12
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
USER nonroot
EXPOSE 3000
CMD ["dist/server.js"]
```

### Python (FastAPI/Flask)

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM python:3.12-slim
WORKDIR /app
RUN useradd --create-home appuser
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app .
ENV PATH="/opt/venv/bin:$PATH"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Go

```dockerfile
FROM golang:1.24-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /server ./cmd/server

FROM gcr.io/distroless/static-debian12
COPY --from=builder /server /server
USER nonroot
EXPOSE 8080
ENTRYPOINT ["/server"]
```

### Rust

```dockerfile
FROM rust:1.82-slim AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs && cargo build --release && rm -rf src
COPY src/ src/
RUN touch src/main.rs && cargo build --release

FROM debian:bookworm-slim
RUN useradd --create-home appuser
COPY --from=builder /app/target/release/myapp /usr/local/bin/
USER appuser
EXPOSE 8080
CMD ["myapp"]
```

### Java (Spring Boot / Gradle)

```dockerfile
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app
COPY gradle/ gradle/
COPY gradlew build.gradle.kts settings.gradle.kts ./
RUN ./gradlew dependencies --no-daemon
COPY src/ src/
RUN ./gradlew bootJar --no-daemon

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/build/libs/*.jar app.jar
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:8080/actuator/health || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]
```

## .dockerignore Template

Always create a `.dockerignore` alongside the Dockerfile:

```
.git
.gitignore
.env*
*.md
LICENSE
docker-compose*.yml
Dockerfile*
node_modules
__pycache__
*.pyc
.pytest_cache
.mypy_cache
.venv
target/
build/
dist/
.idea
.vscode
*.log
coverage/
.next
```

Adapt to the specific language -- remove entries that don't apply, add framework-specific build artifacts.

## Validation Checklist

Before finalizing the Dockerfile, verify:

- [ ] Multi-stage build separates build-time from runtime dependencies
- [ ] Base images use exact version tags (no `latest`)
- [ ] Runtime image is minimal (slim, alpine, or distroless)
- [ ] Dependencies copied before source code (layer cache)
- [ ] `USER` instruction sets non-root user in final stage
- [ ] `HEALTHCHECK` instruction present for service containers
- [ ] `.dockerignore` exists and excludes build artifacts, `.git`, `.env`
- [ ] No secrets or credentials baked into the image
- [ ] `EXPOSE` documents the listening port
- [ ] Build arguments used for environment-specific configuration
