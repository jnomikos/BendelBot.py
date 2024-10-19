FROM python:3.10.15-slim-bookworm

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    libffi-dev \
    libnacl-dev \
    libgl1-mesa-glx \
    libglib2.0-0

RUN python3 -m pip install -U py-cord --pre

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]