#     mock.py: module providing mock 10xGenomics data for testing
#     Copyright (C) University of Manchester 2018 Peter Briggs
#
########################################################################

QC_SUMMARY_JSON = """{
    "10x_software_version": "cellranger 2.2.0", 
    "PhiX_aligned": null, 
    "PhiX_error_worst_tile": null, 
    "bcl2fastq_args": "bcl2fastq --minimum-trimmed-read-length 8 --mask-short-adapter-reads 8 --create-fastq-for-index-reads --ignore-missing-positions --ignore-missing-filter --ignore-missing-bcls --use-bases-mask=y26,I8,y98 -R /net/lustre/mqbsspbd/180926_MN00218_0021_A000H2GYCG_analysis/primary_data/180926_MN00218_0021_A000H2GYCG --output-dir=/scratch/mqbsspbd/180926_MN00218_0021_A000H2GYCG_analysis/bcl2fastq --interop-dir=/scratch/mqbsspbd/180926_MN00218_0021_A000H2GYCG_analysis/000H2GYCG/MAKE_FASTQS_CS/MAKE_FASTQS/BCL2FASTQ_WITH_SAMPLESHEET/fork0/chnk0-u4f20ace4f5/files/interop_path --sample-sheet=/scratch/mqbsspbd/180926_MN00218_0021_A000H2GYCG_analysis/000H2GYCG/MAKE_FASTQS_CS/MAKE_FASTQS/PREPARE_SAMPLESHEET/fork0/chnk0-u4f20ace4cb/files/samplesheet.csv -p 6 -d 6 -r 6 -w 6", 
    "bcl2fastq_version": "2.17.1.14", 
    "experiment_name": "", 
    "fwhm_A": null, 
    "fwhm_C": null, 
    "fwhm_G": null, 
    "fwhm_T": null, 
    "index1_PhiX_error_by_cycle": null, 
    "index1_mean_phasing": null, 
    "index1_mean_prephasing": null, 
    "index1_q20_fraction": null, 
    "index1_q20_fraction_by_cycle": null, 
    "index1_q30_fraction": null, 
    "index1_q30_fraction_by_cycle": null, 
    "index2_PhiX_error_by_cycle": null, 
    "index2_mean_phasing": null, 
    "index2_mean_prephasing": null, 
    "index2_q20_fraction": null, 
    "index2_q20_fraction_by_cycle": null, 
    "index2_q30_fraction": null, 
    "index2_q30_fraction_by_cycle": null, 
    "intensity_A": null, 
    "intensity_C": null, 
    "intensity_G": null, 
    "intensity_T": null, 
    "lanecount": 1, 
    "mean_cluster_density": null, 
    "mean_cluster_density_pf": null, 
    "num_clusters": null, 
    "percent_pf_clusters": null, 
    "read1_PhiX_error_by_cycle": null, 
    "read1_mean_phasing": null, 
    "read1_mean_prephasing": null, 
    "read1_q20_fraction": null, 
    "read1_q20_fraction_by_cycle": null, 
    "read1_q30_fraction": null, 
    "read1_q30_fraction_by_cycle": null, 
    "read2_PhiX_error_by_cycle": null, 
    "read2_mean_phasing": null, 
    "read2_mean_prephasing": null, 
    "read2_q20_fraction": null, 
    "read2_q20_fraction_by_cycle": null, 
    "read2_q30_fraction": null, 
    "read2_q30_fraction_by_cycle": null, 
    "rta_version": "unknown", 
    "run_id": "180926_MN00218_0021_A000H2GYCG", 
    "sample_qc": {
        "smpl1": {
            "1": {
                "barcode_exact_match_ratio": 0.940013016010283, 
                "barcode_q30_base_ratio": 0.9468684602040338, 
                "bc_on_whitelist": 0.9634447859958355, 
                "gem_count_estimate": 68214, 
                "mean_barcode_qscore": 35.47116735755179, 
                "number_reads": 3388135, 
                "read1_q30_base_ratio": 0.9460734878931605, 
                "read2_q30_base_ratio": 0.7687690301946499
            }, 
            "all": {
                "barcode_exact_match_ratio": 0.940013016010283, 
                "barcode_q30_base_ratio": 0.9468684602040338, 
                "bc_on_whitelist": 0.9634447859958355, 
                "gem_count_estimate": 68214, 
                "mean_barcode_qscore": 35.47116735755179, 
                "number_reads": 3388135, 
                "read1_q30_base_ratio": 0.9460734878931605, 
                "read2_q30_base_ratio": 0.7687690301946499
            }
        }, 
        "smpl2": {
            "1": {
                "barcode_exact_match_ratio": 0.9412661883398474, 
                "barcode_q30_base_ratio": 0.9483778169720642, 
                "bc_on_whitelist": 0.9653697937148712, 
                "gem_count_estimate": 21399, 
                "mean_barcode_qscore": 35.50137749763865, 
                "number_reads": 2990424, 
                "read1_q30_base_ratio": 0.9474780353080827, 
                "read2_q30_base_ratio": 0.7802990769663007
            }, 
            "all": {
                "barcode_exact_match_ratio": 0.9412661883398474, 
                "barcode_q30_base_ratio": 0.9483778169720642, 
                "bc_on_whitelist": 0.9653697937148712, 
                "gem_count_estimate": 21399, 
                "mean_barcode_qscore": 35.50137749763865, 
                "number_reads": 2990424, 
                "read1_q30_base_ratio": 0.9474780353080827, 
                "read2_q30_base_ratio": 0.7802990769663007
            }
        }
    }, 
    "signoise_ratio": null, 
    "start_datetime": "None", 
    "surfacecount": 2, 
    "swathcount": 3, 
    "tilecount": 6, 
    "total_cluster_density": null, 
    "total_cluster_density_pf": null, 
    "yield": null, 
    "yield_pf": null, 
    "yield_pf_q30": null
}
"""

