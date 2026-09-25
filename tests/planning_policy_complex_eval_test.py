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


CORRECT_SOURCES = {'catalog.py': 'def normalize(records):\n'
               '    result, seen = [], set()\n'
               '    for record in records:\n'
               "        identifier = record['id'].strip().casefold()\n"
               "        amount = record['amount']\n"
               '        if not identifier:\n'
               "            raise ValueError('empty id')\n"
               '        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:\n'
               "            raise ValueError('invalid amount')\n"
               '        if identifier in seen:\n'
               "            raise ValueError('duplicate id')\n"
               '        seen.add(identifier)\n'
               "        result.append({'id': identifier, 'label': ' '.join(record['label'].split()), "
               "'amount': amount})\n"
               '    return result\n',
 'summary.py': 'from catalog import normalize\n'
               '\n'
               'def totals(records):\n'
               '    result = {}\n'
               '    for record in normalize(records):\n'
               "        key = record['id'][0]\n"
               "        result[key] = result.get(key, 0) + record['amount']\n"
               '    return dict(sorted(result.items()))\n',
 'render.py': 'from catalog import normalize\n'
              '\n'
              'def rows(records):\n'
              '    return [f"{r[\'id\']}|{r[\'label\']}|{r[\'amount\']}" for r in sorted(normalize(records), '
              "key=lambda r: r['id'])]\n",
 'export.py': 'from summary import totals\n'
              'from render import rows\n'
              '\n'
              'def build(records):\n'
              "    return {'totals': totals(records), 'rows': rows(records)}\n"}

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
            for name, content in CORRECT_SOURCES.items():
                (trial / name).write_text(content)
            self.assertTrue(grader.run_oracle(trial)['passed'])
            (trial / 'catalog.py').write_text((trial / 'catalog.py').read_text().replace('if identifier in seen:', 'if False:'))
            self.assertFalse(grader.run_oracle(trial)['passed'])

    def test_real_fork_join_lifecycle_and_generated_packets_survive_fresh_processes(self):
        ledger_script = ROOT / 'souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py'
        helper_script = ROOT / 'souroldgeezer-policy/skills/git-workflow-policy/references/scripts/planning_worktree.py'
        with tempfile.TemporaryDirectory() as temporary:
            trial = Path(temporary) / 'trial'
            shutil.copytree(FIXTURE, trial)
            (trial / '.gitignore').write_text('.worktrees/\n.evaluation/\n')
            def command(argv, cwd=trial, successful=True):
                proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
                if successful:
                    self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
                return proc
            command(['git', 'init', '-q', '--initial-branch=main'])
            command(['git', 'config', 'user.email', 'fixture@example.invalid'])
            command(['git', 'config', 'user.name', 'Fixture'])
            command(['git', 'add', '--', '.'])
            command(['git', 'commit', '-qm', 'Fixture baseline'])
            evidence = trial / '.evaluation'
            evidence.mkdir()
            modules = [('catalog', []), ('summary', ['catalog']), ('render', ['catalog']), ('export', ['summary', 'render'])]
            assertions = {
                'catalog': 'from catalog import normalize; assert normalize([]) == []',
                'summary': 'from summary import totals; assert totals([]) == {}',
                'render': 'from render import rows; assert rows([]) == []',
                'export': "from export import build; assert build([]) == {'totals': {}, 'rows': []}",
            }
            import shlex
            leaves = [{
                'id': name, 'dependencies': deps, 'task': f'Implement {name} from the shared catalog requirements.',
                'boundary': f'Only {name}.py', 'read_set': ['task.md', f'{name}.py'], 'write_set': [f'{name}.py'],
                'settled_decisions': {'contract': 'Follow shared plan decisions and task.md.'},
                'size': 'small', 'portable_tier': 'standard', 'worktree_owner': f'worker/{name}',
                'acceptance_command': f'{shlex.quote(sys.executable)} -B -c {shlex.quote(assertions[name])}',
                'return_contract': 'bounded-step-return-v1', 'stop_conditions': ['missing_load_bearing_information'],
                'work_unit_id': name, 'max_attempts': 2,
                'capability_requirements': {'baseline': 'plan-step-base-v1', 'additional': []},
            } for name, deps in modules]
            plan = {'contract_version': 5, 'objective': 'Deliver consistent catalog exports.',
                'scope_summary': 'The four named Python modules only.',
                'approved_decisions': ['IDs use strip then casefold.', 'Reject duplicates; do not merge them.',
                                       'Validate empty ID before amount before duplicate ID.', 'Never mutate caller records.'],
                'work_units': [{'id': name, 'original_size': 'small', 'cohesive_outcome': f'Deliver {name}',
                                'decomposition': {'shape': 'single'}} for name, _ in modules], 'leaves': leaves}
            import hashlib
            digest = hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            binding = {'schema': 'planning-capability-binding-v1', 'plan_sha256': digest, 'bindings': [
                {'step_id': leaf['id'], 'host': 'codex', 'executor': 'gpt-5.6-terra',
                 'requirements': leaf['capability_requirements'], 'evidence': ['Synthetic deterministic executor.']} for leaf in leaves]}
            assignments = [{'id': name, 'harness': 'codex', 'model_or_alias': 'gpt-5.6-terra',
                            'effort': 'medium', 'worktree': str(trial / '.worktrees' / name)} for name, _ in modules]
            for filename, data in [('plan', plan), ('binding', binding), ('assignments', assignments)]:
                (evidence / f'{filename}.json').write_text(json.dumps(data))
            def call(*args, successful=True):
                return command([sys.executable, '-B', str(ledger_script), '--repo-root', str(trial),
                                '--plan-id', 'complex-evaluation', *args], successful=successful)
            init = json.loads(call('init-v5', '--actor', 'parent', '--approved', '--plan-file',
                str(evidence / 'plan.json'), '--assignments-file', str(evidence / 'assignments.json'),
                '--capability-binding-file', str(evidence / 'binding.json')).stdout)
            run_id = init['run_id']
            self.assertNotEqual(call('transition', '--actor', 'parent', '--run-id', run_id,
                '--step-id', 'export', '--to', 'ready', '--agent-id', 'premature', successful=False).returncode, 0)
            for leaf in leaves:
                name = leaf['id']
                worktree = trial / '.worktrees' / name
                command(['git', 'worktree', 'add', '-q', '-b', f'worker/{name}', str(worktree), 'main'])
                for state in ('ready', 'in_progress'):
                    call('transition', '--actor', 'parent', '--run-id', run_id, '--step-id', name,
                         '--to', state, '--agent-id', f'worker-{name}')
                # Each invocation is a fresh process; recovery reads only persisted state.
                resumed = json.loads(call('show', '--run-id', run_id, '--next-only').stdout)
                self.assertIn('next', resumed)
                packet = json.loads(call('handoff', '--run-id', run_id, '--step-id', name).stdout)['handoff']
                self.assertEqual(packet['plan_context']['approved_decisions'], plan['approved_decisions'])
                self.assertEqual(packet['leaf']['dependencies'], leaf['dependencies'])
                (worktree / f'{name}.py').write_text(CORRECT_SOURCES[f'{name}.py'])
                command(shlex.split(leaf['acceptance_command']), cwd=worktree)
                command(['git', 'add', '--', f'{name}.py'], cwd=worktree)
                command(['git', 'commit', '-qm', f'Implement {name}'], cwd=worktree)
                commit = command(['git', 'rev-parse', 'HEAD'], cwd=worktree).stdout.strip()
                returned = {'schema': 'bounded-step-return-v1', 'step_id': name, 'agent_id': packet['agent_id'],
                    'attempt_id': packet['attempt_id'], 'status': 'completed', 'changed_paths': [f'{name}.py'],
                    'acceptance': {'command': leaf['acceptance_command'], 'exit_code': 0, 'summary': 'Passed scoped check.'},
                    'blockers': [], 'notes': [], 'unstarted_remainder': [], 'commit_hash': commit}
                handoff_file, return_file = evidence / f'{name}-handoff.json', evidence / f'{name}-return.json'
                handoff_file.write_text(json.dumps(packet)); return_file.write_text(json.dumps(returned))
                call('validate-return', '--handoff-file', str(handoff_file), '--return-file', str(return_file))
                call('record-return', '--actor', 'parent', '--run-id', run_id, '--return-file', str(return_file))
                integrate_file, cleanup_file = evidence / f'{name}-integrate.json', evidence / f'{name}-cleanup.json'
                helper_base = ['--repo-root', str(trial), '--target', 'main', '--branch', f'worker/{name}', '--worktree', str(worktree)]
                integrated = command([sys.executable, '-B', str(helper_script), 'integrate', *helper_base, '--source-commit', commit])
                integrate_file.write_text(integrated.stdout)
                if json.loads(integrated.stdout)['rebased_tree_changed']:
                    command(shlex.split(leaf['acceptance_command']), cwd=worktree)
                call('transition', '--actor', 'parent', '--run-id', run_id, '--step-id', name, '--to', 'integrated', '--worktree-result', str(integrate_file))
                cleaned = command([sys.executable, '-B', str(helper_script), 'cleanup', *helper_base, '--integrated-result', str(integrate_file)])
                cleanup_file.write_text(cleaned.stdout)
                call('transition', '--actor', 'parent', '--run-id', run_id, '--step-id', name, '--to', 'cleaned', '--worktree-result', str(cleanup_file))
            call('validate', '--run-id', run_id, '--closeout')
            call('close', '--actor', 'parent', '--run-id', run_id, '--outcome', 'completed')
            graded = load_grader().grade(trial, 'complex-evaluation', run_id)
            self.assertTrue(graded['passed'], graded)
            self.assertEqual(graded['worker_leaves'], 4)
            self.assertIsNone(graded['observations']['worker_rediscovery'])

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
