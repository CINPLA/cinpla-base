from expipe_plugin_cinpla.imports import *
from . import utils


def register_entity(project, entity_id, user, message, location, tag, overwrite,
                    birthday, templates, **kwargs):
    DTIME_FORMAT = expipe.core.datetime_format
    user = user or project.config.get('username')
    if user is None:
        print('Missing option "user".')
        return
    if birthday is None:
        print('Missing option "birthday".')
        return
    try:
        entity = project.create_entity(entity_id)
    except KeyError as e:
        if overwrite:
            project.delete_entity(entity_id)
            entity = project.create_entity(entity_id)
        else:
            print(str(e) + '. Use "overwrite"')
            return
    if isinstance(birthday, str):
        birthday = datetime.datetime.strftime(
            datetime.datetime.strptime(birthday, '%d.%m.%Y'), DTIME_FORMAT)
    utils.register_templates(entity, templates)
    entity.datetime = datetime.datetime.now()
    entity.type = 'Subject'
    entity.tags.extend(list(tag))
    entity.location = location
    print('Registering user ' + user)
    entity.users = [user]
    if message:
        entity.create_message(text=message, user=user, datetime=datetime.datetime.now())
    for key, val in kwargs.items():
        if 'register' not in entity.modules:
            entity.modules['register'] = {}
        if isinstance(val, (str, float, int)):
            entity.modules['register'][key]['value'] = val
        elif isinstance(val, tuple):
            if not None in val:
                entity.modules['register'][key] = pq.Quantity(val[0], val[1])
        elif isinstance(val, type(None)):
            pass
        else:
            print('Not recognized type ' + str(type(val)))
