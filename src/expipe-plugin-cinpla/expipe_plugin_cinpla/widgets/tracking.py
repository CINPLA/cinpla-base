from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts import tracking
from .utils import SelectDirectoryButton, MultiInput, SearchSelectMultiple, SelectFileButton, \
    required_values_filled, none_if_empty, split_tags, SearchSelect, ParameterSelectList
import ast


def process_tracking_view(project):
    openephys_path = SelectDirectoryButton(description='*Select OpenEphys path')
    action_id = SearchSelect(project.actions, description='*Actions', layout={'width': 'initial'})
    run = ipywidgets.Button(description='Process', layout={'width': '100%', 'height': '100px'})
    run.style.button_color = 'pink'

    main_box = ipywidgets.VBox([
            ipywidgets.HBox([openephys_path, action_id]), run
        ], layout={'width': '100%'})
    main_box.layout.display = 'flex'

    def on_run(change):
        if not required_values_filled(openephys_path, action_id):
            return

        if len(openephys_path.directories) > 1:
            print('Select a single folder')
        else:
            tracking.process_tracking(
                project=project,
                action_id=action_id.value,
                openephys_path=openephys_path.directories[0])

    run.on_click(on_run)
    return main_box
