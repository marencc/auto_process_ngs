#!/usr/bin/env python
#
#     icell8.pipeline.py: pipeline components for ICELL8 data
#     Copyright (C) University of Manchester 2018 Peter Briggs
#

"""
icell8.pipeline.py

Pipeline components for processing the outputs from the ICELL8 platform.

Pipeline classes:

- ICell8QCFilter
- ICell8FinalReporting

Pipeline command classes:

- ICell8Statistics
- SplitAndFilterFastqPair
- BatchFastqs
- ConcatFastqs
- TrimFastqPair
- FilterPolyGReads
- ContaminantFilterFastqPair

Pipeline task classes:

- SetupDirectories
- CollectFiles
- GetICell8Stats
- GetICell8PolyGStats
- SplitFastqsIntoBatches
- FilterICell8Fastqs
- TrimReads
- GetReadsWithPolyGRegions
- FilterContaminatedReads
- SplitByBarcodes
- MergeBarcodeFastqs
- MergeSampleFastqs
- CheckICell8Barcodes
- ConvertStatsToXLSX
- ReportProcessing
- UpdateProjectData
- CleanupDirectory

Functions:

- tmp_dir
- convert_to_xlsx
"""
######################################################################
# Imports
######################################################################

import os
import shutil
from bcftbx.utils import mkdir
from bcftbx.utils import AttributeDictionary
from bcftbx.utils import strip_ext
from bcftbx.utils import mkdir
from bcftbx.FASTQFile import FastqIterator
from bcftbx.TabFile import TabFile
from bcftbx.simple_xls import XLSWorkBook
from ..applications import Command
from ..analysis import AnalysisFastq
from ..analysis import AnalysisProject
from ..fastq_utils import pair_fastqs
from ..fastq_utils import get_read_number
from ..pipeliner import Pipeline
from ..pipeliner import PipelineCommand
from ..pipeliner import PipelineCommandWrapper
from ..pipeliner import PipelineTask
from ..pipeliner import FileCollector
from .utils import ICell8WellList
from .utils import normalize_sample_name

#######################################################################
# Constants
#######################################################################

import constants
MAXIMUM_BATCH_SIZE = constants.MAXIMUM_BATCH_SIZE
DEFAULT_BATCH_SIZE = 5000000

######################################################################
# ICELL8 pipeline classes
######################################################################

