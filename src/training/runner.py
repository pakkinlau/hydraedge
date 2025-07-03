import torch, numpy as np
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from ..model.cosine_kernel import CosineKernel

def run_dummy_epoch() -> None:
    x = torch.randn(64, 16)  # fake data
    y = torch.randn(64, 16)
    loader = DataLoader(TensorDataset(x, y), batch_size=32)
    model = nn.Linear(16, 16)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3)
    kernel = CosineKernel()
    for xb, yb in loader:
        loss = 1.0 - torch.mean(torch.tensor([
            kernel.forward(a.numpy(), b.numpy()) for a, b in zip(xb, yb)
        ]))
        opt.zero_grad(); loss.backward(); opt.step()

if __name__ == "__main__":
    run_dummy_epoch()