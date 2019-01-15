
.. _auto_process_configuration:

*************
Configuration
*************

--------
Overview
--------

The autoprocessor reads its global settings for the local system from a
``settings.ini`` file, which it looks for in order in the following
locations:

1. The current directory
2. The ``config`` subdirectory of the installation directory
3. The installation directory (for legacy installations only)

To create a ``settings.ini`` file for a new installation, use the command

::

    auto_process.py config --init

To see the current settings, do

::

    auto_process.py config


To change the settings, either use the ``--set`` options, for example

::

    auto_process.py config --set bcl2fastq.nprocessors=4

or simply edit the ``settings.ini`` file by hand using a text editor.


.. note::

   If no ``settings.ini`` file exists then ``auto_process`` will run
   using the built-in default values.

.. note::

   Many of the configuration options can be over-ridden at run time
   using command line options for the specific ``auto_process``
   subcommands.

.. _basic_configuration:

-------------------
Basic configuration
-------------------

Using the basic ``auto_process`` Fastq generation requires minimal
configuration when running locally; provided that the required
``bcl2fastq`` software is available on the system (see
:ref:`software_dependencies`) it should run without further setup.

Running the QC pipeline requires additional software plus reference data
which are described in more detail in :ref:`reference_data`.

.. _config_sequencer_platforms:

------------------------
Sequencers and platforms
------------------------

The ``sequencers`` section of the configuration file allows
platform names to be associated with the instrument names for the
sequencers used at the local site.

For example if the local facility has a HISeq 4000 instrument
with ID ``SN7001250`` then this would be defined in ``settings.ini``
as follows:

::

   [sequencers]
   SN7001250 = hiseq4000

The instrument name can be derived from the name of the directories
produced by the sequencer (see :ref:`run_and_fastq_naming_conventions`).

.. _running_on_compute_cluster:

----------------------------
Running on a compute cluster
----------------------------

Within ``auto_process``, "job runners" are used to tell the pipelines
how to run their jobs. There are currently two types of runner available:

* ``SimpleJobRunner`` runs jobs as a subprocess of the current process,
  so they run locally (i.e. on the same hardware that the ``auto_process``
  command was started on)
* ``GEJobRunner`` submits jobs to Grid Engine (GE), which enables it to
  exploit additional resources available on a compute cluster.

By default ``auto_process`` is configured to use ``SimpleJobRunner``
for all jobs; to switch to using ``GEJobRunner``, set the default runner
in the settings:

::

   [general]
   default_runner = GEJobRunner

Additional options for Grid Engine submission can be specified by
enclosing when defining the runner, for example sending all jobs to a
particular queue might use:

::

   default_runner = GEJobRunner(-q ngs.queue)

This default runer can further be over-ridden for specific pipeline
stages by the settings in the ``runners`` section of the configuration
file. For example, to run ``bcl2fastq`` jobs in parallel environment
with 8 cores might look like:

::

   [runners]
    bcl2fastq = GEJobRunner(-pe smp.pe 8)

.. note::

   If you specify multiple processors for the ``bcl2fastq`` runner and are
   using ``GEJobRunner`` then you should ensure that the job runner requests
   a suitable number of cores when submitting jobs.

.. note::

   When running on a cluster the ``auto_process`` driver process should
   run on the cluster login node; it has a small CPU and memory footprint
   which should impact minimally on other users of the system.

.. _environment-modules:

-------------------------
Using environment modules
-------------------------

`Environment modules <http://modules.sourceforge.net/>`_ provide a way to
dynamic modify the user's environment. They can be especially useful to
provide access to multiple versions of the same software package, and to
manage conflicts between packages.

The ``[modulefiles]`` section in ``settings.ini`` allows specific module
files to be loaded before a specific step, for example::

    [modulefiles]
    make_fastqs = apps/bcl2fastq/1.8.4

.. note::

   These can be overridden for the ``make_fastqs`` and ``run_qc`` using
   the ``--modulefiles`` option.

.. _required_bcl2fastq_versions:

---------------------------
Required bcl2fastq versions
---------------------------

Different versions of Illumina's ``bcl2fastq`` software can be specified
both as a default and dependent on the sequencer platform, by setting the
appropriate parameters in the ``settings.ini`` file.

The ``[bcl2fastq]`` directive specifies the defaults to use for all
platforms in the absence of more specific settings, for example::

    [bcl2fastq]
    default_version = 1.8.4
    nprocessors = 8

These settings can be overriden for specific platforms, by creating optional
directives of the form ``[platform:NAME]`` (where ``NAME`` is the name of the
platform). For example to set the version to use when processing data from a
NextSeq instrument to be specifically ``2.17.1.14``::

    [platform:nextseq]
    bcl2fastq = 2.17.1.14

A range of versions can be specified by prefacing the version number by
one of the operators ``>``, ``>=``, ``<=`` and ``<`` (``==`` can also be
specified explicitly), for example::

    bcl2fastq = >=2.0

Alternatively a comma-separated list can be provided::

    bcl2fastq = >=1.8.3,<2.0

If no bcl2fastq version is explicitly specified then the highest available
version will be used.

.. note::

   This mechanism allows multiple ``bcl2fastq`` versions to be present
   in the environment simultaneously.

-------------------
Bash tab completion
-------------------

The ``auto_process-completion.bash`` file (installed into the
``etc/bash_completion.d`` subdirectory of the installation location) can
used to enable tab completion of auto_process.py commands within ``bash``
shells.

* For a global installation, copy the file to the system's
  ``/etc/bash_completion.d/`` directory, to make it available
  to all users
* For a local installation, source the file when setting up the
  environment for the installation (or source it in your
  ``~/.bashrc`` or similar).