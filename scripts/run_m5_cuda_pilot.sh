#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT=${WORKSPACE_ROOT:-/workspace}
INPUT_ROOT=${INPUT_ROOT:-$WORKSPACE_ROOT/input}
SOURCE_ROOT=${SOURCE_ROOT:-$WORKSPACE_ROOT/src}
VENV_ROOT=${VENV_ROOT:-$WORKSPACE_ROOT/venvs}
RECEIPT_ROOT=${RECEIPT_ROOT:?set RECEIPT_ROOT to the run-scoped remote receipt directory}
CONTRACT_COMMIT=${CONTRACT_COMMIT:-bb2a23596bc7d676c616f3f4277812d009df645f}
GENESIS_COMMIT=93cd5f261200acb5176f12c417c31c1d877be41a
WALKING_COMMIT=109e06d4ce4921b635c5609e5304079fc30960ae
BACKFLIP_COMMIT=8bde27eb141c8f14db05fc4370e536521203a98d
BAM_COMMIT=62bd8ce12154340be97e06f7f41a0ca8f116d967
PRICE_USD_PER_HOUR=1.62
export PYGLET_HEADLESS=1

mkdir -p "$SOURCE_ROOT" "$VENV_ROOT" "$RECEIPT_ROOT/logs" "$RECEIPT_ROOT/artifacts"
START_EPOCH=$(date -u +%s)
if [[ ! -f "$RECEIPT_ROOT/start-utc.txt" ]]; then
  date -u +%Y-%m-%dT%H:%M:%SZ > "$RECEIPT_ROOT/start-utc.txt"
fi

run_logged() {
  local name=$1
  shift
  "$@" 2>&1 | tee "$RECEIPT_ROOT/logs/$name.log"
}

for bundle in genesis.bundle official-walking.bundle official-backflip.bundle; do
  test -s "$INPUT_ROOT/$bundle"
done
test -s "$INPUT_ROOT/run_m5_cuda_pilot.sh"
cp "$INPUT_ROOT/run_m5_cuda_pilot.sh" "$RECEIPT_ROOT/run_m5_cuda_pilot.sh"
sha256sum "$RECEIPT_ROOT/run_m5_cuda_pilot.sh" > "$RECEIPT_ROOT/harness-sha256.txt"

run_logged host-nvidia-smi nvidia-smi
run_logged host-kernel uname -a
run_logged base-cuda bash -lc 'nvcc --version && cat /etc/os-release'

export DEBIAN_FRONTEND=noninteractive
run_logged apt-bootstrap apt-get update
run_logged apt-install apt-get install -y --no-install-recommends \
  ca-certificates git libegl1 libgl1 libglib2.0-0 libxrender1 \
  python3 python3-pip python3-venv

if [[ ! -x "$VENV_ROOT/tools/bin/python" ]]; then
  python3 -m venv "$VENV_ROOT/tools"
fi
run_logged uv-install "$VENV_ROOT/tools/bin/pip" install uv==0.8.19
UV=$VENV_ROOT/tools/bin/uv

if [[ ! -d "$SOURCE_ROOT/genesis-current/.git" ]]; then
  git clone "$INPUT_ROOT/genesis.bundle" "$SOURCE_ROOT/genesis-current"
fi
git -C "$SOURCE_ROOT/genesis-current" checkout --detach "$CONTRACT_COMMIT"
if [[ ! -d "$SOURCE_ROOT/genesis-training/.git" ]]; then
  git clone "$SOURCE_ROOT/genesis-current" "$SOURCE_ROOT/genesis-training"
fi
git -C "$SOURCE_ROOT/genesis-training" checkout --detach "$GENESIS_COMMIT"
if [[ ! -d "$SOURCE_ROOT/microduck-rl/.git" ]]; then
  git clone "$INPUT_ROOT/official-walking.bundle" "$SOURCE_ROOT/microduck-rl"
fi
git -C "$SOURCE_ROOT/microduck-rl" checkout --detach "$WALKING_COMMIT"
if [[ ! -d "$SOURCE_ROOT/microduck-backflip/.git" ]]; then
  git clone "$INPUT_ROOT/official-backflip.bundle" "$SOURCE_ROOT/microduck-backflip"
