FROM python:3.10-alpine3.15

RUN mkdir app

WORKDIR /app

COPY . .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8084

CMD python -m uvicorn main:app --host 0.0.0.0 --port 8084
