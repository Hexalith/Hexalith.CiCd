"""Exercise every relocated entry point through its real fixture/output paths."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class QualificationRelocationTests(unittest.TestCase):
    def test_runner_bodies_preserve_results_and_frozen_fixture_reads(self):
        with tempfile.TemporaryDirectory(prefix='qualification-relocation-') as temporary:
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'tools/qualification/exercise_relocation.py'), '--allow-dirty'],
                cwd=ROOT, env=dict(os.environ, TMPDIR=temporary, TMP=temporary, TEMP=temporary),
                text=True, capture_output=True, timeout=60,
            )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(
            {'folders-product', 'folders-final', 'projects', 'g6', 'eventstore', 'parties', 'parties-success', 'released-policy-refusal'},
            set(report['exercises']),
        )
        for name, exercise in report['exercises'].items():
            with self.subTest(name=name):
                self.assertTrue(exercise['code_and_fixtures_unchanged'])
                self.assertGreater(exercise['controlled_external_calls'], 0)
                self.assertTrue(exercise['fixture_reads'])
        self.assertEqual('failed', report['exercises']['folders-product']['preserved_result'])
        self.assertEqual('blocked', report['exercises']['folders-final']['preserved_result'])
        self.assertIn('exact-input refusal', report['exercises']['parties']['preserved_result'])
        success = report['exercises']['parties-success']
        self.assertIn('controlled disposable receipts and source', success['fixture_basis'])
        self.assertEqual({
            'parties': {'path': 'parties-publication-results/parties-commit-message.txt',
                        'contents': 'build(cicd): prepare Parties shared pipeline migration\n'},
            'cicd': {'path': 'parties-publication-results/cicd-commit-message.txt',
                     'contents': 'build(cicd): record Parties migration preparation\n'},
        }, success['messages'])
        self.assertIn('full preparation body completed', report['exercises']['eventstore']['preserved_result'])
        self.assertIn('do not establish fresh module readiness', report['scope'])

    def test_parties_receipts_match_in_both_interpreter_modes(self):
        # The outer unittest checks the actual receipts, including when -O
        # disables the relocation exercise's own assertions in the child.
        runner = (
            "import json, os\n"
            "from pathlib import Path\n"
            "from exercise_relocation import ROOT, exercise\n"
            "scratch = Path(os.environ['TMPDIR'])\n"
            "checks = ('qualification_error', 'fixture_reads', 'controlled_external_calls', 'policy_calls')\n"
            "results = {}\n"
            "for case in ('source', 'pin', 'tree', 'commitlint', 'success'):\n"
            "    run = exercise(ROOT, scratch / case, 'parties', parties_case=case)\n"
            "    results[case] = {key: run[key] for key in checks}\n"
            "print(json.dumps(results))\n"
        )
        fixtures = ROOT / 'tools/qualification/pre-adoption/parties/fixtures'
        source = json.loads((fixtures / 'current-preparation-state.json').read_text())['untracked_inputs'][0]
        errors = {'source': source['path'], 'pin': 'dependency pin mismatch: references/Hexalith.Builds',
                  'tree': 'staged tree ' + 'c' * 40 + ' differs from expected ' + 'd' * 40,
                  'commitlint': 'controlled commitlint rejection'}
        results = []
        for flags in ([], ['-O']):
            with self.subTest(flags=flags), tempfile.TemporaryDirectory() as temporary:
                env = dict(os.environ, TMPDIR=temporary, TMP=temporary, TEMP=temporary)
                env.pop('PYTHONOPTIMIZE', None)
                child = subprocess.run([sys.executable, *flags, '-B', '-c', runner],
                                       cwd=ROOT / 'tools/qualification', env=env,
                                       capture_output=True, text=True, timeout=60)
                self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
                report = Path('parties/scratch/parties-publication-results/pre-push-qualification.json')
                traces = json.loads(child.stdout)
                receipts = {}
                for case, expected in errors.items():
                    with self.subTest(case=case):
                        refused = json.loads((Path(temporary) / case / report).read_text())
                        self.assertEqual(traces[case]['qualification_error'], expected)
                        self.assertEqual((refused['result'], refused['error']), ('failed', expected))
                        receipts[case] = refused
                passed = json.loads((Path(temporary) / 'success' / report).read_text())
                self.assertIsNone(traces['success']['qualification_error'])
                self.assertEqual((passed['result'], passed['exact_verified_inputs']), ('pass', True))
                self.assertEqual(passed['released_audit_lint'], 'pass')
                self.assertEqual(passed['released_action_lint'], 'pass')
                self.assertEqual({name: entry['result'] for name, entry in passed['messages'].items()},
                                 {'parties': 'pass', 'cicd': 'pass'})
                # Only the disposable fixture root is specific to a run.
                evidence = Path(passed['existing_product_test_evidence']).relative_to(temporary)
                passed['existing_product_test_evidence'] = str(evidence)
                results.append((receipts, passed, traces))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], results[1])


if __name__ == '__main__':
    unittest.main()
