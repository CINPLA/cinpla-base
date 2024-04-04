from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts import psychopy
from . import utils


def attach_to_process(cli):
    @cli.command('psychopy',
                 short_help='Process open ephys recordings.')
    @click.argument('action-id', type=click.STRING)
    @click.option('-j', '--jsonpath',
                  type=click.STRING,
                  help='Psyschopy for visual analysis files are present.')
    def _process_psychopy(action_id, jsonpath):
        psychopy.process_psychopy(project=project, action_id=action_id, jsonpath=jsonpath)
