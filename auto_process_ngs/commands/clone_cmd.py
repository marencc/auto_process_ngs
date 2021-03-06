#!/usr/bin/env python
#
#     clone_cmd.py: implement auto process clone command
#     Copyright (C) University of Manchester 2019 Peter Briggs
#
#########################################################################

#######################################################################
# Imports
#######################################################################

import os
import logging
import shutil
from ..analysis import AnalysisProject
from ..metadata import AnalysisDirParameters
import bcftbx.utils as bcf_utils

# Module specific logger
logger = logging.getLogger(__name__)

#######################################################################
# Command functions
#######################################################################

def clone(ap,clone_dir,copy_fastqs=False,exclude_projects=False):
    """
    Make a 'clone' (i.e. copy) of an analysis directory

    Makes a functional copy of an existing analysis directory,
    including metadata and parameters, stats files, processing
    reports and project subdirectories.

    By default the 'unaligned' directory in the new directory is
    simply a symlink from the original directory; set the
    'copy_fastqs' to make copies instead.

    Arguments
      ap (AutoProcessor): autoprocessor pointing to the parent
        analysis directory
      clone_dir (str): path to the new directory to create as a
        clone (must not already exist).
      copy_fastqs (boolean): set to True to copy the Fastq files
        (otherwise default behaviour is to make symlinks)
      exclude_projects (boolean): set to True to exclude any
        projects from the parent analysis directory
    """
    clone_dir = os.path.abspath(clone_dir)
    print("Cloning into %s" % clone_dir)
    if os.path.exists(clone_dir):
        # Directory already exists
        logger.critical("Target directory '%s' already exists" %
                        clone_dir)
        raise Exception("Clone failed: target directory '%s' "
                        "already exists" % clone_dir)
    bcf_utils.mkdir(clone_dir)
    # Copy metadata and parameters
    for f in (ap.metadata_file,ap.parameter_file):
        if os.path.exists(f):
            shutil.copy(f,os.path.join(clone_dir,os.path.basename(f)))
    # Primary data directory
    if ap.params.primary_data_dir:
        primary_data_dir = os.path.join(ap.analysis_dir,
                                        ap.params.primary_data_dir)
        if os.path.isdir(primary_data_dir):
            clone_primary_data_dir = os.path.join(clone_dir,
                                                  os.path.basename(primary_data_dir))
            print("[Primary data] making %s" % clone_primary_data_dir)
            bcf_utils.mkdir(clone_primary_data_dir)
            data_dir = os.path.basename(ap.params.data_dir)
            if os.path.exists(os.path.join(primary_data_dir,data_dir)):
                clone_data_dir = os.path.join(clone_primary_data_dir,data_dir)
                print("[Primary data] symlinking %s" % clone_data_dir)
                os.symlink(os.path.join(primary_data_dir,data_dir),
                           clone_data_dir)
    # Link to or copy fastqs
    if not ap.params.unaligned_dir:
        for d in ('Unaligned','bcl2fastq',):
            unaligned_dir = os.path.join(ap.analysis_dir,d)
            if os.path.isdir(unaligned_dir):
                break
            unaligned_dir = None
    else:
        unaligned_dir = os.path.join(ap.analysis_dir,ap.params.unaligned_dir)
    if os.path.isdir(unaligned_dir):
        clone_unaligned_dir = os.path.join(clone_dir,
                                           os.path.basename(unaligned_dir))
        if not copy_fastqs:
            # Link to unaligned dir
            print("[Unaligned] symlinking %s" % clone_unaligned_dir)
            os.symlink(unaligned_dir,clone_unaligned_dir)
        else:
            # Copy unaligned dir
            print("[Unaligned] copying %s" % clone_unaligned_dir)
            shutil.copytree(unaligned_dir,clone_unaligned_dir)
    else:
        print("[Unaligned] no 'unaligned' dir found")
    # Duplicate project directories
    projects = ap.get_analysis_projects()
    if projects and not exclude_projects:
        for project in ap.get_analysis_projects():
            print("[Projects] duplicating project '%s'" % project.name)
            fastqs = project.fastqs
            new_project = AnalysisProject(
                project.name,
                os.path.join(clone_dir,project.name),
                user=project.info.user,
                PI=project.info.PI,
                library_type=project.info.library_type,
                single_cell_platform=project.info.single_cell_platform,
                organism=project.info.organism,
                run=project.info.run,
                comments=project.info.comments,
                platform=project.info.platform)
            new_project.create_directory(fastqs=fastqs,
                                         link_to_fastqs=(not copy_fastqs))
    # Copy additional files, if found
    for f in ("SampleSheet.orig.csv",
              ("custom_SampleSheet.csv"
               if not ap.params.sample_sheet
               else ap.params.sample_sheet),
              ("projects.info"
               if not ap.params.project_metadata
               else ap.params.project_metadata),
              ("statistics.info"
               if not ap.params.stats_file
               else ap.params.stats_file),
              ("per_lane_statistics.info"
               if not ap.params.per_lane_stats_file
               else ap.params.per_lane_stats_file),
              "statistics_full.info",
              "per_lane_sample_stats.info",
              "processing_qc.html",):
        if not f:
            continue
        srcpath = os.path.join(ap.analysis_dir,f)
        if os.path.exists(srcpath):
            print("[Files] copying %s" % f)
            shutil.copy(srcpath,clone_dir)
    # Create the basic set of subdirectories
    for subdir in ('logs','ScriptCode',):
        print("[Subdirectories] making %s" % subdir)
        bcf_utils.mkdir(os.path.join(clone_dir,subdir))
    # Update the settings
    parameter_file = os.path.join(clone_dir,
                                  os.path.basename(ap.parameter_file))
    params = AnalysisDirParameters(filen=os.path.join(
        clone_dir,
        os.path.basename(ap.parameter_file)))
    for p in ("sample_sheet","primary_data_dir"):
        if not params[p]:
            continue
        print("[Parameters] updating '%s'" % p)
        params[p] = os.path.join(clone_dir,
                                 os.path.relpath(params[p],
                                                 ap.analysis_dir))
    params.save()
