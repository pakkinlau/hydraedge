#!/usr/bin/env bash
set -euo pipefail

# 0) Activate your venv if you have one
if [ -f ./venv/bin/activate ]; then
  . ./venv/bin/activate
elif [ -f /opt/venv/bin/activate ]; then
  . /opt/venv/bin/activate
fi

# 1) Upgrade pip & wheel
pip install --upgrade pip wheel

# 2) Keep numpy <2 so any existing GPU libs (CuPy, blis, etc) stay happy
pip install "numpy<2"

# 3) Install spaCy & only the small English model
pip install "spacy==3.7.5"
python - <<'PYCODE'
import spacy, sys
# only download if not already installed
if not spacy.util.is_package("en_core_web_sm"):
    print("⏬ Installing en_core_web_sm…")
    spacy.cli.download("en_core_web_sm")
else:
    print("✔ en_core_web_sm already installed.")
PYCODE

# 4) Install HF-SRL head + minimal transformer stack + protobuf shim
pip install "transformers==4.41.1" protobuf
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121

# 5) Run _only_ the extractor unit tests
pytest tests/unit/extractor