class ICell8QCFilter(Pipeline):
    """
    Run QC filtering on ICELL8 data

    Pipeline to perform QC filtering on ICELL8 Fastq data:

    * Splits reads into batches
    * Filter out reads which don't match any of the
      barcode sequences
    * Optionally: filter out reads which don't meet the
      barcode or UMI quality criteria
    * Trim and quality filter reads with cutadapt
    * Estimate numbers of reads with poly-G regions
    * Optionally: perform contaminant filtering
    * Assemble reads into Fastqs by barcode and by sample
      name

    Also generates statistics for numbers of reads and UMIs
    for each barcode at each stage.
    """
    def __init__(self,outdir,fastqs,well_list_file,
                 mammalian_conf,contaminants_conf,
                 batch_size,stats_dir="stats",
                 barcode_fastqs_dir="fastqs.barcodes",
                 sample_fastqs_dir="fastqs.samples",
                 basename=None,aligner=None,
                 do_contaminant_filter=True,
                 do_quality_filter=False,
                 do_clean_up = True,
                 nprocessors=None,runners=None):
        """
        Arguments:
          outdir (str): path to output directory
          fastqs (list): list of paths to Fastq files to
            perform QC pipeline filtering on
          well_list_file (str): path to input well list
            file
          mammalian_conf (str): path to Fastq_screen
            conf file with indexes for mammalian
            genomes
          contaminant_conf (str): path to Fastq_screen
            conf file with indexes for mammalian
            genomes
          stats_dir (str): path to the directory
            where statistics will be written (default:
            'stats' subdir of outdir)
          barcode_fastqs_dir (str): path to the
            directory where the barcode Fastqs will be
            written (default: 'fastqs.barcodes')
          sample_fastqs_dir (str): path to the
            directory where the sample Fastqs will be
            written (default: 'fastqs.samples'),
          basename (str): optional, specific basename
            to use for output files
          aligner (str): optional, specify the aligner
            to use for contaminant screening
          do_contaminant_filter (bool): if set then
            perform contaminant filtering (default: True)
          do quality_filter (bool): if set then
            perform filtering based on barcode and UMI
            quality (default: False)
          do_clean_up (bool): if set then remove
            pipeline intermediates on completion
            (default: True)
          nprocessors (dict): number of processors to
            use for specific pipeline stages
          runners (dict): runners to use for specific
            pipeline stages
        """
        # Initialise the pipeline superclass
        Pipeline.__init__(self,name="ICELL8: QC filter")

        ###################
        # Do internal setup
        ###################

        # Basename for output fastqs and job names etc
        if not basename:
            basename = AnalysisFastq(fastqs[0]).sample_name

        # Final output directory
        outdir = os.path.abspath(outdir)

        # Directory to write statistics to
        if not os.path.isabs(stats_dir):
            stats_dir = os.path.join(outdir,stats_dir)

        # Final Fastq directories
        if not os.path.isabs(barcode_fastqs_dir):
            barcode_fastqs_dir = os.path.join(outdir,
                                              barcode_fastqs_dir)
        if not os.path.isabs(sample_fastqs_dir):
            sample_fastqs_dir = os.path.join(outdir,
                                             sample_fastqs_dir)

        # Temporary dir
        tmp_dir = os.path.join(outdir,"tmp.%s" % self._id)

        # Only build pipeline if the final fastqs don't exist
        if (os.path.exists(barcode_fastqs_dir) and
            os.path.exists(sample_fastqs_dir)):
            self.report("Final outputs already exist")
            # Empty pipeline will still run but will do
            # nothing
            return

        ####################
        # Build the pipeline
        ####################

        # Create directory structure
        setup_dirs = SetupDirectories("Setup output directories",
                                      (outdir,
                                       stats_dir,
                                       tmp_dir))
        self.add_task(setup_dirs)

        # Initial stats
        initial_stats = GetICell8Stats("Initial statistics",
                                       fastqs,
                                       os.path.join(stats_dir,
                                                    "icell8_stats.tsv"),
                                       well_list_file,
                                       unassigned=True,
                                       nprocs=nprocessors['statistics'],
                                       temp_dir=tmp_dir)
        self.add_task(initial_stats,runner=runners['statistics'],
                      requires=(setup_dirs,))

        # Split fastqs into batches
        batch_dir = os.path.join(outdir,"_fastqs.batched")
        batch_fastqs = SplitFastqsIntoBatches("Batch Fastqs",fastqs,
                                              batch_dir,basename,
                                              batch_size=batch_size)
        self.add_task(batch_fastqs,requires=(setup_dirs,))
        collect_batch_fastqs = CollectFiles("Collect batched files",
                                            batch_dir,
                                            batch_fastqs.output().pattern)
        self.add_task(collect_batch_fastqs,requires=(batch_fastqs,))

        # Setup the filtering jobs as a group
        filter_dir = os.path.join(outdir,"_fastqs.quality_filter")
        filter_fastqs = FilterICell8Fastqs("Filter Fastqs",
                                           collect_batch_fastqs.output(),
                                           filter_dir,
                                           well_list=well_list_file,
                                           mode='none',
                                           discard_unknown_barcodes=True,
                                           quality_filter=do_quality_filter)
        self.add_task(filter_fastqs,requires=(collect_batch_fastqs,))
        # Collect the files from the filtering jobs
        collect_filtered_fastqs = CollectFiles(
            "Collect filtered fastqs",
            filter_dir,
            filter_fastqs.output().patterns.assigned)
        collect_filtered_unassigned = CollectFiles(
            "Collect filtered fastqs (unassigned barcodes)",
            filter_dir,
            filter_fastqs.output().patterns.unassigned)
        collect_filtered_failed_barcodes = CollectFiles(
            "Collect filtered fastqs (failed barcodes)",
            filter_dir,
            filter_fastqs.output().patterns.failed_barcodes)
        collect_filtered_failed_umis = CollectFiles(
            "Collect filtered fastqs (failed UMIs)",
            filter_dir,
            filter_fastqs.output().patterns.failed_umis)
        for task in (collect_filtered_fastqs,
                     collect_filtered_unassigned,
                     collect_filtered_failed_barcodes,
                     collect_filtered_failed_umis):
            self.add_task(task,requires=(filter_fastqs,))

        # Post filtering stats
        filter_stats = GetICell8Stats("Post-filtering statistics",
                                      collect_filtered_fastqs.output(),
                                      initial_stats.output(),
                                      suffix="_filtered",
                                      append=True,
                                      nprocs=nprocessors['statistics'],
                                      temp_dir=tmp_dir)
        self.add_task(filter_stats,requires=(initial_stats,
                                            collect_filtered_fastqs),
                     runner=runners['statistics'])

        # Use cutadapt to find reads with poly-G regions
        poly_g_dir = os.path.join(outdir,"_fastqs.poly_g")
        get_poly_g_reads = GetReadsWithPolyGRegions(
            "Find reads with poly-G regions",
            collect_filtered_fastqs.output(),
            poly_g_dir)
        self.add_task(get_poly_g_reads,requires=(collect_filtered_fastqs,))
        collect_poly_g_fastqs = CollectFiles("Collect poly-G fastqs",
                                             poly_g_dir,
                                             get_poly_g_reads.output().pattern)
        self.add_task(collect_poly_g_fastqs,requires=(get_poly_g_reads,))
        poly_g_stats = GetICell8PolyGStats("Poly-G region statistics",
                                           collect_poly_g_fastqs.output(),
                                           initial_stats.output(),
                                           suffix="_poly_g",
                                           append=True,
                                           nprocs=nprocessors['statistics'],
                                           temp_dir=tmp_dir)
        self.add_task(poly_g_stats,
                      requires=(collect_poly_g_fastqs,filter_stats),
                      runner=runners['statistics'])

        # Set up the cutadapt jobs as a group
        trim_dir = os.path.join(outdir,"_fastqs.trim_reads")
        trim_reads = TrimReads("Read trimming",
                               collect_filtered_fastqs.output(),
                               trim_dir)
        self.add_task(trim_reads,requires=(collect_filtered_fastqs,))
        collect_trimmed_fastqs = CollectFiles("Collect trimmed fastqs",
                                              trim_dir,
                                              trim_reads.output().pattern)
        self.add_task(collect_trimmed_fastqs,requires=(trim_reads,))

        # Post read trimming stats
        trim_stats = GetICell8Stats("Post-trimming statistics",
                                    collect_trimmed_fastqs.output(),
                                    initial_stats.output(),
                                    suffix="_trimmed",
                                    append=True,
                                    nprocs=nprocessors['statistics'],
                                    temp_dir=tmp_dir)
        self.add_task(trim_stats,requires=(collect_trimmed_fastqs,
                                           poly_g_stats),
                      runner=runners['statistics'])

        # Set up the contaminant filter jobs as a group
        if do_contaminant_filter:
            contaminant_filter_dir = os.path.join(
                outdir,
                "_fastqs.contaminant_filter")
            contaminant_filter = FilterContaminatedReads(
                "Contaminant filtering",
                collect_trimmed_fastqs.output(),
                contaminant_filter_dir,
                mammalian_conf,
                contaminants_conf,
                aligner=aligner,
                threads=nprocessors['contaminant_filter'])
            self.add_task(contaminant_filter,
                          requires=(collect_trimmed_fastqs,),
                          runner=runners['contaminant_filter'])
            collect_contaminant_filtered = CollectFiles(
                "Collect contaminant-filtered fastqs",
                contaminant_filter_dir,
                contaminant_filter.output().pattern)
            self.add_task(collect_contaminant_filtered,
                          requires=(contaminant_filter,))

            # Post contaminant filter stats
            final_stats = GetICell8Stats(
                "Post-contaminant filter statistics",
                collect_contaminant_filtered.output(),
                initial_stats.output(),
                suffix="_contaminant_filtered",
                append=True,
                nprocs=nprocessors['statistics'],
                temp_dir=tmp_dir)
            self.add_task(final_stats,
                          requires=(collect_contaminant_filtered,
                                    trim_stats),
                          runner=runners['statistics'])
            fastqs_in = collect_contaminant_filtered.output()
            split_barcodes_requires = (collect_contaminant_filtered,)
        else:
            fastqs_in = collect_trimmed_fastqs.output()
            split_barcodes_requires = (collect_trimmed_fastqs,)

        # Prepare for rebatching reads by barcode and sample by splitting
        # each batch by barcode
        split_barcoded_fastqs_dir = os.path.join(outdir,
                                                 "_fastqs.split_barcodes")
        split_barcodes = SplitByBarcodes("Split batches by barcode",
                                         fastqs_in,
                                         split_barcoded_fastqs_dir)
        self.add_task(split_barcodes,requires=split_barcodes_requires)
        collect_split_barcodes = CollectFiles("Collect barcode-split fastqs",
                                              split_barcoded_fastqs_dir,
                                              split_barcodes.output().pattern)
        self.add_task(collect_split_barcodes,requires=(split_barcodes,))
        # Merge (concat) fastqs into single pairs per barcode
        barcode_fastqs = MergeBarcodeFastqs(
            "Assemble reads by barcode",
            collect_split_barcodes.output(),
            collect_filtered_unassigned.output(),
            collect_filtered_failed_barcodes.output(),
            collect_filtered_failed_umis.output(),
            barcode_fastqs_dir,
            basename)
        self.add_task(barcode_fastqs,requires=(collect_split_barcodes,))
        collect_barcode_fastqs = CollectFiles(
            "Collect final barcoded fastqs",
            barcode_fastqs_dir,
            barcode_fastqs.output().patterns.assigned)
        self.add_task(collect_barcode_fastqs,requires=(barcode_fastqs,))
        # Merge (concat) fastqs into single pairs per barcode
        sample_fastqs_dir = os.path.join(outdir,"fastqs.samples")
        sample_fastqs = MergeSampleFastqs("Assemble reads by sample",
                                          collect_split_barcodes.output(),
                                          well_list_file,
                                          sample_fastqs_dir)
        self.add_task(sample_fastqs,requires=(collect_split_barcodes,))

        # Final stats for verification
        final_barcode_stats = GetICell8Stats(
            "Post-barcode splitting and merging statistics",
            collect_barcode_fastqs.output(),
            initial_stats.output(),
            suffix="_final",
            append=True,
            nprocs=nprocessors['statistics'],
            temp_dir=tmp_dir)
        if do_contaminant_filter:
            final_barcode_stats_requires = (collect_barcode_fastqs,
                                            final_stats,)
        else:
            final_barcode_stats_requires = (collect_barcode_fastqs,
                                            trim_stats,)
        self.add_task(final_barcode_stats,
                      requires=final_barcode_stats_requires,
                      runner=runners['statistics'])

        # Verify that barcodes are okay
        check_barcodes = CheckICell8Barcodes(
            "Verify barcodes are consistent",
            collect_barcode_fastqs.output())
        self.add_task(check_barcodes,requires=(collect_barcode_fastqs,))

        # Generate XLSX version of stats
        xlsx_stats = ConvertStatsToXLSX(
            "Convert statistics to XLSX",
            final_barcode_stats.output(),
            os.path.join(stats_dir,"icell8_stats.xlsx"))
        self.add_task(xlsx_stats,requires=(final_barcode_stats,))

        # Cleanup outputs
        cleanup_tasks = []
        cleanup_tasks.append(CleanupDirectory("Remove batched Fastqs",
                                              batch_dir))
        cleanup_tasks.append(CleanupDirectory("Remove filtered Fastqs",
                                              filter_dir))
        cleanup_tasks.append(CleanupDirectory("Remove poly-G region stats data",
                                              poly_g_dir))
        cleanup_tasks.append(CleanupDirectory("Remove trimmed Fastqs",
                                              trim_dir))
        cleanup_tasks.append(CleanupDirectory("remove barcode split Fastqs",
                                              split_barcoded_fastqs_dir))
        cleanup_tasks.append(CleanupDirectory("remove tmp directory",
                                              tmp_dir))
        if do_contaminant_filter:
            cleanup_tasks.append(CleanupDirectory("Remove contaminant "
                                                  "filtered Fastqs",
                                                  contaminant_filter_dir))

        if do_clean_up:
            # Wait until all stages are finished before doing clean up
            cleanup_requirements = [collect_barcode_fastqs,
                                    sample_fastqs]
            if do_contaminant_filter:
                cleanup_requirements.append(final_stats)
            else:
                cleanup_requirements.append(trim_stats)
            for task in cleanup_tasks:
                self.add_task(task,requires=cleanup_requirements)

