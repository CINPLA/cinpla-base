from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts import axona
from .utils import SelectFilesButton, MultiInput, SearchSelectMultiple, required_values_filled, none_if_empty, split_tags


def axona_view(project):
    axona_button = SelectFilesButton('.set')
    user = ipywidgets.Text(placeholder='*User', value=project.config.get('username'))
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

    load_input = ipywidgets.Checkbox(description='Load .inp', value=False)
    set_zero_cluster_to_noise = ipywidgets.Checkbox(description='Zero cluster noise', value=True)
    load_cut = ipywidgets.Checkbox(description='Load .cut', value=True)
    overwrite = ipywidgets.Checkbox(description='Overwrite', value=False)
    register = ipywidgets.Button(description='Register')

    fields = ipywidgets.VBox([
        user,
        location,
        action_id,
        entity_id,
        message,
        tag,
        register
    ])
    checks = ipywidgets.HBox([axona_button, register_depth, overwrite, load_cut, load_input])
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
        tags = split_tags(tag)
        if not required_values_filled(user, location):
            return
        no_cut = not load_cut.value
        for path in axona_button.files:
            axona.register_axona_recording(
                project=project,
                action_id=none_if_empty(action_id.value),
                axona_filename=path,
                depth=depth.value,
                user=user.value,
                overwrite=overwrite.value,
                templates=templates.value,
                entity_id=none_if_empty(entity_id.value),
                location=location.value,
                message=none_if_empty(message.value),
                tag=tags,
                get_inp=load_input.value,
                no_cut=no_cut,
                cluster_group=[],
                set_zero_cluster_to_noise=set_zero_cluster_to_noise.value,
                register_depth=register_depth.value,
                correct_depth_answer=True)

    register.on_click(on_register)
    return main_box
