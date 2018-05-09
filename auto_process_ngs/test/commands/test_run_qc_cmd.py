#######################################################################
# Tests for run_qc_cmd.py module
#######################################################################

import unittest
import tempfile
import shutil
import os
from bcftbx.JobRunner import SimpleJobRunner
from auto_process_ngs.auto_processor import AutoProcess
from auto_process_ngs.mock import MockAnalysisDirFactory
from auto_process_ngs.mock import MockIlluminaQcSh
from auto_process_ngs.mock import MockMultiQC
from auto_process_ngs.commands.run_qc_cmd import run_qc

# Set to False to keep test output dirs
REMOVE_TEST_OUTPUTS = True

class TestAutoProcessRunQc(unittest.TestCase):
    """
    Tests for AutoProcess.run_qc
    """
    def setUp(self):
        # Create a temp working dir
        self.dirn = tempfile.mkdtemp(suffix='TestAutoProcessRunQc')
        # Create a temp 'bin' dir
        self.bin = os.path.join(self.dirn,"bin")
        os.mkdir(self.bin)
        # Store original location so we can get back at the end
        self.pwd = os.getcwd()
        # Store original PATH
        self.path = os.environ['PATH']
        # Move to working dir
        os.chdir(self.dirn)
        # Placeholders for test objects
        self.ap = None

    def tearDown(self):
        # Return to original dir
        os.chdir(self.pwd)
        # Restore PATH
        os.environ['PATH'] = self.path
        # Remove the temporary test directory
        if REMOVE_TEST_OUTPUTS:
            shutil.rmtree(self.dirn)

    def test_run_qc(self):
        """run_qc: standard QC run
        """
        # Make mock illumina_qc.sh and multiqc
        MockIlluminaQcSh.create(os.path.join(self.bin,
                                             "illumina_qc.sh"))
        MockMultiQC.create(os.path.join(self.bin,"multiqc"))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Make mock analysis directory
        mockdir = MockAnalysisDirFactory.bcl2fastq2(
            '170901_M00879_0087_000000000-AGEW9',
            'miseq',
            metadata={ "instrument_datestamp": "170901" },
            top_dir=self.dirn)
        mockdir.create()
        # Make autoprocess instance
        ap = AutoProcess(analysis_dir=mockdir.dirn)
        # Run the QC
        status = run_qc(ap,
                        run_multiqc=True,
                        max_jobs=1)
        self.assertEqual(status,0)
        # Check output and reports
        for p in ("AB","CDE","undetermined"):
            for f in ("qc",
                      "qc_report.html",
                      "qc_report.%s.%s_analysis.zip" % (
                          p,
                          '170901_M00879_0087_000000000-AGEW9'),
                      "multiqc_report.html"):
                self.assertTrue(os.path.exists(os.path.join(mockdir.dirn,
                                                            p,f)),
                                "Missing %s in project '%s'" % (f,p))