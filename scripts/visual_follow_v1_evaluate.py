"""Named compute-guard entrypoint for the isolated visual-marker experiment."""
import importlib.util
from pathlib import Path
import sys

directory = Path(__file__).resolve().parents[1] / "experiments/visual-follow-v1"
sys.path.insert(0, str(directory))
spec = importlib.util.spec_from_file_location("visual_follow_v1_runner", directory / "run.py")
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)

if __name__ == "__main__":
    runner.main()
