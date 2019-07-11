#######################################################################
# Tests for metadata.py module
#######################################################################

import unittest
import os
import tempfile
import pickle
import cloudpickle
from auto_process_ngs.metadata import *

class TestMetadataDict(unittest.TestCase):
    """Tests for the MetadataDict class
    """

    def setUp(self):
        self.metadata_file = None

    def tearDown(self):
        if self.metadata_file is not None:
            os.remove(self.metadata_file)

    def test_create_metadata_object(self):
        """Check creation of a metadata object
        """
        metadata = MetadataDict(attributes={'salutation':'Salutation',
                                            'valediction': 'Valediction'})
        self.assertEqual(metadata.salutation,None)
        self.assertEqual(metadata.valediction,None)

    def test_set_and_get(self):
        """Check metadata values can be stored and retrieved
        """
        metadata = MetadataDict(attributes={'salutation':'Salutation',
                                            'valediction': 'Valediction'})
        metadata['salutation'] = "hello"
        metadata['valediction'] = "goodbye"
        self.assertEqual(metadata.salutation,"hello")
        self.assertEqual(metadata.valediction,"goodbye")

    def test_save_and_load(self):
        """Check metadata can be saved to file and reloaded
        """
        self.metadata_file = tempfile.mkstemp()[1]
        metadata = MetadataDict(attributes={'salutation':'Salutation',
                                            'valediction': 'Valediction',
                                            'chat': 'Chit chat'})
        metadata['salutation'] = "hello"
        metadata['valediction'] = "goodbye"
        metadata.save(self.metadata_file)
        metadata2 = MetadataDict(attributes={'salutation':'Salutation',
                                             'valediction': 'Valediction',
                                             'chat': 'Chit chat'})
        metadata2.load(self.metadata_file)
        self.assertEqual(metadata2.salutation,"hello")
        self.assertEqual(metadata2.valediction,"goodbye")
        self.assertEqual(metadata2.chat,None)

    def test_get_non_existent_attribute(self):
        """Check that accessing non-existent attribute raises exception
        """
        metadata = MetadataDict(attributes={'salutation':'Salutation',
                                            'valediction': 'Valediction'})
        self.assertRaises(AttributeError,lambda: metadata.conversation)

    def test_specify_key_order(self):
        """Check that specified key ordering is respected
        """
        self.metadata_file = tempfile.mkstemp()[1]
        expected_keys = ('Salutation',
                         'Chit chat',
                         'Valediction',)
        metadata = MetadataDict(attributes={'salutation':'Salutation',
                                            'valediction': 'Valediction',
                                            'chat': 'Chit chat'},
                                order=('salutation','chat','valediction'))
        metadata.save(self.metadata_file)
        fp = open(self.metadata_file,'rU')
        for line,expected_key in zip(fp,expected_keys):
            self.assertEqual(line.split('\t')[0],expected_key)

    def test_implicit_key_order(self):
        """Check that keys are implicitly ordered on output
        """
        self.metadata_file = tempfile.mkstemp()[1]
        metadata = MetadataDict(attributes={'salutation':'Salutation',
                                            'valediction': 'Valediction',
                                            'chat': 'Chit chat'})
        expected_keys = ('Chit chat',
                         'Salutation',
                         'Valediction',)
        metadata.save(self.metadata_file)
        fp = open(self.metadata_file,'rU')
        for line,expected_key in zip(fp,expected_keys):
            self.assertEqual(line.split('\t')[0],expected_key)

    def test_get_null_items(self):
        """Check fetching of items with null values
        """
        metadata = MetadataDict(attributes={'salutation':'.',
                                            'valediction': '.',
                                            'chat': '.'})
        self.assertEqual(metadata.null_items(),['chat',
                                                'salutation',
                                                'valediction'])
        #
        metadata['salutation'] = 'hello'
        metadata['valediction'] = 'ave'
        metadata['chat'] = 'awight'
        self.assertEqual(metadata.null_items(),[])
        #
        metadata['chat'] = None
        self.assertEqual(metadata.null_items(),['chat'])

    def test_undefined_items_in_file(self):
        """Check handling of additional undefined items in file
        """
        # Set up a metadata dictionary
        metadata = MetadataDict(attributes={'salutation':'salutation',
                                            'valediction': 'valediction'})
        # Create a file with an additional item
        self.metadata_file = tempfile.mkstemp()[1]
        contents = ('salutation\thello',
                    'valediction\tgoodbye',
                    'chit_chat\tstuff')
        with open(self.metadata_file,'w') as fp:
            for line in contents:
                fp.write("%s\n" % line)
        # Load into the dictionary and check that all
        # items are present
        metadata.load(self.metadata_file,strict=False)
        self.assertEqual(metadata.salutation,'hello')
        self.assertEqual(metadata.valediction,'goodbye')
        self.assertEqual(metadata.chit_chat,'stuff')

    def test_cloudpickle_metadata(self):
        """Check Metadata object can be serialised with 'cloudpickle'
        """
        # Set up a metadata dictionary
        metadata = MetadataDict(attributes={'chit_chat':'chit_chat',
                                            'salutation':'salutation',
                                            'valediction': 'valediction'})
        metadata['salutation'] = "hello"
        metadata['valediction'] = "goodbye"
        metadata['chit_chat'] = "stuff"
        self.assertEqual(metadata.salutation,'hello')
        self.assertEqual(metadata.valediction,'goodbye')
        self.assertEqual(metadata.chit_chat,'stuff')
        # Pickle it
        pickled = cloudpickle.dumps(metadata)
        # Unpickle it
        unpickled = cloudpickle.loads(pickled)
        self.assertEqual(unpickled.salutation,'hello')
        self.assertEqual(unpickled.valediction,'goodbye')
        self.assertEqual(unpickled.chit_chat,'stuff')

    def test_pickle_metadata(self):
        """Check Metadata object can be serialised with 'pickle'
        """
        # Set up a metadata dictionary
        metadata = MetadataDict(attributes={'chit_chat':'chit_chat',
                                            'salutation':'salutation',
                                            'valediction': 'valediction'})
        metadata['salutation'] = "hello"
        metadata['valediction'] = "goodbye"
        metadata['chit_chat'] = "stuff"
        self.assertEqual(metadata.salutation,'hello')
        self.assertEqual(metadata.valediction,'goodbye')
        self.assertEqual(metadata.chit_chat,'stuff')
        # Pickle it
        pickled = pickle.dumps(metadata)
        # Unpickle it
        unpickled = pickle.loads(pickled)
        self.assertEqual(unpickled.salutation,'hello')
        self.assertEqual(unpickled.valediction,'goodbye')
        self.assertEqual(unpickled.chit_chat,'stuff')

