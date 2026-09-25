# Build from the portfolio root: docker build -f codebase-demo/Dockerfile .
FROM node:22-slim AS frontend
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html vite.config.js ./
COPY src ./src
COPY public ./public
COPY codebase-demo/index.html ./codebase-demo/index.html
COPY codebase-demo/frontend ./codebase-demo/frontend
RUN npm run build

FROM python:3.12-slim
WORKDIR /app/backend
RUN pip install --no-cache-dir uv
COPY codebase-demo/backend/pyproject.toml codebase-demo/backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY codebase-demo/backend/*.py ./
# Explicit COPY includes this artifact even though Git ignores it.
# Missing artifacts fail the image build, rather than indexing at startup.
ARG DEMO_BUNDLE=codebase-demo/data/psf--requests/default/bundle-openai-indexed.json
COPY ${DEMO_BUNDLE} /app/data/bundle.json
COPY --from=frontend /build/dist /app/dist
ENV DEMO_BUNDLE_PATH=/app/data/bundle.json
ENV DEMO_STATIC_DIR=/app/dist
ENV DEMO_USAGE_PATH=/app/usage/usage.sqlite
ENV PATH="/app/backend/.venv/bin:$PATH"
RUN useradd --create-home demo && mkdir /app/usage && chown demo:demo /app/usage
USER demo
EXPOSE 8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-proxy-headers"]
