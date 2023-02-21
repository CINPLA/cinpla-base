from expipe_plugin_cinpla.imports import *


def required_values_filled(*widgets):
    filled = []
    for w in widgets:
        if hasattr(w, 'value'):
            if w.value is None or w.value == '' or not w.value:
                if isinstance(w, ipywidgets.Text):
                    assert w.placeholder[0] == '*'
                    print('Missing option ', w.placeholder[1:])
                else:
                    assert w.description[0] == '*'
                    print('Missing option ', w.description[1:])
                filled.append(False)
    return all(filled)


def none_if_empty(txt):
    return txt if txt != '' else None


def split_tags(tag):
    if tag.value == '':
        return ()
    else:
        return tag.value.split(';')


class SearchSelectMultiple(ipywidgets.VBox):
    def __init__(self, options, *args, **kwargs):
        super(SearchSelectMultiple, self).__init__(*args, **kwargs)
        self.select_multiple = ipywidgets.SelectMultiple(
            options=sorted(options),
            value=(),
            disabled=False,
            layout={'height': '200px', 'width': '300px'}
        )
        update = ipywidgets.Button(
            description='Update', style={'description_width': 'initial'}, layout={'width': 'initial'})
        self.description = kwargs.get('description') or '' # TODO move into placeholder
        self.search_widget = ipywidgets.Text(
            placeholder=self.description,
            layout={'width': self.select_multiple.layout.width})

        # Wire the search field to the checkboxes
        def on_text_change(change):
            search_input = change['new']
            if search_input == '':
                # Reset search field
                new_options = sorted(options)
            else:
                # Filter by search field.
                new_options = [a for a in options if search_input in a]
            self.select_multiple.options = sorted(new_options)

        self.search_widget.observe(on_text_change, names='value')
        self.children = [self.search_widget, self.select_multiple]

    @property
    def value(self):
        return self.select_multiple.value


class SearchSelect(ipywidgets.VBox):
    def __init__(self, options, *args, **kwargs):
        super(SearchSelect, self).__init__(*args, **kwargs)
        self.select = ipywidgets.Select(
            options=sorted(options),
            value=None,
            disabled=False,
            layout={'height': '200px', 'width': '300px'}
        )
        self.description = kwargs.get('description') or ''
        search_widget = ipywidgets.Text(
            placeholder=self.description,
            layout={'width': self.select.layout.width})
        # Wire the search field to the checkboxes
        def on_text_change(change):
            search_input = change['new']
            if search_input == '':
                # Reset search field
                new_options = sorted(options)
            else:
                # Filter by search field.
                new_options = [a for a in options if search_input in a]
            self.select.options = sorted(new_options)

        search_widget.observe(on_text_change, names='value')
        self.children = [search_widget, self.select]

    @property
    def value(self):
        return self.select.value


class MultiInput(ipywidgets.VBox):
    def __init__(self, placeholders, description, *args, **kwargs):
        super(MultiInput, self).__init__(*args, **kwargs)
        self.description = description
        more_input = ipywidgets.Button(
            description=description, layout={'width': '160px'})
        self.children = [ipywidgets.HBox(
            [more_input] +
            [ipywidgets.Text(placeholder=v, layout={'width': '60px'})
            for v in placeholders])]

        def on_more_input(change):
            children = list(self.children)
            children.append(
                ipywidgets.HBox(
                    [ipywidgets.Output(layout={'width': '165px'})] +
                    [ipywidgets.Text(placeholder=v, layout={'width': '60px'})
                     for v in placeholders])
            )
            self.children = children

        more_input.on_click(on_more_input)

    @property
    def value(self):
        multi_inputs = []
        for ch in self.children:
            val = [a.value for a in ch.children[1:]]
            if all([a!='' for a in val]):
                multi_inputs.append(val)

        return tuple(multi_inputs)


class ParameterSelectList(ipywidgets.VBox):
    def __init__(self, param_dict, description, *args, **kwargs):
        super(ParameterSelectList, self).__init__(*args, **kwargs)
        self.description = description
        self.update_params(param_dict)

    def update_params(self, param_dict):
        children = []
        for (k, v) in param_dict.items():
            if isinstance(v, bool):
                wid = ipywidgets.ToggleButton(
                    description=k, value=v, disabled=False, button_style='',
                    tooltip='Description', icon='check',
                    style={'description_width': 'initial'})
                children.append(wid)
            elif isinstance(v, (int, np.integer)):
                wid = ipywidgets.IntText(
                    description=k, value=v,
                    style={'description_width': 'initial'})
                children.append(wid)
            elif isinstance(v, (float, np.float)):
                wid = ipywidgets.FloatText(
                    description=k, value=v,
                    style={'description_width': 'initial'})
                children.append(wid)
            elif not isinstance(v, dict):
                wid = ipywidgets.Text(
                    description=k, value=str(v),
                    style={'description_width': 'initial'})
                children.append(wid)
            else:
                print('not showing dictionary')
        self.children = children

    @property
    def value(self):
        keys = []
        values = []
        for ch in self.children:
            keys.append(ch.description)
            values.append(ch.value)
        return dict(zip(keys, values))


class DateTimePicker(ipywidgets.HBox):
    def __init__(self, *args, **kwargs):
        super(DateTimePicker, self).__init__(*args, **kwargs)
        self.d = ipywidgets.DatePicker(disabled=False)
        self.h = ipywidgets.Text(placeholder='HH', layout={'width': '60px'})
        self.m = ipywidgets.Text(placeholder='MM', layout={'width': '60px'})
        self.s = ipywidgets.Text(placeholder='SS', layout={'width': '60px'})
        self.children = [self.d, self.h, self.m, self.s]

    @property
    def value(self):
        d, h, m, s = self.d.value, self.h.value, self.m.value, self.s.value
        h = h if h != '' else 0
        m = m if m != '' else 0
        s = s if s != '' else 0
        t = dt.time(int(h), int(m), int(s))

        if d:
            return dt.datetime.combine(d, t)
        else:
            return None


