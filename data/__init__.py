"""
Lightweight helpers for bundled demo data.
"""
from importlib.resources import files
from pathlib import Path
import json, numpy as np, pandas as pd

def path(relative: str) -> Path:
    return files(__package__).joinpath(relative)

def load_jsonl(name: str):
    with open(path(name), "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]

def load_npy(name: str):
    return np.load(path(name), allow_pickle=True)
