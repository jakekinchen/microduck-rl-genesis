"""Validate walking/backflip gates with positive, assisted, and failure fixtures."""

from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, os.fspath(ROOT))
from evaluator.success import classify_backflip, classify_walking, load_task  # noqa: E402

fixtures = json.loads((ROOT / "tests/fixtures/success-classifiers-v1.json").read_text())
walking_task = load_task("walking")
backflip_task = load_task("backflip")

walking = []
for command in walking_task["acceptance"]["commands"]:
    for start in walking_task["acceptance"]["start_populations"]:
        for seed in walking_task["acceptance"]["seeds"]:
            walking.append({"command_id":command["id"],"start_population_id":start["id"],"seed":seed,**copy.deepcopy(fixtures["walking_positive_template"])})
assert classify_walking(walking, walking_task)["passed"]
assisted_walking = copy.deepcopy(walking)
assisted_walking[0]["assistance"]["state_or_action_correction"] = True
assert classify_walking(assisted_walking, walking_task)["failures"] == ["assistance"]
failed_walking = copy.deepcopy(walking)
for episode in failed_walking:
    episode["linear_velocity_rmse_m_s"] = 0.5
assert classify_walking(failed_walking, walking_task)["failures"] == ["tracking"]
assert "coverage" in classify_walking(walking[:-1], walking_task)["failures"]

backflip = []
for start in backflip_task["acceptance"]["start_populations"]:
    for seed in backflip_task["acceptance"]["seeds"]:
        backflip.append({"start_population_id":start["id"],"seed":seed,**copy.deepcopy(fixtures["backflip_positive_template"])})
assert classify_backflip(backflip, backflip_task)["passed"]
assisted_backflip = copy.deepcopy(backflip)
assisted_backflip[0]["assistance"]["virtual_upward_force"] = True
assert classify_backflip(assisted_backflip, backflip_task)["failures"] == ["assistance"]
failed_backflip = copy.deepcopy(backflip)
for episode in failed_backflip:
    episode["airborne_backward_rotation_rad"] = 5.0
assert classify_backflip(failed_backflip, backflip_task)["failures"] == ["rotation"]
assert "coverage" in classify_backflip(backflip[:-1], backflip_task)["failures"]
print("success classifiers verified: walking 230 cells, backflip 20 cells, assisted/failure/coverage rejected")
