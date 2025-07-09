# src/hydraedge/extractor/wp6_roles.py

"""
WP-6: Global role registry loader.
Loads a TSV of (role_name, ±1-vector…) → in-memory map.
Always exposes get_vector(role) even if the file is empty.
"""

from __future__ import annotations
import csv
import numpy as np
from pathlib import Path
from typing import Dict, Optional

class RoleLibrary:
    def __init__(self, tsv_path: Path):
        self.roles: Dict[str, np.ndarray] = {}
        if tsv_path.exists():
            with open(tsv_path, newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh, delimiter="\t")
                for row in reader:
                    if not row:
                        continue
                    role = row[0]
                    # remaining columns are ±1 entries
                    vec  = np.array([int(v) for v in row[1:]], dtype=int)
                    self.roles[role] = vec

    def get_vector(self, role_name: str) -> Optional[np.ndarray]:
        """
        Return the stored vector for this role, or None if not found.
        Calling code can use this to validate existence.
        """
        return self.roles.get(role_name)
