Expression: 100 / 100.

# HyDRA-Edge Rapid-Startup Environment  
### (Python 3.10 · CUDA 12.1 · FAISS GPU 1.11 · VS Code ready)

> **Goal**: give reviewers and teammates a **one-shot, GPU-enabled dev box** with the exact stack we used for the EMNLP-2025 system-demo paper—no local Python conflicts, no CUDA hell.

---

## 0 · Prerequisites

| Tool               | Minimum version | Notes                                                                               |
|--------------------|-----------------|-------------------------------------------------------------------------------------|
| **Docker**         | 20.10+          | Docker Desktop is fine (enable **GPU support** in Settings ▶ Resources ▶ GPU).      |
| **NVIDIA Driver**  | R525+           | Must support CUDA ≥ 12.1.                                                           |
| **VS Code**        | 1.85+           | Plus the **Remote - Containers** extension.                                         |

---

# ▶ Two setup paths

You may either **build locally** from our `Dockerfile` and then clone/install the packages yourself, or **pull** our prebuilt image from Docker Hub—or GitHub Container Registry.

---

## A · Build & install local packages

1. **Build the base image** (one-off):

   ```bash
   cd <repo-root>           # contains Dockerfile
   docker build -t hydraedge-base:py310-cuda-faiss-12.1 .
````

2. **Run the container**:

   ```bash
   docker run --gpus all \
     -v "$(pwd)/HyDRA-Edge resource packages:/workspace/packages" \
     --name hydraedge-dev -it hydraedge-base:py310-cuda-faiss-12.1 bash
   ```

3. **Inside the container**, clone & install your packages in editable mode:

   ```bash
   cd /workspace/packages
   git clone https://github.com/your-org/allennlp.git
   git clone https://github.com/your-org/allennlp-models.git
   git clone https://github.com/your-org/faiss.git

   pip install -e allennlp
   pip install -e allennlp-models
   pip install -e faiss
   ```

4. **Verify**:

   ```bash
   python -c "import allennlp, allennlp_models, faiss; print('OK')"
   ```

---

## B · Pull & run prebuilt image

1. **Pull** from Docker Hub (or GHCR):

   ```bash
   docker pull ghcr.io/your-org/hydraedge:py310-cuda-faiss-12.1
   # or
   docker pull your-dockerhub-username/hydraedge:py310-cuda-faiss-12.1
   ```

2. **Run** with your workspace mounted:

   ```bash
   docker run --gpus all \
     -v "$(pwd):/workspace" \
     --name hydraedge-dev -it ghcr.io/your-org/hydraedge:py310-cuda-faiss-12.1 bash
   ```

---

## Next steps (both paths)

1. **GPU / FAISS sanity check** (optional):

   ```bash
   python - <<'PY'
   import faiss, numpy as np, torch, os
   print("CUDA:", torch.version.cuda, "GPUs:", faiss.get_num_gpus())
   xb = np.random.rand(2,128).astype('float32')
   index = faiss.index_cpu_to_all_gpus(faiss.index_factory(128, "Flat"))
   index.add(xb)
   print("Distances:", index.search(xb, 1)[0].ravel())
   PY
   ```

2. **Attach VS Code** (Remote Containers):

   * Command Palette → **Remote-Containers: Attach to Running Container…** → select **hydraedge-dev**
   * Install Python extension inside the container
   * Select `/usr/bin/python` as interpreter

3. **Dev-container (optional)**: add `.devcontainer/devcontainer.json` with:

   ```jsonc
   {
     "name": "hydraedge-dev",
     "image": "ghcr.io/your-org/hydraedge:py310-cuda-faiss-12.1",
     "extensions": ["ms-python.python","ms-toolsai.jupyter"],
     "settings": {"python.defaultInterpreterPath":"/usr/bin/python"},
     "postCreateCommand": "pip install -r requirements.txt || true"
   }
   ```

---

## Cleanup

```bash
exit
docker stop hydraedge-dev
docker rm hydraedge-dev
```

---

## Troubleshooting

| Symptom                        | Fix                                                                                                    |
| ------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `faiss.get_num_gpus() -> 0`    | Ensure Docker’s NVIDIA runtime is enabled; on Windows/WSL enable WSL 2 engine + GPU in Docker Desktop. |
| No ▶︎ Run button in VS Code    | Install the **Python** extension inside the container.                                                 |
| `AssertionError` in FAISS test | GPU not visible; verify `--gpus all` and driver compatibility.                                         |
| Slow build (large CUDA layers) | First build pulls \~500 MB; subsequent builds use cache.                                               |

