from expipe_plugin_cinpla.imports import *
from . import utils


def register_axona_recording(
    project, action_id, axona_filename, depth, user, overwrite, templates,
    entity_id, location, message, tag, get_inp, no_cut, cluster_group,
    set_zero_cluster_to_noise, register_depth, correct_depth_answer=None):
    user = user or project.config.get('username')
    if user is None:
        print('Missing option "user".')
        return
    location = location or project.config.get('location')
    if location is None:
        print('Missing option "location".')
        return
    axona_filename = pathlib.Path(axona_filename)
    if not axona_filename.suffix == '.set':
        print("Sorry, we need an Axona .set file not " +
              "'{}'.".format(axona_filename))
        print('Aborting registration!')
        return
    if len(cluster_group) == 0:
        cluster_group = None # TODO set proper default via callback
    entity_id = entity_id or axona_filename.parent.stem
    axona_file = pyxona.File(str(axona_filename))
    if action_id is None:
        session_dtime = datetime.datetime.strftime(axona_file._start_datetime,
                                          '%d%m%y')
        basename = str(axona_filename.stem)
        session = basename[-2:]
        action_id = entity_id + '-' + session_dtime + '-' + session
    try:
        action = project.create_action(action_id)
    except KeyError as e:
        if overwrite:
            project.delete_action(action_id)
            action = project.create_action(action_id)
        else:
            print(str(e) + '. Use "overwrite"')
            return
    utils.register_templates(action, templates)
    action.datetime = axona_file._start_datetime
    action.tags = list(tag) + ['axona']
    print('Registering action id ' + action_id)
    print('Registering entity id ' + entity_id)
    action.entities = [entity_id]
    print('Registering user ' + user)
    action.users = [user]
    print('Registering location ' + location)
    action.location = location
    action.type = 'Recording'
    if message:
        action.create_message(text=message, user=user, datetime=datetime.datetime.now())
    if register_depth:
        correct_depth = utils.register_depth(
            project=project, action=action, depth=depth,
            answer=correct_depth_answer)
        if not correct_depth:
            print('Aborting registration!')
            project.delete_action(action_id)
            return
    exdir_path = utils._make_data_path(action, overwrite)
    axona.convert(axona_file, exdir_path)
    axona.generate_tracking(exdir_path, axona_file)
    axona.generate_analog_signals(exdir_path, axona_file)
    axona.generate_spike_trains(exdir_path, axona_file)
    if not no_cut:
        axona.generate_units(exdir_path, axona_file,
                             cluster_group=cluster_group,
                             set_noise=set_zero_cluster_to_noise)
        axona.generate_clusters(exdir_path, axona_file)
    if get_inp:
        axona.generate_inp(exdir_path, axona_file)
    else:
        print('WARNING: Not registering Axona ".inp".')
    time_string = exdir.File(exdir_path).attrs['session_start_time']
    dtime = datetime.datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S')
    action.datetime = dtime
