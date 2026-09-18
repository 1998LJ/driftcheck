# Driftcheck — containerized drift scanning
# Usage: docker run --rm -v $(pwd):/repo yunaremaia/driftcheck /repo

FROM python:3.11-slim

LABEL maintainer="Yunare Maia <yunare@gmail.com>"
LABEL description="Detect version drift between docs and toolchain files"

WORKDIR /app

# Install driftcheck
COPY pyproject.toml uv.lock ./
COPY src ./src
COPY README.md LICENSE ./

RUN pip install --no-cache-dir -e .

# Default entrypoint
ENTRYPOINT ["driftcheck"]
CMD ["--help"]
