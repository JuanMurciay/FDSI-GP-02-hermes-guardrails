FROM python:3.11-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

COPY src/ /app/src/

RUN mkdir -p /permitidos && chown -R appuser:appgroup /permitidos

USER appuser

ENTRYPOINT ["python", "-m", "src.tools"]
