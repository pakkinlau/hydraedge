# scripts/validate_json.py  (new file – lives next to build_tiny_index.py)
import json, jsonschema, pathlib

# minimal schema-stub; extend later if you tighten spec
SCHEMA = {
    "type"      : "object",
    "required"  : ["version", "sentence", "nodes", "edges", "layouts"],
    "properties": {
        "version" : {"type": "string"},
        "sentence": {"type": "string"},
        "nodes"   : {"type": "array"},
        "edges"   : {"type": "array"},
        "layouts" : {"type": "object"},
    },
}

def check_file(path: str | pathlib.Path) -> None:
    """Raise `jsonschema.ValidationError` if the file is invalid."""
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    jsonschema.validate(instance=doc, schema=SCHEMA)
