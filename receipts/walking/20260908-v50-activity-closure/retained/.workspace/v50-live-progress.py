import json,re,shutil
from pathlib import Path
p=Path('logs/retention-native-20260908-v50/coverage-progress.json')
r=json.loads(p.read_text()) if p.exists() else {}
text=Path('.workspace/v50-full.log').read_text()
iterations=re.findall(r'Learning iteration\s+(\d+)/(\d+)',text)
print({'last_iteration':iterations[-1] if iterations else None,'transitions':r.get('transitions'), 'finished_180s_training_episodes':sum(r.get('complete_180s_episodes',[])), 'free_GiB':round(shutil.disk_usage('.').free/2**30,2)})
