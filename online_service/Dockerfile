FROM python:3.14-slim
WORKDIR /app
COPY online_service /app/online_service
ENV HOST=0.0.0.0 PORT=8080 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 65532:65532
EXPOSE 8080
CMD ["python", "-m", "online_service.server"]
