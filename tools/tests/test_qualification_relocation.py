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


if __name__ == '__main__':
    unittest.main()
