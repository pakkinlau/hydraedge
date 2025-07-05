import torch, transformers, sys
import google.protobuf  as protobuf
print("torch", torch.__version__,
      "• transformers", transformers.__version__,
      "• protobuf", protobuf.__version__,
      "• python", sys.version.split()[0])