"""Compute admission regressions; never import Genesis or create a GUI."""
from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch

from experiment_ops.activity import inspect, parse_processes, require_idle

ROOT = Path(__file__).resolve().parents[1]


class ComputePreflightTests(unittest.TestCase):
    def test_suite_and_standalone_simulator_are_visible_alongside_trainer(self):
        processes = parse_processes(
            "7511 1366 02:00 python3.12 tests/run_all.py\n"
            "8462 1366 00:30 python3 scripts/train_walking_future.py --run-id PRIVATE\n"
            "8634 7511 00:09 python3 tests/smoke_env.py --rough\n"
        )
        self.assertEqual([p['workload'] for p in processes],
                         ['simulation_suite', 'training', 'simulation_test'])
        self.assertEqual([p['ppid'] for p in processes], [1366, 1366, 7511])
        self.assertNotIn('PRIVATE', str(processes))

    def test_python_options_and_module_launches(self):
        for command in ('python3 -u -W ignore -X dev tests/run_all.py',
                        'python3 -m tests.run_all',
                        'python3 -- /repo/tests/run_all.py'):
            with self.subTest(command=command):
                self.assertEqual(parse_processes(f'12 1 00:01 {command}')[0]['workload'],
                                 'simulation_suite')

    def test_script_names_in_arguments_and_inline_code_are_not_jobs(self):
        for command in ('python3 -c "print(1)" scripts/train_walking.py',
                        'python3 scripts/inspect.py tests/run_all.py',
                        'python3 scripts/verify_workspace.py',
                        'zsh -c "python3 tests/run_all.py"'):
            with self.subTest(command=command):
                self.assertEqual(parse_processes(f'12 1 00:01 {command}'), [])

    def test_full_runner_excludes_only_itself_and_sees_another_suite(self):
        ps = subprocess.CompletedProcess([], 0,
            f'{os.getpid()} 1 00:01 python3 tests/run_all.py\n'
            '12345 1 00:02 python3 tests/run_all.py\n', '')
        cwd = subprocess.CompletedProcess([], 0, f'p12345\nfcwd\nn{ROOT}\n', '')
        with patch('experiment_ops.activity.subprocess.run', side_effect=[ps, cwd]):
            result = inspect(ROOT)
        self.assertEqual(result['status'], 'busy')
        self.assertEqual([p['pid'] for p in result['processes']], [12345])

    def test_missing_process_inventory_fails_closed(self):
        with patch('experiment_ops.activity.subprocess.run', side_effect=OSError('unavailable')):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                require_idle(ROOT)
        self.assertEqual(raised.exception.code, 2)

    def test_busy_full_suite_refuses_before_spawning_any_test(self):
        with patch('experiment_ops.activity.inspect', return_value={'status': 'busy', 'processes': []}):
            with patch('subprocess.run') as spawn:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    runpy.run_path(str(ROOT / 'tests/run_all.py'), run_name='__main__')
        self.assertEqual(raised.exception.code, 3)
        spawn.assert_not_called()

    def test_idle_full_suite_preserves_test_commands_and_child_failures(self):
        for child_exit in (0, 1):
            with self.subTest(child_exit=child_exit):
                with patch('experiment_ops.activity.inspect', return_value={'status': 'no_known_training_process'}):
                    with patch('subprocess.run', return_value=subprocess.CompletedProcess([], child_exit)) as spawn:
                        with redirect_stdout(io.StringIO()):
                            if child_exit:
                                with self.assertRaises(SystemExit) as raised:
                                    runpy.run_path(str(ROOT / 'tests/run_all.py'), run_name='__main__')
                                self.assertEqual(raised.exception.code, 1)
                            else:
                                runpy.run_path(str(ROOT / 'tests/run_all.py'), run_name='__main__')
                commands = [call.args[0] for call in spawn.call_args_list]
                self.assertTrue(any(command[-2:] == [str(ROOT / 'tests/smoke_env.py'), '--rough']
                                    for command in commands))
                self.assertGreater(len(commands), 10)


if __name__ == '__main__':
    unittest.main()
