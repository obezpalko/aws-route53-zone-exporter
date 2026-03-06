# Build stage
FROM python:3.12-alpine AS builder
WORKDIR /app
COPY app/ ./
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-slim AS final
WORKDIR /app
COPY --from=builder /app/ ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "aws_exporter:app"]
