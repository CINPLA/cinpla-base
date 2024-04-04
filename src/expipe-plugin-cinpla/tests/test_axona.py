import pytest
import expipe
import subprocess
import click
from click.testing import CliRunner
import quantities as pq
import os.path as op
from expipe_plugin_cinpla.axona import AxonaPlugin
from expipe_plugin_cinpla.main import CinplaPlugin

expipe.ensure_testing()


@click.group()
@click.pass_context
def cli(ctx):
    pass

AxonaPlugin().attach_to_cli(cli)
CinplaPlugin().attach_to_cli(cli)


def run_command(command_list, inp=None):
    result = CliRunner().invoke(cli, command_list, input=inp)
    if result.exit_code != 0:
        print(result.output)
        raise result.exception
    return result


def test_axona(module_teardown_setup_project_setup):
    project = module_teardown_setup_project_setup
    #
    action_id = pytest.RAT_ID + '-311013-03'
    data_path = op.join(expipe.settings['data_path'],
                        pytest.USER_PAR.project_id,
                        action_id)
    if op.exists(data_path):
        import shutil
        shutil.rmtree(data_path)
    currdir = op.abspath(op.dirname(__file__))
    axona_filename = op.join(currdir, 'test_data', 'axona', 'DVH_2013103103.set')
    res = run_command(['register-axona', axona_filename,
                         '--subject-id', pytest.RAT_ID,
                         '-m', 'register-axona message',
                         '-t', pytest.project.config.get('possible_tags') or [][0]], inp='y')

    run_command(['spikesort', action_id])
    run_command(['register-units', action_id,
                '-m', 'register-units message',
                '-t', pytest.project.config.get('possible_tags') or [][0],
                '-t', pytest.project.config.get('possible_tags') or [][1]])
