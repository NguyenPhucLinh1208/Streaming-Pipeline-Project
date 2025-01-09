# Base image
FROM python:3.12-slim-bullseye

# Install basic tools and Java
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    openjdk-11-jdk \
    procps \ 
    && apt-get clean

# Set JAVA_HOME
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64

# Set working directory
WORKDIR /opt

RUN useradd -m -d /home/spark -s /bin/bash spark && \
    chown -R spark:spark /opt /usr

# Upgrade pip and install project dependencies
COPY .devcontainer/requirements.txt /opt/.devcontainer/requirements.txt

RUN pip install --upgrade pip && pip install --no-cache-dir -r /opt/.devcontainer/requirements.txt

USER spark

# Add a dummy command to keep the container running
CMD ["tail", "-f", "/dev/null"]
