"""Behavioral coverage for host-aware owning G-6 scheduler publication."""
from pathlib import Path
import importlib.util
import json
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'tools/qualification/qualify-owning-g6.py'
SPEC = importlib.util.spec_from_file_location('g6_host_ports', SOURCE)
G6 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G6)


class G6HostPortsTests(unittest.TestCase):
    def test_windows_ranges_parse_without_relying_on_header_language(self):
        result = subprocess.CompletedProcess([], 0, 'Ports exclus\r\n 51801 51900 *\r\n 52000 52099\r\n')
        with patch.object(G6.shutil, 'which', return_value='netsh.exe'), \
                patch.object(G6.subprocess, 'run', return_value=result):
            self.assertEqual(((51801, 51900), (52000, 52099)), G6._windows_excluded_ports())

    def test_invalid_windows_range_fails(self):
        result = subprocess.CompletedProcess([], 0, '51900 51801\n')
        with patch.object(G6.shutil, 'which', return_value='netsh.exe'), \
                patch.object(G6.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(ValueError, 'Invalid Windows'):
                G6._windows_excluded_ports()

    def test_unrecognized_numeric_windows_row_is_not_silently_ignored(self):
        result = subprocess.CompletedProcess([], 0, '51801 invalid\n')
        with patch.object(G6.shutil, 'which', return_value='netsh.exe'), \
                patch.object(G6.subprocess, 'run', return_value=result):
            with self.assertRaisesRegex(ValueError, 'Unrecognized Windows'):
                G6._windows_excluded_ports()

    def test_windows_query_is_optional_only_when_tool_is_absent(self):
        with patch.object(G6.shutil, 'which', return_value=None), \
                patch.object(G6.platform, 'release', return_value='generic-linux'), \
                patch.object(G6.subprocess, 'run') as run:
            self.assertEqual((), G6._windows_excluded_ports())
            run.assert_not_called()

    def test_wsl_uses_windows_tool_when_interop_path_is_not_imported(self):
        result = subprocess.CompletedProcess([], 0, '51801 51900\n')
        with patch.object(G6.shutil, 'which', return_value=None), \
                patch.object(G6.platform, 'release', return_value='microsoft-standard-WSL2'), \
                patch.object(G6.Path, 'is_file', return_value=True), \
                patch.object(G6.subprocess, 'run', return_value=result) as run:
            self.assertEqual(((51801, 51900),), G6._windows_excluded_ports())
            self.assertEqual('/mnt/c/Windows/System32/netsh.exe', run.call_args.args[0][0])

    def test_windows_query_refusal_is_preserved(self):
        with patch.object(G6.shutil, 'which', return_value='netsh.exe'), \
                patch.object(G6.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['netsh.exe'])):
            with self.assertRaises(subprocess.CalledProcessError):
                G6._windows_excluded_ports()

    def test_locally_free_but_windows_excluded_port_is_not_selected(self):
        allocate = Mock(side_effect=[51825, 53123])
        with patch.object(G6, '_windows_excluded_ports', return_value=((51801, 51900),)):
            self.assertEqual(53123, G6._scheduler_host_port(allocate=allocate))
        self.assertEqual(2, allocate.call_count)

    def test_excluded_allocation_exhaustion_is_bounded(self):
        allocate = Mock(return_value=51825)
        with patch.object(G6, '_windows_excluded_ports', return_value=((51801, 51900),)):
            with self.assertRaisesRegex(RuntimeError, 'bounded allocation'):
                G6._scheduler_host_port(allocate=allocate, attempts=3)
        self.assertEqual(3, allocate.call_count)

    @staticmethod
    def publication_error():
        return subprocess.CalledProcessError(125, ['docker', 'run'], stderr=(
            'ports are not available: /forwards/expose returned unexpected status: 500'))

    def test_publication_collision_cleans_failed_attempt_before_retry(self):
        events = []

        def create(port, attempt):
            events.append(('create', port, attempt))
            if attempt == 1:
                raise self.publication_error()
            return 'owned-scheduler', port

        result = G6._start_scheduler(create, lambda: events.append(('discard',)),
                                     allocate=Mock(side_effect=[53123, 53124]))
        self.assertEqual(('owned-scheduler', 53124), result)
        self.assertEqual([('create', 53123, 1), ('discard',), ('create', 53124, 2)], events)

    def test_nonpublication_failure_is_not_retried(self):
        create = Mock(side_effect=subprocess.CalledProcessError(125, ['docker', 'run'], stderr='image access denied'))
        discard = Mock()
        with self.assertRaises(subprocess.CalledProcessError):
            G6._start_scheduler(create, discard, allocate=lambda: 53123)
        create.assert_called_once()
        discard.assert_not_called()

    def test_native_docker_publication_collisions_are_retried(self):
        for diagnostic in ('port is already allocated', 'bind: address already in use'):
            with self.subTest(diagnostic=diagnostic):
                error = subprocess.CalledProcessError(125, ['docker', 'run'], stderr=diagnostic)
                create = Mock(side_effect=[error, ('owned-scheduler', 53123)])
                discard = Mock()
                self.assertEqual(('owned-scheduler', 53123), G6._start_scheduler(create, discard, allocate=lambda: 53123))
                discard.assert_called_once()

    def test_final_publication_failure_is_not_hidden(self):
        failure = self.publication_error()
        create, discard = Mock(side_effect=failure), Mock()
        with self.assertRaises(subprocess.CalledProcessError) as caught:
            G6._start_scheduler(create, discard, allocate=lambda: 53123, attempts=3)
        self.assertIs(failure, caught.exception)
        self.assertEqual(3, create.call_count)
        self.assertEqual(3, discard.call_count)

    def test_advertised_and_published_scheduler_ports_must_match(self):
        with self.assertRaisesRegex(ValueError, 'advertised port'):
            G6._start_scheduler(lambda *_: ('owned-scheduler', 53124), Mock(), allocate=lambda: 53123)

    def test_cleanup_refuses_foreign_container(self):
        with patch.object(G6.subprocess, 'check_output', return_value=json.dumps({'hexalith.story18-g6': 'foreign'})), \
                patch.object(G6.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'custody changed'):
                G6._remove_owned_container('a' * 64, 'owned')
            run.assert_not_called()

    def test_cleanup_does_not_treat_control_plane_refusal_as_absence(self):
        responses = [json.dumps({'hexalith.story18-g6': 'owned'}), subprocess.CalledProcessError(1, ['docker', 'container', 'ls'])]
        with patch.object(G6.subprocess, 'check_output', side_effect=responses), patch.object(G6.subprocess, 'run'):
            with self.assertRaises(subprocess.CalledProcessError):
                G6._remove_owned_container('a' * 64, 'owned')

    def test_cleanup_requires_verified_removal(self):
        responses = [json.dumps({'hexalith.story18-g6': 'owned'}), 'a' * 64 + '\n']
        with patch.object(G6.subprocess, 'check_output', side_effect=responses), patch.object(G6.subprocess, 'run'):
            with self.assertRaisesRegex(ValueError, 'removal could not be verified'):
                G6._remove_owned_container('a' * 64, 'owned')

    def test_cleanup_records_verified_owned_removal(self):
        responses = [json.dumps({'hexalith.story18-g6': 'owned'}), '']
        with patch.object(G6.subprocess, 'check_output', side_effect=responses), patch.object(G6.subprocess, 'run'):
            self.assertEqual({'id': 'a' * 64, 'removed': True}, G6._remove_owned_container('a' * 64, 'owned'))

    def test_uncertain_create_recovers_exact_owned_identity_without_a_valid_cid(self):
        for content in (None, '', 'invalid'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                cidfile = Path(directory) / 'owned.cid'
                if content is not None:
                    cidfile.write_text(content)
                owned = []
                with patch.object(G6.subprocess, 'check_output', return_value='a' * 64 + '\n') as query:
                    self.assertEqual('a' * 64, G6._record_container_custody(cidfile, 'owned-scheduler', 'owned', owned))
                self.assertEqual(['a' * 64], owned)
                command = query.call_args.args[0]
                self.assertIn('name=^/owned-scheduler$', command)
                self.assertIn('label=hexalith.story18-g6=owned', command)

    def test_uncertain_create_query_failure_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(G6.subprocess, 'check_output', side_effect=subprocess.CalledProcessError(1, ['docker', 'ls'])):
            with self.assertRaises(subprocess.CalledProcessError):
                G6._record_container_custody(Path(directory) / 'absent.cid', 'owned-scheduler', 'owned', [])

    def test_cleanup_rechecks_absence_after_successful_remove_and_failed_verification(self):
        removed = set()
        failure = subprocess.CalledProcessError(1, ['docker', 'container', 'ls'])
        responses = [json.dumps({'hexalith.story18-g6': 'owned'}), failure, '']
        with patch.object(G6.subprocess, 'check_output', side_effect=responses) as query, \
                patch.object(G6.subprocess, 'run') as remove:
            with self.assertRaises(subprocess.CalledProcessError):
                G6._remove_owned_container('a' * 64, 'owned', removed=removed)
            self.assertEqual({'id': 'a' * 64, 'removed': True}, G6._remove_owned_container('a' * 64, 'owned', removed=removed))
            remove.assert_called_once()
            self.assertEqual(1, sum(call.args[0][1] == 'inspect' for call in query.call_args_list))

    def test_cleanup_attempts_every_identity_and_writes_failures(self):
        error = subprocess.CalledProcessError(1, ['docker', 'inspect'])
        with tempfile.TemporaryDirectory() as directory, patch.object(G6, '_remove_owned_container',
                side_effect=[error, {'id': 'a' * 64, 'removed': True}]) as remove:
            report = Path(directory) / 'cleanup.json'
            with self.assertRaises(ExceptionGroup):
                G6._cleanup_owned_containers(['a' * 64, 'b' * 64], 'owned', set(), [], report)
            records = json.loads(report.read_text())
            self.assertEqual(2, remove.call_count)
            self.assertFalse(records[0]['removed'])
            self.assertTrue(records[1]['removed'])

    def test_late_owned_create_is_reconciled_again_during_final_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            cidfile = Path(directory) / 'absent.cid'
            owned = []
            with patch.object(G6.subprocess, 'check_output', side_effect=['', 'a' * 64 + '\n']), \
                    patch.object(G6, '_remove_owned_container', return_value={'id': 'a' * 64, 'removed': True}) as remove:
                self.assertEqual('', G6._record_container_custody(cidfile, 'owned-scheduler', 'owned', owned))
                G6._cleanup_owned_containers(owned, 'owned', set(), [], Path(directory) / 'cleanup.json',
                    pending={'owned-scheduler': cidfile})
                remove.assert_called_once()
                self.assertEqual(['a' * 64], owned)

    def test_unresolved_create_never_reports_complete_cleanup(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(G6.subprocess, 'check_output', return_value=''):
            report = Path(directory) / 'cleanup.json'
            with self.assertRaises(ExceptionGroup):
                G6._cleanup_owned_containers([], 'owned', set(), [], report,
                    pending={'owned-scheduler': Path(directory) / 'absent.cid'})
            self.assertTrue(json.loads(report.read_text())[0]['custody_unresolved'])


if __name__ == '__main__':
    unittest.main()
