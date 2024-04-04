from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts import curation
from .utils import (
    SelectDirectoryButton, MultiInput, SearchSelectMultiple, SelectFileButton,
    required_values_filled, none_if_empty, split_tags, SearchSelect,
    ParameterSelectList)
from ..scripts.utils import _get_data_path


def process_curation_view(project):
    action_id = SearchSelectMultiple(
        project.actions, description='*Actions', layout={'width': 'initial'})

    sorter_label = ipywidgets.Label(value='Spike sorters')

    sorter_list = ipywidgets.SelectMultiple(
        description='',
        options=[],
        style={'description_width': 'initial'}, layout={'width': 'initial'}
    )

    run_phy = ipywidgets.Button(
        description='Run Phy', style={'description_width': 'initial'}, layout={'width': 'initial'})
    run_phy.style.button_color = 'pink'
    run_consensus = ipywidgets.Button(
        description='Run consensus-based', style={'description_width': 'initial'}, layout={'width': 'initial'})
    run_consensus.style.button_color = 'pink'
    run_save = ipywidgets.Button(
        description='Save to exdir', style={'description_width': 'initial'}, layout={'width': 'initial'})
    run_consensus.style.button_color = 'pink'

    get_sorters = ipywidgets.Button(
        description='Get sorters', style={'description_width': 'initial'}, layout={'width': 'initial'})
    get_sorters.style.button_color = 'gray'

    restore = ipywidgets.ToggleButton(
        value=False,
        description='Restore',
        disabled=False,
        button_style='',  # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Restore unsorted clusters',
        layout={'width': 'initial'}
    )

    min_agr = ipywidgets.IntText(
        description='Minumum agreement', value=2,
        tooltip='Minimum agreement for consensus-based',
        style={'description_width': 'initial'})

    buttons = ipywidgets.VBox([
        run_phy,
        run_consensus,
        run_save,
    ])

    sorting = ipywidgets.VBox([
        sorter_label,
        sorter_list,
        restore,
        min_agr,
    ])



    actions = ipywidgets.VBox([
        action_id,
        get_sorters,
    ])

    main_box = ipywidgets.HBox([buttons, actions, sorting], layout={'width': '100%'}) #, run ], layout={'width': '100%'})
    main_box.layout.display = 'flex'

    def on_action(change):
        if len(action_id.value) > 1:
            print("Select one action at a time")
        else:
            action = project.actions[action_id.value[0]]
            # if exdir_path is None:
            exdir_path = _get_data_path(action)
            exdir_file = exdir.File(exdir_path, plugins=exdir.plugins.quantities)
            if 'processing' in exdir_file.keys():
                spikesorting = exdir_file['processing']['electrophysiology']['spikesorting']
                sorting_groups = list(spikesorting.keys())
                sorter_list.options = sorting_groups
            else:
                sorter_list.options = []

    def on_run_phy(change):
        if not required_values_filled(sorter_list, action_id):
            return
        else:
            if len(action_id.value) > 1:
                print("Select one action at a time")
            elif len(sorter_list.value) > 1:
                print("Select one spike sorting output at a time")
            else:
                curation.process_phy(project, action_id.value[0], sorter_list.value[0], restore.value)

    def on_run_consensus(change):
        if not required_values_filled(sorter_list, action_id):
            return
        else:
            if len(action_id.value) > 1:
                print("Select one action at a time")
            elif len(sorter_list.value) == 1:
                print("Select more than one spike sorting output to get consensus-based output")
            else:
                curation.process_consensus(project, action_id.value[0], sorter_list.value, min_agr.value)

    def on_run_save(change):
        if not required_values_filled(sorter_list, action_id):
            return
        else:
            if len(action_id.value) > 1:
                print("Select one action at a time")
            elif len(sorter_list.value) > 1:
                print("Select one spike sorting output at a time")
            else:
                curation.process_save_phy(project, action_id.value[0], sorter_list.value[0])

    run_phy.on_click(on_run_phy)
    run_consensus.on_click(on_run_consensus)
    run_save.on_click(on_run_save)
    get_sorters.on_click(on_action)
    return main_box