class ICell8FinalReporting(Pipeline):
    """
    Perform final reporting from ICELL8 pipeline

    Pipeline to perform final reporting of the ICELL8
    processing:

    * Write the final processing report
    * Set the primary fastq dir to 'fastqs.samples' (if in
      an analysis project directory)
    """
    def __init__(self,outdir,project=None):
        """
        Set up FinalReporting pipeline instance

        Arguments:
          outdir (str): path of directory to write the
            report to
          project (AnalysisProject): optional, AnalysisProject
            instance with the ICELL8 Fastq files
        """
        # Initialise the pipeline superclass
        Pipeline.__init__(self,name="ICELL8: final reporting")
        # Reset primary fastq dir (if working in a project)
        if project is not None:
            update_project_data = UpdateProjectData(
                "Updating metadata associated with the project",
                project.dirn,
                "fastqs.samples")
            self.add_task(update_project_data)
        # Final report
        final_report = ReportProcessing("Generate processing report",
                                        outdir)
        self.add_task(final_report)

######################################################################
# ICELL8 pipeline command classes
######################################################################

class ICell8Statistics(PipelineCommand):
    """
    Build command to run the 'icell8_stats.py' utility
    """
    def init(self,fastqs,stats_file,well_list=None,
             suffix=None,unassigned=False,append=False,
             nprocs=1,temp_dir=None):
        """
        Create new ICell8Statistics instance

        Arguments:
          fastqs (list): list of FASTQ file names
          stats_file (str): path to output file
          well_list (str): path to 'well list' file (optional)
          suffix (str): suffix to append to columns with read and
            UMI counts (optional)
          unassigned (bool): if True then also collect stats for
            read pairs that don't match any of the expected
            barcodes from the well list or existing stats file
            (by default unassigned stats are not collected)
          append (bool): if True then append columns to existing
            output file (by default creates new output file)
          nprocs (int): number of cores available for stats
            (default: 1)
        """
        self._fastqs = fastqs
        self._stats_file = os.path.abspath(stats_file)
        self._well_list = well_list
        if self._well_list is not None:
            self._well_list = os.path.abspath(self._well_list)
        self._append = append
        self._unassigned = unassigned
        self._suffix = suffix
        self._nprocs = nprocs
        self._temp_dir = temp_dir
        if self._temp_dir is not None:
            self._temp_dir = os.path.abspath(self._temp_dir)
    def cmd(self):
        # Build command
        cmd = Command('icell8_stats.py',
                      '-f',self._stats_file,
                      '-n',self._nprocs)
        if self._well_list:
            cmd.add_args('-w',self._well_list)
        if self._suffix:
            cmd.add_args('--suffix',self._suffix)
        if self._append:
            cmd.add_args('--append')
        if self._unassigned:
            cmd.add_args('--unassigned')
        if self._temp_dir:
            cmd.add_args('--temporary-dir',
                         self._temp_dir)
        cmd.add_args(*self._fastqs)
        return cmd

class SplitAndFilterFastqPair(PipelineCommand):
    """
    Build command to run the 'split_icell8_fastqs.py' utility
    """
    def init(self,fastq_pair,out_dir,well_list=None,
             basename=None,mode='none',
             discard_unknown_barcodes=False,
             quality_filter=False,
             compress=False):
        """
        Create a new SplitAndFilterFastqPair instance

        Arguments:
          fastq_pair (list): R1/R2 FASTQ file pair
          out_dir (str): destination directory to
            write output files to
          well_list (str): 'well list' file to use
            (optional)
          basename (str): basename to use for output
            FASTQ files (optional)
          mode (str): mode to run the utility in
          discard_unknown_barcodes (bool): if True
            then discard read pairs where the barcode
            doesn't match one of those in the well
            list file (nb well list file must also
            be supplied in this case) (all reads are
            kept by default)
          quality_filter (bool): if True then also
            do filtering based on barcode- and
            UMI-quality (no filtering is performed
            by default)
          compress (bool): if True then gzip the
            output files (FASTQs are uncompressed
            by default)
        """
        self._fastq_pair = fastq_pair
        self._out_dir = os.path.abspath(out_dir)
        self._well_list = well_list
        self._basename = basename
        self._mode = mode
        self._discard_unknown_barcodes = discard_unknown_barcodes
        self._quality_filter = quality_filter
        self._compress = compress
        if self._well_list is not None:
            self._well_list = os.path.abspath(self._well_list)
    def cmd(self):
        cmd = Command('split_icell8_fastqs.py',
                      '-o',self._out_dir,
                      '-b',self._basename)
        if self._well_list:
            cmd.add_args('-w',self._well_list)
        if self._mode:
            cmd.add_args('-m',self._mode)
        if self._discard_unknown_barcodes:
            cmd.add_args('--discard-unknown-barcodes')
        if self._quality_filter:
            cmd.add_args('--quality-filter')
        if self._compress:
            cmd.add_args('--compress')
        cmd.add_args(*self._fastq_pair)
        return cmd

class BatchFastqs(PipelineCommand):
    """
    Split reads from Fastqs into batches using (z)cat/split

    Given a list of Fastq files, combines them and then
    splits into batches of a specified number of reads by
    running a combination of '(z)cat' and 'split' commands.

    Fastqs can be gzipped, but must have the same read number
    (i.e. R1 or R2).
    """
    def init(self,fastqs,batch_dir,basename,
             batch_size=DEFAULT_BATCH_SIZE):
        """
        Create a new BatchFastqs instance

        Arguments:
          fastqs (list): list of input Fastq files
          batch_dir (str): destination directory to
            write output files to
          basename (str): basename for output Fastqs
          batch_size (int): number of reads per output
            FASTQ (in batch mode) (optional)
        """
        # Store inputs
        self._fastqs = fastqs
        self._batch_dir = os.path.abspath(batch_dir)
        self._basename = basename
        self._batch_size = batch_size
        # Determine if fastqs are gzipped
        first_fastq = self._fastqs[0]
        self._gzipped = first_fastq.endswith('.gz')
        # Determine read number
        self._read_number = get_read_number(first_fastq)
    def cmd(self):
        # Constructs command line of the form:
        # zcat FASTQ | split -l BATCH_SIZE*4 -d -a 3 \
        #   --additional-suffix=.r1.fastq - BASENAME.B
        if self._gzipped:
            cmd = Command('zcat')
        else:
            cmd = Command('cat')
        cmd.add_args(*self._fastqs)
        cmd.add_args('|',
                     'split',
                     '-l',self._batch_size*4,
                     '-d',
                     '-a',3,
                     '--additional-suffix=.r%d.fastq' %
                     self._read_number,
                     '-',
                     os.path.join(self._batch_dir,
                                  '%s.B' % self._basename))
        return cmd