class TestAnalysisDirParameters(unittest.TestCase):
    """Tests for the AnalysisDirParameters class
    """

    def test_create_analysis_dir_parameters(self):
        """Check creation of an empty AnalysisDirParameters object
        """
        params = AnalysisDirParameters()
        self.assertEqual(params.analysis_dir,None)
        self.assertEqual(params.data_dir,None)
        self.assertEqual(params.sample_sheet,None)
        self.assertEqual(params.bases_mask,None)
        self.assertEqual(params.primary_data_dir,None)
        self.assertEqual(params.unaligned_dir,None)
        self.assertEqual(params.project_metadata,None)
        self.assertEqual(params.stats_file,None)

class TestAnalysisDirMetadata(unittest.TestCase):
    """Tests for the AnalysisDirMetadata class
    """

    def test_create_analysis_dir_metadata(self):
        """Check creation of an empty AnalysisDirMetadata object
        """
        metadata = AnalysisDirMetadata()
        self.assertEqual(metadata.run_number,None)
        self.assertEqual(metadata.platform,None)
        self.assertEqual(metadata.source,None)
        self.assertEqual(metadata.assay,None)
        self.assertEqual(metadata.bcl2fastq_software,None)
        self.assertEqual(metadata.cellranger_software,None)

class TestProjectMetadataFile(unittest.TestCase):
    """Tests for the ProjectMetadataFile class
    """

    def setUp(self):
        self.metadata_file = tempfile.mkstemp()[1]
        self.projects = list()
        self.lines = list()

    def tearDown(self):
        if self.metadata_file is not None:
            os.remove(self.metadata_file)

    def test_empty_project_metadata_file(self):
        """Create and save empty ProjectMetadataFile
        """
        # Make an empty 'file'
        metadata = ProjectMetadataFile()
        contents = "#Project\tSamples\tUser\tLibrary\tSC_Platform\tOrganism\tPI\tComments\n"
        self.assertEqual(len(metadata),0)
        for project in metadata:
            self.fail()
        # Save to an actual file and check its contents
        metadata.save(self.metadata_file)
        self.assertEqual(open(self.metadata_file,'r').read(),contents)

    def test_create_new_project_metadata_file(self):
        """Create and save ProjectMetadataFile with content
        """
        # Make new 'file' and add projects
        metadata = ProjectMetadataFile()
        metadata.add_project('Charlie',['C1','C2'],
                             user="Charlie P",
                             library_type="RNA-seq",
                             organism="Yeast",
                             PI="Marley")
        metadata.add_project('Farley',['F3','F4'],
                             user="Farley G",
                             library_type="ChIP-seq",
                             organism="Mouse",
                             PI="Harley",
                             comments="Squeak!")
        contents = "#Project\tSamples\tUser\tLibrary\tSC_Platform\tOrganism\tPI\tComments\nCharlie\tC1,C2\tCharlie P\tRNA-seq\t.\tYeast\tMarley\t.\nFarley\tF3,F4\tFarley G\tChIP-seq\t.\tMouse\tHarley\tSqueak!\n"
        self.assertEqual(len(metadata),2)
        # Save to an actual file and check its contents
        metadata.save(self.metadata_file)
        self.assertEqual(open(self.metadata_file,'r').read(),contents)

    def test_read_existing_project_metadata_file(self):
        """Read contents from existing ProjectMetadataFile
        """
        # Create metadata file independently
        data = list()
        data.append(dict(Project="Charlie",
                         Samples="C1-2",
                         User="Charlie P",
                         Library="RNA-seq",
                         SC_Platform=".",
                         Organism="Yeast",
                         PI="Marley",
                         Comments="."))
        data.append(dict(Project="Farley",
                         Samples="F3-4",
                         User="Farley G",
                         Library="ChIP-seq",
                         SC_Platform=".",
                         Organism="Mouse",
                         PI="Harley",
                         Comments="Squeak!"))
        contents = "#Project\tSamples\tUser\tLibrary\tSC_Platform\tOrganism\tPI\tComments\nCharlie\tC1-2\tCharlie P\tRNA-seq\t.\tYeast\tMarley\t.\nFarley\tF3-4\tFarley G\tChIP-seq\t.\tMouse\tHarley\tSqueak!\n"
        open(self.metadata_file,'w').write(contents)
        # Load and check contents
        metadata = ProjectMetadataFile(self.metadata_file)
        self.assertEqual(len(metadata),2)
        for x,y in zip(data,metadata):
            for attr in ('Project','User','Library','Organism','PI','Comments'):
                self.assertEqual(x[attr],y[attr])

    def test_projects_with_numbers_for_names(self):
        """Handle projects with names that look like numbers
        """
        metadata = ProjectMetadataFile()
        metadata.add_project('1234',['C1','C2'],
                             user="Charlie P",
                             library_type="RNA-seq",
                             organism="Yeast",
                             PI="Marley")
        metadata.add_project('56.78',['F3','F4'],
                             user="Farley G",
                             library_type="ChIP-seq",
                             organism="Mouse",
                             PI="Harley",
                             comments="Squeak!")
        self.assertEqual(metadata[0]['Project'],"1234")
        self.assertEqual(metadata[1]['Project'],"56.78")

    def test_refuse_to_add_duplicate_projects(self):
        """Refuse to add duplicated project names
        """
        # Make new 'file' and add project
        metadata = ProjectMetadataFile()
        metadata.add_project('Charlie',['C1','C2'],
                             user="Charlie P",
                             library_type="RNA-seq",
                             organism="Yeast",
                             PI="Marley")
        # Attempt to add same project name again
        self.assertRaises(Exception,
                          metadata.add_project,'Charlie',['C1','C2'])

    def test_check_if_project_in_metadata(self):
        """Check if project appears in metadata
        """
        # Make new 'file' and add project
        metadata = ProjectMetadataFile()
        metadata.add_project('Charlie',['C1','C2'],
                             user="Charlie P",
                             library_type="RNA-seq",
                             organism="Yeast",
                             PI="Marley")
        # Check for existing project
        self.assertTrue("Charlie" in metadata)
        # Check for non-existent project
        self.assertFalse("Marley" in metadata)

    def test_update_exisiting_project(self):
        """Update the data for an existing project
        """
        # Make new 'file' and add project
        metadata = ProjectMetadataFile()
        metadata.add_project('Charlie',['C1','C2'],
                             user="Charlie P",
                             library_type="scRNA-seq",
                             organism="Yeast",
                             PI="Marley")
        # Check initial data is correct
        self.assertTrue("Charlie" in metadata)
        project = metadata.lookup("Project","Charlie")[0]
        self.assertEqual(project[1],"C1,C2")
        self.assertEqual(project[2],"Charlie P")
        self.assertEqual(project[3],"scRNA-seq")
        self.assertEqual(project[4],".")
        self.assertEqual(project[5],"Yeast")
        self.assertEqual(project[6],"Marley")
        # Update some attributes
        metadata.update_project('Charlie',
                                user="Charlie Percival",
                                library_type="scRNA-seq",
                                sc_platform="ICell8")
        # Check the data has been updated
        self.assertTrue("Charlie" in metadata)
        project = metadata.lookup("Project","Charlie")[0]
        self.assertEqual(project[1],"C1,C2")
        self.assertEqual(project[2],"Charlie Percival")
        self.assertEqual(project[3],"scRNA-seq")
        self.assertEqual(project[4],"ICell8")
        self.assertEqual(project[5],"Yeast")
        self.assertEqual(project[6],"Marley")
        # Update the samples
        metadata.update_project('Charlie',
                                sample_names=['C01','C02'])
        # Check the data has been updated
        self.assertTrue("Charlie" in metadata)
        project = metadata.lookup("Project","Charlie")[0]
        self.assertEqual(project[1],"C01,C02")
        self.assertEqual(project[2],"Charlie Percival")
        self.assertEqual(project[3],"scRNA-seq")
        self.assertEqual(project[4],"ICell8")
        self.assertEqual(project[5],"Yeast")
        self.assertEqual(project[6],"Marley")

class TestAnalysisProjectInfo(unittest.TestCase):
    """Tests for the AnalysisDirMetadata class
    """

    def test_create_analysis_project_info(self):
        """Check creation of an empty AnalysisProjectInfo object
        """
        info = AnalysisProjectInfo()
        self.assertEqual(info.run,None)
        self.assertEqual(info.platform,None)
        self.assertEqual(info.user,None)
        self.assertEqual(info.PI,None)
        self.assertEqual(info.organism,None)
        self.assertEqual(info.library_type,None)
        self.assertEqual(info.single_cell_platform,None)
        self.assertEqual(info.number_of_cells,None)
        self.assertEqual(info.icell8_well_list,None)
        self.assertEqual(info.paired_end,None)
        self.assertEqual(info.primary_fastq_dir,None)
        self.assertEqual(info.samples,None)
        self.assertEqual(info.comments,None)
