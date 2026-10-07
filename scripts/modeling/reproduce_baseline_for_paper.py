from pathlib import Path
import json
import sys

root = Path.cwd()
sys.path.insert(0, str(root / 'scripts/modeling'))
from build_question2 import solve

path = root / 'output/question2/q2_model_inputs.json'
data = json.loads(path.read_text(encoding='utf-8'))
result = solve(data)
assert result['success']
for name in ['score', 'total_person_hours', 'drone_flight_hours']:
    print(name, round(result[name], 2))