class ConcatFastqs(PipelineCommand):
    """
    Concatenate reads from multiple Fastqs into a single file

    Given a list of Fastq files, combines them into a single
    Fastq using the 'cat' utility.

    If the output FASTQ names end with .gz then they will be
    automatically compressed with gzip after concatenation.

    FASTQs cannot be gzipped, and must all be same read number
    (i.e. R1 or R2).
    """
    def init(self,fastqs,concat_dir,fastq_out):
        """
        Create a new ConcatFastqs instance

        Arguments:
          fastqs (list): list of input FASTQ files
          concat_dir (str): destination directory to
            write output file to
          fastq_out (str): name of output Fastq file
        """
        # Store inputs
        self._fastqs = fastqs
        self._concat_dir = os.path.abspath(concat_dir)
        self._fastq_out = fastq_out
    def cmd(self):
        compress = self._fastq_out.endswith('.gz')
        if compress:
            fastq_out = '.'.join(self._fastq_out.split('.')[:-1])
        else:
            fastq_out = self._fastq_out
        fastq_out = os.path.join(self._concat_dir,fastq_out)
        cmd = Command('cat')
        cmd.add_args(*self._fastqs)
        cmd.add_args('>',fastq_out)
        if compress:
            cmd.add_args('&&','gzip',fastq_out)
        return cmd

class TrimFastqPair(PipelineCommand):
    """
    Build command to run 'cutadapt' with ICell8 settings
    """
    def init(self,fastq_pair,trim_dir):
        """
        Create a new TrimFastqPair instance

        Arguments:
          fastq_pair (list): R1/R1 FASTQ file pair
          trim_dir (str): destination directory to
            write output files to
        """
        self._fastq_pair = fastq_pair
        self._trim_dir = os.path.abspath(trim_dir)
    def cmd(self):
        # Generate output file pair names
        fastq_pair_out = [os.path.join(self._trim_dir,
                                       strip_ext(os.path.basename(fq),'.fastq')
                                       + '.trimmed.fastq')
                          for fq in self._fastq_pair]
        # Build command
        cmd = Command(
            'cutadapt',
            '-a','AATGATACGGCGACCACCGAGATCTACACTCTTTCCCTACACGACGCTCTTCCGATCT',
            '-a','AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTAGATCTCGGTGGTCGCCGTATCATT',
            '-a','AAAAAAAA',
            '-a','TTTTTTTT',
            '-m',20,
            '--trim-n',
            '--max-n',0.7,
            '-q',25)
        # NB reverse R1 and R2 for input and output
        cmd.add_args('-o',fastq_pair_out[1],
                     '-p',fastq_pair_out[0])
        cmd.add_args(self._fastq_pair[1],
                     self._fastq_pair[0])
        return cmd

class FilterPolyGReads(PipelineCommand):
    """
    Run 'cutadapt' to fetch reads with poly-G regions
    """
    def init(self,fastq_pair,out_dir):
        """
        Create a new GetPolyGReads instance

        Arguments:
          fastq_pair (list): R1/R1 FASTQ file pair
          out_dir (str): destination directory to
            write output files to
        """
        self._fastq_pair = fastq_pair
        self._out_dir = os.path.abspath(out_dir)
    def cmd(self):
        # Generate output file pair names
        fastq_pair_out = [os.path.join(self._out_dir,
                                       strip_ext(os.path.basename(fq),'.fastq')
                                       + '.poly_g.fastq')
                          for fq in self._fastq_pair]
        # Build command
        cmd = Command(
            'cutadapt',
            '-a','GGGGGGG',
            '--discard-untrimmed')
        # NB reverse R1 and R2 for input and output
        cmd.add_args('-o',fastq_pair_out[1],
                     '-p',fastq_pair_out[0])
        cmd.add_args(self._fastq_pair[1],
                     self._fastq_pair[0])
        return cmd

class ContaminantFilterFastqPair(PipelineCommand):
    """
    Build command to run 'icell8_contaminantion_filter.py' utility
    """
    def init(self,fastq_pair,filter_dir,
             mammalian_conf,contaminants_conf,
             aligner=None,threads=None):
        """
        Create a new TrimFastqPair instance

        Arguments:
          fastq_pair (list): R1/R1 FASTQ file pair
          filter_dir (str): destination directory to
            write output files to
          mammalian_conf (str): path to FastqScreen
            .conf file with mammalian genome indexes
          contaminants_conf (str): path FastqScreen
            .conf file with contaminant genome indexes
          aligner (str): explicitly specify name of
            aligner to use with FastqScreen (e.g.
            'bowtie2') (optional)
          threads (int): explicitly specify number of
            threads to run FastqScreen using
            (optional)
        """
        self._fastq_pair = fastq_pair
        self._filter_dir = os.path.abspath(filter_dir)
        self._mammalian_conf = os.path.abspath(mammalian_conf)
        self._contaminants_conf = os.path.abspath(contaminants_conf)
        self._aligner = aligner
        self._threads = threads
    def cmd(self):
        # Build the command
        cmd = Command(
            'icell8_contamination_filter.py',
            '-m',self._mammalian_conf,
            '-c',self._contaminants_conf,
            '-o',self._filter_dir)
        if self._threads:
            cmd.add_args('-n',self._threads)
        if self._aligner is not None:
            cmd.add_args('-a',self._aligner)
        cmd.add_args(*self._fastq_pair)
        return cmd

######################################################################
# ICELL8 pipeline task classes
######################################################################

class SetupDirectories(PipelineTask):
    """
    Create directories

    Given a list of directories, check for and if
    necessary create each one
    """
    def init(self,dirs):
        """
        Initialise the SetupDirectories task

        Arguments:
          dirs (list): list of directories to
            ensure are present
        """
        pass
    def setup(self):
        for dirn in self.args.dirs:
            dirn = os.path.abspath(dirn)
            if os.path.exists(dirn):
                print "%s: already exists" % dirn
            else:
                print "%s: making directory" % dirn
                mkdir(dirn)
    def output(self):
        return None

class CollectFiles(PipelineTask):
    """
    Collect list of files matching glob pattern

    This is a utility task that can be used to collect
    a list of files in a directory which matches a
    'glob'-style pattern.

    It is intended to offer an alternative to the
    FileCollector class, when it is desirable to farm
    out the file collection to an external process
    (e.g. when there are very large numbers of files
    to examine).
    """
    def init(self,dirn,pattern):
        """
        Initialise the CollectFiles task

        Arguments:
          dirn (str): path to the directory holding the
            files to be collected
          pattern (str): glob-style pattern to match to
            file names
        """
        self.files = list()
    def setup(self):
        # Run 'ls' command and return one file per line
        # Follow with a null command (echo -n) to mask the
        # non-zero exit code from 'ls' when there are no
        # matching files
        self.add_cmd(
            PipelineCommandWrapper(
                "List contents of dir '%s' matching pattern '%s"
                % (self.args.dirn,self.args.pattern),
                "ls","-1",
                "%s" % (os.path.join(self.args.dirn,
                                     self.args.pattern)),
                "2>&1",
                ";","echo","-n"))
    def finish(self):
        # Process the output from the 'ls' command which
        # was written to stdout
        # Only keep lines that start with the supplied
        # directory path
        for line in self.stdout.split('\n'):
            if not line.startswith(self.args.dirn):
                continue
            self.files.append(line)
        self.files.sort()
    def output(self):
        return self.files

