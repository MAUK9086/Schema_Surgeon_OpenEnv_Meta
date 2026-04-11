FROM python:3.10-slim

WORKDIR /app

COPY SchemaSurgeon/server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt openenv-core

COPY . .

EXPOSE 7860

CMD ["uvicorn", "SchemaSurgeon.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
