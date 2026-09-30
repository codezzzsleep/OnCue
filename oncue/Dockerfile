FROM python:3.12-slim
WORKDIR /app
COPY server/ ./server/
USER 10001:10001
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8787
CMD ["python3", "server/app.py", "--host", "0.0.0.0", "--port", "8787"]
