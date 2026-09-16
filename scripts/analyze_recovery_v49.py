"""Offline V49 evidence audit and compact outcome comparison."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.walking.recovery_v49 import ROOT,CAPTURE,COMPARE,SEARCH,FREEZE,digest,manifest,seal


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    import numpy as np
    from scripts.probe_recovery_v49 import binding
    assert binding()==json.loads(FREEZE.read_text())
    manifests={str(p.relative_to(ROOT)):manifest(p) for p in [CAPTURE,COMPARE,SEARCH]}
    capture,compare,search=[json.loads((p/'result.json').read_text()) for p in [CAPTURE,COMPARE,SEARCH]]
    assert capture['complete'] and compare['complete'] and search['complete']
    assert len(capture['states'])==12 and len(compare['branches'])==24 and len(search['states'])==6
    trial_count=0;offset=0;counts={};generation_counts={};zero_controls=0;selected_controls=0
    selected_by_trial={s['selected_trial']:s for s in search['states'] if 'selected_trial' in s}
    with gzip.open(SEARCH/'all-actions-float32.bin.gz','rb') as actions,gzip.open(SEARCH/'all-observations-float32.bin.gz','rb') as observations:
        for line in (SEARCH/'trials.jsonl').read_text().splitlines():
            r=json.loads(line);n=r['controls'];a=actions.read(n*14*4);o=observations.read(n*61*4)
            assert r['trial']==trial_count and r['raw_row_offset']==offset
            assert len(a)==n*14*4 and len(o)==n*61*4
            assert hashlib.sha256(a).hexdigest()==r['action_sha256'] and hashlib.sha256(o).hexdigest()==r['observation_sha256']
            assert np.isfinite(np.frombuffer(a,dtype='<f4')).all() and np.isfinite(np.frombuffer(o,dtype='<f4')).all()
            knots=np.asarray(r['knots']);assert knots.shape==(5,14) and np.isfinite(knots).all() and abs(knots).max()<=1.500001
            assert np.isfinite(r['cost']) and 0<n<=250
            if r['generation']==0 and not knots.any():
                folder=COMPARE/(r['state_id']+'--'+r['anchor'])
                assert a==np.load(folder/'actions-float32.npy')[:n].tobytes()
                assert o==np.load(folder/'observations-float32.npy')[:n].tobytes()
                zero_controls+=n
            if r['trial'] in selected_by_trial:
                folder=SEARCH/r['state_id']
                assert a==np.load(folder/'actions-float32.npy')[:n].tobytes()
                assert o==np.load(folder/'observations-float32.npy')[:n].tobytes()
                selected_controls+=n
            key=(r['state_id'],r['generation'],r['anchor']);generation_counts[key]=generation_counts.get(key,0)+1
            counts[r['state_id']]=counts.get(r['state_id'],0)+1
            offset+=n;trial_count+=1
        assert not actions.read(1) and not observations.read(1)
    assert trial_count==search['search_trials']<=2304 and offset==search['simulated_search_controls']<=576000
    for count in counts.values():assert count==384
    for count in generation_counts.values():assert count==24
    state_ids={r['id'] for r in capture['states']}
    assert all(b['state_id'] in state_ids and b['repeat_exact'] for b in compare['branches'])
    rows=[]
    for entry in capture['states']:
        arms=[r for r in compare['branches'] if r['state_id']==entry['id']]
        assert {r['anchor'] for r in arms}=={'original','v48'}
        row={'state_id':entry['id'],'search_target':entry['search_target'],'controls':{}}
        for r in arms:
            row['controls'][r['anchor']]={k:r[k] for k in ['passed','current_window_passed','restart_window_passed','observed_duration_s','suffix_controls']}
        if entry['search_target']:
            selected=next(r for r in search['states'] if r['state_id']==entry['id'])
            if 'search_skipped' in selected:
                assert entry['id'] not in counts and any(r['passed'] for r in arms)
                row['search']=selected
            else:
                assert counts[entry['id']]==384 and selected['repeat_exact']
                row['search']={k:selected[k] for k in ['anchor','selected_trial','search_cost','passed','current_window_passed','restart_window_passed','observed_duration_s','suffix_controls']}
                # Verify selected parameters and cost against the lowest stored
                # proxy score, without selecting another validation outcome.
                trials=[json.loads(line) for line in (SEARCH/'trials.jsonl').read_text().splitlines() if json.loads(line)['state_id']==entry['id']]
                best=min(trials,key=lambda r:r['cost'])
                assert selected['search_cost']==best['cost']
                chosen=next(r for r in trials if r['trial']==selected['selected_trial'])
                assert chosen['cost']==best['cost'] and chosen['anchor']==selected['anchor']
                knots=np.load(SEARCH/entry['id']/'chosen-knots-float32.npy')
                assert knots.tobytes()==np.asarray(chosen['knots'],np.float32).tobytes()
        rows.append(row)
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(complete=True,receipt_manifests=manifests,freeze_sha256=digest(FREEZE),reproduced_controls=capture['reproduced_controls'],
        exact_reset_controls=capture['exact_reset_controls'],exact_comparison_repeat_controls=compare['exact_repeated_controls'],
        exact_comparison_source_controls=compare['exact_source_controls'],verified_search_trials=trial_count,
        verified_search_action_observation_rows=offset,states=rows,
        zero_residual_exact_comparison_controls=zero_controls,selected_search_exact_validation_controls=selected_controls,
        retained='V30 with original V21/V15',policy_trained=False,physical_transfer=False,held_out=False,
        boundary='Evidence integrity and exposed same-state recovery diagnosis. Same-state repeats are not independent trials or generalization.')
    (args.output/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# V49 recorded branch outcomes','',
        '| State | Original stander | V48 stander | Selected search |',
        '|---|---|---|---|']
    def outcome(r):
        return ('PASS' if r['passed'] else 'FAIL')+f"; {r['observed_duration_s']:.2f}s; current/restart {r['current_window_passed']}/{r['restart_window_passed']}"
    for r in rows:
        result=r.get('search')
        s='not targeted' if result is None else 'unmodified arm already passes' if 'search_skipped' in result else outcome(result)
        lines.append(f"| {r['state_id']} | {outcome(r['controls']['original'])} | {outcome(r['controls']['v48'])} | {s} |")
    lines+=['','Durations include the verified original prefix. PASS requires every original full-session gate. Current/restart are separately scored windows; search failure does not prove impossibility.']
    (args.output/'comparison.md').write_text('\n'.join(lines)+'\n')
    shutil.copy2(Path(__file__),args.output/Path(__file__).name);seal(args.output)
    print(json.dumps({k:v for k,v in report.items() if k not in ['states','receipt_manifests']}))


if __name__=='__main__':main()
