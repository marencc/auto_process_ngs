#######################################################################
# Unit tests for qc/utils.py
#######################################################################

import unittest
import tempfile
import shutil
import os
from bcftbx.JobRunner import SimpleJobRunner
from auto_process_ngs.mock import MockAnalysisProject
from auto_process_ngs.mock import UpdateAnalysisProject
from auto_process_ngs.analysis import AnalysisProject
from auto_process_ngs.qc.utils import verify_qc
from auto_process_ngs.qc.utils import report_qc

# Set to False to keep test output dirs
REMOVE_TEST_OUTPUTS = True

class TestVerifyQCFunction(unittest.TestCase):
    """
    Tests for verify_qc function
    """
    def setUp(self):
        # Create a temp working dir
        self.wd = tempfile.mkdtemp(suffix='TestVerifyQCFunction')
        # Create a temp 'bin' dir
        self.bin = os.path.join(self.wd,"bin")
        os.mkdir(self.bin)
        # Store original location
        self.pwd = os.getcwd()
        # Store original PATH
        self.path = os.environ['PATH']
        # Move to working dir
        os.chdir(self.wd)

    def tearDown(self):
        # Return to original dir
        os.chdir(self.pwd)
        # Restore PATH
        os.environ['PATH'] = self.path
        # Remove the temporary test directory
        if REMOVE_TEST_OUTPUTS:
            shutil.rmtree(self.wd)

    def test_verify_qc_all_outputs(self):
        """verify_qc: project with all QC outputs present
        """
        # Make mock analysis project
        p = MockAnalysisProject("PJB",("PJB1_S1_R1_001.fastq.gz",
                                       "PJB1_S1_R2_001.fastq.gz",
                                       "PJB2_S2_R1_001.fastq.gz",
                                       "PJB2_S2_R2_001.fastq.gz"))
        p.create(top_dir=self.wd)
        # Add QC outputs
        project = AnalysisProject("PJB",
                                  os.path.join(self.wd,"PJB"))
        UpdateAnalysisProject(project).add_qc_outputs()
        # Do verification
        self.assertTrue(verify_qc(project))

    def test_verify_qc_incomplete_outputs(self):
        """verify_qc: project with some QC outputs missing
        """
        # Make mock analysis project
        p = MockAnalysisProject("PJB",("PJB1_S1_R1_001.fastq.gz",
                                       "PJB1_S1_R2_001.fastq.gz",
                                       "PJB2_S2_R1_001.fastq.gz",
                                       "PJB2_S2_R2_001.fastq.gz"))
        p.create(top_dir=self.wd)
        # Add QC outputs
        project = AnalysisProject("PJB",
                                  os.path.join(self.wd,"PJB"))
        UpdateAnalysisProject(project).add_qc_outputs()
        # Remove an output
        os.remove(os.path.join(self.wd,
                               "PJB",
                               "qc",
                               "PJB1_S1_R1_001_fastqc.html"))
        # Do verification
        self.assertFalse(verify_qc(project))

    def test_verify_qc_no_outputs(self):
        """verify_qc: project with no QC outputs
        """
        # Make mock analysis project
        p = MockAnalysisProject("PJB",("PJB1_S1_R1_001.fastq.gz",
                                       "PJB1_S1_R2_001.fastq.gz",
                                       "PJB2_S2_R1_001.fastq.gz",
                                       "PJB2_S2_R2_001.fastq.gz"))
        p.create(top_dir=self.wd)
        project = AnalysisProject("PJB",
                                  os.path.join(self.wd,"PJB"))
        # Do verification
        self.assertFalse(verify_qc(project))

class TestReportQCFunction(unittest.TestCase):
    """
    Tests for report_qc function
    """
    def setUp(self):
        # Create a temp working dir
        self.wd = tempfile.mkdtemp(suffix='TestReportQCFunction')
        # Create a temp 'bin' dir
        self.bin = os.path.join(self.wd,"bin")
        os.mkdir(self.bin)
        # Store original location
        self.pwd = os.getcwd()
        # Store original PATH
        self.path = os.environ['PATH']
        # Move to working dir
        os.chdir(self.wd)

    def tearDown(self):
        # Return to original dir
        os.chdir(self.pwd)
        # Restore PATH
        os.environ['PATH'] = self.path
        # Remove the temporary test directory
        if REMOVE_TEST_OUTPUTS:
            shutil.rmtree(self.wd)

    def test_report_qc_all_outputs(self):
        """report_qc: project with all QC outputs present
        """
        # Make mock analysis project
        p = MockAnalysisProject("PJB",("PJB1_S1_R1_001.fastq.gz",
                                       "PJB1_S1_R2_001.fastq.gz",
                                       "PJB2_S2_R1_001.fastq.gz",
                                       "PJB2_S2_R2_001.fastq.gz"))
        p.create(top_dir=self.wd)
        # Add QC outputs
        project = AnalysisProject("PJB",
                                  os.path.join(self.wd,"PJB"))
        UpdateAnalysisProject(project).add_qc_outputs()
        # Do reporting
        self.assertEqual(report_qc(project),0)
        # Check output and reports
        for f in ("qc_report.html",
                  "qc_report.PJB.%s.zip" % os.path.basename(self.wd),
                  "multiqc_report.html"):
            self.assertTrue(os.path.exists(os.path.join(self.wd,
                                                        "PJB",f)),
                            "Missing %s" % f)

    def test_report_qc_incomplete_outputs(self):
        """report_qc: project with some QC outputs missing
        """
        # Make mock analysis project
        p = MockAnalysisProject("PJB",("PJB1_S1_R1_001.fastq.gz",
                                       "PJB1_S1_R2_001.fastq.gz",
                                       "PJB2_S2_R1_001.fastq.gz",
                                       "PJB2_S2_R2_001.fastq.gz"))
        p.create(top_dir=self.wd)
        # Add QC outputs
        project = AnalysisProject("PJB",
                                  os.path.join(self.wd,"PJB"))
        UpdateAnalysisProject(project).add_qc_outputs()
        # Remove an output
        os.remove(os.path.join(self.wd,
                               "PJB",
                               "qc",
                               "PJB1_S1_R1_001_fastqc.html"))
        # Do reporting
        self.assertEqual(report_qc(project),1)
        # Check output and reports
        for f in ("qc_report.html",
                  "qc_report.PJB.%s.zip" % os.path.basename(self.wd),
                  "multiqc_report.html"):
            self.assertTrue(os.path.exists(os.path.join(self.wd,
                                                        "PJB",f)),
                            "Missing %s" % f)

    def test_report_qc_no_outputs(self):
        """report_qc: project with no QC outputs
        """
        # Make mock analysis project
        p = MockAnalysisProject("PJB",("PJB1_S1_R1_001.fastq.gz",
                                       "PJB1_S1_R2_001.fastq.gz",
                                       "PJB2_S2_R1_001.fastq.gz",
                                       "PJB2_S2_R2_001.fastq.gz"))
        p.create(top_dir=self.wd)
        project = AnalysisProject("PJB",
                                  os.path.join(self.wd,"PJB"))
        # Do reporting
        self.assertEqual(report_qc(project),1)
        # Check output and reports
        for f in ("qc_report.html",
                  "qc_report.PJB.%s.zip" % os.path.basename(self.wd),
                  "multiqc_report.html"):
            self.assertFalse(os.path.exists(os.path.join(self.wd,
                                                        "PJB",f)),
                            "Found %s (should be missing)" % f)