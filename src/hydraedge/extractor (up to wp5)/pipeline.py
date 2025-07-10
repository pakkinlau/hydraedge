import importlib
from pathlib import Path
from .base import Ctx, get_stage

class PipelineRunner:
    def __init__(self, config):
        self.cfg = config
        # import wp* modules so they self-register
        for mod in sorted(Path(__file__).parent.glob("wp*.py")):
            importlib.import_module(f"hydraedge.extractor.{mod.stem}")

        self.stages = [get_stage(n)(config) for n in config["order"]]

    def run_sentence(self, sentence: str) -> Ctx:
        ctx = Ctx(text=sentence)
        for stage in self.stages:
            if all(k in ctx.data for k in stage.requires):
                stage.run(ctx)
        return ctx
