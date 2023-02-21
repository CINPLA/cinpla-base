from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts.utils import register_templates, query_yes_no
from expipe_plugin_cinpla.scripts import entity
from . import utils


def attach_to_cli(cli):
    @cli.command('entity',
                 short_help=('Register a entity.'))
    @click.argument('entity-id')
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the registration.',
                  )
    @click.option('--location',
                  required=True,
                  type=click.STRING,
                  help='The location of the animal.',
                  )
    @click.option('--birthday',
                  required=True,
                  type=click.STRING,
                  help='The birthday of the entity, format: "dd.mm.yyyy".',
                  )
    @click.option('--cell_line',
                  type=click.STRING,
                  callback=utils.optional_choice,
                  envvar=project.config.get('possible_cell_lines') or [],
                  help='Add cell line to entity.',
                  )
    @click.option('--developmental-stage',
                  type=click.STRING,
                  help="The developemtal stage of the entity. E.g. 'embroyonal', 'adult', 'larval' etc.",
                  )
    @click.option('--gender',
                  type=click.STRING,
                  help='Male or female?',
                  )
    @click.option('--genus',
                  type=click.STRING,
                  help='The Genus of the studied entity. E.g "rattus"',
                  )
    @click.option('--health_status',
                  type=click.STRING,
                  help='Information about the health status of this entity.',
                  )
    @click.option('--label',
                  type=click.STRING,
                  help='If the entity has been labled in a specific way. The lable can be described here.',
                  )
    @click.option('--population',
                  type=click.STRING,
                  help='The population this entity is offspring of. This may be the bee hive, the ant colony, etc.',
                  )
    @click.option('--species',
                  type=click.STRING,
                  help='The scientific name of the species e.g. Apis mellifera, Homo sapiens.',
                  )
    @click.option('--strain',
                  type=click.STRING,
                  help='The strain the entity was taken from. E.g. a specific genetic variation etc.',
                  )
    @click.option('--trivial_name',
                  type=click.STRING,
                  help='The trivial name of the species like Honeybee, Human.',
                  )
    @click.option('--weight',
                  nargs=2,
                  type=(click.FLOAT, click.STRING),
                  default=(None, None),
                  help='The weight of the animal.',
                  )
    @click.option('--message', '-m',
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    @click.option('-t', '--tag',
                  multiple=True,
                  type=click.STRING,
                  callback=utils.optional_choice,
                  envvar=project.config.get('possible_tags') or [],
                  help='Add tags to entity.',
                  )
    @click.option('--overwrite',
                  is_flag=True,
                  help='Overwrite existing module',
                  )
    @click.option('--templates',
                  multiple=True,
                  type=click.STRING,
                  help='Which templates to add',
                  )
    def _register_entity(entity_id, user, message, location, tag, overwrite,
                         templates, **kwargs):
        entity.register_entity(project, entity_id, user, message, location, tag, overwrite,
                             templates, **kwargs)
