FROM python:3.9.20

# 可选：传入内网 Debian 源与 PyPI 源
ARG DEBIAN_MIRROR
ARG DEBIAN_SECURITY_MIRROR
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST

ENV PYTHONUNBUFFERED=1
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_TRUSTED_HOST=${PIP_TRUSTED_HOST}

# 配置（可选）内网 Debian 源并安装构建依赖
RUN set -eux; \
    if [ -n "${DEBIAN_MIRROR:-}" ]; then \
      CODENAME=$(grep VERSION_CODENAME /etc/os-release | cut -d= -f2); \
      printf 'deb %s %s main contrib non-free\n' "$DEBIAN_MIRROR" "$CODENAME" > /etc/apt/sources.list; \
      printf 'deb %s %s-updates main contrib non-free\n' "$DEBIAN_MIRROR" "$CODENAME" >> /etc/apt/sources.list; \
      if [ -n "${DEBIAN_SECURITY_MIRROR:-}" ]; then \
        printf 'deb %s %s-security main contrib non-free\n' "$DEBIAN_SECURITY_MIRROR" "$CODENAME" >> /etc/apt/sources.list; \
      fi; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends gcc build-essential ca-certificates; \
    rm -rf /var/lib/apt/lists/*

# 使用 pip（走内网 PyPI 源）安装 Poetry，避免 curl 外网安装脚本
RUN pip install --no-cache-dir "poetry==1.8.3"

# 使用容器系统 Python，不创建虚拟环境
RUN poetry config virtualenvs.create false && \
    poetry config virtualenvs.in-project false

# 为 Poetry 设置内网源为主源（若提供）
RUN if [ -n "${PIP_INDEX_URL:-}" ]; then poetry source add --priority primary internal "${PIP_INDEX_URL}"; fi

COPY pyproject.toml poetry.lock ./

# 安装项目依赖（使用内网源）
RUN poetry install --no-interaction --no-ansi

WORKDIR /app
