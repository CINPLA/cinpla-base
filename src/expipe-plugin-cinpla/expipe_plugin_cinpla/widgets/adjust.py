from expipe_plugin_cinpla.scripts import adjust
from expipe_plugin_cinpla.imports import *
from .utils import (
    DateTimePicker, MultiInput, required_values_filled, none_if_empty,
    SearchSelect, SearchSelectMultiple, split_tags)


def adjustment_view(project):
    entity_id = SearchSelect(options=project.entities, description='*Entities')
    user = ipywidgets.Text(placeholder='*User', value=project.config.get('username'))
    date = DateTimePicker()
    adjustment = MultiInput(['*Key', '*Probe', '*Adjustment', '*Unit'], 'Add adjustment')
    depth = MultiInput(['Key', 'Probe', 'Depth', 'Unit'], 'Add depth')
    depth_from_surgery = ipywidgets.Checkbox(description='Get depth from surgery', value=True)
    register = ipywidgets.Button(description='Register')

    fields = ipywidgets.VBox([
        user,
        date,
        adjustment,
        register])
    main_box = ipywidgets.VBox([
            depth_from_surgery,
            ipywidgets.HBox([fields, entity_id])
        ])


    def on_manual_depth(change):
        if change['name'] == 'value':
            if not change['owner'].value:
                children = list(main_box.children)
                children = children[:5] + [depth] + children[5:]
                main_box.children = children
            else:
                children = list(main_box.children)
                del(children[5])
                main_box.children = children

    depth_from_surgery.observe(on_manual_depth, names='value')

    def on_register(change):
        if not required_values_filled(entity_id, user, adjustment):
            return
        adjust.register_adjustment(
            project=project,
            entity_id=entity_id.value,
            date=date.value,
            adjustment=adjustment.value,
            user=user.value,
            depth=depth.value,
            yes=True)

    register.on_click(on_register)
    return main_box


def annotate_view(project):
    action_id = SearchSelectMultiple(options=project.actions, description='*Actions')
    user = ipywidgets.Text(placeholder='*User', value=project.config.get('username'))
    date = DateTimePicker()
    depth = MultiInput(['Key', 'Probe', 'Depth', 'Unit'], 'Add depth')
    location = ipywidgets.Text(placeholder='Location', value=project.config.get('location'))
    entity_id = ipywidgets.Text(placeholder='Entity id')
    action_type = ipywidgets.Text(placeholder='Type (e.g. recording)')
    message = ipywidgets.Text(placeholder='Message')
    tag = ipywidgets.Text(placeholder='Tags (; to separate)')
    templates = SearchSelectMultiple(project.templates, description='Templates')
    register = ipywidgets.Button(description='Register')

    fields = ipywidgets.VBox([
        user,
        date,
        location,
        message,
        action_type,
        tag,
        depth,
        entity_id,
        register])
    main_box = ipywidgets.VBox([
            ipywidgets.HBox([fields, action_id, templates])
        ])


    def on_register(change):
        if not required_values_filled(action_id, user):
            return
        tags = split_tags(tag)
        for a in action_id.value:
            adjust.register_annotation(
                project=project,
                action_id=a,
                user=user.value,
                action_type=action_type.value,
                date=date.value,
                location=location.value,
                message=message.value,
                tag=tags,
                depth=depth.value,
                entity_id=entity_id.value,
                templates=templates.value,
                correct_depth_answer=True)

    register.on_click(on_register)
    return main_box
