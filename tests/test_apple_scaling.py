"""Validate Apple scaling receipt schema and default selection."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.apple_scaling import REQUIRED_SIZES, assemble_sweep, select_default, validate_sweep
from scripts.benchmark_apple_scaling import learner_parameters_finite


class FakeTensor:
    pass


class FakeModule:
    def __init__(self, parameters):
        self._parameters = parameters

    def parameters(self):
        return iter(self._parameters)


class FakeTorch:
    @staticmethod
    def is_tensor(value):
        return isinstance(value, FakeTensor)

    @staticmethod
    def isfinite(value):
        return value


class FakeAlgorithm:
    actor = FakeModule([FakeTensor()])
    critic = FakeModule([FakeTensor()])


FakeTensor.all = lambda self: self
FakeTensor.item = lambda self: True

assert learner_parameters_finite(FakeAlgorithm(), FakeTorch)


def row(size: int, total: float, headroom: float = 0.8, thermal: str = "nominal") -> dict:
    return {
        "schema_version":"microduck.apple-scaling-row/v1",
        "num_envs":size,"construction_s":1.0,"warmup_iteration_s":2.0,
        "collection_s":total * 0.7,"learner_update_s":total * 0.3,
        "total_iteration_s":total,"reset_s":0.1,"synchronization_s":0.01,
        "env_steps_per_s":1000.0,"samples_per_minute":50000.0,
        "peak_rss_bytes":1000,"unified_memory":{"method":"peak_process_rss_proxy","headroom_fraction_proxy":headroom,"limitations":"RSS proxy only"},
        "devices":{"physics":"metal","learner":"mps"},
        "backend":{"genesis":"metal","torch_mps_available":True},
        "thermal":{"method":"pmset","limitations":"warning state only","state_after":thermal},
        "finite":{"observations":True,"learner_parameters":True},"termination_reason":"completed",
        "benchmark":{"warmup_iterations":1,"measured_iterations":1},
        "source":{"commit":"0123456789abcdef","dirty":False},
        "machine":{"model":"Mac","serial_recorded":False},
        "packages":{"genesis-world":"x","torch":"x","rsl-rl-lib":"x"},
        "proof_class":"performance_characterization","task_success":"not_evaluated",
    }

rows = [row(size, total) for size, total in zip(REQUIRED_SIZES, (5,4,3,3.5,4))]
receipt = {"schema_version":"microduck.apple-scaling-sweep/v1","source_commit":"0123456789abcdef","rows":rows,"proof_class":"performance_characterization","task_success":"not_evaluated"}
validate_sweep(receipt)
assert select_default(rows) == 256
unsafe = copy.deepcopy(rows)
unsafe[2]["thermal"]["state_after"] = "warning_or_unavailable"
assert select_default(unsafe) == 512
unsafe[3]["unified_memory"]["headroom_fraction_proxy"] = 0.1
assert select_default(unsafe) == 128
bad = copy.deepcopy(receipt)
bad["rows"][0]["devices"]["learner"] = "cpu"
try:
    validate_sweep(bad)
except AssertionError:
    pass
else:
    raise AssertionError("unsupported learner device accepted")
with tempfile.TemporaryDirectory() as temp_dir:
    paths = []
    for item in rows:
        path = Path(temp_dir) / f"{item['num_envs']}.json"
        path.write_text(json.dumps(item))
        paths.append(path)
    assembled = assemble_sweep(paths, "test-run")
    assert assembled["source_commit"] == "0123456789abcdef"
    assert assembled["run_id"] == "test-run"
print("Apple scaling schema/default selection verified")