CELLRANGER_QC_SUMMARY = """<html>
<head>
<title>mkfastq QC report</title>
<style type="text/css">

h1    { background-color: #42AEC2;
        color: white;
        padding: 5px 10px; }
h2    { background-color: #8CC63F;
        color: white;
        display: inline-block;
        padding: 5px 15px;
        margin: 0;
        border-top-left-radius: 20px;
        border-bottom-right-radius: 20px; }
h3, h4 { background-color: grey;
         color: white;
         display: block;
         padding: 5px 15px;
         margin: 0;
         border-top-left-radius: 20px;
         border-bottom-right-radius: 20px; }
table { margin: 10 10;
        border: solid 1px grey;
        background-color: white; }
th    { background-color: grey;
        color: white;
        padding: 2px 5px; }
td    { text-align: left;
        vertical-align: top;
        padding: 2px 5px;
        border-bottom: solid 1px lightgray; }
td.param { background-color: grey;
           color: white;
           padding: 2px 5px;
           font-weight: bold; }
p.footer { font-style: italic;
           font-size: 70%; }

table { font-size: 80%;
        font-family: sans-serif; }
td { text-align: right; }</style>
</head>
<body>
<h1>mkfastq QC report</h1>
<div id='toc'>
<h2>Contents</h2>
<ul><li><a href='#General_information'>General information</a></li><li><a href='#Sample_smpl1'>Sample: smpl1</a></li><li><a href='#Sample_smpl2'>Sample: smpl2</a></li></ul>
</div>
<div id='General_information'>
<h2>General information</h2>
<table>
<tr><th>Parameter</th><th>Value</th></tr>
<tr><td>run_id</td><td>180926_MN00218_0021_A000H2GYCG</td></tr>
<tr><td>experiment_name</td><td></td></tr>
<tr><td>10x_software_version</td><td>cellranger 2.2.0</td></tr>
<tr><td>bcl2fastq_version</td><td>2.17.1.14</td></tr>
<tr><td>bcl2fastq_args</td><td>bcl2fastq --minimum-trimmed-read-length 8 --mask-short-adapter-reads 8 --create-fastq-for-index-reads --ignore-missing-positions --ignore-missing-filter --ignore-missing-bcls --use-bases-mask=y26,I8,y98 -R /net/lustre/mqbsspbd/180926_MN00218_0021_A000H2GYCG_analysis/primary_data/180926_MN00218_0021_A000H2GYCG --output-dir=/scratch/mqbsspbd/180926_MN00218_0021_A000H2GYCG_analysis/bcl2fastq --interop-dir=/scratch/mqbsspbd/180926_MN00218_0021_A000H2GYCG_analysis/000H2GYCG/MAKE_FASTQS_CS/MAKE_FASTQS/BCL2FASTQ_WITH_SAMPLESHEET/fork0/chnk0-u4f20ace4f5/files/interop_path --sample-sheet=/scratch/mqbsspbd/180926_MN00218_0021_A000H2GYCG_analysis/000H2GYCG/MAKE_FASTQS_CS/MAKE_FASTQS/PREPARE_SAMPLESHEET/fork0/chnk0-u4f20ace4cb/files/samplesheet.csv -p 6 -d 6 -r 6 -w 6</td></tr>
<tr><td>rta_version</td><td>unknown</td></tr>
</table>
</div>
<div id='Sample_smpl1'>
<h2>Sample: smpl1</h2>
<table>
<tr><th></th><th>1</th><th>all</th></tr>
<tr><td>bc_on_whitelist</td><td>0.966331905673</td><td>0.966331905673</td></tr>
<tr><td>barcode_exact_match_ratio</td><td>0.942857435466</td><td>0.942857435466</td></tr>
<tr><td>read2_q30_base_ratio</td><td>0.772020178873</td><td>0.772020178873</td></tr>
<tr><td>gem_count_estimate</td><td>39745</td><td>39745</td></tr>
<tr><td>number_reads</td><td>2831672</td><td>2831672</td></tr>
<tr><td>read1_q30_base_ratio</td><td>0.946857262157</td><td>0.946857262157</td></tr>
<tr><td>mean_barcode_qscore</td><td>35.4841823647</td><td>35.4841823647</td></tr>
<tr><td>barcode_q30_base_ratio</td><td>0.947610600507</td><td>0.947610600507</td></tr>
</table>
</div>
<div id='Sample_smpl2'>
<h2>Sample: smpl2</h2>
<table>
<tr><th></th><th>1</th><th>all</th></tr>
<tr><td>bc_on_whitelist</td><td>0.967838002215</td><td>0.967838002215</td></tr>
<tr><td>barcode_exact_match_ratio</td><td>0.943587582063</td><td>0.943587582063</td></tr>
<tr><td>read2_q30_base_ratio</td><td>0.772472408134</td><td>0.772472408134</td></tr>
<tr><td>gem_count_estimate</td><td>13063</td><td>13063</td></tr>
<tr><td>number_reads</td><td>2972732</td><td>2972732</td></tr>
<tr><td>read1_q30_base_ratio</td><td>0.946434513574</td><td>0.946434513574</td></tr>
<tr><td>mean_barcode_qscore</td><td>35.4759437333</td><td>35.4759437333</td></tr>
<tr><td>barcode_q30_base_ratio</td><td>0.947180621102</td><td>0.947180621102</td></tr>
</table>
</div></body>
</html>
"""