class GetICell8Stats(PipelineTask):
    """
    Generate statistics for ICell8 processing stage

    Counts the reads and distinct UMIs per barcode for
    reads pooled from the set of supplied Fastqs and
    writes these to columns in a tab-delimited output
    file.

    If the output file doesn't exist then it will
    created. If 'append' isn't specified then an
    existing file will be deleted and its contents
    lost.

    The barcodes are either taken from the supplied
    well list file, or from the first column of the
    output file (if it exists).

    If 'unassigned' is specified then stats will also
    be collected on reads which don't match any
    barcode.

    By default the counts are written to columns called
    ``Nreads`` and ``Distinct_UMIs``; a suffix can be
    specified to distinguish the counts from those from
    different stages.

    If the columns already exist in the file when
    appending then they will be overwritten.
    """
    def init(self,fastqs,stats_file,well_list=None,
             suffix=None,unassigned=False,append=False,
             nprocs=1,temp_dir=None):
        """
        Initialise the GetICell8Stats task

        Arguments:
          fastqs (list): list of Fastqs to get stats from
          stats_file (str): path to stats file
          well_list (str): path to a well list file to
            take the barcodes from (optional)
          suffix (str): suffix to append to the output
            column names (optional)
          unassigned (bool): if True then also collect stats
            for read pairs that don't match any of the expected
            barcodes from the well list or existing stats file
            (by default unassigned stats are not collected)
          append (bool): if True then append columns to
            existing output file (by default creates new
            output file)
          nprocs (int): number of cores available for stats
            (default: 1)
        """
        pass
    def setup(self):
        # Check if requested columns already exist
        if os.path.exists(self.args.stats_file):
            got_cols = True
            stats = TabFile(self.args.stats_file,first_line_is_header=True)
            for col in ('Nreads','Distinct_UMIs'):
                if self.args.suffix is not None:
                    col = '%s%s' % (col,self.args.suffix)
                if col not in stats.header():
                    print "Column not in file: %s" % col
                    got_cols = False
                else:
                    print "Found column: %s" % col
            if got_cols:
                # Skip statistics collection
                print "Stats file already contains data"
                return
        # Set up the statistics collection
        self.add_cmd(ICell8Statistics(self.args.fastqs,
                                      self.args.stats_file,
                                      well_list=self.args.well_list,
                                      suffix=self.args.suffix,
                                      append=self.args.append,
                                      unassigned=self.args.unassigned,
                                      nprocs=self.args.nprocs,
                                      temp_dir=self.args.temp_dir))
    def output(self):
        """
        Returns the path to the output statistics file
        """
        return self.args.stats_file

class GetICell8PolyGStats(GetICell8Stats):
    """
    Generate statistics for ICell8 poly-G detection

    Subclass of ``GetICell8Stats`` task; generates
    and appends additional column expressing poly-G
    read counts as a percentage of total filtered
    read counts for each barcode.
    """
    def finish(self):
        # Method invoked once commands have run
        # Adds another column to the stats file
        # with the percentage of 'unfiltered' reads
        # with poly-G regions
        print "Add number of reads with poly-G regions as percentage"
        stats_file = self.args.stats_file
        stats = TabFile(stats_file,first_line_is_header=True)
        # Check if data is already present
        if "%reads_poly_g" in stats.header():
            print "Poly-G stats already collected"
            return
        # Add and populate the new column
        stats.appendColumn("%reads_poly_g")
        for line in stats:
            try:
                perc_poly_g = (float(line['Nreads_poly_g'])/
                               float(line['Nreads_filtered'])*100.0)
            except ZeroDivisionError:
                perc_poly_g = 0.0
            line["%reads_poly_g"] = ("%.2f" % perc_poly_g)
        # Write out the updated stats file
        stats.write(stats_file,include_header=True)

class SplitFastqsIntoBatches(PipelineTask):
    """
    Split reads from Fastq pairs into batches

    Sorts the input Fastq files into R1/R2 pairs,
    pools read pairs and divides into new Fastq
    pairs consisting of "batches" of specified
    number of read pairs.

    The output Fastqs will be named
    ``<BASENAME>.B###.r[1|2].fastq`` (where
    ``###`` is the batch number)
    """
    def init(self,fastqs,batch_dir,basename,
             batch_size=DEFAULT_BATCH_SIZE):
        """
        Initialise the SplitFastqsIntoBatches task

        Arguments:
          fastqs (list): list of input Fastq files
          batch_dir (str): destination directory to
            write output files to
          basename (str): basename for output Fastqs
          batch_size (int): number of reads per output
            FASTQ (in batch mode) (optional)
        """
        pass
    def setup(self):
        # If output directory already exists then nothing to do
        if os.path.exists(self.args.batch_dir):
            print "%s already exists" % self.args.batch_dir
            return
        # Make temp directory for outputs
        self.tmp_batch_dir = tmp_dir(self.args.batch_dir)
        # Set up the commands
        fastq_pairs = pair_fastqs(self.args.fastqs)[0]
        fastqs_r1 = [p[0] for p in fastq_pairs]
        self.add_cmd(BatchFastqs(fastqs_r1,
                                 self.tmp_batch_dir,
                                 self.args.basename,
                                 batch_size=self.args.batch_size))
        fastqs_r2 = [p[1] for p in fastq_pairs]
        self.add_cmd(BatchFastqs(fastqs_r2,
                                 self.tmp_batch_dir,
                                 self.args.basename,
                                 batch_size=self.args.batch_size))
    def finish(self):
        # On success move the temp dir to the final location
        if not os.path.exists(self.args.batch_dir):
            print "Moving tmp dir to final location"
            os.rename(self.tmp_batch_dir,self.args.batch_dir)
    def output(self):
        """
        Returns object pointing to outputs

        Returned object has the following properties:

        - pattern: glob-style pattern matching output Fastq
          file names
        - fastqs: FileCollector listing output Fastq files
        """
        out_dir = self.args.batch_dir
        pattern = "*.B*.r*.fastq"
        return AttributeDictionary(
            pattern=pattern,
            fastqs=FileCollector(out_dir,pattern)
        )

class FilterICell8Fastqs(PipelineTask):
    """
    Perform read assignment and optional quality filtering

    For each input R1/R2 Fastq file pair:

    - if a well list is supplied then check that the
      ICell8 barcode matches one in the well list
    - if filtering is turned on then remove reads
      where the ICell8 barcode and/or UMI fail to
      meet the minimum quality standard across all
      bases
    """
    def init(self,fastqs,filter_dir,well_list=None,
              mode='none',discard_unknown_barcodes=False,
              quality_filter=False):
        """
        Initialise the FilterICell8Fastqs task

        Arguments:
          fastqs (list): input FASTQ files
          filter_dir (str): destination directory to
            write output files to
          well_list (str): 'well list' file to use
            (optional)
          mode (str): mode to run the utility in
          discard_unknown_barcodes (bool): if True
            then discard read pairs where the barcode
            doesn't match one of those in the well
            list file (nb well list file must also
            be supplied in this case) (all reads are
            kept by default)
          quality_filter (bool): if True then also
            do filtering based on barcode- and
            UMI-quality (no filtering is performed
            by default)
        """
        pass
    def setup(self):
        if os.path.exists(self.args.filter_dir):
            print "%s already exists" % self.args.filter_dir
            return
        self.tmp_filter_dir = tmp_dir(self.args.filter_dir)
        fastq_pairs = pair_fastqs(self.args.fastqs)[0]
        for fastq_pair in fastq_pairs:
            basename = os.path.basename(fastq_pair[0])[:-len(".r1.fastq")]
            self.add_cmd(SplitAndFilterFastqPair(
                fastq_pair,
                self.tmp_filter_dir,
                well_list=self.args.well_list,
                basename=basename,
                mode=self.args.mode,
                discard_unknown_barcodes=self.args.discard_unknown_barcodes,
                quality_filter=self.args.quality_filter))
    def finish(self):
        print self.stdout
        if not os.path.exists(self.args.filter_dir):
            print "Moving tmp dir to final location"
            os.rename(self.tmp_filter_dir,self.args.filter_dir)
    def output(self):
        """Returns object pointing to outputs

        The returned object has the following properties:

        - 'fastqs': object with properties which point to iterators
           listing output Fastqs (see below)
        - 'patterns': object with properties which are glob-style
           patterns matching output Fastqs (see below)

        The output Fastqs are:

        - 'assigned': Fastqs with reads assigned to known barcodes
        - 'unassigned': Fastqs with reads not assigned to known
          barcodes
        - 'failed_barcodes': Fastqs with reads which failed the
          barcode quality check
        - 'failed_umis': Fastqs with reads which failed the UMI
          quality check

        For example:

        * output().pattern.assigned = glob pattern to match Fastqs
          with assigned reads
        * output().fastqs.unassigned = iterator listing Fastqs with
          unassigned reads

        NB the 'failed_barcodes' and 'failed_umis' will be empty
        unless the 'quality_filter' argument was set to True.
        """
        out_dir = self.args.filter_dir
        patterns = AttributeDictionary(
            assigned="*.B*.filtered.r*.fastq",
            unassigned="*.unassigned.r*.fastq",
            failed_barcodes="*.failed_barcode.r*.fastq",
            failed_umis="*.failed_umi.r*.fastq"
        )
        fastqs = AttributeDictionary(
            assigned=FileCollector(out_dir,patterns.assigned),
            unassigned=FileCollector(out_dir,patterns.unassigned),
            failed_barcodes=FileCollector(out_dir,patterns.failed_barcodes),
            failed_umis=FileCollector(out_dir,patterns.failed_umis)
        )
        return AttributeDictionary(
            patterns=patterns,
            fastqs=fastqs,
        )

