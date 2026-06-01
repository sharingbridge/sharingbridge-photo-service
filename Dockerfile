FROM python:3.10-slim

WORKDIR /app

COPY requirements-prod.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY start.sh ./start.sh
RUN chmod +x start.sh

ENV PORT=8092
EXPOSE 8092

CMD ["./start.sh"]
