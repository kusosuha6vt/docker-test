FROM python:latest
WORKDIR /code
COPY . .
RUN pip install --no-cache-dir  -r requirements.txt
CMD ["python", "-u", "app.py"]
