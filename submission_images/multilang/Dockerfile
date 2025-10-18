FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        clang \
        cmake \
        git \
        gdb \
        make \
        ninja-build \
        pkg-config \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
        openjdk-17-jdk-headless \
        maven \
        gradle \
        curl \
        wget \
        unzip \
        zip \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel

RUN useradd --create-home --uid 1000 codalab \
    && mkdir -p /app/program /app/output /app/input /app/input_data /app/shared \
    && chown -R codalab:codalab /app

COPY language_entry.sh /usr/local/bin/language_entry.sh
RUN chmod +x /usr/local/bin/language_entry.sh

USER codalab
WORKDIR /app/program

CMD ["/bin/bash"]
