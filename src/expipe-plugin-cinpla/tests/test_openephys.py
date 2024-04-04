import pytest
import expipe
import subprocess
import click
from click.testing import CliRunner
import quantities as pq
import os.path as op
from expipe_plugin_cinpla.openephys import OpenEphysPlugin
from expipe_plugin_cinpla.optogenetics import OptoPlugin
from expipe_plugin_cinpla.main import CinplaPlugin

expipe.ensure_testing()


@click.group()
@click.pass_context
def cli(ctx):
    pass


OpenEphysPlugin().attach_to_cli(cli)
OptoPlugin().attach_to_cli(cli)
CinplaPlugin().attach_to_cli(cli)


def run_command(command_list, inp=None):
    runner = CliRunner()
    result = runner.invoke(cli, command_list, input=inp)
    if result.exit_code != 0:
        print(result.output)
        raise result.exception


def test_openephys_opto():#module_teardown_setup_project_setup):
    currdir = op.abspath(op.dirname(__file__))
    openephys_path = op.join(currdir, 'test_data', 'openephys',
                             'test-rat_2017-06-21_12-33-43_01')
    action_id = 'test-rat-210617-01'
    data_path = op.join(expipe.settings['data_path'],
                        pytest.USER_PAR.project_id,
                        action_id)
    if op.exists(data_path):
        import shutil
        shutil.rmtree(data_path)
    run_command(['register-openephys', openephys_path, '--no-move'], inp='y')
    run_command(['register-opto', action_id,
                 '--brain-area', 'MECL',
                 '--tag', 'opto-train',
                 '--message', 'opto message'])
    run_command(['process-openephys', action_id])
    run_command(['analyse', action_id, '-a', 'all'])
