import os
import shutil
import pathlib

def store_notebook(action, notebook_path):
    notebook_path = pathlib.Path(notebook_path)
    action.data["notebook"] = notebook_path.name
    notebook_output_path = action.data_path('notebook')
    shutil.copy(notebook_path, notebook_output_path)
    # As HTML
    os.system('jupyter nbconvert --to html {}'.format(notebook_path))
    html_path = notebook_path.with_suffix(".html")
    action.data["html"] = html_path.name
    html_output_path = action.data_path('html')
    shutil.copy(html_path, html_output_path)
