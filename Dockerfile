FROM python:3.7.7-slim-buster

# Copy dependencies
COPY ./third_party /app/third_party

# Install our dependencies
RUN pip install -r /app/third_party/requirements.txt

COPY . /app/

CMD ["python3", "/app/main.py", "/app/configs/config.yml"]
