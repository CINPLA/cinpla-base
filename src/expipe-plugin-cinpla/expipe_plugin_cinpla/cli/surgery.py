from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts.utils import register_templates, query_yes_no
from expipe_plugin_cinpla.scripts import surgery
from . import utils


def attach_to_cli(cli):
    @cli.command('surgery', short_help='Register a surgery action.')
    @click.argument('entity-id')
    @click.option('--date', '-d',
                  required=True,
                  type=click.STRING,
                  help='The date of the surgery format: "dd.mm.yyyyTHH:MM".',
                  )
    @click.option('-t', '--tag',
                  multiple=True,
                  type=click.STRING,
                  callback=utils.optional_choice,
                  envvar=project.config.get('possible_tags') or [],
                  help='Add tags to action.',
                  )
    @click.option('--procedure',
                  required=True,
                  type=click.Choice(['implantation', 'injection']),
                  help='The type of surgery "implantation" or "injection".',
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite modules or not.',
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the surgery.',
                  )
    @click.option('-w', '--weight',
                  nargs=2,
                  type=(click.FLOAT, click.STRING),
                  default=(None, None),
                  help='The weight of the entity with unit i.e. <200 g> (ommit <>).',
                  )
    @click.option('-p', '--position',
                  required=True,
                  multiple=True,
                  callback=utils.validate_position,
                  help='The position e.g. <"mecl 0 x y z mm"> (ommit <>).',
                  )
    @click.option('-a', '--angle',
                  required=True,
                  multiple=True,
                  callback=utils.validate_angle,
                  help='The angle of implantation/injection.',
                  )
    @click.option('--message', '-m',
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    @click.option('-l', '--location',
                  type=click.STRING,
                  callback=utils.optional_choice,
                  envvar=project.config.get('possible_locations') or [],
                  help='The location of the recording, i.e. "room-1-ibv".'
                  )
    @click.option('--templates',
                  multiple=True,
                  type=click.STRING,
                  help='Which templates to add',
                  )
    def _register_surgery(
        project, entity_id, procedure, date, user, weight, location,
        overwrite, position, angle, message, tag, templates):
        surgery.register_surgery(
            project, entity_id, procedure, date, user, weight, location,
            overwrite, position, angle, message, tag, templates)


    @cli.command('perfusion',
                 short_help=('Register a perfusion action. ' +
                             'Also tags the entity as perfused and euthanised.'))
    @click.argument('entity-id')
    @click.option('--date', '-d',
                  required=True,
                  type=click.STRING,
                  help='The date of the surgery format: "dd.mm.yyyyTHH:MM".',
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the surgery.',
                  )
    @click.option('--weight',
                  nargs=2,
                  type=(click.FLOAT, click.STRING),
                  default=(None, None),
                  help='The weight of the animal.',
                  )
    @click.option('-l', '--location',
                  type=click.STRING,
                  callback=utils.optional_choice,
                  envvar=project.config.get('possible_locations') or [],
                  help='The location of the recording, i.e. "room-1-ibv".'
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite files and expipe action.',
                  )
    @click.option('--message', '-m',
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    @click.option('--templates',
                  multiple=True,
                  type=click.STRING,
                  help='Which templates to add',
                  )
    def _register_perfusion(entity_id, date, user, weight, overwrite, message, templates, location):
        surgery.register_perfusion(
            project, entity_id, date, user, weight, overwrite, message,
            templates, location)
