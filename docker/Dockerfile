###############################################################################
# CUDA 12.1 + build tool-chain (no Faiss wheel)
###############################################################################
FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.10 python3.10-dev python3-pip \
        build-essential git wget ca-certificates \
        libopenblas-dev swig libgflags-dev && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    pip install --no-cache-dir numpy==1.26.4 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
CMD ["/bin/bash"]