class TrimReads(PipelineTask):
    """
    Run 'cutadapt' with ICell8 settings

    Given a set of Fastqs, arranges into R1/R2 pairs
    and performs following operations on the R2
    reads:

    - Remove sequencing primers
    - Remove poly-A/T and poly-N sequences
    - Apply quality filter of Q <= 25
    - Remove short reads (<= 20 bases) post-trimming

    If an R2 read fails any of the filters then the read
    pair is rejected.

    Output Fastqs contain the filtered and trimmed reads
    only.
    """
    def init(self,fastqs,trim_dir):
        """
        Initialise the TrimReads task

        Arguments:
          fastqs (list): input Fastqs
          trim_dir (str): destination directory to
            write output files to
        """
        pass
    def setup(self):
        if os.path.exists(self.args.trim_dir):
            print "%s already exists" % self.args.trim_dir
            return
        self.tmp_trim_dir = tmp_dir(self.args.trim_dir)
        fastq_pairs = pair_fastqs(self.args.fastqs)[0]
        for fastq_pair in fastq_pairs:
            self.add_cmd(TrimFastqPair(fastq_pair,
                                       self.tmp_trim_dir))
    def finish(self):
        if not os.path.exists(self.args.trim_dir):
            os.rename(self.tmp_trim_dir,self.args.trim_dir)
    def output(self):
        """
        Returns object pointing to trimmed Fastq files

        Returned object has the following properties:

        - pattern: glob-style pattern matching output Fastq
          file names
        - fastqs: FileCollector listing output Fastq files
        """
        out_dir = self.args.trim_dir
        pattern = "*.trimmed.fastq"
        return AttributeDictionary(
            pattern=pattern,
            fastqs=FileCollector(out_dir,pattern)
        )

class GetReadsWithPolyGRegions(PipelineTask):
    """
    Run 'cutadapt' to identify reads with poly-G regions

    Given a set of Fastqs, arranges into R1/R2 pairs
    and identifies read pairs for which R2 appears to
    contain poly-G regions (all other read pairs are
    discarded).
    """
    def init(self,fastqs,poly_g_regions_dir):
        """
        Initialise the GetReadsWithPolyGRegions task

        Arguments:
          fastqs (list): input Fastq files
          out_dir (str): destination directory to
            write output files to
        """
        pass
    def setup(self):
        if os.path.exists(self.args.poly_g_regions_dir):
            print "%s already exists" % self.args.poly_g_regions_dir
            return
        self.tmp_poly_g_regions_dir = tmp_dir(self.args.poly_g_regions_dir)
        fastq_pairs = pair_fastqs(self.args.fastqs)[0]
        for fastq_pair in fastq_pairs:
            self.add_cmd(FilterPolyGReads(fastq_pair,
                                          self.tmp_poly_g_regions_dir))
    def finish(self):
        if not os.path.exists(self.args.poly_g_regions_dir):
            os.rename(self.tmp_poly_g_regions_dir,self.args.poly_g_regions_dir)
    def output(self):
        """
        Returns object pointing to Fastqs with poly-G regions

        Returned object has the following properties:

        - pattern: glob-style pattern matching output Fastq
          file names
        - fastqs: FileCollector listing output Fastq files
        """
        out_dir = self.args.poly_g_regions_dir
        pattern = "*.poly_g.fastq"
        return AttributeDictionary(
            pattern=pattern,
            fastqs=FileCollector(out_dir,pattern)
        )

class FilterContaminatedReads(PipelineTask):
    """
    Filter 'contaminated' reads from Fastq files

    Given a set of Fastqs, arrange into R1/R2 file
    pairs and run 'fastq_screen' on the R2 reads
    against panels of 'mammalian' and 'contaminant'
    organisms.

    Read pairs where there is an exclusive match to
    the contaminants (i.e. without any match to the
    mammalian genomes) are excluded.
    """
    def init(self,fastqs,filter_dir,mammalian_conf,
             contaminants_conf,aligner=None,threads=None):
        """
        Initialise the FilterContaminatedReads task

        Arguments:
          fastqs (list): input Fastqs
          filter_dir (str): destination directory to
            write output files to
          mammalian_conf (str): path to FastqScreen
            .conf file with mammalian genome indexes
          contaminants_conf (str): path FastqScreen
            .conf file with contaminant genome indexes
          aligner (str): explicitly specify name of
            aligner to use with FastqScreen (e.g.
            'bowtie2') (optional)
          threads (int): explicitly specify number of
            threads to run FastqScreen using
            (optional)
        """
        pass
    def setup(self):
        if os.path.exists(self.args.filter_dir):
            print "%s already exists" % self.args.filter_dir
            return
        self.tmp_filter_dir = tmp_dir(self.args.filter_dir)
        fastq_pairs = pair_fastqs(self.args.fastqs)[0]
        for fastq_pair in fastq_pairs:
            self.add_cmd(ContaminantFilterFastqPair(
                fastq_pair,
                self.tmp_filter_dir,
                self.args.mammalian_conf,
                self.args.contaminants_conf,
                aligner=self.args.aligner,
                threads=self.args.threads))
    def finish(self):
        if not os.path.exists(self.args.filter_dir):
            os.rename(self.tmp_filter_dir,self.args.filter_dir)
    def output(self):
        """
        Returns object pointing to the contaminant-filtered Fastqs

        Returned object has the following properties:

        - pattern: glob-style pattern matching output Fastq
          file names
        - fastqs: FileCollector listing output Fastq files
        """
        out_dir = self.args.filter_dir
        pattern = "*.trimmed.filtered.fastq"
        return AttributeDictionary(
            pattern=pattern,
            fastqs=FileCollector(out_dir,pattern)
        )

class SplitByBarcodes(PipelineTask):
    """
    Given a set of Fastq files, arrange into
    R1/R2 pairs then pool read pairs and group
    into new Fastq file pairs by ICell8 barcode.

    Output Fastqs are named:
    ``<BASENAME>.<BARCODE>.r[1|2].fastq``.
    """
    def init(self,fastqs,barcodes_dir):
        """
        Initialise the SplitByBarcodes task

        Arguments:
          fastqs (list): input Fastq files
          barcodes_dir (str): destination directory
            to write output files to
        """
        pass
    def setup(self):
        if os.path.exists(self.args.barcodes_dir):
            print "%s already exists" % self.args.barcodes_dir
            return
        self.tmp_barcodes_dir = tmp_dir(self.args.barcodes_dir)
        fastq_pairs = pair_fastqs(self.args.fastqs)[0]
        for fastq_pair in fastq_pairs:
            basename = os.path.basename(fastq_pair[0])[:-len(".r1.fastq")+1]
            self.add_cmd(SplitAndFilterFastqPair(
                fastq_pair,
                self.tmp_barcodes_dir,
                basename=basename,
                mode="barcodes"))
    def finish(self):
        if not os.path.exists(self.args.barcodes_dir):
            os.rename(self.tmp_barcodes_dir,self.args.barcodes_dir)
    def output(self):
        """
        Returns object pointing to the barcode-pooled Fastqs

        Returned object has the following properties:

        - pattern: glob-style pattern matching output Fastq
          file names
        - fastqs: FileCollector listing output Fastq files
        """
        out_dir = self.args.barcodes_dir
        pattern = "*.r*.fastq"
        return AttributeDictionary(
            pattern=pattern,
            fastqs=FileCollector(out_dir,pattern)
        )

