FROM amazonlinux:latest
RUN yum -y update && yum clean metadata && \
    yum -y install \
    wget \
    tar \
    gzip \
    make \
    gcc \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    sqlite-devel \
    python3-devel \
    zlib-devel \
    zip \
    git \
    which && \
    cd /opt && \
    wget https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz && \
    tar xzf Python-3.11.8.tgz && \
    cd  /opt/Python-3.11.8 && \
    ./configure --enable-optimizations && \
    make altinstall && \
    cd / && \
    rm -rf /opt/Python-3.11.8* && \
    ln -s $(which python3.11) /usr/local/bin/python3 && \
    python3 -m pip install -U pip

ENV PYTHONPATH "/app"
COPY pyproject.toml .
COPY uv.lock .
RUN uv sync
COPY app/ /app/app/
WORKDIR /app
RUN adduser -m userapp && chown -R userapp:userapp /app
USER userapp

CMD ["python3", "/app/app/main.py" ]