#######################################################################
# Tests for make_fastqs_cmd.py module
#######################################################################

import unittest
import tempfile
import shutil
import os
from auto_process_ngs.settings import Settings
from auto_process_ngs.auto_processor import AutoProcess
from bcftbx.mock import MockIlluminaRun
from auto_process_ngs.mock import MockBcl2fastq2Exe
from auto_process_ngs.mock import MockCellrangerExe
from auto_process_ngs.commands.make_fastqs_cmd import make_fastqs

# Set to False to keep test output dirs
REMOVE_TEST_OUTPUTS = True

class TestAutoProcessMakeFastqs(unittest.TestCase):
    """
    Tests for AutoProcess.make_fastqs
    """
    def setUp(self):
        # Create a temp working dir
        self.wd = tempfile.mkdtemp(suffix='TestAutoProcessMakeFastqs')
        # Create settings instance
        # This allows us to set the polling interval for the
        # unit tests
        settings_ini = os.path.join(self.wd,"auto_process.ini")
        with open(settings_ini,'w') as s:
            s.write("""[general]
poll_interval = 0.5
""")
        self.settings = Settings(settings_ini)
        # Create a temp 'bin' dir
        self.bin = os.path.join(self.wd,"bin")
        os.mkdir(self.bin)
        # Store original location
        self.pwd = os.getcwd()
        # Store original PATH
        self.path = os.environ['PATH']
        # Move to working dir
        os.chdir(self.wd)
        # Placeholders for test objects
        self.ap = None

    def tearDown(self):
        # Delete autoprocessor object
        if self.ap is not None:
            del(self.ap)
        # Return to original dir
        os.chdir(self.pwd)
        # Restore PATH
        os.environ['PATH'] = self.path
        # Remove the temporary test directory
        if REMOVE_TEST_OUTPUTS:
            shutil.rmtree(self.wd)
            
    #@unittest.skip("Skipped")
    def test_make_fastqs_standard_protocol_bcl2fastq_2_17(self):
        """make_fastqs: standard protocol (bcl2fastq v2.17)
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_M00879_00002_AHGXXXX",
            "miseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 version='2.17.1.14')
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_M00879_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,protocol="standard")
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_M00879_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_M00879_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_M00879_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_standard_protocol_bcl2fastq_2_20(self):
        """make_fastqs: standard protocol (bcl2fastq v2.20)
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_M00879_00002_AHGXXXX",
            "miseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 version="2.20.0.422")
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_M00879_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,protocol="standard")
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_M00879_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_M00879_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_M00879_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_standard_protocol_no_demultiplexing(self):
        """make_fastqs: standard protocol with no demultiplexing
        """
        # Sample sheet with no barcodes
        samplesheet_no_demultiplexing = """[Header]
IEMFileVersion,4
Assay,Nextera XT

[Reads]
76
76

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
AB1,AB1,,,,,AB,
"""
        sample_sheet = os.path.join(self.wd,"SampleSheet.csv")
        with open(sample_sheet,'w') as fp:
            fp.write(samplesheet_no_demultiplexing)
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_NB500968_00002_AHGXXXX",
            "nextseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        # Check that bases mask is as expected
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 assert_bases_mask="y76,nnnnnn,y76")
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_NB500968_00002_AHGXXXX"),
                 sample_sheet=sample_sheet)
        self.assertTrue(ap.params.sample_sheet is not None)
        make_fastqs(ap,protocol="standard")
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_NB500968_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_NB500968_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_standard_protocol_chromium_sc_indices(self):
        """make_fastqs: standard protocol with Chromium SC indices raises exception
        """
        # Sample sheet with 10xGenomics Chromium SC indices
        samplesheet_chromium_sc_indices = """[Header]
IEMFileVersion,4
Assay,Nextera XT

[Reads]
76
76

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
smpl1,smpl1,,,A001,SI-GA-A1,10xGenomics,
smpl2,smpl2,,,A005,SI-GA-B1,10xGenomics,
smpl3,smpl3,,,A006,SI-GA-C1,10xGenomics,
smpl4,smpl4,,,A007,SI-GA-D1,10xGenomics,
"""
        sample_sheet = os.path.join(self.wd,"SampleSheet.csv")
        with open(sample_sheet,'w') as fp:
            fp.write(samplesheet_chromium_sc_indices)
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_NB500968_00002_AHGXXXX",
            "nextseq",
            top_dir=self.wd)
        illumina_run.create()
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_NB500968_00002_AHGXXXX"),
                 sample_sheet=sample_sheet)
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertRaises(Exception,
                          make_fastqs,
                          ap,
                          protocol="standard")

    #@unittest.skip("Skipped")
    def test_make_fastqs_standard_protocol_stores_bases_mask(self):
        """make_fastqs: standard protocol stores supplied bases mask
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_M00879_00002_AHGXXXX",
            "miseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_M00879_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        make_fastqs(ap,protocol="standard",bases_mask="y101,I8,I8,y101")
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"y101,I8,I8,y101")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_M00879_00002_AHGXXXX_analysis",
                                      "primary_data"))
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_M00879_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_M00879_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_icell8_protocol(self):
        """make_fastqs: icell8 protocol
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_SN7001250_00002_AHGXXXX",
            "hiseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        # Check that bases mask is as expected
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 assert_bases_mask="y25n76,I8,I8,y101")
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_SN7001250_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,protocol="icell8")
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_SN7001250_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_SN7001250_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_SN7001250_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs_icell8"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_10x_chromium_sc_protocol(self):
        """make_fastqs: 10x_chromium_sc protocol
        """
        # Sample sheet with 10xGenomics Chromium SC indices
        samplesheet_chromium_sc_indices = """[Header]
IEMFileVersion,4
Assay,Nextera XT

[Reads]
76
76

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
1,smpl1,smpl1,,,A001,SI-GA-A1,10xGenomics,
2,smpl2,smpl2,,,A005,SI-GA-B1,10xGenomics,
"""
        sample_sheet = os.path.join(self.wd,"SampleSheet.csv")
        with open(sample_sheet,'w') as fp:
            fp.write(samplesheet_chromium_sc_indices)
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_SN7001250_00002_AHGXXXX",
            "hiseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq and cellranger
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"))
        MockCellrangerExe.create(os.path.join(self.bin,
                                              "cellranger"))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_SN7001250_00002_AHGXXXX"),
                 sample_sheet=sample_sheet)
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,protocol="10x_chromium_sc")
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_SN7001250_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_SN7001250_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_SN7001250_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs_10x_chromium_sc"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_10x_chromium_sc_atac_protocol(self):
        """make_fastqs: 10x_chromium_sc_atac protocol
        """
        # Sample sheet with 10xGenomics Chromium SC ATAC-seq indices
        samplesheet_chromium_sc_atac_indices = """[Header]
IEMFileVersion,4
Assay,Nextera XT

[Reads]
76
76

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Lane,Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
1,smpl1,smpl1,,,A001,SI-NA-A1,10xGenomics,
2,smpl2,smpl2,,,A005,SI-NA-B1,10xGenomics,
"""
        sample_sheet = os.path.join(self.wd,"SampleSheet.csv")
        with open(sample_sheet,'w') as fp:
            fp.write(samplesheet_chromium_sc_atac_indices)
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_SN7001250_00002_AHGXXXX",
            "hiseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq and cellranger-atac
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"))
        MockCellrangerExe.create(os.path.join(self.bin,
                                              "cellranger-atac"),
                                 reads=('R1','R2','R3','I1',))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_SN7001250_00002_AHGXXXX"),
                 sample_sheet=sample_sheet)
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,protocol="10x_chromium_sc_atac")
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_SN7001250_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_SN7001250_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_SN7001250_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs_10x_chromium_sc_atac"),
                       "bcl2fastq",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_icell8_protocol_no_demultiplexing(self):
        """make_fastqs: icell8 protocol with no demultiplexing
        """
        # Sample sheet with no barcodes
        samplesheet_no_demultiplexing = """[Header]
IEMFileVersion,4
Assay,Nextera XT

[Reads]
76
76

[Settings]
ReverseComplement,0
Adapter,CTGTCTCTTATACACATCT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,Sample_Project,Description
AB1,AB1,,,,,icell8,
"""
        sample_sheet = os.path.join(self.wd,"SampleSheet.csv")
        with open(sample_sheet,'w') as fp:
            fp.write(samplesheet_no_demultiplexing)
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_NB500968_00002_AHGXXXX",
            "nextseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        # Check that bases mask is as expected
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 assert_bases_mask="y25n51,nnnnnn,y76")
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_NB500968_00002_AHGXXXX"),
                 sample_sheet=sample_sheet)
        self.assertTrue(ap.params.sample_sheet is not None)
        make_fastqs(ap,protocol="icell8")
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_NB500968_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_NB500968_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs_icell8"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_missing_fastqs_no_placeholders(self):
        """make_fastqs: missing fastqs, no placeholders
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_M00879_00002_AHGXXXX",
            "miseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 missing_fastqs=(
                                     "Sample1_S1_L001_R1_001.fastq.gz",
                                     "Sample1_S1_L001_R2_001.fastq.gz",))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_M00879_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        self.assertRaises(Exception,
                          make_fastqs,
                          ap,
                          protocol="standard",
                          create_empty_fastqs=False)
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_M00879_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_M00879_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_M00879_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs"),
                       "bcl2fastq"):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertFalse(os.path.exists(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)
        self.assertTrue(
            os.path.exists(
                os.path.join(analysis_dir,
                             "logs",
                             "002_make_fastqs",
                             "missing_fastqs.log")))

    #@unittest.skip("Skipped")
    def test_make_fastqs_missing_fastqs_with_placeholders(self):
        """make_fastqs: missing fastqs with placeholders
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_M00879_00002_AHGXXXX",
            "miseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 missing_fastqs=(
                                     "Sample1_S1_L001_R1_001.fastq.gz",
                                     "Sample1_S1_L001_R2_001.fastq.gz",))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_M00879_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,
                    protocol="standard",
                    create_empty_fastqs=True)
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_M00879_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_M00879_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_M00879_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info"):
            self.assertTrue(os.path.exists(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)
        self.assertTrue(
            os.path.exists(
                os.path.join(analysis_dir,
                             "logs",
                             "002_make_fastqs",
                             "missing_fastqs.log")))

    #@unittest.skip("Skipped")
    def test_make_fastqs_handle_bcl2fastq2_failure(self):
        """make_fastqs: handle bcl2fastq2 failure
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_M00879_00002_AHGXXXX",
            "miseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq which will fail (i.e.
        # return non-zero exit code)
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 exit_code=1)
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_M00879_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertRaises(Exception,
                          make_fastqs,
                          ap,
                          protocol="standard")
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_M00879_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_M00879_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs"),
                       "bcl2fastq",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertFalse(os.path.exists(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_unknown_platform(self):
        """make_fastqs: unknown platform raises exception
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_UNKNOWN_00002_AHGXXXX",
            "miseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_UNKNOWN_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        self.assertRaises(Exception,
                          make_fastqs,
                          ap,
                          protocol="standard")

    #@unittest.skip("Skipped")
    def test_make_fastqs_explicitly_specify_platform(self):
        """make_fastqs: explicitly specify the platform
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_UNKNOWN_00002_AHGXXXX",
            "miseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 platform="miseq")
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_UNKNOWN_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,
                       protocol="standard",
                       platform="miseq")
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_UNKNOWN_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_UNKNOWN_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_UNKNOWN_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_specify_platform_via_metadata(self):
        """make_fastqs: implicitly specify the platform via metadata
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_UNKNOWN_00002_AHGXXXX",
            "miseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 platform="miseq")
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_UNKNOWN_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertTrue(ap.metadata.platform is None)
        ap.metadata["platform"] = "miseq"
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,protocol="standard")
        # Check parameters
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_UNKNOWN_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_UNKNOWN_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_UNKNOWN_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs"),
                       "bcl2fastq",
                       "barcode_analysis",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    #@unittest.skip("Skipped")
    def test_make_fastqs_invalid_barcodes(self):
        """make_fastqs: stop for invalid barcodes
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_M00879_00002_AHGXXXX",
            "miseq",
            sample_sheet_content="""[Header],,,,,,,,,
