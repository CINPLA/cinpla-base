from expipe_plugin_cinpla.scripts import entity
from expipe_plugin_cinpla.imports import *
from .utils import DatePicker, SearchSelectMultiple, required_values_filled, none_if_empty, split_tags


def entity_view(project):
    entity_id = ipywidgets.Text(placeholder='*Entity id')
    user = ipywidgets.Text(placeholder='*User', value=project.config.get('username'))
    message = ipywidgets.Text(placeholder='Message')
    location = ipywidgets.Text(placeholder='*Location')
    tag = ipywidgets.Text(placeholder='Tags (; to separate)')
    birthday = DatePicker(description='*Birthday', disabled=False)
    templates = SearchSelectMultiple(project.templates, description='Templates')

    overwrite = ipywidgets.Checkbox(description='Overwrite', value=False)

    register = ipywidgets.Button(description='Register')

    fields = ipywidgets.VBox([
        entity_id,
        user,
        location,
        birthday,
        message,
        tag,
        register])

    main_box = ipywidgets.VBox([
            overwrite,
            ipywidgets.HBox([fields, templates])

        ])

    def on_register(change):
        tags = split_tags(tag)
        if not required_values_filled(entity_id, user, location, birthday):
            return
        entity.register_entity(
            project=project,
            entity_id=entity_id.value,
            user=user.value,
            message=none_if_empty(message.value),
            birthday=birthday.datetime,
            overwrite=overwrite,
            location=location.value,
            tag=tags,
            templates=templates.value)

    register.on_click(on_register)
    return main_box
