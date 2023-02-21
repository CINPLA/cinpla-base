from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts import intan
from .utils import SelectDirectoryButton, MultiInput, SearchSelectMultiple, SelectFileButton, \
    required_values_filled, none_if_empty, split_tags, SearchSelect, ParameterSelectList
import ast


def register_intan_view(project):
    intan_path = SelectFileButton(description='*Select Intan rhs or rhd path', initialdir=str(project._backend.path))
    user = ipywidgets.Text(placeholder='*User', value=project.config.get('username'))
    session = ipywidgets.Text(placeholder='Session')
    location = ipywidgets.Text(placeholder='*Location', value=project.config.get('location'))
    action_id = ipywidgets.Text(placeholder='Action id')
    entity_id = ipywidgets.Text(placeholder='Entity id')
    message = ipywidgets.Text(placeholder='Message')
    tag = ipywidgets.Text(placeholder='Tags (; to separate)')
    templates = SearchSelectMultiple(project.templates, description='Templates')
    depth = MultiInput(['Key', 'Probe', 'Depth', 'Unit'], 'Add depth')
    register_depth = ipywidgets.Checkbox(description='Register depth', value=False)
    register_depth_from_adjustment = ipywidgets.Checkbox(
        description='Find adjustments', value=True)

    overwrite = ipywidgets.Checkbox(description='Overwrite', value=False)
    delete_raw_data = ipywidgets.Checkbox(
        description='Delete raw data', value=False)
    register = ipywidgets.Button(description='Register')

    fields = ipywidgets.VBox([
        user,
        location,
        session,
        action_id,
        entity_id,
        message,
        tag,
        register
    ])
    checks = ipywidgets.HBox([intan_path, register_depth, overwrite, delete_raw_data])
    main_box = ipywidgets.VBox([
            checks,
            ipywidgets.HBox([fields, templates])
        ])

    def on_register_depth(change):
        if change['name'] == 'value':
            if change['owner'].value:
                children = list(checks.children)
                children = children[:2] + [register_depth_from_adjustment] + children[2:]
                checks.children = children
            else:
                children = list(checks.children)
                del(children[2])
                checks.children = children

    def on_register_depth_from_adjustment(change):
        if change['name'] == 'value':
            if not change['owner'].value:
                children = list(fields.children)
                children = children[:5] + [depth] + children[5:]
                fields.children = children
            else:
                children = list(fields.children)
                del(children[5])
                fields.children = children

    register_depth.observe(on_register_depth)
    register_depth_from_adjustment.observe(on_register_depth_from_adjustment)

    def on_register(change):
        if not required_values_filled(user, location, intan_path):
            return
        tags = split_tags(tag)
        intan.register_intan_recording(
            templates=templates.value,
            project=project,
            action_id=none_if_empty(action_id.value),
            intan_path=intan_path.file,
            depth=depth.value,
            overwrite=overwrite.value,
            register_depth=register_depth.value,
            entity_id=none_if_empty(entity_id.value),
            user=user.value,
            session=session.value,
            location=location.value,
            message=none_if_empty(message.value),
            tag=tags,
            delete_raw_data=delete_raw_data.value,
            correct_depth_answer=True)

    register.on_click(on_register)
    return main_box


