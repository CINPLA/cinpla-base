from expipe_plugin_cinpla.imports import *
import IPython.display as ipd
from .psychopy import process_psychopy_view
from .openephys import register_openephys_view, process_openephys_view
from .intan import register_intan_view, process_intan_view
from .tracking import process_tracking_view
from .entity import entity_view
from .adjust import adjustment_view, annotate_view
from .surgery import perfuse_view, surgery_view
from .axona import axona_view
from .curation import process_curation_view
import expipe

# TODO: how to make templates
# TODO: convert templates to yaml
# TODO: transfer to db for processing
# TODO: processing
# TODO: fix old data


def display(project_path):
    project = expipe.get_project(project_path)
    # register tab
    register_tab_tab_titles = [
        'OpenEphys',
        'Intan',
        'Axona',
        'Adjustment',
        'Entity',
        'Surgery',
        'Perfusion',
        'Annotate']
    register_tab = ipywidgets.Tab()
    register_tab.children = [
        register_openephys_view(project),
        register_intan_view(project),
        axona_view(project),
        adjustment_view(project),
        entity_view(project),
        surgery_view(project),
        perfuse_view(project),
        annotate_view(project)
    ]
    for i, title in enumerate(register_tab_tab_titles):
        register_tab.set_title(i, title)

    process_tab_tab_titles = [
        'OpenEphys', 'Intan', 'Tracking', 'Psychopy', 'Curation']
    process_tab = ipywidgets.Tab()
    process_tab.children = [
        process_openephys_view(project),
        process_intan_view(project),
        process_tracking_view(project),
        process_psychopy_view(project),
        process_curation_view(project)
    ]
    for i, title in enumerate(process_tab_tab_titles):
        process_tab.set_title(i, title)

    tab_titles = ['Register', 'Process']
    tab = ipywidgets.Tab()
    tab.children = [
        register_tab,
        process_tab
    ]
    for i, title in enumerate(tab_titles):
        tab.set_title(i, title)
    ipd.display(tab)
