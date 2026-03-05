# Build stage
FROM python:3.12-alpine AS builder
WORKDIR /app
COPY app/ ./
RUN pip install --no-cache-dir --target /app/python -r requirements.txt

# Final stage
FROM gcr.io/distroless/python3-debian12
WORKDIR /
COPY --from=builder /app/python /usr/lib/python3.12/site-packages
COPY --from=builder /app/aws_exporter.py /
COPY --from=builder /app/templates /templates
COPY --from=builder /app/static /static

USER nonroot
EXPOSE 8080
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "aws_exporter:app"]
