"""Run a frozen offline material bank, including after compiler failure."""
from pathlib import Path
import argparse
import hashlib
import json
import signal
from material_validation_v62 import validate_meshes

ROOT = Path(__file__).resolve().parents[4]


def main():
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGINT, signal.SIGTERM})
    parser = argparse.ArgumentParser()
    parser.add_argument('bank', type=Path)
    args = parser.parse_args()
    bank = json.loads(args.bank.read_text())
    for name, digest in bank['input_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    output = ROOT / bank['output']
    if output.exists():
        raise RuntimeError('material result already exists; no implicit rerun')
    inputs = {name: {key: (ROOT / value if key in {'source_stl', 'parts_npz', 'complete_json'} else value)
                     for key, value in spec.items()} for name, spec in bank['meshes'].items()}
    witnesses = json.loads((ROOT / bank['cavity_witnesses']).read_text()) if bank.get('cavity_witnesses') else None
    result = validate_meshes(inputs, max_parts=bank['max_parts'], cavity_witnesses=witnesses)
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'sampled_material_gates_passed': result['sampled_material_gates_passed'],
                      'cavity_bank_evaluated': result['cavity_bank_evaluated'],
                      'cavity_gates_passed': result['cavity_gates_passed'],
                      'meshes': {k: {key: value for key, value in v.items() if key not in {'part_geometry', 'inputs'}}
                                 for k, v in result['meshes'].items()}}), flush=True)


if __name__ == '__main__':
    main()
