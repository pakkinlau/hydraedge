import faiss, numpy as np, torch

# 1) Check PyTorch sees the GPU
print("PyTorch CUDA available:", torch.cuda.is_available())

# 2) Check how many GPUs FAISS sees
n_gpus = faiss.get_num_gpus()
print("FAISS sees this many GPUs:", n_gpus)

# 3) Build a pure‐GPU index and do a tiny search
res = faiss.StandardGpuResources()               # allocate GPU resources
d = 64
cfg = faiss.GpuIndexFlatConfig()
cfg.device = 0                                   # GPU #0
gpu_index = faiss.GpuIndexFlatL2(res, d, cfg)    # L2‐flat on GPU

# random data
xb = np.random.rand(1000, d).astype("float32")
xq = xb[:5]

gpu_index.add(xb)                                # this lives on the GPU
D, I = gpu_index.search(xq, 3)

print("Index size:", gpu_index.ntotal)
print("Distances:\n", D)
print("Indices:\n", I)

""" 
Output:

PyTorch CUDA available: True
FAISS sees this many GPUs: 2
Index size: 1000
Distances:
 [[0.0000000e+00 6.4841957e+00 6.8897820e+00]
 [7.6293945e-06 5.5765228e+00 5.7021790e+00]
 [0.0000000e+00 6.2319984e+00 6.2375813e+00]
 [3.8146973e-06 5.8741207e+00 6.5100346e+00]
 [0.0000000e+00 6.1715317e+00 6.6805782e+00]]
Indices:
 [[  0 530 417]
 [  1 267 895]
 [  2 175 222]
 [  3 189 157]
 [  4 636 334]]
(venv) root@9fe3b22286dd:/workspace/tests/smoke# 

"""