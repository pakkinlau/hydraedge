import faiss, numpy as np, torch
print("Faiss :", faiss.__version__)
print("GPUs  :", faiss.get_num_gpus(), torch.cuda.device_count())

xb = np.random.random((4, 128)).astype('float32')
cpu   = faiss.index_factory(128, "Flat", faiss.METRIC_L2)
gpu   = faiss.index_cpu_to_all_gpus(cpu)
gpu.add(xb)
D, I = gpu.search(xb, 1)
print("Distances OK:", D.ravel())
