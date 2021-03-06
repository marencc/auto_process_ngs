#!/usr/bin/env python
#
#     run_qc_cmd.py: implement auto process run_qc command
#     Copyright (C) University of Manchester 2018-2019 Peter Briggs
#
#########################################################################

#######################################################################
# Imports
#######################################################################

import os
import logging
from ..applications import Command
from ..qc.pipeline import QCPipeline
from ..qc.fastq_strand import build_fastq_strand_conf
from ..qc.utils import determine_qc_protocol
from ..utils import get_organism_list

# Module specific logger
logger = logging.getLogger(__name__)

#######################################################################
# Command functions
#######################################################################

def run_qc(ap,projects=None,max_jobs=4,ungzip_fastqs=False,
           fastq_screen_subset=100000,nthreads=1,
           runner=None,fastq_dir=None,qc_dir=None,
           cellranger_chemistry='auto',
           cellranger_transcriptomes=None,
           cellranger_premrna_references=None,
           report_html=None,run_multiqc=True,
           poll_interval=None):
    """Run QC pipeline script for projects

    Run the illumina_qc.sh script to perform QC on projects.

    Note that if all QC outputs already exist for a project then
    the QC will *not* be run for that project.

    A subset of projects can be selected for QC by setting the
    'projects' argument to a name or pattern, only matching
    projects will be examined.

    Arguments:
      projects (str): specify a pattern to match one or more
        projects to run the QC for (default is to run QC for all
        projects)
      max_jobs (int): maximum number of jobs that will be
        scheduled to run at one time (passed to the scheduler;
        default is 4, set to zero to remove the limit)
      ungzip_fastqs (bool): if True then run the QC script with
        the '--ungzip-fastqs' option to create decompressed
        copies of any fastq.gz inputs (default: False i.e. don't
        decompress the input files)
      fastq_screen_subset (int): subset of reads to use in
        FastQScreen, set to zero or None to use all reads
        (default: 100000)
      nthreads (int): specify number of threads to run the QC jobs
        with (default: 1)
      runner (JobRunner): specify a non-default job runner to use
        for the QC jobs
      fastq_dir (str): specify the subdirectory to take the
        Fastq files from; will be used for all projects that are
        processed (default: 'fastqs')
      qc_dir (str): specify a non-standard directory to write the
        QC outputs to; will be used for all projects that are
        processed (default: 'qc')
      cellranger_chemistry (str): assay configuration for
        10xGenomics scRNA-seq data (set to 'auto' to let cellranger
        determine this automatically (default: 'auto')
      cellranger_transcriptomes (dict): mapping of organism names
        to cellranger transcriptome reference data
      cellranger_premrna_references (dict): mapping of organism
        names to cellranger pre-mRNA reference data
      report_html (str): specify the name for the output HTML QC
        report (default: '<QC_DIR>_report.html')
      run_multiqc (bool): if True then run MultiQC at the end of
        the QC run (default)
      poll_interval (float): specifies non-default polling
        interval for scheduler used for running QC

    Returns:
      Integer: UNIX-style integer returncode where 0 = successful
        termination, non-zero indicates an error.
    """
    # Process project pattern matching
    if projects is None:
        project_pattern = '*'
        sample_pattern = '*'
    else:
        project_pattern = projects.split('/')[0]
        try:
            sample_pattern = projects.split('/')[1]
        except IndexError:
            sample_pattern = '*'
    # Get project dir data
    projects = ap.get_analysis_projects(project_pattern)
    # Check we have projects
    if len(projects) == 0:
        logger.warning("No projects found for QC analysis")
        return 1
    # Set 10x cellranger reference data
    if not cellranger_transcriptomes:
        cellranger_transcriptomes = dict()
    if ap.settings['10xgenomics_transcriptomes']:
        for organism in ap.settings['10xgenomics_transcriptomes']:
            if organism not in cellranger_transcriptomes:
                cellranger_transcriptomes[organism] = \
                    ap.settings['10xgenomics_transcriptomes'][organism]
    if not cellranger_premrna_references:
        cellranger_premrna_references = dict()
    if ap.settings['10xgenomics_premrna_references']:
        for organism in ap.settings['10xgenomics_premrna_references']:
            if organism not in cellranger_premrna_references:
                cellranger_premrna_references[organism] = \
                    ap.settings['10xgenomics_premrna_references'][organism]
    # Set up runners
    default_runner = ap.settings.general.default_runner
    if runner is None:
        qc_runner = ap.settings.runners.qc
        cellranger_runner = ap.settings.runners.cellranger
    # Get environment modules
    envmodules = dict()
    for name in ('illumina_qc',
                 'fastq_strand',
                 'cellranger',
                 'report_qc',):
        try:
            envmodules[name] = ap.settings.modulefiles[name]
        except KeyError:
            envmodules[name] = None
    # Get scheduler parameters
    if max_jobs is None:
        max_jobs = ap.settings.general.max_concurrent_jobs
    if poll_interval is None:
        poll_interval = ap.settings.general.poll_interval
    # Set up a master log directory and file
    ap.set_log_dir(ap.get_log_subdir('run_qc'))
    log_file = os.path.join(ap.log_dir,"run_qc.log")
    # Set up the QC for each project
    runqc = QCPipeline()
    for project in projects:
        # Determine the QC protocol
        protocol = determine_qc_protocol(project)
        runqc.add_project(project,
                          qc_dir=qc_dir,
                          fastq_dir=fastq_dir,
                          organism=project.info.organism,
                          qc_protocol=protocol,
                          sample_pattern=sample_pattern,
                          multiqc=True)
    # Collect the cellranger data and parameters
    cellranger_settings = ap.settings['10xgenomics']
    cellranger_jobmode = cellranger_settings.cellranger_jobmode
    cellranger_mempercore = cellranger_settings.cellranger_mempercore
    cellranger_jobinterval = cellranger_settings.cellranger_jobinterval
    cellranger_localcores = cellranger_settings.cellranger_localcores
    cellranger_localmem = cellranger_settings.cellranger_localmem
    cellranger_atac_references = ap.settings['10xgenomics_atac_genome_references']
    # Run the QC
    status = runqc.run(nthreads=nthreads,
                       fastq_strand_indexes=
                       ap.settings.fastq_strand_indexes,
                       cellranger_transcriptomes=cellranger_transcriptomes,
                       cellranger_premrna_references=\
                       cellranger_premrna_references,
                       cellranger_atac_references=cellranger_atac_references,
                       cellranger_chemistry=cellranger_chemistry,
                       cellranger_jobmode=cellranger_jobmode,
                       cellranger_maxjobs=max_jobs,
                       cellranger_mempercore=cellranger_mempercore,
                       cellranger_jobinterval=cellranger_jobinterval,
                       cellranger_localcores=cellranger_localcores,
                       cellranger_localmem=cellranger_localmem,
                       log_file=log_file,
                       poll_interval=poll_interval,
                       max_jobs=max_jobs,
                       runners={
                           'cellranger_runner': cellranger_runner,
                           'qc_runner': qc_runner,
                           'verify_runner': default_runner,
                           'report_runner': default_runner,
                       },
                       default_runner=default_runner,
                       envmodules=envmodules)
    return status
