FROM python:3.11-slim

# Only needed if lxml fails to install from wheel
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    gcc \
#    libxml2-dev \
#    libxslt-dev \
#    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/task/

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
