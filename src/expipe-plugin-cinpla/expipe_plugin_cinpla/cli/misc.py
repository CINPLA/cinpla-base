from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts.utils import (
    register_templates, query_yes_no)
from . import utils

def attach_to_cli(cli):
    @cli.command('annotate', short_help='Parse info about recorded units')
    @click.argument('action-id', type=click.STRING)
    @click.option('-t', '--tag',
                    multiple=True,
                    type=click.STRING,
                    callback=utils.optional_choice,
                    envvar=project.config.get('possible_tags') or [],
                    help='Add tags to action.',
                    )
    @click.option('--message', '-m',
                  type=click.STRING,
                  help='Add message, use "text here" for sentences.',
                  )
    @click.option('-u', '--user',
                  type=click.STRING,
                  help='The experimenter performing the annotation.',
                  )
    def annotate(action_id, tag, message, user):

        action = project.actions[action_id]
        user = user or project.config.get('username')
        if user is None:
            raise ValueError('Please add user name')
        users = list(set(action.users))
        if user not in users:
            users.append(user)
        action.users = users
        if message:
            action.create_message(text=m, user=user, datetime=datetime.now())
        action.tags.extend(tag)

    @cli.command('add-server')
    @click.option(
        '--name', '-n', type=click.STRING, help='The name of the server'
    )
    @click.option(
        '--domain', '-d', type=click.STRING, help='The server domain (or IP address)'
    )
    @click.option(
        '--username', '-un', type=click.STRING, help='The username to access the server.'
    )
    @click.option(
        '--password', '-pw', type=click.STRING, prompt=True, hide_input=True, help='The server password (will be prompted)'
    )
    def add_server(name, domain, username, password):
        """Add server info."""
        cwd = pathlib.Path.cwd()
        local_root, _ = expipe.config._load_local_config(cwd)
        path = None
        config = expipe.config._load_config_by_name(path)
        current_servers = config.get('servers') or []
        if name is not None and domain is not None and username is not None and password is not None:
            pass
        else:
            raise Exception("Provide server name, domain, and username. Password is prompted.")
        new_server = {'host': name, 'domain': domain, 'user': username, 'password': password}
        current_servers.append(new_server)
        config['servers'] = current_servers
        expipe.config._dump_config_by_name(path, config)
