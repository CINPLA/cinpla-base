# cinpla-base
Repository to fork when you want to start a new project

# Installation
If you want to use phy you have to use conda in order to install pyqt4
```
conda install python=3.5 pyqt=4
```
Then, to install expipe etc.
```
git clone git@github.com:CINPLA/cinpla-base.git
cd cinpla-base
pip install -r requirements.txt
```

To add the cinpla plugin
```
expipe config global --add plugin expipe_plugin_cinpla
```


If you have a project specific plugin (`my-plugin`) which is installed through `requirements.txt` you should navigate to the project (`my-project`) directory 
```
cd /path/to/my-project
expipe config project --add plugin my_plugin
```


If you have other project specific plugins (`my-other-plugin`) you want to add to `my-project`:
```
cd /path/to/my-other-plugin
python setup.py develop
cd /path/to/my-project
expipe config project --add plugin my_other_plugin
```
