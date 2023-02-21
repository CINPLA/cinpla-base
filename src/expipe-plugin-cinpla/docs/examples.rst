Examples
========

Nomenclature for CINPLA
-----------------------

**Axona**

``FILENAME``: "axona navn" e.g. `22031701`, ``DATE``: `220317`, ``SESSION``:
`01`, ``SUBJECT``: subject-id e.g. `1704`, ``ACTION-ID`` is thus ``SUBJECT-DATE-SESSION``.

**Open Ephys**

``FOLDERNAME``: e.g. `1704_2017-05-13_13-52-26_03`, ``DATE``:
`2017-05-13_13-52-26`, which is automatically shortened to `130517`, ``SESSION``:
`03`, ``SUBJECT``: subject-id e.g. `1704`, ``ACTION-ID`` er thus ``SUBJECT-DATE-SESSION``

**NWB file structure and exdir**

An action is stored in a folder named after the ``ACTION-ID``. In this folder
you will find ``main.exdir`` containing ``acquisition``, ``general``, ``analysis``,
``processing``. The ``acquisition`` contains all the raw data from your measuring
instrument, ``processing`` contains extracted data which is and shall be processed.
Finnaly, in the ``analysis`` folder, you will find figures etc. after analysis
is perfomed.

General
-------

Note that you can get all available commands with::

  $ expipe --help

Furthermore if you want help on one particular command::

  $ expipe transfer --help

Transfer data to and from server
--------------------------------

Currently we support two means of transferring data: SCP (SSH), and copy.
To maximize transfer speed we recomend using SCP (expecially on Windows). The
SCP protocoll in `expipe-plugin-cinpla` is governed by the command ``transfer``.
In the ``config.yaml`` file (see :ref:`installation page <installation_page>`) you will find:

.. code-block:: yaml

  data_path: c:/users/uiousername/expipe_temp_storage
  norstore:
    data_path: /norstore_osl/projects/NS9048K/server
    username: <norstore username>
    hostname: login.norstore.uio.no

Here ``norstore`` is the server name, the first ``data_path`` is the local path and
the ``data_path`` under ``norstore`` we refer to as the server path. To transfer
local data to the server, in it's most simple form the ``transfer`` command can be
used as::

  $ expipe transfer ACTION-ID --from-local

This is because ``norstore`` is the default server name. In order to transfer
to a different server we need to add it's name with the ``--server`` command::

  $ expipe transfer ACTION-ID --from-local --server processing

When you want to retrieve your data for manual analysis, you don't want to
download all the ``acquisition`` data, e.g. only ``processing`` and
``analysis``. This can be achieved with the ``--exclude`` and ``--include``::

  $ expipe transfer ACTION-ID --to-local --include processing --include analysis

Note that many commands have a short name, e.g. ``--include`` can also be used
with ``-i``::

    $ expipe transfer ACTION-ID --to-local -i processing -i analysis

Conversly if you want to transfer the entire action only excluding the acquisition::

  $ expipe transfer ACTIO-ID --to-local --exclude acquisition

Registering subject
-------------------

Subjects are registered under the project-id ``subjects-registry``. This is to
have a complete overview of animals in the lab i.e. `active`, `dead`, `newborn`
which information is stored in tags. To register a subject use ``register-subject``::

  $ expipe register-subject SUBJECT --birthday 01.02.2017 --cell_line wild-type

Registering surgery
-------------------

When performing surgery you can register information with the ``register-surgery``
command.::

  $ expipe register-surgery SUBJECT --date 14.05.2017:12:35 --procedure implantation --weight 400

Drive adjustment
----------------

The first time you want to adjust the brain-area ``X``, ``Y``
(reffering to ``PAR.TEMPLATES['implantation']['X']``) of a drive
an amount of ``um`` you need to
initialize an adjustment action with the command::

  $ expipe adjust SUBJECT --init

When you have initialized and later make a new adjustment::

  $ expipe adjust SUBJECT --date dd.mm.yyyyTHH:MM --adjustment X um --adjustment Y um

Note that in stead of ``--date dd.mm.yyyyTHH:MM`` can use ``-d now``.

Working with Axona
------------------

Open Anaconda 3 prompt::

  activate phy

To get an overview of available commands::
  expipe --help
For help på en spesifikk kommando::
  expipe axona register --help

To overwrite existing data use ``--overwrite``::

  expipe axona register z:\USER\DATA\SUBJECT\FILENAME.set

Now modules are loaded to the firebase server and depth registration
is promted to the user.

**Spikesorting**::

  $ expipe spikesort ACTION-ID

Manual spikesoring with phy::

  $ phy neo-gui c:\user\uiousername\expipe_temp_storage\ACTION-ID\main.exdir --channel-group 0

Save with `ctrl-s`

Working with Open Ephys
-----------------------

Open Anaconda 3 prompt::

  activate phy

To get an overview of available commands::
  expipe --help
For help på en spesifikk kommando::
  expipe openephys register --help

To overwrite existing data use ``--overwrite``::

  expipe openephys register c:\open_ephys\data\1704_2017-05-13_13-52-26_03

Now modules are loaded to the firebase server and depth registration
is promted to the user.

.. todo:: probefile etc.

**Data processing**::

  $ expipe openephys process ACTION-ID

.. todo:: Detail the processing: ground channels, cmr vs car, filtering, probe

Manual spikesoring with phy::

  $ phy neo-gui c:\user\uiousername\expipe_temp_storage\ACTION-ID\main.exdir --channel-group 0

Save with `ctrl-s`


Plotting og analysis
--------------------

**Plotting with notebook**::

  $ expipe generate-notebook ACTION-ID --run

``kernel -> restart and run all``

**Make png figurer**::

  $ expipe analyse ACTION-ID --spatial

If you only want to look at a particular channel group::

  $ expipe analyse ACTION-ID --channel-group 0

**Register cells and transfer data to norstore**

When your are finished with the analysis you want to produce a representation
of the channel groups on the firebase server. This can be performed with the
command::

  $ expipe register-units ACTION-ID --tag GC --tag BC --message "found a beatiful grid cell on channel group 2"

*Example tags:*
Bare dritt: no, Good shit: yes, Vet ikke: maybe, Head direction: HD, Grid cell: GC,
Place cell: PC, Spatial cell: SC, Boarder cell: BC.

Go to `SERVER/PROJECT/ACTION-ID/main.exdir/analysis` to check out the results.
