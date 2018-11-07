# cinpla-base
Repository to fork when you want to start a new project

# Installation
## Anaconda
```
conda create -n expipe
conda activate expipe
```
If you want to use phy you have to install pyqt4 and python 3.5
```
conda install python=3.5 pyqt=4
```
Then, to install expipe etc. follow the instructions for PyPi, but first, make sure you have the latest version of pip
```
conda update pip
```
## PyPi
If you are not using anaconda, we recomend using [virtualenv](https://virtualenvwrapper.readthedocs.io/en/latest/)
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
