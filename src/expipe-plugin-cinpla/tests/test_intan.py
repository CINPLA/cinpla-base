import pytest
import expipe
import subprocess
import click
from click.testing import CliRunner
import quantities as pq
import os.path as op
from expipe_plugin_cinpla.intan import IntanPlugin
from expipe_plugin_cinpla.electrical_stimulation import ElectricalStimulationPlugin
from expipe_plugin_cinpla.main import CinplaPlugin

expipe.ensure_testing()


@click.group()
@click.pass_context
def cli(ctx):
    pass


IntanPlugin().attach_to_cli(cli)
ElectricalStimulationPlugin().attach_to_cli(cli)
CinplaPlugin().attach_to_cli(cli)


def run_command(command_list, inp=None):
    runner = CliRunner()
    result = runner.invoke(cli, command_list, input=inp)
    if result.exit_code != 0:
        print(result.output)
        raise result.exception


def test_intan():#module_teardown_setup_project_setup):
    currdir = op.abspath(op.dirname(__file__))
    intan_path = op.join(currdir, 'test_data', 'intan',
                             'test-rat_2017-06-23_11-15-46_1',
                             'test_170623_111545_stim.rhs')
    action_id = 'test-rat-230617-01'
    data_path = op.join(expipe.settings['data_path'],
                        pytest.USER_PAR.project_id,
                        action_id)
    if op.exists(data_path):
        import shutil
        shutil.rmtree(data_path)
    run_command(['register-intan', intan_path, '--no-move'], inp='y')
    run_command(['process-intan', action_id])
    run_command(['analyse', action_id, '--spike-stat', '--psd', '--tfr','--spike-stat'])

def test_intan_ephys():#module_teardown_setup_project_setup):
    currdir = op.abspath(op.dirname(__file__))
    intan_ephys_path = op.join(currdir, 'test_data', 'intan',
                             'test-rat_2017-06-23_11-15-46_1')
    action_id = 'test-rat-230617-01'
    data_path = op.join(expipe.settings['data_path'],
                        pytest.USER_PAR.project_id,
                        action_id)
    if op.exists(data_path):
        import shutil
        shutil.rmtree(data_path)
    run_command(['register-intan-ephys', intan_ephys_path, '--no-move'], inp='y')
    run_command(['process-intan-ephys', action_id])
    run_command(['analyse', action_id, '--all'])