IEMFileVersion,4
Date,11/23/2015
Workflow,GenerateFASTQ
Application,FASTQ Only
Assay,TruSeq HT
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA
AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
Sample1,Sample1,,,D701,CGTGTAGG,D501,GACCTGNN,,
Sample2,Sample2,,,D702,CGTGTAGG,D501,ATGTAACT,,
""",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 platform="miseq")
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_M00879_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        self.assertRaises(Exception,
                          make_fastqs,
                          ap)

    #@unittest.skip("Skipped")
    def test_make_fastqs_samplesheet_with_invalid_characters(self):
        """make_fastqs: stop for invalid characters in sample sheet
        """
        # Create mock source data with samplesheet with backspace
        illumina_run = MockIlluminaRun(
            "171020_M00879_00002_AHGXXXX",
            "miseq",
            sample_sheet_content="""[Header],,,,,,,,,
IEMFileVersion,4
Date,11/23/2015
Workflow,GenerateFASTQ
Application,FASTQ Only
Assay,TruSeq HT
Description,
Chemistry,Amplicon

[Reads]
101
101

[Settings]
ReverseComplement,0
Adapter,AGATCGGAAGAGCACACGTCTGAACTCCAGTCA
AdapterRead2,AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT

[Data]
Sample_ID,Sample_Name,Sample_Plate,Sample_Well,I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,Description
Sample1,Sample1,,,D701,CGTGTAGG,D501,GACCTGTC,,\b
Sample2,Sample2,,,D702,CGTGTAGG,D501,ATGTAACT,,
""",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq
        MockBcl2fastq2Exe.create(os.path.join(self.bin,
                                              "bcl2fastq"),
                                 platform="miseq")
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_M00879_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        self.assertRaises(Exception,
                          make_fastqs,
                          ap)

    #@unittest.skip("Skipped")
    def test_make_fastqs_10x_chromium_sc_protocol(self):
        """make_fastqs: 10x_chromium_sc protocol
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_SN7001250_00002_AHGXXXX",
            "hiseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq and cellranger executables
        MockBcl2fastq2Exe.create(os.path.join(self.bin,"bcl2fastq"))
        MockCellrangerExe.create(os.path.join(self.bin,"cellranger"))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_SN7001250_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,protocol="10x_chromium_sc")
        # Check parameters
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_SN7001250_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check outputs
        analysis_dir = os.path.join(
            self.wd,
            "171020_SN7001250_00002_AHGXXXX_analysis")
        for subdir in (os.path.join("primary_data",
                                    "171020_SN7001250_00002_AHGXXXX"),
                       os.path.join("logs",
                                    "002_make_fastqs_10x_chromium_sc"),
                       "bcl2fastq",
                       "HGXXXX",):
            self.assertTrue(os.path.isdir(
                os.path.join(analysis_dir,subdir)),
                            "Missing subdir: %s" % subdir)
        for filen in ("statistics.info",
                      "statistics_full.info",
                      "per_lane_statistics.info",
                      "per_lane_sample_stats.info",
                      "projects.info",
                      "processing_qc.html",
                      "cellranger_qc_summary.html"):
            self.assertTrue(os.path.isfile(
                os.path.join(analysis_dir,filen)),
                            "Missing file: %s" % filen)

    def test_make_fastqs_primary_data_is_link(self):
        """make_fastqs: check primary data is a link by default
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_SN7001250_00002_AHGXXXX",
            "hiseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq and cellranger executables
        MockBcl2fastq2Exe.create(os.path.join(self.bin,"bcl2fastq"))
        MockCellrangerExe.create(os.path.join(self.bin,"cellranger"))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_SN7001250_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,only_fetch_primary_data=True)
        # Check parameters
        self.assertEqual(ap.params.primary_data_dir,
                         os.path.join(self.wd,
                                      "171020_SN7001250_00002_AHGXXXX_analysis",
                                      "primary_data"))
        self.assertTrue(ap.params.acquired_primary_data)
        # Check primary data is a link
        primary_data = os.path.join(ap.params.primary_data_dir,
                                    "171020_SN7001250_00002_AHGXXXX")
        self.assertTrue(os.path.islink(primary_data))

    def test_make_fastqs_force_rsync_of_primary_data(self):
        """make_fastqs: force rsync of primary data
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_SN7001250_00002_AHGXXXX",
            "hiseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq and cellranger executables
        MockBcl2fastq2Exe.create(os.path.join(self.bin,"bcl2fastq"))
        MockCellrangerExe.create(os.path.join(self.bin,"cellranger"))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_SN7001250_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        make_fastqs(ap,only_fetch_primary_data=True,
                    force_copy_of_primary_data=True)
        # Check primary data is not a link
        primary_data = os.path.join(ap.params.primary_data_dir,
                                    "171020_SN7001250_00002_AHGXXXX")
        self.assertFalse(os.path.islink(primary_data))

    def test_make_fastqs_unknown_protocol(self):
        """make_fastqs: fails with unknown protocol
        """
        # Create mock source data
        illumina_run = MockIlluminaRun(
            "171020_SN7001250_00002_AHGXXXX",
            "hiseq",
            top_dir=self.wd)
        illumina_run.create()
        # Create mock bcl2fastq and cellranger executables
        MockBcl2fastq2Exe.create(os.path.join(self.bin,"bcl2fastq"))
        MockCellrangerExe.create(os.path.join(self.bin,"cellranger"))
        os.environ['PATH'] = "%s:%s" % (self.bin,
                                        os.environ['PATH'])
        # Do the test
        ap = AutoProcess(settings=self.settings)
        ap.setup(os.path.join(self.wd,
                              "171020_SN7001250_00002_AHGXXXX"))
        self.assertTrue(ap.params.sample_sheet is not None)
        self.assertEqual(ap.params.bases_mask,"auto")
        self.assertTrue(ap.params.primary_data_dir is None)
        self.assertFalse(ap.params.acquired_primary_data)
        self.assertRaises(Exception,
                          make_fastqs,
                          ap,
                          protocol="undefined_protocol")
