from expipe_plugin_cinpla.imports import *
from expipe_plugin_cinpla.scripts import surgery
from .utils import DatePicker, MultiInput, SearchSelectMultiple, required_values_filled, none_if_empty, split_tags, SearchSelect


def surgery_view(project):
    entity_id = SearchSelect(options=project.entities, description='*Entities')
    procedure = ipywidgets.Dropdown(
        description='*Procedure', options=['implantation', 'injection'])
    date = DatePicker(description='*Date', disabled=False)
    user = ipywidgets.Text(placeholder='*User', value=project.config.get('username'))
    weight = ipywidgets.HBox([
        ipywidgets.Text(placeholder='*Weight', layout={'width': '60px'}),
        ipywidgets.Text(placeholder='*Unit', layout={'width': '60px'})])
    location = ipywidgets.Text(placeholder='*Location', value=project.config.get('location'))
    message = ipywidgets.Text(placeholder='Message', value=None)
    tag = ipywidgets.Text(placeholder='Tags (; to separate)')
    position = MultiInput(['*Key', '*Probe', '*x', '*y', '*z', '*Unit'], 'Add position')
    angle = MultiInput(['*Key', '*Probe', '*Angle', '*Unit'], 'Add angle')
    templates = SearchSelectMultiple(project.templates, description='Templates')
    overwrite = ipywidgets.Checkbox(description='Overwrite', value=False)
    register = ipywidgets.Button(description='Register')

    fields = ipywidgets.VBox([
        user,
        location,
        date,
        weight,
        position,
        angle,
        message,
        procedure,
        tag,
        register
    ])
    main_box = ipywidgets.VBox([
            overwrite,
            ipywidgets.HBox([fields, ipywidgets.VBox([entity_id, templates])])
        ])



    def on_register(change):
        if not required_values_filled(
            entity_id, user, location, procedure, date, *weight.children, position, angle):
            return
        tags = split_tags(tag)
        weight_val = (weight.children[0].value, weight.children[1].value)
        surgery.register_surgery(
            project=project,
            overwrite=overwrite.value,
            entity_id=entity_id.value,
            user=user.value,
            procedure=procedure.value,
            location=location.value,
            weight=weight_val,
            date=date.datetime,
            templates=templates.value,
            position=position.value,
            angle=angle.value,
            message=none_if_empty(message.value),
            tag=tags)

    register.on_click(on_register)
    return main_box


def perfuse_view(project):
    entity_id = SearchSelect(options=project.entities, description='*Entities')
    date = DatePicker(disabled=False)
    user = ipywidgets.Text(placeholder='*User', value=project.config.get('username'))
    location = ipywidgets.Text(placeholder='*Location')
    message = ipywidgets.Text(placeholder='Message')
    weight = ipywidgets.HBox([
        ipywidgets.Text(placeholder='*Weight', layout={'width': '60px'}),
        ipywidgets.Text(placeholder='*Unit', layout={'width': '60px'})])
    templates = SearchSelectMultiple(project.templates, description='Templates')
    overwrite = ipywidgets.Checkbox(description='Overwrite', value=False)

    register = ipywidgets.Button(description='Register')
    fields = ipywidgets.VBox([
        user,
        location,
        date,
        weight,
        message,
        register
    ])
    main_box = ipywidgets.VBox([
        overwrite,
        ipywidgets.HBox([fields, entity_id, templates])
    ])

    def on_register(change):
        if not required_values_filled(user, entity_id, *weight.children):
            return
        weight_val = (weight.children[0].value, weight.children[1].value)
        surgery.register_perfusion(
            project=project,
            entity_id=entity_id.value,
            location=location.value,
            user=user.value,
            overwrite=overwrite.value,
            templates=templates.value,
            date=date.datetime,
            weight=weight_val,
            message=none_if_empty(message.value))

    register.on_click(on_register)
    return main_box
