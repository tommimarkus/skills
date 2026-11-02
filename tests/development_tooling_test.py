"""Routing contracts for conditional development tooling, not model behavior proof."""
import json
import unittest

from tests.surface_test_lib import REPO_ROOT, load_script_module, read, read_jsonl

PROCEDURE = 'souroldgeezer-design/docs/design-reference/development-tooling.md'
DESIGN = 'souroldgeezer-design/skills'


class DevelopmentToolingTest(unittest.TestCase):
    def test_public_trigger_and_router_discover_tooling(self):
        for path in (f'{DESIGN}/software-design/SKILL.md',
                     'souroldgeezer-design/agents/software-design.md'):
            description = read(path).split('---')[1]
            self.assertIn('development tooling', description)
            self.assertIn('reference-derived data', description)

    def test_each_owner_links_the_single_shared_procedure(self):
        for owner in ('software-design', 'app-design', 'api-design', 'infra-design'):
            with self.subTest(owner=owner):
                text = read(f'{DESIGN}/{owner}/SKILL.md')
                self.assertIn('../../docs/design-reference/development-tooling.md', text)
                self.assertTrue((REPO_ROOT / PROCEDURE).is_file())
        short_lane = read(f'{DESIGN}/software-design/references/procedures/file-edit-lane.md')
        self.assertNotIn('development-tooling.md', short_lane)

    def test_declared_routes_include_tooling_only_when_relevant(self):
        scenarios = json.loads(read('tests/skill_load_cost/scenarios.json'))
        by_id = {row['id']: row for row in scenarios}
        expected = {'sd-build-tooling', 'sd-review-tooling', 'sd-lookup-reference-data',
                    'app-build-tooling', 'api-review-tooling', 'infra-build-tooling'}
        found = set()
        for row in scenarios:
            targets = row.get('files', []) + [r['target'] for r in row.get('load_routes', [])]
            if PROCEDURE in targets:
                found.add(row['id'])
                self.assertEqual(1, targets.count(PROCEDURE), row['id'])
        self.assertEqual(expected, found)
        for identifier in expected:
            self.assertIn(identifier, by_id)

    def test_behavior_pack_covers_decisions_with_original_evidence(self):
        cases = {row['id']: row for row in read_jsonl(
            f'{DESIGN}/software-design/references/evals/behavior-cases.jsonl')}
        for suffix in ('reuse', 'first-use', 'importer', 'ambiguous-unsupported',
                       'source-disagreement', 'trivial', 'read-only',
                       'uninstalled', 'licence-choice', 'user-preference', 'task-favorites'):
            case = cases[f'software-design-behavior-tooling-{suffix}']
            self.assertTrue(case['required_checks'])
            self.assertTrue(case['forbidden_behaviors'])
            self.assertFalse(case['contains_third_party_text'])
        for owner in ('app-design', 'api-design', 'infra-design'):
            cases = read_jsonl(f'{DESIGN}/{owner}/references/evals/behavior-cases.jsonl')
            self.assertIn(f'{owner}-behavior-tooling-opportunity', {c['id'] for c in cases})

    def test_original_fixture_demonstrates_valid_but_unfaithful_data(self):
        root = REPO_ROOT / DESIGN / 'software-design/references/evals/development-tooling'
        importer = load_script_module('tooling_fixture_importer', root / 'importer.py')
        consumer = load_script_module('tooling_fixture_consumer', root / 'consumer.py')
        records = json.loads((root / 'records.json').read_text())
        importer.validate(records)
        self.assertEqual(records, importer.extract((root / 'reference.md').read_text()))
        oracle = json.loads((root / 'oracle.json').read_text())
        self.assertNotEqual(oracle['saturation'], consumer.execute(records, ['pulse'] * 4))
        self.assertEqual(oracle['damp'], consumer.execute(records, ['pulse', 'damp-pulse']))
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            consumer.execute(records, ['relay'])


if __name__ == '__main__':
    unittest.main()
