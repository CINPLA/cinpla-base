from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts import curation
import spikesorters as ss
from . import utils


def attach_to_process(cli):
    @cli.command('phy2exdir',
                 short_help='Save curation output to exdir.')
    @click.argument('action-id', type=click.STRING)
    @click.option('--sorter',
                  default='kilosort2',
                  type=click.Choice([s.sorter_name for s in ss.sorter_full_list]),
                  help='Spike sorter software to be used.',
                  )
    @click.option('--check-exists',
                  is_flag=True,
                  help='Check if the exdir unit_ids are the same as in phy.',
                  )
    def _phy_to_exdir(action_id, sorter, check_exists):
        curation.process_save_phy(project, action_id, sorter, check_exists=check_exists)
