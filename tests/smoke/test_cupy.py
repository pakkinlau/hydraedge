#!/usr/bin/env python3
import cupy as cp
import numpy as np
from cuvs.neighbors import cagra

def main():
    # 1. Generate random base and query vectors (float32)
    xb = cp.asarray(np.random.rand(10_000, 256).astype(np.float32))
    xq = cp.asarray(np.random.rand(5, 256).astype(np.float32))

    # 2. Build the index
    index = cagra.build(cagra.IndexParams(), xb)

    # 3. Prepare search parameters
    search_params = cagra.SearchParams()

    # 4. Set Top-k
    k = 5

    # 5. Perform the search (returns distances, neighbor indices)
    distances, neighbors = cagra.search(search_params, index, xq, k)

    # 6. Move results to host and display
    print("Top-5 distances:\n", distances.get())
    print("Top-5 neighbor indices:\n", neighbors.get())

if __name__ == "__main__":
    main()