METRICS_SUMMARY = """Estimated Number of Cells,Mean Reads per Cell,Median Genes per Cell,Number of Reads,Valid Barcodes,Reads Mapped Confidently to Transcriptome,Reads Mapped Confidently to Exonic Regions,Reads Mapped Confidently to Intronic Regions,Reads Mapped Confidently to Intergenic Regions,Reads Mapped Antisense to Gene,Sequencing Saturation,Q30 Bases in Barcode,Q30 Bases in RNA Read,Q30 Bases in Sample Index,Q30 Bases in UMI,Fraction Reads in Cells,Total Genes Detected,Median UMI Counts per Cell
"2,272","107,875","1,282","245,093,084",98.3%,69.6%,71.9%,6.1%,3.2%,4.4%,51.3%,98.5%,79.2%,93.6%,98.5%,12.0%,"16,437","2,934"
"""

ATAC_SUMMARY = """annotated_cells,bc_q30_bases_fract,cellranger-atac_version,cells_detected,frac_cut_fragments_in_peaks,frac_fragments_nfr,frac_fragments_nfr_or_nuc,frac_fragments_nuc,frac_fragments_overlapping_peaks,frac_fragments_overlapping_targets,frac_mapped_confidently,frac_waste_chimeric,frac_waste_duplicate,frac_waste_lowmapq,frac_waste_mitochondrial,frac_waste_no_barcode,frac_waste_non_cell_barcode,frac_waste_overall_nondup,frac_waste_total,frac_waste_unmapped,median_fragments_per_cell,median_per_cell_unique_fragments_at_30000_RRPC,median_per_cell_unique_fragments_at_50000_RRPC,num_fragments,r1_q30_bases_fract,r2_q30_bases_fract,si_q30_bases_fract,total_usable_fragments,tss_enrichment_score
5682,0.925226023701,1.0.1,6748,0.512279447992,0.392368676637,0.851506103882,0.459137427245,0.556428090013,0.575082094792,0.534945791083,0.00123066129161,0.160515305655,0.0892973647982,0.00899493352094,0.352907229061,0.0135851297269,0.471714266123,0.632229571777,0.00569894772443,16119.5,5769.94794925,8809.29425158,366582587,0.947387774999,0.941378123188,0.962708567847,134818235,6.91438390781
"""
