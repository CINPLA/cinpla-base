from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts import adjust
from . import utils
from datetime import datetime as dt


def attach_to_cli(cli):
    @cli.command('adjust',
                 short_help='Parse info about drive depth adjustment')
    @click.argument('entity-id',  type=click.STRING)
    @click.option('--date',
                  type=click.STRING,
                  help=('The date of the surgery format: "dd.mm.yyyyTHH:MM" ' +
                        'or "now".'),
                  )
    @click.option('-a', '--adjustment',
                  multiple=True,
                  callback=utils.validate_adjustment,
                  help=('The adjustment amount on given anatomical location ' +
                        'given as <key num value unit>'),
                  )
    @click.option('--index',
                  type=click.INT,
                  help=('Index for module name, this is found automatically ' +
                        'by default.'),
                  )
    @click.option('--init',
                  is_flag=True,
                  help='Initialize, retrieve depth from surgery.',
                  )
    @click.option('-d', '--depth',
                  multiple=True,
                  callback=utils.validate_depth,
                  help=('The depth given as <key num depth unit> e.g. ' +
                        '<mecl 0 10 um> (omit <>).'),
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the adjustment.',
                  )
    @click.option('-y', '--yes',
                  is_flag=True,
                  help='No query for correct adjustment.',
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite existing action',
                  )
    def _register_adjustment(entity_id, date, adjustment, user, index, init,
                             depth, yes, overwrite):
        adjust.register_adjustment(
            project, entity_id, date, adjustment, user, index, init,
            depth, yes, overwrite)