class MergeBarcodeFastqs(PipelineTask):
    """
    Given a set of Fastq files with filtered reads,
    arrange into R1/R2 pairs then pool read pairs
    belonging to the same ICell8 barcode.

    Also concatenate R1/R2 Fastq pairs for unassigned
    reads, 
    """
    def init(self,fastqs,unassigned_fastqs,
             failed_barcode_fastqs,failed_umi_fastqs,
             merge_dir,basename,batch_size=25):
        """
        Initialise the MergeBarcodeFastqs task

        Arguments:
          fastqs (list): input Fastq files
          unassigned_fastqs (list): Fastq files with
            reads not assigned to ICell8 barcodes
          failed_barcode_fastqs (list): Fastq files
            with reads failing barcode quality check
          failed_umi_fastqs (list): Fastq files
            with reads failing UMI quality check
          merge_dir (str): destination directory to
            write output files to
          basename (str): basename to use for output
            FASTQ files
          batch_size (int): number of barcodes to
            group together into one command for
            merging (larger batches = fewer jobs, but
            each job takes longer) (default=25)
        """
        pass
    def setup(self):
        # If output directory already exists then nothing to do
        if os.path.exists(self.args.merge_dir):
            print "%s already exists" % self.args.merge_dir
            return
        # Make temp directory for outputs
        self.tmp_merge_dir = "%s.tmp" % self.args.merge_dir
        if os.path.exists(self.tmp_merge_dir):
            print "Removing existing tmp dir '%s'" % self.tmp_merge_dir
            shutil.rmtree(self.tmp_merge_dir)
        mkdir(self.tmp_merge_dir)
        # Extract the barcodes from the fastq names
        barcodes = set()
        for fq in self.args.fastqs:
            barcode = os.path.basename(fq).split('.')[-3]
            barcodes.add(barcode)
        barcodes = sorted(list(barcodes))
        # Group files by barcode
        fastq_groups = dict()
        for barcode in barcodes:
            fqs = filter(lambda fq: (fq.endswith("%s.r1.fastq" % barcode) or
                                     fq.endswith("%s.r2.fastq" % barcode)),
                         self.args.fastqs)
            fastq_groups[barcode] = fqs
        # Group barcodes into batches
        barcode_batches = [barcodes[i:i+self.args.batch_size]
                           for i in xrange(0,len(barcodes),
                                           self.args.batch_size)]
        # Concat fastqs
        for i,barcode_batch in enumerate(barcode_batches):
            batch_name = "barcodes%06d" % i
            print "Barcode batch: %s" % batch_name
            fastq_pairs = []
            for barcode in barcode_batch:
                print "-- %s" % barcode
                fastq_pairs.extend(fastq_groups[barcode])
            self.add_cmd(SplitAndFilterFastqPair(fastq_pairs,
                                                 self.tmp_merge_dir,
                                                 basename=self.args.basename,
                                                 mode="barcodes",
                                                 compress=True))
        # Handle unassigned and failed quality reads
        for name,fqs in (('unassigned',self.args.unassigned_fastqs),
                         ('failed_barcodes',self.args.failed_barcode_fastqs),
                         ('failed_umis',self.args.failed_umi_fastqs)):
            if not fqs:
                continue
            fastq_pairs = pair_fastqs(fqs)[0]
            fqs_r1 = [p[0] for p in fastq_pairs]
            self.add_cmd(ConcatFastqs(fqs_r1,
                                      self.tmp_merge_dir,
                                      "%s.%s.r1.fastq.gz" %
                                      (self.args.basename,name)))
            fqs_r2 = [p[1] for p in fastq_pairs]
            self.add_cmd(ConcatFastqs(fqs_r2,
                                      self.tmp_merge_dir,
                                      "%s.%s.r2.fastq.gz" %
                                      (self.args.basename,name)))
    def finish(self):
        # On success move the temp dir to the final location
        if not os.path.exists(self.args.merge_dir):
            print "Moving tmp dir to final location"
            os.rename(self.tmp_merge_dir,self.args.merge_dir)
    def output(self):
        """Returns object pointing to outputs

        The returned object has the following properties:

        - 'fastqs': object with properties which point to iterators
           listing output Fastqs (see below)
        - 'patterns': object with properties which are glob-style
           patterns matching output Fastqs (see below)

        The output Fastqs are:

        - 'assigned': Fastqs with reads assigned to known barcodes
        - 'unassigned': Fastqs with reads not assigned to known
          barcodes
        - 'failed_barcodes': Fastqs with reads which failed the
          barcode quality check
        - 'failed_umis': Fastqs with reads which failed the UMI
          quality check

        For example:

        * output().pattern.assigned = glob pattern to match Fastqs
          with assigned reads
        * output().fastqs.unassigned = iterator listing Fastqs with
          unassigned reads
        """
        out_dir = self.args.merge_dir
        patterns = AttributeDictionary(
            assigned="*.[ACGT]*.r*.fastq.gz",
            unassigned="*.unassigned.r*.fastq.gz",
            failed_barcodes="*.failed_barcodes.r*.fastq.gz",
            failed_umis="*.failed_umis.r*.fastq.gz",
        )
        fastqs = AttributeDictionary(
            assigned=FileCollector(out_dir,patterns.assigned),
            unassigned=FileCollector(out_dir,patterns.unassigned),
            failed_barcodes=FileCollector(out_dir,patterns.failed_barcodes),
            failed_umis=FileCollector(out_dir,patterns.failed_umis),
        )
        return AttributeDictionary(
            patterns=patterns,
            fastqs=fastqs
        )

class MergeSampleFastqs(PipelineTask):
    """
    Given a set of Fastq files with ICell8 barcodes
    in the names, arrange into R1/R2 file pairs
    and pool reads into new Fastq files according
    to the sample names associated with each barcode
    in the well list file.
    """
    def init(self,fastqs,well_list,merge_dir):
        """
        Initialise the MergeSampleFastqs task

        Arguments:
          fastqs (list): input Fastq files
          well_list (str): 'well list' file to get
            sample names and barcodes from
          merge_dir (str): destination directory to
            write output files to
        """
        pass
    def setup(self):
        # If output directory already exists then nothing to do
        if os.path.exists(self.args.merge_dir):
            print "%s already exists" % self.args.merge_dir
            return
        # Make temp directory for outputs
        self.tmp_merge_dir = "%s.tmp" % self.args.merge_dir
        if os.path.exists(self.tmp_merge_dir):
            print "Removing existing tmp dir '%s'" % self.tmp_merge_dir
            shutil.rmtree(self.tmp_merge_dir)
        mkdir(self.tmp_merge_dir)
        # Group fastqs by sample
        well_list = ICell8WellList(self.args.well_list)
        fastq_groups = dict()
        for fq in self.args.fastqs:
            barcode = os.path.basename(fq).split('.')[-3]
            sample = normalize_sample_name(well_list.sample(barcode))
            try:
                fastq_groups[sample].append(fq)
            except KeyError:
                fastq_groups[sample] = [fq,]
        # Set up merge for fastq pairs in each sample
        for sample in fastq_groups:
            fastq_pairs = pair_fastqs(fastq_groups[sample])[0]
            fqs_r1 = [p[0] for p in fastq_pairs]
            self.add_cmd(ConcatFastqs(fqs_r1,
                                      self.tmp_merge_dir,
                                      "%s.r1.fastq.gz" % sample))
            fqs_r2 = [p[1] for p in fastq_pairs]
            self.add_cmd(ConcatFastqs(fqs_r2,
                                      self.tmp_merge_dir,
                                      "%s.r2.fastq.gz" % sample))
    def finish(self):
        # On success move the temp dir to the final location
        if not os.path.exists(self.args.merge_dir):
            print "Moving tmp dir to final location"
            os.rename(self.tmp_merge_dir,self.args.merge_dir)
    def output(self):
        """
        Returns object pointing to the merged Fastqs

        Returned object has the following properties:

        - pattern: glob-style pattern matching output Fastq
          file names
        - fastqs: FileCollector listing output Fastq files
        """
        out_dir = self.args.merge_dir
        pattern = "*.r*.fastq.gz"
        return AttributeDictionary(
            pattern=pattern,
            fastqs=FileCollector(out_dir,pattern),
        )

