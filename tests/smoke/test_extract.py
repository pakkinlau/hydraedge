from transformers import AutoTokenizer, AutoModelForTokenClassification
mdl = AutoModelForTokenClassification.from_pretrained("liaad/srl-en_mbert-base")
tok = AutoTokenizer.from_pretrained("liaad/srl-en_mbert-base")
print("✅  Weights cached at:", mdl.base_model_prefix)