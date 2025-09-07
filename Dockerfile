FROM python:3.12-slim

WORKDIR /app

# Install package in editable mode with dependencies
COPY pyproject.toml .
COPY README.md .
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Default environment variables (can be overridden)
ENV API_BASE_URL=""
ENV API_TOKEN=""

# Expose the default port
EXPOSE 8080

# Default entrypoint using the installed script
ENTRYPOINT ["mcp-swagger"]

# Default command shows help
CMD ["--help"]