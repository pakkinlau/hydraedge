import faiss_utils
import numpy as np
import torch

print("Faiss :", faiss_utils.__version__)
print("GPUs  :", faiss_utils.get_num_gpus(), torch.cuda.device_count())

xb = np.random.random((4, 128)).astype('float32')
cpu   = faiss_utils.index_factory(128, "Flat", faiss_utils.METRIC_L2)
gpu   = faiss_utils.index_cpu_to_all_gpus(cpu)
gpu.add(xb)
D, I = gpu.search(xb, 1)
print("Distances OK:", D.ravel())
