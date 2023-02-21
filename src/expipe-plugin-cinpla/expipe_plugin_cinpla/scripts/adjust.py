from expipe_plugin_cinpla.imports import *
from . import utils
from datetime import datetime as dt


adjustment_template = {
    "adjustment": {
        "unit": "um",
        "value": ""
    },
    "date": "dd.mm.yyyy:HH:MM",
    "definition": "Adjustment length of drive",
    "depth": {
        "unit": "mm",
        "value": ""
    },
    "experimenter": "",
    "identifier": "drive_depth_adjustment",
    "location": "Left, Right",
    "name": "drive_depth_adjustment",
    "notes": {
        "value": ""
    }
}


def register_adjustment(project, entity_id, date, adjustment, user,
                        depth, yes):
    user = user or project.config.get('username')
    if user is None:
        print('Missing option "user".')
        return
    if len(adjustment) == 0:
        print('Missing option "adjustment".')
        return
    if date is None:
        print('Missing option "date".')
        return
    DTIME_FORMAT = expipe.core.datetime_format
    if date == 'now':
        date = dt.now()
    if isinstance(date, str):
        date = dt.strptime(date, DTIME_FORMAT)
    datestring = date.strftime(DTIME_FORMAT)
    action_id = entity_id + '-adjustment'
    try:
        action = project.actions[action_id]
        init = False
    except KeyError as e:
        action = project.create_action(action_id)
        init = True

    if not init:
        deltas = []
        for name in action.modules.keys():
            if name.endswith('adjustment'):
                deltas.append(int(name.split('_')[0]))
        index = max(deltas) + 1
        prev_depth = action.modules[
            '{:03d}_adjustment'.format(max(deltas))].contents['depth']
    if init:
        if len(depth) > 0:
            prev_depth = utils.position_to_dict(depth)
        else:
            prev_depth = utils.get_depth_from_surgery(
                project=project, entity_id=entity_id)
        index = 0

    name = '{:03d}_adjustment'.format(index)
    if not isinstance(prev_depth, dict):
        print('Unable to retrieve previous depth.')
        return
    adjustment_dict = {key: dict() for key in prev_depth}
    current = {key: dict() for key in prev_depth}
    for key, probe, val, unit in adjustment:
        pos_key = 'probe_{}'.format(probe)
        adjustment_dict[key][pos_key] = pq.Quantity(val, unit)
    for key, val in prev_depth.items():
        for pos_key in prev_depth[key]:
            adjust_value = adjustment_dict[key].get(pos_key) or 0 * pq.mm
            adjust_value = adjust_value.rescale('mm').astype(float)
            prev_value = prev_depth[key][pos_key].rescale('mm')
            print(adjust_value, prev_value)
            current[key][pos_key] = round(prev_value + adjust_value, 3) # round to um

    def last_probe(x):
        return '{:03d}'.format(int(x.split('_')[-1]))
    correct = utils.query_yes_no(
        'Correct adjustment?: \n' +
        ' '.join('{} {} = {}\n'.format(key, pos_key, val[pos_key])
                 for key, val in adjustment_dict.items()
                 for pos_key in sorted(val, key=lambda x: last_probe(x))) +
        'New depth: \n' +
        ' '.join('{} {} = {}\n'.format(key, pos_key, val[pos_key])
                 for key, val in current.items()
                 for pos_key in sorted(val, key=lambda x: last_probe(x))),
        answer=yes
    )
    if not correct:
        print('Aborting adjustment.')
        return
    print(
        'Registering adjustment: \n' +
        ' '.join('{} {} = {}\n'.format(key, pos_key, val[pos_key])
                 for key, val in adjustment_dict.items()
                 for pos_key in sorted(val, key=lambda x: last_probe(x))) +
        ' New depth: \n' +
        ' '.join('{} {} = {}\n'.format(key, pos_key, val[pos_key])
                 for key, val in current.items()
                 for pos_key in sorted(val, key=lambda x: last_probe(x)))
    )

    adjustment_template['depth'] = current
    adjustment_template['adjustment'] = adjustment_dict
    adjustment_template['experimenter'] = user
    adjustment_template['date'] = datestring
    action.create_module(name=name, contents=adjustment_template)

    action.type = 'Adjustment'
    action.entities = [entity_id]
    action.users.append(user)


def register_annotation(
    project, action_id, entity_id, action_type, date, user, location,
    depth, message, tag, templates, correct_depth_answer):
    user = user or project.config.get('username')
    action = project.actions[action_id]
    print('Action ', action_id)
    if user is None:
        print('Missing option "user".')
        return
    print('Registering user', user)
    action.users = [user]
    if date:
        print('Registering date ', date)
        action.datetime = date
    if action_type:
        print('Registering type', action_type)
        action.type = action_type
    utils.register_templates(action, templates, overwrite=True)
    if tag:
        print('Registering tags', tag)
        action.tags.extend(list(tag))
    if entity_id:
        print('Registering entity id', entity_id)
        action.entities = [entity_id]
    if location:
        print('Registering location', location)
        action.location = location
    if message:
        print('Registering message', message)
        action.create_message(text=message, user=user, datetime=datetime.datetime.now())
    if depth:
        correct_depth = utils.register_depth(
            project=project, action=action, depth=depth,
            answer=correct_depth_answer, overwrite=True)
