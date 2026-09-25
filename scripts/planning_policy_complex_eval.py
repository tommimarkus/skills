#!/usr/bin/env python3
"""Grade a completed complex-plan trial without dispatch or usage collection."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / 'tests/planning_policy_complex/oracle.py'
OBSERVATION_KEYS = {'first_attempt_handoff_acceptance', 'worker_rediscovery', 'parent_repairs', 'interruption_recovery'}


def dependency_shape(leaves):
    """Find independent branches with a common ancestor and a later join."""
    graph = {leaf['id']: set(leaf['dependencies']) for leaf in leaves}
    def ancestors(node, visited=None):
        visited = set() if visited is None else visited
        for dependency in graph.get(node, set()):
            if dependency not in visited:
                visited.add(dependency)
                ancestors(dependency, visited)
        return visited
    reach = {node: ancestors(node) for node in graph}
    for join in graph:
        branches = sorted(reach[join])
        for index, left in enumerate(branches):
            for right in branches[index + 1:]:
                if left not in reach.get(right, set()) and right not in reach.get(left, set()):
                    if reach.get(left, set()) & reach.get(right, set()):
                        return True
    return False


def observations(value):
    """Observer-supplied facts cannot be reconstructed from successful returns."""
    if value is None:
        return dict.fromkeys(sorted(OBSERVATION_KEYS))
    if not isinstance(value, dict) or set(value) != OBSERVATION_KEYS:
        raise ValueError('observations must contain exactly the four documented fields')
    for name, count in value.items():
        if count is None:
            continue
        if name == 'interruption_recovery':
            if not isinstance(count, bool):
                raise ValueError('interruption_recovery must be boolean or null')
        elif isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError('observation counts must be nonnegative integers or null')
    return value


def run_oracle(trial):
    try:
        run = subprocess.run([sys.executable, '-B', str(ORACLE), str(trial)],
            cwd=trial, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        return {'passed': run.returncode == 0, 'exit_code': run.returncode,
                'sha256': hashlib.sha256(ORACLE.read_bytes()).hexdigest()}
    except (OSError, subprocess.TimeoutExpired):
        return {'passed': False, 'exit_code': None, 'sha256': hashlib.sha256(ORACLE.read_bytes()).hexdigest()}


def grade(trial, plan_id, run_id, observed=None):
    result = {'schema': 'planning-complex-evaluation-v1', 'task_oracle': run_oracle(trial),
              'workflow': 'not-evaluated', 'dependency_fork_join': False,
              'observations': observations(observed), 'limits': ['No provider usage or worker behavior is inferred from ledger success.']}
    try:
        top = subprocess.run(['git', '-C', str(trial), 'rev-parse', '--show-toplevel'],
            text=True, capture_output=True, check=True, timeout=10).stdout.strip()
        if Path(top).resolve() != trial.resolve():
            raise ValueError('trial-root must be the synthetic repository root')
        source = ROOT / 'souroldgeezer-policy/skills/planning-policy/references/scripts/planning_ledger.py'
        spec = importlib.util.spec_from_file_location('complex_trial_ledger', source)
        ledger = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ledger)
        args = SimpleNamespace(repo_root=str(trial), ledger_root=None, plan_id=plan_id, run_id=run_id)
        directory, data, plan, _ = ledger.load2(args)
        ledger.validate_events2(directory, data)
        result['plan_sha256'] = data['plan_hash']
        result['dependency_fork_join'] = dependency_shape(plan['leaves'])
        result['worker_leaves'] = len(data['steps'])
        result['ledger_attempts'] = sum(step['attempt_count'] for step in data['steps'].values())
        result['workflow'] = 'passed' if (data['run_status'] == 'closed' and data['outcome'] == 'completed'
            and all(step['status'] == 'cleaned' for step in data['steps'].values())) else 'failed'
        dirty = subprocess.run(['git', '-C', str(trial), 'status', '--porcelain'], capture_output=True, text=True, check=True, timeout=10)
        if dirty.stdout.strip():
            result['workflow'] = 'failed'
            result['limits'].append('Trial repository has uncommitted changes.')
    except Exception as error:
        # Any unreadable or malformed evidence prevents a workflow verdict.
        result['workflow'] = 'not-evaluated'
        result['limits'].append(str(error)[:240])
    result['passed'] = bool(result['task_oracle']['passed'] and result['workflow'] == 'passed' and result['dependency_fork_join'])
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trial-root', type=Path, required=True)
    parser.add_argument('--plan-id', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--observations-file', type=Path)
    args = parser.parse_args(argv)
    try:
        observed = None
        if args.observations_file:
            with args.observations_file.open('rb') as stream:
                raw = stream.read(4097)
            if len(raw) > 4096:
                raise ValueError('observations exceed 4 KiB')
            observed = json.loads(raw)
        result = grade(args.trial_root.resolve(), args.plan_id, args.run_id, observed)
    except (ValueError, OSError) as error:
        print(json.dumps({'schema': 'planning-complex-evaluation-v1', 'passed': False, 'error': str(error)[:240]}))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(',', ':')))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
