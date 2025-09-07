FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY main.py .
COPY config/ ./config/
COPY filters/ ./filters/
COPY generators/ ./generators/
COPY api_client/ ./api_client/
COPY models/ ./models/
COPY parsers/ ./parsers/
COPY utils/ ./utils/

# Default environment variables (can be overridden)
ENV API_BASE_URL=""
ENV API_TOKEN=""

# Expose the default port
EXPOSE 8080

# Default entrypoint - requires swagger spec path as argument
ENTRYPOINT ["python", "main.py"]

# Default command shows help
CMD ["--help"]