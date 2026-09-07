import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.planning_policy_shared_contract_test import leaf, v4_plan, v5_plan

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'souroldgeezer-policy/skills/planning-policy/references/scripts/validate_plan_contract.py'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def envelope(plan):
    return {'schema': 'planning-approval-handoff-v1',
            'plan_sha256': hashlib.sha256(canonical(plan)).hexdigest(), 'plan': plan}


class PlanningPolicyHandoffTest(unittest.TestCase):
    def setUp(self):
        cache = ROOT / '.cache'
        cache.mkdir(exist_ok=True)
        directory = tempfile.TemporaryDirectory(dir=cache, prefix='handoff-test-')
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.plan = v5_plan(leaf('prepare', 'u1', tier='mechanical'))
        self.path = self.directory / 'plan.json'
        self.path.write_text(json.dumps(self.plan))

    def cli(self, *args, value=None, raw=None, env=None):
        result = subprocess.run([sys.executable, str(SCRIPT), *args],
                                input=json.dumps(value) if value is not None else raw,
                                cwd=self.directory, capture_output=True, text=True,
                                timeout=10, env={**os.environ, **(env or {})})
        self.assertNotIn('Traceback', result.stderr)
        return result.returncode, json.loads(result.stdout)

    def recovered(self, result, plan=None):
        code, value = result
        expected = self.plan if plan is None else plan
        self.assertEqual(code, 0, value)
        self.assertEqual(value['plan'], expected)
        self.assertEqual(hashlib.sha256(canonical(value['plan'])).hexdigest(),
                         envelope(expected)['plan_sha256'])
        self.assertTrue(value['validation']['approval_ready'])
        self.assertFalse(value['validation']['dispatch_ready'])

    def test_inline_survives_source_removal_in_fresh_process(self):
        code, emitted = self.cli('validate', '-', '--emit-handoff', 'inline', value=self.plan)
        self.assertEqual(code, 0, emitted)
        carried = json.dumps(emitted['handoff'])
        self.path.unlink()
        self.recovered(self.cli('resolve-handoff', '-', raw=carried))
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_relative_reference_emits_absolute_and_is_read_only(self):
        before = self.path.read_bytes()
        code, emitted = self.cli('validate', 'plan.json', '--emit-handoff', 'reference')
        self.assertEqual(code, 0, emitted)
        self.assertEqual(emitted['handoff']['plan_path'], str(self.path.resolve()))
        self.path.write_text(json.dumps(self.plan, indent=4))
        self.recovered(self.cli('resolve-handoff', '-', value=emitted['handoff']))
        self.assertEqual(json.loads(before), json.loads(self.path.read_bytes()))
        self.assertEqual(list(self.directory.iterdir()), [self.path])

    def test_tampering_never_returns_partial_plan(self):
        for mode in ('inline', 'reference'):
            with self.subTest(mode=mode):
                self.path.write_text(json.dumps(self.plan))
                code, emitted = self.cli('validate', str(self.path), '--emit-handoff', mode)
                self.assertEqual(code, 0, emitted)
                handoff = emitted['handoff']
                changed = copy.deepcopy(self.plan)
                changed['leaves'][0]['write_set'] = ['unauthorized.py']
                if mode == 'inline':
                    handoff['plan'] = changed
                else:
                    self.path.write_text(json.dumps(changed))
                code, result = self.cli('resolve-handoff', '-', value=handoff)
                self.assertEqual(code, 1, result)
                self.assertEqual(result['blocked'], 'blocked:plan_tampered')
                self.assertNotIn('plan', result)

    def test_malformed_or_ambiguous_envelopes(self):
        base = envelope(self.plan)
        cases = ['summary only', {}, {**base, 'plan_path': str(self.path)},
                 {k: v for k, v in base.items() if k != 'plan'},
                 {**base, 'schema': 'wrong'}, {**base, 'plan_sha256': 'bad'}]
        for path in (None, 3, [], 'relative.json', ''):
            cases.append({'schema': base['schema'], 'plan_sha256': base['plan_sha256'], 'plan_path': path})
        for case in cases:
            with self.subTest(case=case):
                code, result = self.cli('resolve-handoff', '-', value=case)
                self.assertEqual(code, 1, result)
                self.assertEqual(result['blocked'], 'blocked:missing_input')
                self.assertNotIn('plan', result)

    def test_missing_or_truncated_reference_is_io_failure(self):
        handoff = envelope(self.plan)
        del handoff['plan']
        handoff['plan_path'] = str(self.path)
        for content in (None, '{'):
            if content is None:
                self.path.unlink()
            else:
                self.path.write_text(content)
            code, result = self.cli('resolve-handoff', '-', value=handoff)
            self.assertEqual(code, 2, result)
            self.assertEqual(result['blocked'], 'blocked:missing_input')
            self.assertNotIn('plan', result)

    def test_reference_eligibility(self):
        persistent = self.directory / 'temp'
        persistent.mkdir()
        path = persistent / 'plan.json'
        path.write_text(json.dumps(self.plan))
        self.assertEqual(self.cli('validate', str(path), '--emit-handoff', 'reference')[0], 0)
        self.assertEqual(self.cli('validate', '-', '--emit-handoff', 'reference', value=self.plan)[0], 1)
        self.assertEqual(self.cli('validate', str(path), '--emit-handoff', 'reference',
                                  env={'TMPDIR': str(self.directory)})[0], 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'plan.json'
            path.write_text(json.dumps(self.plan))
            self.assertEqual(self.cli('validate', str(path), '--emit-handoff', 'reference')[0], 1)
        if hasattr(os, 'mkfifo'):
            pipe = self.directory / 'pipe'
            os.mkfifo(pipe)
            self.assertEqual(self.cli('validate', str(pipe), '--emit-handoff', 'reference')[0], 1)

    def test_exact_canonical_plan_limit_including_unicode(self):
        for mode in ('inline', 'reference'):
            for marker in ('x', 'é'):
                with self.subTest(mode=mode, marker=marker):
                    plan = copy.deepcopy(self.plan)
                    plan['leaves'][0]['settled_decisions']['padding'] = marker
                    plan['leaves'][0]['settled_decisions']['padding'] += 'x' * (64 * 1024 - len(canonical(plan)))
                    self.assertEqual(len(canonical(plan)), 64 * 1024)
                    self.path.write_text(json.dumps(plan))
                    code, result = self.cli('validate', str(self.path), '--emit-handoff', mode)
                    self.assertEqual(code, 0, result)
                    self.recovered(self.cli('resolve-handoff', '-', value=result['handoff']), plan)
                    plan['leaves'][0]['settled_decisions']['padding'] += 'x'
                    self.path.write_text(json.dumps(plan))
                    code, result = self.cli('validate', str(self.path), '--emit-handoff', mode)
                    self.assertEqual(code, 1, result)
                    self.assertNotIn('handoff', result)

    def test_envelope_limits_and_invalid_json(self):
        for raw, expected in (('{', 2), (json.dumps(envelope(self.plan)) + ' ' * (68 * 1024), 1)):
            code, result = self.cli('resolve-handoff', '-', raw=raw)
            self.assertEqual(code, expected, result)
            self.assertNotIn('plan', result)
        handoff = envelope(self.plan)
        del handoff['plan']
        handoff['plan_path'] = '/' + 'a' * 4096
        code, result = self.cli('resolve-handoff', '-', value=handoff)
        self.assertEqual(code, 1, result)
        self.assertNotIn('plan', result)

    def test_legacy_validate_unchanged_but_cannot_emit_new_handoff(self):
        plan = v4_plan(leaf('prepare', 'u1', tier='mechanical'))
        code, result = self.cli('validate', '-', value=plan)
        self.assertEqual(code, 0, result)
        self.assertTrue(result['resume_ready'])
        self.assertNotIn('handoff', result)
        code, result = self.cli('validate', '-', '--emit-handoff', 'inline', value=plan)
        self.assertEqual(code, 1, result)
        self.assertNotIn('handoff', result)
