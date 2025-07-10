# setup_extractor_env.ps1
# ————————————————————————————————————————————————————————————————
# 1) Upgrade pip & wheel
# 2) Install requirements + HF SRL, SpaCy
# 3) Run only tests/unit/extractor
# ————————————————————————————————————————————————————————————————

# 1️⃣ Upgrade pip & wheel
pip install --upgrade pip wheel

# 2️⃣ Core deps
pip install -r requirements.txt

# 3️⃣ SpaCy + English model
pip install spacy==3.7.5
python -m spacy download en_core_web_sm

# 4️⃣ Transformers + PyTorch
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121
pip install transformers==4.41.1

# 5️⃣ Protobuf
pip install protobuf

# 6️⃣ Run extractor tests only
pytest .\tests\unit\extractor
