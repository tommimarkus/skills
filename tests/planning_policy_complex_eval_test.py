"""Complex-plan evidence must distinguish task success from workflow evidence."""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/planning_policy_complex_eval.py'
FIXTURE = ROOT / 'tests/planning_policy_complex/fixture'


def load_grader():
    spec = importlib.util.spec_from_file_location('complex_eval', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ComplexPlanEvalTest(unittest.TestCase):
    def test_dependency_shape_requires_a_real_fork_and_join(self):
        grade = load_grader().dependency_shape
        independent = [{'id': name, 'dependencies': []} for name in ('core', 'a', 'b', 'join')]
        self.assertFalse(grade(independent))
        graph = [
            {'id': 'core', 'dependencies': []},
            {'id': 'a', 'dependencies': ['core']},
            {'id': 'b', 'dependencies': ['core']},
            {'id': 'join', 'dependencies': ['a', 'b']},
        ]
        self.assertTrue(grade(graph))
        graph[2]['dependencies'] = ['a']
        self.assertFalse(grade(graph))

    def test_observations_remain_unknown_without_independent_evidence(self):
        grader = load_grader()
        self.assertEqual(grader.observations(None), {
            'first_attempt_handoff_acceptance': None,
            'worker_rediscovery': None,
            'parent_repairs': None,
            'interruption_recovery': None,
        })
        with self.assertRaises(ValueError):
            grader.observations({'first_attempt_handoff_acceptance': True})

    def test_immutable_oracle_rejects_stubs_and_accepts_correct_outputs(self):
        grader = load_grader()
        with tempfile.TemporaryDirectory() as temporary:
            trial = Path(temporary) / 'trial'
            shutil.copytree(FIXTURE, trial)
            self.assertFalse(grader.run_oracle(trial)['passed'])
            (trial / 'catalog.py').write_text('''def normalize(records):
    result, seen = [], set()
    for record in records:
        identifier = record['id'].strip().casefold()
        amount = record['amount']
        if not identifier:
            raise ValueError('empty id')
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise ValueError('invalid amount')
        if identifier in seen:
            raise ValueError('duplicate id')
        seen.add(identifier)
        result.append({'id': identifier, 'label': ' '.join(record['label'].split()), 'amount': amount})
    return result
''')
            (trial / 'summary.py').write_text('''from catalog import normalize

def totals(records):
    result = {}
    for record in normalize(records):
        key = record['id'][0]
        result[key] = result.get(key, 0) + record['amount']
    return dict(sorted(result.items()))
''')
            (trial / 'render.py').write_text('''from catalog import normalize

def rows(records):
    return [f"{r['id']}|{r['label']}|{r['amount']}" for r in sorted(normalize(records), key=lambda r: r['id'])]
''')
            (trial / 'export.py').write_text('''from summary import totals
from render import rows

def build(records):
    return {'totals': totals(records), 'rows': rows(records)}
''')
            self.assertTrue(grader.run_oracle(trial)['passed'])
            (trial / 'catalog.py').write_text((trial / 'catalog.py').read_text().replace('if identifier in seen:', 'if False:'))
            self.assertFalse(grader.run_oracle(trial)['passed'])

    def test_cli_reports_missing_ledger_without_claiming_workflow_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            trial = Path(temporary) / 'trial'
            shutil.copytree(FIXTURE, trial)
            proc = subprocess.run([sys.executable, '-B', str(SCRIPT), '--trial-root', str(trial),
                '--plan-id', 'complex-evaluation', '--run-id', '11111111-1111-4111-8111-111111111111'], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            result = json.loads(proc.stdout)
            self.assertEqual(result['workflow'], 'not-evaluated')
            self.assertFalse(result['task_oracle']['passed'])
            self.assertIsNone(result['observations']['parent_repairs'])