fi
git -C "$SOURCE_ROOT/microduck-backflip" checkout --detach "$BACKFLIP_COMMIT"

if [[ ! -x "$VENV_ROOT/genesis/bin/python" ]]; then
  "$UV" venv --python python3 "$VENV_ROOT/genesis"
fi
run_logged genesis-dependencies "$UV" pip install \
  --python "$VENV_ROOT/genesis/bin/python" torch==2.9.1 \
  -r "$SOURCE_ROOT/genesis-training/requirements.txt"

run_logged official-walking-sync "$UV" sync \
  --project "$SOURCE_ROOT/microduck-rl" --frozen
run_logged official-backflip-sync "$UV" sync \
  --project "$SOURCE_ROOT/microduck-backflip" --frozen

if [[ ! -d "$SOURCE_ROOT/bam/.git" ]]; then
  run_logged bam-materialize "$VENV_ROOT/genesis/bin/python" \
    "$SOURCE_ROOT/genesis-current/scripts/materialize_bam_authority.py" \
    "$SOURCE_ROOT/bam"
fi
test "$(git -C "$SOURCE_ROOT/bam" rev-parse HEAD)" = "$BAM_COMMIT"

{
  printf 'contract_commit=%s\n' "$(git -C "$SOURCE_ROOT/genesis-current" rev-parse HEAD)"
  printf 'genesis_training_commit=%s\n' "$(git -C "$SOURCE_ROOT/genesis-training" rev-parse HEAD)"
  printf 'official_walking_commit=%s\n' "$(git -C "$SOURCE_ROOT/microduck-rl" rev-parse HEAD)"
  printf 'official_backflip_commit=%s\n' "$(git -C "$SOURCE_ROOT/microduck-backflip" rev-parse HEAD)"
  printf 'bam_commit=%s\n' "$(git -C "$SOURCE_ROOT/bam" rev-parse HEAD)"
} > "$RECEIPT_ROOT/source-identities.txt"

run_logged runtime-versions "$VENV_ROOT/genesis/bin/python" -c \
  'import importlib.metadata as m, genesis, mujoco, torch; print("python packages"); print("torch", torch.__version__, "cuda", torch.version.cuda, "available", torch.cuda.is_available(), "device", torch.cuda.get_device_name(0)); print("genesis", genesis.__version__); print("mujoco", mujoco.__version__); print("rsl-rl", m.version("rsl-rl-lib"))'
run_logged official-runtime-versions "$SOURCE_ROOT/microduck-rl/.venv/bin/python" -c \
  'import importlib.metadata as m, mujoco, torch, warp; import mujoco_warp; print("torch", torch.__version__, "cuda", torch.version.cuda, "available", torch.cuda.is_available(), "device", torch.cuda.get_device_name(0)); print("mujoco", mujoco.__version__); print("warp", warp.__version__); print("mujoco-warp", m.version("mujoco-warp")); print("mjlab", m.version("mjlab"))'

run_logged full-suite env \
  BAM_REPO="$SOURCE_ROOT/bam" \
  OFFICIAL_MICRODUCK_REPO="$SOURCE_ROOT/microduck-rl" \
  OFFICIAL_MJLAB_PYTHON="$SOURCE_ROOT/microduck-rl/.venv/bin/python" \
  "$VENV_ROOT/genesis/bin/python" "$SOURCE_ROOT/genesis-current/tests/run_all.py"

cd "$SOURCE_ROOT/genesis-training"
run_logged genesis-walking "$VENV_ROOT/genesis/bin/python" train.py \
  --task walking --num-envs 64 --max-iterations 5 --physics-backend gpu \
  --learner-device auto --seed 51001 --exp-name m5-pilot-genesis-walking
run_logged genesis-walking-export "$VENV_ROOT/genesis/bin/python" export_onnx.py \
  --exp-name m5-pilot-genesis-walking \
  --output "$RECEIPT_ROOT/artifacts/genesis-walking.normalized.onnx"
cp -a logs/m5-pilot-genesis-walking "$RECEIPT_ROOT/artifacts/genesis-walking-log"

run_logged genesis-backflip "$VENV_ROOT/genesis/bin/python" train.py \
  --task backflip --num-envs 64 --max-iterations 5 --physics-backend gpu \
  --learner-device auto --seed 52001 --exp-name m5-pilot-genesis-backflip
