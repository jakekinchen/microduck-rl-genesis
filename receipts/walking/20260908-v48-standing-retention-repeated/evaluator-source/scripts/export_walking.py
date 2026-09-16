"""Walking-record adapter around the frozen normalized MLP exporter."""
import copy
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_laser import digest


def export_walking(run_id,output):
    import torch
    import onnx
    import onnxruntime as ort
    import numpy as np
    from tensordict import TensorDict
    from rsl_rl.models import MLPModel
    from export_onnx import ExportedPolicy
    if not run_id.replace("-","").isalnum():raise ValueError("invalid run id")
    folder=ROOT/"logs"/run_id
    record=json.loads((folder/"run.json").read_text())
    if record["schema"]!="microduck.walking-training/v1" or record["status"]!="completed":raise ValueError("completed walking record required")
    checkpoint=folder/record["checkpoint"]
    if checkpoint.parent!=folder or checkpoint.is_symlink() or digest(checkpoint)!=record["checkpoint_sha256"]:raise ValueError("checkpoint identity mismatch")
    for source,sha in record["source_sha256"].items():
        if digest(ROOT/source)!=sha:raise ValueError(f"source drift: {source}")
    cfg=copy.deepcopy(record["train_cfg"]);actor_cfg=cfg["actor"];actor_cfg.pop("class_name")
    actor=MLPModel(TensorDict({"policy":torch.zeros(1,61)},[1]),cfg["obs_groups"],"actor",14,**actor_cfg)
    actor.load_state_dict(torch.load(checkpoint,map_location="cpu",weights_only=True)["actor_state_dict"],strict=True)
    actor.eval();exported=ExportedPolicy(actor).eval()
    path=output/"policy.onnx"
    torch.onnx.export(exported,torch.zeros(1,61),path,input_names=["obs"],output_names=["action"],opset_version=17,dynamic_axes=None,dynamo=False)
    onnx.checker.check_model(onnx.load(path))
    session=ort.InferenceSession(str(path),providers=["CPUExecutionProvider"])
    if session.get_inputs()[0].shape!=[1,61] or session.get_outputs()[0].shape!=[1,14]:raise ValueError("export ABI changed")
    probes=np.random.default_rng(76509).normal(size=(65,61)).astype(np.float32);probes[0]=0
    with torch.no_grad():expected=exported(torch.from_numpy(probes)).numpy()
    actual=np.concatenate([session.run(None,{"obs":r[None]})[0] for r in probes])
    error=float(np.abs(expected-actual).max())
    if not np.isfinite(error) or error>=1e-4:raise ValueError("export parity failed")
    (output/"normalizer.json").write_text(json.dumps({"mean":exported.mean.tolist(),"std":exported.std.tolist(),"epsilon":exported.eps},indent=2)+"\n")
    shutil.copy2(folder/"run.json",output/"training.json")
    shutil.copy2(checkpoint,output/"source-checkpoint.pt")
    for name in record["source_sha256"]:
        dest=output/"source"/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest)
    return path,{"random_observations":65,"max_abs_action_error_rad":error},exported