class CheckICell8Barcodes(PipelineTask):
    """
    Check the barcodes are consistent

    This is a sanity check: ensure that the inline barcodes
    for all reads in the R1 Fastq for the barcode Fastq pairs
    matches the assigned barcode.
    """
    def init(self,fastqs):
        """
        Initialise the CheckICell8Barcodes task

        Arguments:
          fastqs (list): Fastq files to check
        """
        self.bad_barcodes = None
    def setup(self):
        batch_size = 25
        # Reduce fastq list to just R1 files
        fastqs = filter(lambda fq:
                        AnalysisFastq(fq).read_number == 1,
                        self.args.fastqs)
        # Set up verification on batches of fastqs
        while fastqs:
            cmd = PipelineCommandWrapper("Check ICell8 barcodes")
            for fq in fastqs[:batch_size]:
                if AnalysisFastq(fq).extension.endswith('.gz'):
                    cat = 'zcat'
                else:
                    cat = 'cat'
                barcode = AnalysisFastq(fq).barcode_sequence
                if cmd.cmd() is not None:
                    cmd.add_args("&&")
                cmd.add_args(
                    "echo","-n","%s:" % barcode,"&&",
                    "%s" % cat,fq,"|",
                    "sed","-n","'2~4p'","|",
                    "grep","-v","^%s" % barcode,"|",
                    "wc","-l"
                )
            self.add_cmd(cmd)
            fastqs = fastqs[batch_size:]
    def finish(self):
        # Read the stdout looking for barcodes
        # with non-zero counts
        print self.stdout
        self.bad_barcodes = []
        for line in self.stdout.split('\n'):
            try:
                if line.startswith("#### "):
                    # Ignore lines from pipeline wrapper scripts
                    # which start with "#### ..."
                    pass
                barcode,count = line.split(':')
                count = int(count)
                if count > 0:
                    self.bad_barcodes.append((barcode,count))
            except ValueError:
                pass
        # If there are bad barcodes then fail
        if self.bad_barcodes:
            for barcode in self.bad_barcodes:
                print "ERROR %s: %d non-matching reads" % (barcode[0],
                                                           barcode[1])
            self.fail()
    def output(self):
        """Returns object pointing to bad barcodes outputs

        The returned object has the following properties:

        - 'bad_barcodes': list of tuples with 'bad' barcode
          and count of times it is not correct
        """
        return AttributeDictionary(
            bad_barcodes=self.bad_barcodes
        )

class ConvertStatsToXLSX(PipelineTask):
    """
    Convert the stats file to XLSX format
    """
    def init(self,stats_file,xlsx_file):
        """
        Initialise the ConvertStatsToXLSX task

        Arguments:
          stats_file (str): path to input stats file
          xlsx_file (str): path to output XLSX file
        """
        pass
    def setup(self):
        convert_to_xlsx(self.args.stats_file,
                        self.args.xlsx_file,
                        title="ICell8 stats",
                        freeze_header=True)
    def output(self):
        """Returns object pointing to output files

        The returned object has the following properties:

        - 'xlsx_file': path to the output XLSX file
        """
        return AttributeDictionary(
            xlsx_file=self.args.xlsx_file
        )

class ReportProcessing(PipelineTask):
    """
    Generate an HTML report on the processing

    Runs the ``icell8_report.py`` script to generate
    the report.
    """
    def init(self,dirn,stats_file=None,out_file=None,name=None):
        """
        Initialise the ReportProcessing task

        Arguments:
          dirn (str): directory with the ICell8
            pipeline outputs
          stats_file (str): name of stats file
          out_file (str): name of output report
            file (default: 'icell8_processing.html')
          name (str): title of report
        """
        self.out_file = None
    def setup(self):
        dirn = self.args.dirn
        if not os.path.isabs(dirn):
            dirn = os.path.abspath(dirn)
        if self.args.out_file is None:
            self.out_file = "icell8_processing.html"
        else:
            self.out_file = self.args.out_file
        if not os.path.isabs(self.out_file):
            self.out_file = os.path.join(dirn,self.out_file)
        cmd = PipelineCommandWrapper(
            "Report ICell8 processing",
            'icell8_report.py',
            '--out_file',self.out_file)
        if self.args.stats_file is not None:
            cmd.add_args('--stats_file',
                         self.args.stats_file)
        if self.args.name is not None:
            cmd.add_args('--name',
                         self.args.name)
        cmd.add_args(dirn)
        self.add_cmd(cmd)
    def output(self):
        """Returns object pointing to output files

        The returned object has the following properties:

        - 'report_html': path to the output HTML report
        """
        return AttributeDictionary(
            report_html=self.out_file
        )

class UpdateProjectData(PipelineTask):
    """
    Updates data (e.g. primary Fastq set) in a project
    """
    def init(self,project_dir,primary_fastq_dir):
        """
        Initialise the SetPrimaryFastqDir task

        Arguments:
          project_dir (str): path to the project
            directory
          primary_fastq_dir (str): name of the 
            Fastq subdirectory to make the
            primary Fastq set
        """
        pass
    def setup(self):
        # Load the project data
        project_dir = os.path.abspath(self.args.project_dir)
        project = AnalysisProject(project_dir,
                                  os.path.basename(project_dir))
        # Set the primary fastq set
        project.set_primary_fastq_dir(self.args.primary_fastq_dir)
        # Set the number of cells
        well_list_file = os.path.join(project_dir,
                                      project.info.icell8_well_list)
        well_list = ICell8WellList(well_list_file)
        project.info['number_of_cells'] = len(well_list.barcodes())
        project.info.save()
        # Report
        print "Primary fastq dir: %s" % project.info.primary_fastq_dir
        print "Number of cells  : %s" % project.info.number_of_cells

class CleanupDirectory(PipelineTask):
    """
    Remove a directory and all its contents
    """
    def init(self,dirn):
        """
        Initialise the CleanupDirectory task

        Arguments:
          dirn (str): path to the directory to
            remove
        """
        pass
    def setup(self):
        dirn = os.path.abspath(self.args.dirn)
        if not os.path.isdir(dirn):
            self.report("No directory '%s'" % self.args.dirn)
        else:
            self.add_cmd(
                PipelineCommandWrapper(
                    "Clean up directory '%s'" % dirn,
                    "rm","-f","%s" % os.path.join(dirn,'*'),
                    "&&",
                    "rmdir","%s" % dirn))

######################################################################
# Functions
######################################################################

def tmp_dir(d):
    """
    Create a temp dir for directory 'd'
    """
    # Make temp directory for outputs
    tmp = "%s.tmp" % d
    if os.path.exists(tmp):
        print "Removing existing tmp dir '%s'" % tmp
        shutil.rmtree(tmp)
    print "Creating tmp dir '%s'" % tmp
    mkdir(tmp)
    return tmp

def convert_to_xlsx(tsv_file,xlsx_file,title=None,freeze_header=False):
    """
    Convert a tab-delimited file to an XLSX file

    Arguments:
      tsv_file (str): path to the input TSV file
      xlsx_file (str): path to the output XLSX file
      title (str): optional, name to give the worksheet in
        the output XLSX file (defaults to the input file name)
      freeze_header (bool): optional, if True then 'freezes'
        the first line of the XLSX file (default is not to
        freeze the first line)
    """
    if title is None:
        title = os.path.basename(tsv_file)
    wb = XLSWorkBook(title)
    ws = wb.add_work_sheet(title)
    with open(tsv_file,'r') as stats:
        for line in stats:
            ws.append_row(data=line.rstrip('\n').split('\t'))
    # Freeze the top row
    if freeze_header:
        ws.freeze_panes = 'A2'
    wb.save_as_xlsx(xlsx_file)