run_logged genesis-backflip-export "$VENV_ROOT/genesis/bin/python" export_onnx.py \
  --exp-name m5-pilot-genesis-backflip \
  --output "$RECEIPT_ROOT/artifacts/genesis-backflip.normalized.onnx"
cp -a logs/m5-pilot-genesis-backflip "$RECEIPT_ROOT/artifacts/genesis-backflip-log"

cd "$SOURCE_ROOT/microduck-rl"
run_logged official-walking .venv/bin/train Mjlab-Velocity-Flat-MicroDuck \
  --env.scene.num-envs 64 --env.seed 51001 --agent.seed 51001 \
  --agent.max-iterations 5 --agent.save-interval 1 \
  --agent.experiment-name m5_pilot_velocity --agent.run-name m5-pilot-walking \
  --agent.logger tensorboard
WALKING_CKPT=$(find logs/rsl_rl/m5_pilot_velocity -name 'model_*.pt' -type f | sort | tail -1)
test -n "$WALKING_CKPT"
run_logged official-walking-export .venv/bin/python scripts/export.py \
  Mjlab-Velocity-Flat-MicroDuck --checkpoint-file "$WALKING_CKPT" \
  --num-envs 1 --device cpu \
  --onnx-file "$RECEIPT_ROOT/artifacts/official-walking.normalized.onnx"
cp -a logs/rsl_rl/m5_pilot_velocity "$RECEIPT_ROOT/artifacts/official-walking-log"

cd "$SOURCE_ROOT/microduck-backflip"
run_logged official-backflip .venv/bin/train Mjlab-Backflip-Flat-MicroDuck \
  --env.scene.num-envs 64 --env.seed 52001 --agent.seed 52001 \
  --agent.max-iterations 5 --agent.save-interval 1 \
  --agent.experiment-name m5_pilot_backflip --agent.run-name m5-pilot-backflip \
  --agent.logger tensorboard
BACKFLIP_CKPT=$(find logs/rsl_rl/m5_pilot_backflip -name 'model_*.pt' -type f | sort | tail -1)
test -n "$BACKFLIP_CKPT"
run_logged official-backflip-export .venv/bin/python scripts/export.py \
  Mjlab-Backflip-Flat-MicroDuck --checkpoint-file "$BACKFLIP_CKPT" \
  --num-envs 1 --device cpu \
  --onnx-file "$RECEIPT_ROOT/artifacts/official-backflip.normalized.onnx"
cp -a logs/rsl_rl/m5_pilot_backflip "$RECEIPT_ROOT/artifacts/official-backflip-log"

END_EPOCH=$(date -u +%s)
date -u +%Y-%m-%dT%H:%M:%SZ > "$RECEIPT_ROOT/end-utc.txt"
"$VENV_ROOT/genesis/bin/python" - "$START_EPOCH" "$END_EPOCH" \
  "$PRICE_USD_PER_HOUR" "$RECEIPT_ROOT/cost.json" <<'PY'
import json
import sys
start, end = int(sys.argv[1]), int(sys.argv[2])
rate = float(sys.argv[3])
elapsed = end - start
record = {
    "currency": "USD",
    "elapsed_seconds_inside_pilot": elapsed,
    "price_usd_per_hour": rate,
    "computed_inside_pilot_cost_usd": round(elapsed * rate / 3600, 6),
    "billing_clock_requires_manager_reconciliation": True,
}
with open(sys.argv[4], "w", encoding="utf-8") as handle:
    json.dump(record, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY

printf '%s\n' \
  'pilot pipeline execution only; not task success, candidate admission, held-out evaluation, policy acceptance, activation, transfer, or physical authority' \
  > "$RECEIPT_ROOT/EVIDENCE_BOUNDARY.txt"

cd "$RECEIPT_ROOT"
CHECKSUM_TMP=$(mktemp /tmp/m5-pilot-sha256.XXXXXX)
find . -type f ! -name SHA256SUMS -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > "$CHECKSUM_TMP"
mv "$CHECKSUM_TMP" SHA256SUMS
sha256sum -c SHA256SUMS