class DatePicker(ipywidgets.DatePicker):
    def __init__(self, *args, **kwargs):
        super(DatePicker, self).__init__(*args, **kwargs)

    @property
    def datetime(self):
        if self.value:
            return dt.datetime.combine(self.value, dt.time(0, 0))
        else:
            return None


class SelectFileButton(ipywidgets.Button):
    """A file widget that leverages tkfilebrowser."""

    def __init__(self, filetype=None, initialdir=None, *args, **kwargs):
        """Initialize the SelectFileButton class."""
        super(SelectFileButton, self).__init__(*args, **kwargs)
        # Add the selected_file trait
        import traitlets
        self.initialdir = initialdir
        self.add_traits(file=traitlets.traitlets.Unicode())
        # Create the button.
        self.description = kwargs.get('description') or "Select file"
        self.icon = "square-o"
        self.style.button_color = "orange"
        # Set on click behavior.
        self.on_click(self.select_file)
        self.filetype = filetype
        self.value = False

    @staticmethod
    def select_file(self):
        from tkfilebrowser import askopenfilename
        from tkinter import Tk
        # Create Tk root
        root = Tk()
        # Hide the main window
        root.withdraw()
        # Raise the root to the top of all windows.
        root.call('wm', 'attributes', '.', '-topmost', True)
        # List of selected filewill be set to self.value
        ft = self.filetype
        if ft is not None:
            if not ft.startswith('.'):
                ft = '.' + ft
            name = ft[1:].capitalize()
            result = askopenfilename(
                defaultextension=ft,
                filetypes=[
                    ('{} file'.format(name),'*{}'.format(ft)),
                    ('All files','*.*')],
                initialdir=self.initialdir)
            self.file = result if len(result) > 0 else ''
        else:
            result = askopenfilename()
            self.file = result if len(result) > 0 else ''
        if len(self.file) > 0:
            self.description = "File Selected"
            self.icon = "check-square-o"
            self.style.button_color = "lightgreen"
            self.value = True
        else:
            self.value = False
ipywidgets.Text

class SelectFilesButton(ipywidgets.Button):
    """A file widget that leverages tkfilebrowser."""

    def __init__(self, filetype=None, initialdir=None, *args, **kwargs):
        """Initialize the SelectFileButton class."""
        super(SelectFilesButton, self).__init__(*args, **kwargs)
        # Add the selected_file trait
        if isinstance(initialdir, ipywidgets.Text):
            def on_text_change(change):
                path = change['new']
                if path == '':
                    # Reset search field
                    pass
                else:
                    # Filter by search field.
                    self.initialdir = path
            initialdir.observe(on_text_change, names='value')
        import traitlets
        self.initialdir = initialdir
        self.add_traits(file=traitlets.traitlets.Unicode())
        # Create the button.
        self.description = kwargs.get('description') or "Select file"
        self.icon = "square-o"
        self.style.button_color = "orange"
        # Set on click behavior.
        self.on_click(self.select_file)
        self.filetype = filetype
        self.value = False

    @staticmethod
    def select_file(self):
        from tkfilebrowser import askopenfilenames
        from tkinter import Tk
        # Create Tk root
        root = Tk()
        # Hide the main window
        root.withdraw()
        # Raise the root to the top of all windows.
        root.call('wm', 'attributes', '.', '-topmost', True)
        # List of selected filewill be set to self.value
        ft = self.filetype
        if ft is not None:
            if not ft.startswith('.'):
                ft = '.' + ft
            name = ft[1:].capitalize()
            self.files = askopenfilenames(
                defaultextension=ft,
                filetypes=[
                    ('{} file'.format(name),'*{}'.format(ft)),
                    ('All files','*.*')],
                initialdir=self.initialdir)
        else:
            self.files = askopenfilenames()
        if len(self.files) > 0:
            self.description = "File Selected"
            self.icon = "check-square-o"
            self.style.button_color = "lightgreen"
            self.value = True
        else:
            self.value = False


class SelectDirectoryButton(ipywidgets.Button):
    """A directory widget that leverages tkfilebrowser."""

    def __init__(self, initialdir=None, *args, **kwargs):
        """Initialize the SelectDirectoryButton class."""
        super(SelectDirectoryButton, self).__init__(*args, **kwargs)
        # Add the selected_files trait
        import traitlets
        self.initialdir = initialdir
        self.add_traits(directories=traitlets.traitlets.List())
        # Create the button.
        self.description = kwargs.get('description') or "Select Directory"
        self.icon = "square-o"
        self.style.button_color = "orange"
        # Set on click behavior.
        self.on_click(self.select_directories)
        self.value = False

    @staticmethod
    def select_directories(self):
        from tkfilebrowser import askopendirnames
        from tkinter import Tk
        # Create Tk root
        root = Tk()
        # Hide the main window
        root.withdraw()
        # Raise the root to the top of all windows.
        root.call('wm', 'attributes', '.', '-topmost', True)
        # List of selected fileswill be set to self.value
        self.directories = askopendirnames(initialdir=self.initialdir)

        if len(self.directories) > 0:
            self.description = "Directory Selected"
            self.icon = "check-square-o"
            self.style.button_color = "lightgreen"
            self.value = True
        else:
            self.value = False
