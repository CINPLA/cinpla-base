import pytest
import expipe
import subprocess
import click
from click.testing import CliRunner
import quantities as pq

expipe.ensure_testing()


@click.group()
@click.pass_context
def cli(ctx):
    pass


from expipe_plugin_cinpla.main import CinplaPlugin
CinplaPlugin().attach_to_cli(cli)


def run_command(command_list, inp=None):
    runner = CliRunner()
    result = runner.invoke(cli, command_list, input=inp)
    if result.exit_code != 0:
        print(result.output)
        raise result.exception


def test_annotate(setup_project_action):
    project, action = setup_project_action
    runner = CliRunner()
    result = runner.invoke(cli, ['annotate', pytest.ACTION_ID,
                                 '--tag', pytest.project.config.get('possible_tags') or [][0],
                                 '-t', pytest.project.config.get('possible_tags') or [][1],
                                 '--message', 'first message',
                                 '-m', 'second message'])
    if result.exit_code != 0:
        raise result.exception
    assert all(tag in [pytest.project.config.get('possible_tags') or [][0], pytest.project.config.get('possible_tags') or [][1]]
              for tag in action.tags)
    assert action.messages.messages[0]['message'] == 'first message'
    assert action.messages.messages[1]['message'] == 'second message'
    assert action.messages.messages[0]['user'] == pytest.USER_PAR.user_name

    result = runner.invoke(cli, ['annotate', pytest.ACTION_ID,
                                 '--user', 'test_user',
                                 '-m', 'third message'])
    if result.exit_code != 0:
        raise result.exception
    print(action.messages.messages)
    assert action.messages.messages[2]['message'] == 'third message'
    assert action.messages.messages[2]['user'] == 'test_user'


def test_reg_rat_init_depth_adjustment(teardown_setup_project):
    project, _ = teardown_setup_project
    # make surgery action
    run_command(['register-surgery', pytest.RAT_ID,
                 '--weight', '500',
                 '--birthday', '21.05.2017',
                 '--procedure', 'implantation',
                 '-d', '21.01.2017T14:40',
                 '-a', 'mecl', 1.9,
                 '-a', 'mecr', 1.8])

    # init
    run_command(['adjust', pytest.RAT_ID,
                 '-a', 'mecl', 50,
                 '-a', 'mecr', 50,
                 '-d', 'now',
                 '--init'], inp='y')

    # adjust more
    run_command(['adjust', pytest.RAT_ID,
                 '-a', 'mecl', 50,
                 '-a', 'mecr', 50,
                 '-d', 'now'], inp='y')

    action = project.require_action(pytest.RAT_ID + '-adjustment')
    ad_dict = action.modules.contents
    assert ad_dict['000_adjustment']['depth']['mecl'] == 1.95 * pq.mm
    assert ad_dict['000_adjustment']['depth']['mecr'] == 1.85 * pq.mm
    assert ad_dict['001_adjustment']['depth']['mecl'] == 2 * pq.mm
    assert ad_dict['001_adjustment']['depth']['mecr'] == 1.9 * pq.mm
