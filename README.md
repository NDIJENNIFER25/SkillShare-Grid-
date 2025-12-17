# Bank-app — Docker & CI/CD

This repository contains a small Express app. The repository now includes Docker configuration and a GitHub Actions CI/CD workflow template that performs security checks and can build/publish container images.

Local Docker (build & run)

Build image locally:
```powershell
docker build -t bank-app:local .
```

Run with docker-compose (uses `.env` if present):
```powershell
docker-compose up --build
```

Quick run using `docker`:
```powershell
docker run --rm -p 3000:3000 --env-file .env bank-app:local
```

CI/CD (GitHub Actions)

Files added: `./.github/workflows/ci-cd.yml` — the pipeline:
- Installs dependencies with `npm ci`
- Runs `npm audit` (fails for high-severity vulnerabilities)
- Builds and scans the container image with Trivy
- Publishes the image to GitHub Container Registry (GHCR) when run on the `main` branch and proper secrets are configured

Secrets / setup for publishing
- To push images to GHCR set `GHCR_PAT` (a PAT with `write:packages`) as a repository secret.
- Alternatively for Docker Hub set `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`.

Security best-practices applied
- Multi-stage Docker build to reduce final image size
- Runs application as a non-root user
- `.dockerignore` excludes `.env` and `node_modules`
- CI includes `npm audit` and Trivy image scanning

If you want, I can:
- Tweak the workflow to push to Docker Hub instead of GHCR
- Add a `dev` script and `nodemon` for local development
- Add GitHub Dependabot config for dependency alerts