def process_intan_view(project):
    import spikesorters as ss

    probe_path = SelectFileButton('.prb', description='*Select probe file', style={'description_width': 'initial'},
                                  layout={'width': 'initial'}, initialdir=str(project._backend.path))
    action_id = SearchSelectMultiple(
        project.actions, description='*Actions', layout={'width': 'initial'})

    sorter = ipywidgets.Dropdown(
        description='Sorter', options=[s.sorter_name for s in ss.sorter_full_list],
        style={'description_width': 'initial'}, layout={'width': 'initial'}
    )

    sorter_param = ParameterSelectList(description='Spike sorting options', param_dict={},
                                       layout={'width': 'initial'})
    sorter_param.layout.visibility = 'hidden'
    parallel_box = ipywidgets.Checkbox(description='Parallel', layout={'width': 'initial'})
    parallel_box.layout.visibility = 'hidden'
    sort_by = ipywidgets.Text(description='sort_by', value='group', placeholder='group', layout={'width': 'initial'})
    sort_by.layout.visibility = 'hidden'

    config = expipe.config._load_config_by_name(None)
    current_servers = config.get('servers') or []
    server_list = ['local'] + [s['host'] for s in current_servers]
    servers = ipywidgets.Dropdown(
        description='Server', options=server_list, style={'description_width': 'initial'}, layout={'width': 'initial'}
    )

    compute_lfp = ipywidgets.ToggleButton(
        value=True,
        description='Compute LFP',
        disabled=False,
        button_style='',  # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Compute LFP',
        icon='check',
        layout={'width': 'initial'}
    )
    compute_mua = ipywidgets.ToggleButton(
        value=False,
        description='Compute MUA',
        disabled=False,
        button_style='',  # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Compute MUA',
        icon='check',
        layout={'width': 'initial'}
    )
    spikesort = ipywidgets.ToggleButton(
        value=True,
        description='Spikesort',
        disabled=False,
        button_style='',  # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Spike sort data',
        icon='check',
        layout={'width': 'initial'}
    )

    show_params = ipywidgets.ToggleButton(
        value=False,
        description='Params',
        disabled=False,
        button_style='',  # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Show spike sorting specific params',
        icon='edit',
        layout={'width': 'initial'}
    )

    other_settings = ipywidgets.ToggleButton(
        value=False,
        description='Other setting',
        disabled=False,
        button_style='',  # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Modify other processing settings',
        icon='edit',
        layout={'width': 'initial'}
    )

    reference = ipywidgets.RadioButtons(
        options=['cmr', 'car', 'none'],
        description='Reference:',
        disabled=False,
        tooltips=['Common Median Reference', 'Common Average Reference', 'No re-referencing'],
        orientation='vertical',
        layout={'width': 'initial'}
        #     icons=['check'] * 3
    )
    reference.layout.visibility = 'hidden'

    split_group = ipywidgets.RadioButtons(
        options=['all', 'half', 'custom'],
        description='Ref channels:',
        disabled=False,
        tooltips=['all channels are used to re-reference', 'channels are split in half and re-referenced separately',
                  'custom decided split'],
        orientation='vertical',
        layout={'width': 'initial'}
    )
    split_group.layout.visibility = 'hidden'

    custom_split = ipywidgets.Text(description='Split', value='', placeholder='(e.g. [[1,2,3,...], [4,5,6,...]])',
                                   style={'description_width': 'initial'})
    custom_split.layout.visibility = 'hidden'

    remove_artifacts = ipywidgets.IntText(description='Remove art. ch. (1-based)', value=None, placeholder='None',
                                          style={'description_width': 'initial'})
    remove_artifacts.layout.visibility = 'hidden'

    bad_channels = ipywidgets.Text(description='Bad channels', value='', placeholder='(e.g. 5, 8, 12)',
                                   style={'description_width': 'initial'})
    bad_channels.layout.visibility = 'hidden'

    bad_threshold = ipywidgets.FloatText(
        description='Auto threshold', value=2, placeholder='(e.g 2, default = 2 * std)',
        style={'description_width': 'initial'})
    bad_threshold.layout.visibility = 'hidden'

    min_fr = ipywidgets.FloatText(
        description='Minumum FR threshold', value=0.1, placeholder='(e.g 0.1, default = 0.1)',
        style={'description_width': 'initial'})
    min_fr.layout.visibility = 'hidden'

    min_isi = ipywidgets.FloatText(
        description='ISI violation threshold', value=0, placeholder='(e.g 0.5, default = 0)',
        style={'description_width': 'initial'})
    min_isi.layout.visibility = 'hidden'

    rightbox = ipywidgets.VBox([ipywidgets.Label('Processing options', style={'description_width': 'initial'},
                                                 layout={'width': 'initial'}),
                                spikesort, compute_lfp, compute_mua, servers, other_settings,
                                bad_channels, bad_threshold, min_fr, min_isi, remove_artifacts, reference,
                                split_group, custom_split],
                               layout={'width': 'initial'})

    run = ipywidgets.Button(description='Process', layout={'width': '100%', 'height': '100px'})
    run.style.button_color = 'pink'

    fields = ipywidgets.VBox([
        probe_path,
        sorter,
        show_params,
        sorter_param,
        parallel_box,
        sort_by
    ])

    main_box = ipywidgets.VBox([
            ipywidgets.HBox([fields, action_id, rightbox]), run
        ], layout={'width': '100%'})
    main_box.layout.display = 'flex'

    def on_change(change):
        if change['type'] == 'change' and change['name'] == 'value':
            for s in ss.sorter_full_list:
                if s.sorter_name == sorter.value:
                    params = s.default_params()
            sorter_param.update_params(params)

    def on_run(change):
        if not required_values_filled(probe_path, action_id):
            return

        spikesorter_params = sorter_param.value
        for (k, v) in spikesorter_params.items():
            if v == 'None':
                spikesorter_params[k] = None

        if bad_channels.value is not '':
            bad_chans = [int(b) for b in bad_channels.value.split(',')]
        else:
            bad_chans = []
        if reference.value is not 'none':
            ref = reference.value
        else:
            ref = None
        if split_group is not 'custom':
            split = split_group.value
        elif split_group == 'custom':
            split = ast.literal_eval(split_group.value)
        else:
            split = 'all'
        if sort_by.value == '' or sort_by.value.lower() == 'none':
            sort_by_val = None
        else:
            sort_by_val = sort_by.value
        for a in action_id.value:
            try:
                intan.process_intan(
                    project=project,
                    action_id=a,
                    probe_path=probe_path.file,
                    sorter=sorter.value,
                    spikesort=spikesort.value,
                    compute_lfp=compute_lfp.value,
                    compute_mua=compute_mua.value,
                    spikesorter_params=spikesorter_params,
                    parallel=parallel_box.value,
                    server=servers.value,
                    bad_channels=bad_chans,
                    ref=ref,
                    split=split,
                    remove_artifact_channel=remove_artifacts.value - 1,
                    sort_by=sort_by_val,
                    bad_threshold=bad_threshold.value,
                    firing_rate_threshold=min_fr.value,
                    isi_viol_threshold=min_isi.value)
            except Exception as e:
                print('ERROR: unable to process', a)
                print(str(e))
                pass

    def on_show(change):
        if change['type'] == 'change' and change['name'] == 'value':
            for s in ss.sorter_full_list:
                if s.sorter_name == sorter.value:
                    params = s.default_params()
            sorter_param.update_params(params)
            if show_params.value:
                sorter_param.layout.visibility = 'visible'
                parallel_box.layout.visibility = 'visible'
                sort_by.layout.visibility = 'visible'
            else:
                sorter_param.layout.visibility = 'hidden'
                parallel_box.layout.visibility = 'hidden'
                sort_by.layout.visibility = 'hidden'

    def on_other(change):
        if change['type'] == 'change' and change['name'] == 'value':
            if other_settings.value:
                bad_channels.layout.visibility = 'visible'
                bad_threshold.layout.visibility = 'visible'
                reference.layout.visibility = 'visible'
                remove_artifacts.layout.visibility = 'visible'
                if reference.value != 'none':
                    split_group.layout.visibility = 'visible'
                min_fr.layout.visibility = 'visible'
                min_isi.layout.visibility = 'visible'
            else:
                bad_channels.layout.visibility = 'hidden'
                bad_threshold.layout.visibility = 'hidden'
                reference.layout.visibility = 'hidden'
                split_group.layout.visibility = 'hidden'
                remove_artifacts.layout.visibility = 'hidden'
                min_fr.layout.visibility = 'hidden'
                min_isi.layout.visibility = 'hidden'

    def on_split(change):
        if change['type'] == 'change' and change['name'] == 'value':
            if reference.value is not 'none':
                if split_group.value == 'custom':
                    custom_split.layout.visibility = 'visible'
                else:
                    custom_split.layout.visibility = 'hidden'

    sorter.observe(on_change)
    run.on_click(on_run)
    show_params.observe(on_show)
    other_settings.observe(on_other)
    split_group.observe(on_split)
    return main_box
