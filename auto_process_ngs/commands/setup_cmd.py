#!/usr/bin/env python
#
#     make_fastqs_cmd.py: implement auto process make_fastqs command
#     Copyright (C) University of Manchester 2018-2019 Peter Briggs
#
#########################################################################

import os
import uuid
import shutil
import urllib2
import logging
from ..bcl2fastq_utils import get_sequencer_platform
from ..bcl2fastq_utils import make_custom_sample_sheet
from ..applications import general as general_applications
from ..fileops import exists
from ..fileops import Location
from ..samplesheet_utils import predict_outputs
from ..samplesheet_utils import check_and_warn
from bcftbx.IlluminaData import SampleSheet
from bcftbx.IlluminaData import split_run_name_full

#######################################################################
# Imports
#######################################################################

# Module specific logger
logger = logging.getLogger(__name__)

#######################################################################
# Command functions
#######################################################################

def setup(ap,data_dir,analysis_dir=None,sample_sheet=None):
    """
    Set up the initial analysis directory

    This does all the initialisation of the analysis directory
    and processing parameters

    Arguments:
      ap (AutoProcess): autoprocessor pointing to the analysis
        directory to create Fastqs for
      data_dir (str): source data directory
      analysis_dir (str): corresponding analysis directory
      sample_sheet (str): name and location of non-default sample
        sheet file
    """
    data_dir = data_dir.rstrip(os.sep)
    if not exists(data_dir):
        raise Exception("Data directory '%s' not found" %
                        data_dir)
    if not Location(data_dir).is_remote:
        data_dir = os.path.abspath(data_dir)
    run_name = os.path.basename(data_dir)
    if analysis_dir is None:
        analysis_dir = os.path.join(
            os.getcwd(),run_name)+'_analysis'
    else:
        analysis_dir = os.path.abspath(analysis_dir)
    # Create the analysis directory structure
    if not os.path.exists(analysis_dir):
        # Make a temporary analysis dir
        tmp_analysis_dir = os.path.join(
            os.path.dirname(analysis_dir),
            ".%s.%s" % (os.path.basename(analysis_dir),
                        uuid.uuid4()))
        ap.analysis_dir = tmp_analysis_dir
        logger.debug("Creating temp directory '%s'" %
                     ap.analysis_dir)
        # Create directory structure
        ap.create_directory(ap.analysis_dir)
        ap.log_dir
        ap.script_code_dir
    else:
        # Directory already exists
        logger.warning("Analysis directory '%s' already exists" %
                       analysis_dir)
        ap.analysis_dir = analysis_dir
        # check for parameter file
        if ap.has_parameter_file:
            ap.load_parameters()
        else:
            logger.warning("No parameter file found in %s" %
                           ap.analysis_dir)
    # Run datestamp, instrument name and instrument run number
    try:
        datestamp,instrument,run_number,flow_cell_prefix,flow_cell_id = \
                                    split_run_name_full(run_name)
        run_number = run_number.lstrip('0')
        flow_cell = flow_cell_prefix + flow_cell_id
    except Exception as ex:
        logger.warning("Unable to extract information from run name '%s'" \
                       % run_name)
        logger.warning("Exception: %s" % ex)
        datestamp = None
        instrument= None
        run_number = None
        flow_cell = None
    # Identify missing data and attempt to acquire
    # Sequencing platform
    platform = ap.metadata.platform
    if platform is None:
        platform = get_sequencer_platform(data_dir,
                                          instrument=instrument,
                                          settings=ap.settings)
    print "Platform identified as '%s'" % platform
    # Log dir
    ap.set_log_dir(ap.get_log_subdir('setup'))
    # Custom SampleSheet.csv file
    custom_sample_sheet = ap.params.sample_sheet
    if custom_sample_sheet is None:
        print "Acquiring sample sheet..."
        if sample_sheet is None:
            targets = ('Data/Intensities/BaseCalls/SampleSheet.csv',
                       'SampleSheet.csv',)
        else:
            targets = (sample_sheet,)
        # Try each possibility until one sticks
        for target in targets:
            target = Location(target)
            tmp_sample_sheet = os.path.join(ap.tmp_dir,
                                            os.path.basename(target.path))
            if target.is_url:
                # Try fetching samplesheet from URL
                print "Trying '%s'" % target.url
                try:
                    urlfp = urllib2.urlopen(target.url)
                    with open(tmp_sample_sheet,'w') as fp:
                        fp.write(urlfp.read())
                except urllib2.URLError as ex:
                    logger.warning("Error fetching sample sheet data "
                                   "from '%s': %s" % (target.url,ex))
                    tmp_sample_sheet = None
            else:
                # Assume target samplesheet is a file on a local
                # or remote server
                if target.is_remote:
                    sample_sheet = str(target)
                else:
                    if os.path.isabs(target.path):
                        sample_sheet = target.path
                    else:
                        sample_sheet = os.path.join(data_dir,
                                                    target.path)
                print "Trying '%s'" % sample_sheet
                rsync = general_applications.rsync(sample_sheet,
                                                   ap.tmp_dir)
                print "%s" % rsync
                status = rsync.run_subprocess(log=ap.log_path('rsync.sample_sheet.log'))
                if status != 0:
                    logger.warning("Failed to fetch sample sheet '%s'"
                                   % sample_sheet)
                    tmp_sample_sheet = None
                else:
                    break
        # Bail out if no sample sheet was acquired
        if tmp_sample_sheet is None:
            shutil.rmtree(ap.analysis_dir)
            ap.analysis_dir = None
            raise Exception("Unable to acquire sample sheet")
        # Keep a copy of the original sample sheet
        original_sample_sheet = os.path.join(ap.analysis_dir,
                                             'SampleSheet.orig.csv')
        print "Copying original sample sheet to %s" % original_sample_sheet
        shutil.copyfile(tmp_sample_sheet,original_sample_sheet)
        # Set the permissions for the original SampleSheet
        os.chmod(original_sample_sheet,0664)
        # Process acquired sample sheet
        custom_sample_sheet = os.path.join(ap.analysis_dir,
                                           'custom_SampleSheet.csv')
        sample_sheet = make_custom_sample_sheet(tmp_sample_sheet,
                                                custom_sample_sheet)
    else:
        sample_sheet = SampleSheet(custom_sample_sheet)
        original_sample_sheet = os.path.join(ap.analysis_dir,
                                             'SampleSheet.orig.csv')
    print "Sample sheet '%s'" % custom_sample_sheet
    # Library Prep Kit/Assay
    assay = None
    for item in ('Assay','Library Prep Kit'):
        try:
            assay = SampleSheet(original_sample_sheet).header[item]
            break
        except KeyError:
            logger.warning("No element '%s' found in sample sheet"
                           % item)
    # Bases mask
    print "Bases mask set to 'auto' (will be determined at run time)"
    bases_mask = "auto"
    # Generate and print predicted outputs and warnings
    print predict_outputs(sample_sheet=sample_sheet)
    check_and_warn(sample_sheet=sample_sheet)
    # Move analysis dir to final location if necessary
    if ap.analysis_dir != analysis_dir:
        logger.debug("Moving %s to final directory" % ap.analysis_dir)
        os.rename(ap.analysis_dir,analysis_dir)
        ap.analysis_dir = analysis_dir
        # Update the custom sample sheet path
        custom_sample_sheet = os.path.join(
            analysis_dir,
            os.path.basename(custom_sample_sheet))
        print "Created analysis directory '%s'" % ap.analysis_dir
    # Store the parameters
    ap.params['data_dir'] = data_dir
    ap.params['analysis_dir'] = ap.analysis_dir
    ap.params['sample_sheet'] = custom_sample_sheet
    ap.params['bases_mask'] = bases_mask
    ap.params['acquired_primary_data'] = False
    # Store the metadata
    ap.metadata['run_name'] = ap.run_name
    ap.metadata['platform'] = platform
    ap.metadata['instrument_name'] = instrument
    ap.metadata['instrument_datestamp'] = datestamp
    ap.metadata['instrument_run_number'] = run_number
    ap.metadata['instrument_flow_cell_id'] = flow_cell
    ap.metadata['assay'] = assay
    # Set flags to allow parameters etc to be saved back
    ap._save_params = True
    ap._save_metadata = True
