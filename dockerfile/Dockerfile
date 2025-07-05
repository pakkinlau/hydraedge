FROM nvidia/cuda:12.9.1-devel-ubuntu24.04

# 1) OS deps + venv support:
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      python3.12 python3.12-dev python3-pip python3.12-venv build-essential \
      git wget ca-certificates libopenblas-dev swig libgflags-dev && \
    rm -rf /var/lib/apt/lists/*

# 2) Create /opt/venv, switch PATH:
RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

# 3) Now pip works system-wide inside the venv:
RUN pip install --upgrade pip wheel

WORKDIR /workspace
CMD ["bash"]

# For tester - just build this image and run `pip install requirements.txt`

### Build and run:
#
# docker build -f dockerfile/Dockerfile -t hydraedge-env:cu129-py312 .
# docker run --rm -it --gpus all -v C:\Documents\All_github_repo\hydraedge:/workspace --name hydraedge-play hydraedge-env:cu129-py312

### After running the container, you can activate the virtual environment using:
#
# source /opt/venv/bin/activate


### And Install some key packages:

"""
pip install --upgrade pip wheel          # make sure build tools are modern
pip install \
  torch==2.3.0+cu121 \
  torchvision==0.18.0+cu121 \
  torchaudio==2.3.0+cu121 \
  --extra-index-url https://download.pytorch.org/whl/cu121
pip install spacy==3.7.5 transformers==4.41.1 pycagra
python -m spacy download en_core_web_trf
pip install --quiet git+https://github.com/liaad/srl
"""

