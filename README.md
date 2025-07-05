# HyDRA-Edge Rapid-Startup Environment

### (Python 3.12 · CUDA 12.9 · optional PyTorch 2.3/cu121 · VS Code ready)

> **Goal:** hand team-mates & reviewers a **one-shot GPU dev box** that avoids *“works-on-my-machine”* headaches. Two flavours:
>
> 1. **Clone the pre-baked image** – everything (Torch, spaCy, Cagra) is already inside.  
> 2. **Use the slim base image + `requirements.txt`** – keeps the image tiny; install only the libs you need.

---

## 0 · Prerequisites

| Tool              | Min version | Notes                                                                    |
| ----------------- | ----------- | ------------------------------------------------------------------------ |
| **Docker**        | 20.10+      | Enable GPU in **Settings ▶ Resources ▶ GPU** (Docker Desktop/WSL).        |
| **NVIDIA Driver** | R550+       | Provides CUDA 12.x kernel modules (Blackwell / RTX 50-series supported). |
| **VS Code**       | 1.90+       | Install the **Remote - Containers** extension.                           |

---

# ▶ Two ways to get rolling

## A · Clone the full image (quickest)

```bash
# 1 – pull from GHCR or Docker Hub
docker pull ghcr.io/your-org/hydraedge:cu121-torch-full

# 2 – run it, mount your repo, give it GPUs
docker run --gpus all \
  -v "$(pwd):/workspace" \
  --name hydraedge-dev -it ghcr.io/your-org/hydraedge:cu121-torch-full bash
````

The container drops you straight into an activated virtual-env under `/opt/venv`; all Python packages are ready.

---

## B · Build the slim base image + install from `requirements.txt`

> Recommended if you want a small, cache-friendly image or swap libs frequently.

### 1 Build (≈ 2 min after first layer is cached)

```bash
# repo-root contains dockerfile/Dockerfile
cd dockerfile
docker build -f Dockerfile -t hydraedge-env:cu129-py312 .
```

*Dockerfile excerpt*

```dockerfile
FROM nvidia/cuda:12.9.1-devel-ubuntu24.04

# OS deps + Python 3.12 + venv support
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      python3.12 python3.12-dev python3-pip python3.12-venv build-essential \
      git wget ca-certificates libopenblas-dev swig libgflags-dev && \
    rm -rf /var/lib/apt/lists/*

# create venv in /opt/venv and pre-install pip/wheel
RUN python3 -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
RUN pip install --upgrade pip wheel

WORKDIR /workspace
CMD ["bash"]
```

### 2 Run the container

```bash
docker run --gpus all \
  -v "$(pwd):/workspace" \
  --name hydraedge-dev -it hydraedge-env:cu129-py312 bash
```

The `PATH` already points to `/opt/venv/bin`, so `python` / `pip` are venv-local.

### 3 Install packages from the lightweight manifest

```bash
pip install -r requirements.txt        # <1 min, ~300 MB
```

*Example* `requirements.txt` *(edit to taste)*

```text
# core
numpy>=1.26,<2
scipy>=1.12,<2
spacy==3.7.5
transformers==4.41.1

# GPU stack – cu121 wheels work on any 12.x runtime
torch==2.3.0+cu121        --extra-index-url https://download.pytorch.org/whl/cu121
torchvision==0.18.0+cu121 --extra-index-url https://download.pytorch.org/whl/cu121
torchaudio==2.3.0+cu121   --extra-index-url https://download.pytorch.org/whl/cu121

# NVIDIA Cagra ≈10× faster than FAISS on H100
pycagra>=0.4.0
```

*Why cu121?* No one ships cu129 wheels yet; CUDA 12.x is ABI-stable so cu121 wheels load fine on 12.9.

---

## Next steps (either path)

1. **Smoke-test GPU + Cagra**

   ```bash
   python - <<'PY'
   import torch, cagra, numpy as np
   print("CUDA", torch.version.cuda, "GPUs", torch.cuda.device_count())
   index = cagra.IndexHNSW(dim=128, metric="cosine")
   xb = np.random.rand(1000, 128).astype("float32")
   index.add(xb, list(range(len(xb))))
   print("k-NN OK, id 0 →", index.search(xb[:5], k=1)[0][:,0])
   PY
   ```

2. **Attach VS Code**

   * *Command Palette ▶* **Remote-Containers: Attach…** → `hydraedge-dev`
   * Install Python extension inside the container if prompted.

3. **Optional dev-container config**

   ```jsonc
   {
     "name": "hydraedge-dev",
     "image": "ghcr.io/your-org/hydraedge:cu121-torch-full",
     "extensions": ["ms-python.python","ms-toolsai.jupyter"],
     "postCreateCommand": "pip install -r requirements.txt || true"
   }
   ```

---

## Cleanup

```bash
exit
docker rm -f hydraedge-dev
```

---

## Troubleshooting

| Symptom                                 | Fix / check list                                                  |
| --------------------------------------- | ----------------------------------------------------------------- |
| `torch.cuda.device_count() == 0`        | Driver supports 12.x? Run `nvidia-smi` outside container.         |
| `RuntimeError: CUDA error: invalid ptx` | Using self-built Torch? Compile with `sm_90a` for RTX 5080.       |
| `faiss.get_num_gpus() -> 0`             | Container started without `--gpus all` or missing NVIDIA runtime. |
| Slow build (huge CUDA layer)            | First pull ≈ 3 GB; later builds reuse cache.                      |

