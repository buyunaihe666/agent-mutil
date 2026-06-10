FROM python:3.12-slim

RUN pip install --no-cache-dir \
    numpy \
    pandas \
    matplotlib \
    requests \
    beautifulsoup4

RUN useradd -m -s /bin/bash sandbox
USER sandbox
WORKDIR /workspace

CMD ["python", "-c", "print('nexus sandbox ready')"]
