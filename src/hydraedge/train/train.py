# src/training/train.py
"""
CLI: python -m training.train --cfg ../../configs/train.yaml
(or: python -m training.train --cfg config/train.yaml if you add src/ to PYTHONPATH)
"""

import hydra
import torch
from omegaconf import DictConfig
from hydraedge.kernel.forward import HybridKernel
from hydraedge.rl.model     import Actor, Critic

@hydra.main(version_base=None, config_path="../../../configs", config_name="train")
def main(cfg: DictConfig):
    D       = cfg.kernel.D
    kernel  = HybridKernel(D)
    actor   = Actor(D)
    critic1 = Critic(D)
    critic2 = Critic(D)
    # TODO: wire up env, replay buffer, optimizers, etc.
    print("✔ Scaffold ready – next: Smoke tests")

if __name__ == "__main__":
    main()
