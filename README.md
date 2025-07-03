Below is a **drop-in `README.md`** that rolls together **everything we have discussed so far**— Docker-image build, run, VS Code attachment, interpreter selection, GPU / FAISS sanity checks, and an optional dev-container recipe—so a fresh collaborator can be productive in minutes.

````markdown
# HydraEdge Rapid-Startup Environment  
### (Python 3.10 · CUDA 12.1 · FAISS GPU 1.11 · VS Code ready)

> *Goal *: give reviewers / team-mates a **one-shot, GPU-enabled dev box** with the exact stack we used for the EMNLP-2025 system-demo paper—no local Python conflicts, no CUDA hell.

---

## 0 · Prerequisites

| Tool | Minimum version | Notes |
|------|-----------------|-------|
| **Docker** | 20.10+ | *Docker Desktop* is fine (enable **GPU support** in Settings → Resources → GPU). |
| **NVIDIA Driver** | R525+ | Must support CUDA ≥ 12.1. |
| **VS Code** | 1.85+ | Plus the **Remote - Containers** extension. |

---

## 1 · Build the image (one-off)  

We pin Python 3.10 on top of a small CUDA runtime base and add FAISS-GPU.

```bash
# inside the repo root (contains Dockerfile)
docker build -t py310-cuda-faiss:12.1 .
````

If you prefer to **pull** rather than build, grab our pre-built image:

```bash
docker pull ghcr.io/your-org/py310-cuda-faiss:12.1
```

---

## 2 · Run the container

```bash
docker run --gpus all \
  -v "C:/Documents/All_github_repo/hydraedge:/workspace" \
  -p 8888:8888 -p 6006:6006 \
  --name hydraedge-dev \
  -it py310-cuda-faiss:12.1 bash
```

| Flag                        | Why                                                                     |
| --------------------------- | ----------------------------------------------------------------------- |
| `--gpus all`                | exposes every GPU to the container.                                     |
| `-v local: /workspace`      | your code lives in the container.                                       |
| `-p 8888:8888 -p 6006:6006` | ready for Jupyter & TensorBoard.                                        |
| `-it … bash`                | drop into a shell immediately; feel free to swap for `python` or `zsh`. |

---

## 3 · GPU / FAISS sanity check (optional)

Inside the container run:

```bash
python - <<'PY'
import faiss, numpy as np, torch, os
print("Python  :",  os.sys.version)
print("CUDA    :",  torch.version.cuda)
print("GPUs    :",  faiss.get_num_gpus())
xb = np.random.rand(2,128).astype('float32')
index = faiss.index_cpu_to_all_gpus(faiss.index_factory(128, "Flat"))
index.add(xb)
print("Distances", index.search(xb, 1)[0].ravel())
PY
```

You should see **`GPUs : 1`** (or more) and finite self-distances.

---

## 4 · Attach VS Code (Remote-Containers)

1. **Install** *Remote - Containers* extension (once).
2. **Command Palette → “Remote-Containers: Attach to Running Container…”**
   choose **`hydraedge-dev`** → VS Code reloads into `/workspace`.

### 4.1 Install the Python extension in the container

The first reload shows *“Extensions (in Container)”* at the top of the sidebar.

* Search **Python** → **Install** (again – this time inside the container).
* Reload when prompted.

### 4.2 Pick the interpreter

*Command Palette → Python: Select Interpreter → `/usr/bin/python`*
The green ▶︎ **Run / Debug** buttons now appear.

---

## 5 · Dev-container auto-setup (optional but recommended)

Put this in **`.devcontainer/devcontainer.json`** so newcomers get the tools automatically:

```jsonc
{
  "name": "hydraedge-dev",
  "image": "py310-cuda-faiss:12.1",
  "extensions": [
    "ms-python.python",
    "ms-toolsai.jupyter"
  ],
  "settings": {
    "python.defaultInterpreterPath": "/usr/bin/python"
  },
  "postCreateCommand": "python -m pip install -r requirements.txt || true"
}
```

---

## 6 · Shut-down & cleanup

```bash
# inside the container
exit               # or Ctrl-D

# on host
docker stop hydraedge-dev
docker rm   hydraedge-dev     # optional
```

---

## 7 · Troubleshooting

| Symptom                                      | Fix                                                                                                                                                                                                      |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`faiss.get_num_gpus() -> 0`**              | The Docker runtime cannot see your GPU.<br/>• Check `docker info --format '{{json .Runtimes}}'` shows *nvidia*.<br/>• On Windows / WSL: enable *“Use the WSL 2 based engine”* + *GPU* in Docker Desktop. |
| **No ▶︎ Run button in VS Code**              | Install the *Python* extension **inside** the container (see § 4.1).                                                                                                                                     |
| **`AssertionError` during FAISS test**       | Means `faiss.index_cpu_to_all_gpus` got **0 GPUs**. Fix GPU visibility then rerun.                                                                                                                       |
| **Slow build (downloads huge cuBLAS wheel)** | First build always pulls ≥ 500 MB CUDA libraries. They are cached afterwards.                                                                                                                            |
