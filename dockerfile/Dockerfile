FROM nvidia/cuda:12.9.1-devel-ubuntu24.04

# 1) OS deps + venv support:
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      python3.12 python3.12-venv python3-pip build-essential \
      git wget ca-certificates libopenblas-dev swig libgflags-dev && \
    rm -rf /var/lib/apt/lists/*

# 2) Create /opt/venv, switch PATH:
RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

# 3) Now pip works system-wide inside the venv:
RUN pip install --upgrade pip wheel

WORKDIR /workspace
CMD ["bash"]