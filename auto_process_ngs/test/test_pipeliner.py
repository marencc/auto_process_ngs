#######################################################################
# Tests for pipeliner.py module
#######################################################################

import unittest
import tempfile
import shutil
import time
import os
import io
import getpass
import platform
from builtins import range
import auto_process_ngs.envmod as envmod
from auto_process_ngs.simple_scheduler import SimpleScheduler
from auto_process_ngs.applications import Command
from auto_process_ngs.pipeliner import Pipeline
from auto_process_ngs.pipeliner import PipelineTask
from auto_process_ngs.pipeliner import PipelineFunctionTask
from auto_process_ngs.pipeliner import PipelineCommand
from auto_process_ngs.pipeliner import PipelineCommandWrapper
from auto_process_ngs.pipeliner import PipelineParam
from auto_process_ngs.pipeliner import PipelineFailure
from auto_process_ngs.pipeliner import FileCollector
from auto_process_ngs.pipeliner import Dispatcher
from bcftbx.JobRunner import SimpleJobRunner

# Unit tests

class TestPipeline(unittest.TestCase):

    def setUp(self):
        # Placeholder for scheduler instance
        self.sched = None
        # Make a temporary working dir
        self.working_dir = tempfile.mkdtemp(
            suffix='TestPipeline')

    def _get_scheduler(self):
        # Set up a scheduler
        self.sched = SimpleScheduler(poll_interval=0.01)
        self.sched.start()
        return self.sched

    def tearDown(self):
        # Stop the scheduler
        if self.sched is not None:
            self.sched.stop()
        # Remove temp dir
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)

    def test_simple_pipeline(self):
        """
        Pipeline: define and run a simple pipeline
        """
        # Define a reusable task
        # Appends item to a list
        class Append(PipelineTask):
            def init(self,l,s):
                self.add_output('list',list())
            def setup(self):
                for item in self.args.l:
                    self.output.list.append(item)
                self.output.list.append(self.args.s)
        # Build the pipeline
        ppl = Pipeline()
        task1 = Append("Append 1",(),"item1")
        task2 = Append("Append 2",task1.output.list,"item2")
        ppl.add_task(task2,requires=(task1,))
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1)
        # Check the outputs
        self.assertEqual(exit_status,0)
        self.assertEqual(task1.output.list,["item1"])
        self.assertEqual(task2.output.list,["item1","item2"])

    def test_pipeline_with_commands(self):
        """
        Pipeline: define and run pipeline with commands
        """
        # Define a task
        # Echoes/appends text to a file
        class Echo(PipelineTask):
            def init(self,f,s):
                self.add_output('file',f)
            def setup(self):
                self.add_cmd(
                    PipelineCommandWrapper(
                        "Echo text to file",
                        "echo",self.args.s,
                        ">>",self.args.f))
        # Build the pipeline
        ppl = Pipeline()
        task1 = Echo("Write item1","out.txt","item1")
        task2 = Echo("Write item2",task1.output.file,"item2")
        ppl.add_task(task2,requires=(task1,))
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1)
        # Check the outputs
        self.assertEqual(exit_status,0)
        out_file = os.path.join(self.working_dir,"out.txt")
        self.assertTrue(os.path.exists(out_file))
        self.assertEqual(open(out_file,'r').read(),
                         "item1\nitem2\n")

    def test_pipeline_with_multiple_commands(self):
        """
        Pipeline: define and run pipeline with multiple commands
        """
        # Define a task
        # Echoes/appends text to a file
        class EchoMany(PipelineTask):
            def init(self,*s):
                self.add_output('files',list())
            def setup(self):
                for f,s in self.args.s:
                    self.add_cmd(
                        PipelineCommandWrapper(
                            "Echo text to file",
                            "echo",s,
                            ">>",f))
            def finish(self):
                for f,s in self.args.s:
                    self.output.files.append(f)
        # Build the pipeline
        ppl = Pipeline()
        task = EchoMany("Write items",
                        ("out1.txt","item"),
                        ("out2.txt","item"),)
        ppl.add_task(task)
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1)
        # Check the outputs
        self.assertEqual(exit_status,0)
        out_files = [os.path.join(self.working_dir,f)
                     for f in ("out1.txt","out2.txt")]
        for out_file in out_files:
            self.assertTrue(os.path.exists(out_file))
            self.assertEqual(open(out_file,'r').read(),
                             "item\n")

    def test_pipeline_with_batched_commands(self):
        """
        Pipeline: define and run pipeline with batched commands
        """
        # Define a task
        # Echoes/appends text to a file
        class EchoMany(PipelineTask):
            def init(self,*s):
                self.add_output('files',list())
            def setup(self):
                for f,s in self.args.s:
                    self.add_cmd(
                        PipelineCommandWrapper(
                            "Echo text to file",
                            "echo",s,
                            ">>",f))
            def finish(self):
                for f,s in self.args.s:
                    self.output.files.append(f)
        # Build the pipeline
        ppl = Pipeline()
        task = EchoMany("Write items",
                        ("out1.txt","item"),
                        ("out2.txt","item"),)
        ppl.add_task(task)
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1,
                              batch_size=2)
        # Check the outputs
        self.assertEqual(exit_status,0)
        out_files = [os.path.join(self.working_dir,f)
                     for f in ("out1.txt","out2.txt")]
        for out_file in out_files:
            self.assertTrue(os.path.exists(out_file))
            self.assertEqual(open(out_file,'r').read(),
                             "item\n")

    def test_pipeline_sets_pipelineparam_as_task_input(self):
        """
        Pipeline: handle PipelineParam passed as task input
        """
        # Define a task
        # Echoes/appends text to a file
        class Echo(PipelineTask):
            def init(self,f,s):
                self.add_output('file',f)
            def setup(self):
                self.add_cmd(
                    PipelineCommandWrapper(
                        "Echo text to file",
                        "echo",self.args.s,
                        ">>",self.args.f))
        # Create a pipeline param instance
        s = PipelineParam("hello")
        self.assertEqual(s.value,"hello")
        # Build the pipeline
        ppl = Pipeline()
        task = Echo("Write item1","out.txt",s)
        ppl.add_task(task)
        # Update the pipeline param
        s.set("goodbye")
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1)
        # Check the outputs
        self.assertEqual(exit_status,0)
        out_file = os.path.join(self.working_dir,"out.txt")
        self.assertTrue(os.path.exists(out_file))
        self.assertEqual(open(out_file,'r').read(),"goodbye\n")

    def test_pipeline_with_external_scheduler(self):
        """
        Pipeline: run pipeline using user-defined scheduler
        """
        # Define a task
        # Echoes/appends text to a file
        class Echo(PipelineTask):
            def init(self,f,s):
                self.add_output('file',f)
            def setup(self):
                self.add_cmd(
                    PipelineCommandWrapper(
                        "Echo text to file",
                        "echo",self.args.s,
                        ">>",self.args.f))
        # Build the pipeline
        ppl = Pipeline()
        task1 = Echo("Write item1","out.txt","item1")
        task2 = Echo("Write item2",task1.output.file,"item2")
        ppl.add_task(task2,requires=(task1,))
        # Get a scheduler
        self._get_scheduler()
        # Run the pipeline
        exit_status = ppl.run(sched=self.sched,
                              working_dir=self.working_dir,
                              poll_interval=0.1)
        # Check the outputs
        self.assertEqual(exit_status,0)
        out_file = os.path.join(self.working_dir,"out.txt")
        self.assertTrue(os.path.exists(out_file))
        self.assertEqual(open(out_file,'r').read(),
                         "item1\nitem2\n")

    def test_pipeline_working_dir_is_respected(self):
        """
        Pipeline: check pipeline respects the working directory
        """
        # Define tasks
        # Echoes/appends text to a file via shell command
        class Echo(PipelineTask):
            def init(self,f,s):
                self.add_output('file',f)
            def setup(self):
                self.add_cmd(
                    PipelineCommandWrapper(
                        "Echo text to file",
                        "echo",self.args.s,
                        ">>",self.args.f))
        # Writes text to a file via Python
        class Print(PipelineTask):
            def init(self,f,s):
                self.add_output('file',f)
            def setup(self):
                with open(self.args.f,'a') as fp:
                    fp.write("%s\n" % self.args.s)
        # Build the pipeline
        ppl = Pipeline()
        task1 = Echo("Echo item1","out.txt","item1")
        task2 = Print("Print item2",task1.output.file,"item2")
        ppl.add_task(task2,requires=(task1,))
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1)
        # Check the outputs
        self.assertEqual(exit_status,0)
        out_file = os.path.join(self.working_dir,"out.txt")
        self.assertTrue(os.path.exists(out_file))
        self.assertEqual(open(out_file,'r').read(),
                         "item1\nitem2\n")

    def test_pipeline_stops_on_task_failure(self):
        """
        Pipeline: immediate exit on task failure in 'immediate' mode
        """
        # Define a reusable task
        # Appends item to a list
        class Append(PipelineTask):
            def init(self,l,s):
                self.add_output('list',list())
            def setup(self):
                for item in self.args.l:
                    self.output.list.append(item)
                self.output.list.append(self.args.s)
        # Define a version of the 'append' task that
        # always fails
        class Failure(Append):
            def setup(self):
                self.fail(message="Automatic fail")
        # Build a failing pipeline
        ppl = Pipeline()
        task1 = Append("Append 1",(),"1")
        task2 = Append("Append 2",(),"2")
        task3 = Failure("Failing append 3",(),"3")
        task2_1 = Append("Append 2_1",task2.output.list,"2_1")
        task2_2 = Append("Append 2_2",task2_1.output.list,"2_2")
        task3_1 = Append("Append 3_1",task3.output.list,"3_1")
        task3_2 = Append("Append 3_2",task3_1.output.list,"3_2")
        ppl.add_task(task2,requires=(task1,))
        ppl.add_task(task2_1,requires=(task2,))
        ppl.add_task(task2_2,requires=(task2_1,))
        ppl.add_task(task3,requires=(task1,))
        ppl.add_task(task3_1,requires=(task3,))
        ppl.add_task(task3_2,requires=(task3_1,))
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1,
                              exit_on_failure=PipelineFailure.IMMEDIATE)
        # Check the outputs
        self.assertEqual(exit_status,1)
        self.assertEqual(task1.output.list,["1"])
        self.assertEqual(task2.output.list,["2"])
        self.assertEqual(task2_1.output.list,[])
        self.assertEqual(task2_2.output.list,[])
        self.assertEqual(task3_1.output.list,[])
        self.assertEqual(task3_2.output.list,[])
        # Check the exit codes
        self.assertEqual(task1.exit_code,0)
        self.assertEqual(task2.exit_code,0)
        self.assertEqual(task3.exit_code,1)
        self.assertEqual(task2_1.exit_code,None)
        self.assertEqual(task2_2.exit_code,None)
        self.assertEqual(task3_1.exit_code,None)
        self.assertEqual(task3_2.exit_code,None)
        self.assertEqual(exit_status,1)

    def test_pipeline_defers_task_failure(self):
        """
        Pipeline: deferred exit on task failure in 'deferred' mode
        """
        # Define a reusable task
        # Appends item to a list
        class Append(PipelineTask):
            def init(self,l,s):
                self.add_output('list',list())
            def setup(self):
                for item in self.args.l:
                    self.output.list.append(item)
                self.output.list.append(self.args.s)
        # Define a version of the 'append' task that
        # always fails
        class Failure(Append):
            def setup(self):
                self.fail(message="Automatic fail")
        # Build a failing pipeline
        ppl = Pipeline()
        task1 = Append("Append 1",(),"1")
        task2 = Append("Append 2",(),"2")
        task3 = Failure("Failing append 3",(),"3")
        task2_1 = Append("Append 2_1",task2.output.list,"2_1")
        task2_2 = Append("Append 2_2",task2_1.output.list,"2_2")
        task3_1 = Append("Append 3_1",task3.output.list,"3_1")
        task3_2 = Append("Append 3_2",task3_1.output.list,"3_2")
        ppl.add_task(task2,requires=(task1,))
        ppl.add_task(task2_1,requires=(task2,))
        ppl.add_task(task2_2,requires=(task2_1,))
        ppl.add_task(task3,requires=(task1,))
        ppl.add_task(task3_1,requires=(task3,))
        ppl.add_task(task3_2,requires=(task3_1,))
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1,
                              exit_on_failure=PipelineFailure.DEFERRED)
        # Check the outputs
        self.assertEqual(exit_status,1)
        self.assertEqual(task1.output.list,["1"])
        self.assertEqual(task2.output.list,["2"])
        self.assertEqual(task2_1.output.list,["2","2_1"])
        self.assertEqual(task2_2.output.list,["2","2_1","2_2"])
        self.assertEqual(task3_1.output.list,[])
        self.assertEqual(task3_2.output.list,[])
        # Check the exit codes
        self.assertEqual(task1.exit_code,0)
        self.assertEqual(task2.exit_code,0)
        self.assertEqual(task3.exit_code,1)
        self.assertEqual(task2_1.exit_code,0)
        self.assertEqual(task2_2.exit_code,0)
        self.assertEqual(task3_1.exit_code,None)
        self.assertEqual(task3_2.exit_code,None)

    def test_pipeline_built_in_parameters(self):
        """
        Pipeline: test the built-in parameters are set
        """
        # Define a task to output values passed in
        class OutputValues(PipelineTask):
            def init(self,working_dir,batch_size,verbose):
                self.add_output('builtins',dict())
            def setup(self):
                self.output.builtins['working_dir'] = self.args.working_dir
                self.output.builtins['batch_size'] = self.args.batch_size
                self.output.builtins['verbose'] = self.args.verbose
        # Make a pipeline
        ppl = Pipeline()
        task = OutputValues("Output the built-in parameter values",
                            working_dir=ppl.params.WORKING_DIR,
                            batch_size=ppl.params.BATCH_SIZE,
                            verbose=ppl.params.VERBOSE)
        ppl.add_task(task)
        self.assertTrue("WORKING_DIR" in ppl.params)
        self.assertTrue("BATCH_SIZE" in ppl.params)
        self.assertTrue("VERBOSE" in ppl.params)
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              batch_size=100,
                              verbose=True)
        self.assertEqual(task.output.builtins['working_dir'],
                         self.working_dir)
        self.assertEqual(task.output.builtins['batch_size'],100)
        self.assertEqual(task.output.builtins['verbose'],True)

    def test_pipeline_add_param(self):
        """
        Pipeline: test the 'add_param' method
        """
        # Make an empty pipeline
        ppl = Pipeline()
        # Add a parameter
        self.assertFalse('ncores' in ppl.params)
        ppl.add_param('ncores',value=1,type=int)
        self.assertTrue('ncores' in ppl.params)
        self.assertTrue(isinstance(ppl.params.ncores,
                                   PipelineParam))
        self.assertEqual(ppl.params.ncores.value,1)

    def test_pipeline_add_param_twice_raises_exception(self):
        """
        Pipeline: 'add_param' raises exception when parameter is added twice
        """
        # Make an empty pipeline
        ppl = Pipeline()
        # Add a parameter
        self.assertFalse('ncores' in ppl.params)
        ppl.add_param('ncores',value=1,type=int)
        self.assertTrue('ncores' in ppl.params)
        self.assertRaises(KeyError,
                          ppl.add_param,
                          'ncores')

    def test_pipeline_param_passed_at_runtime(self):
        """
        Pipeline: check parameter is passed at runtime
        """
        # Define task to echoes/append text to a file
        class Echo(PipelineTask):
            def init(self,f,s):
                self.add_output('file',f)
            def setup(self):
                self.add_cmd(
                    PipelineCommandWrapper(
                        "Echo text to file",
                        "echo",self.args.s,
                        ">>",self.args.f))
        # Build the pipeline with a parameter
        ppl = Pipeline()
        ppl.add_param('out_file')
        task1 = Echo("Echo item1",
                     f=ppl.params.out_file,
                     s="item1")
        task2 = Echo("Echo item2",
                     f=ppl.params.out_file,
                     s="item2")
        ppl.add_task(task2,requires=(task1,))
        # Check the parameter before setting a value
        self.assertEqual(ppl.params.out_file.value,None)
        # Run the pipeline setting the output file
        out_file = os.path.join(self.working_dir,"out.txt")
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1,
                              params={ 'out_file': out_file, })
        # Check the outputs
        self.assertEqual(exit_status,0)
        self.assertTrue(os.path.exists(out_file))
        self.assertEqual(open(out_file,'r').read(),
                         "item1\nitem2\n")

    def test_pipeline_add_runner(self):
        """
        Pipeline: test the 'add_runner' method
        """
        # Make an empty pipeline
        ppl = Pipeline()
        # Add a runner definition
        self.assertFalse('test_runner' in ppl.runners)
        ppl.add_runner('test_runner')
        print(ppl.runners)
        self.assertTrue('test_runner' in ppl.runners)
        self.assertTrue(isinstance(ppl.runners['test_runner'],
                                   PipelineParam))
        self.assertTrue(isinstance(ppl.runners['test_runner'].value,
                                   SimpleJobRunner))

    def test_pipeline_add_runner_twice_raises_exception(self):
        """
        Pipeline: 'add_runner' raises exception when runner is added twice
        """
        # Make an empty pipeline
        ppl = Pipeline()
        # Add a runner definition
        self.assertFalse('test_runner' in ppl.runners)
        ppl.add_runner('test_runner')
        self.assertTrue('test_runner' in ppl.runners)
        self.assertRaises(KeyError,
                          ppl.add_runner,
                          'test_runner')

    def test_pipeline_runner_passed_at_runtime(self):
        """
        Pipeline: check runner is passed at runtime
        """
        # Define task to echoes/append text to a file
        class Echo(PipelineTask):
            def init(self,f,s):
                self.add_output('file',f)
            def setup(self):
                self.add_cmd(
                    PipelineCommandWrapper(
                        "Echo text to file",
                        "echo",self.args.s,
                        ">>",self.args.f))
        # Define custom runner for testing
        class TestJobRunner(SimpleJobRunner):
            def __init__(self,*args,**kws):
                SimpleJobRunner.__init__(self,*args,**kws)
        # Build the pipeline
        out_file = os.path.join(self.working_dir,"out.txt")
        ppl = Pipeline()
        ppl.add_runner("test_runner")
        task1 = Echo("Echo item1",
                     f=out_file,
                     s="item1")
        ppl.add_task(task1,
                     runner=ppl.runners["test_runner"])
        # Run the pipeline setting the runner
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1,
                              runners={ 'test_runner':
                                        TestJobRunner(), })
        # Check the outputs
        self.assertEqual(exit_status,0)
        self.assertTrue(os.path.exists(out_file))
        self.assertEqual(open(out_file,'r').read(),"item1\n")

    def test_pipeline_runner_set_default_runner_at_runtime(self):
        """
        Pipeline: check setting default runner at runtime
        """
        # Define task to echoes/append text to a file
        class Echo(PipelineTask):
            def init(self,f,s):
                self.add_output('file',f)
            def setup(self):
                self.add_cmd(
                    PipelineCommandWrapper(
                        "Echo text to file",
                        "echo",self.args.s,
                        ">>",self.args.f))
        # Define custom runners for testing
        class DefaultJobRunner(SimpleJobRunner):
            def __init__(self,*args,**kws):
                SimpleJobRunner.__init__(self,*args,**kws)
        class TestJobRunner(SimpleJobRunner):
            def __init__(self,*args,**kws):
                SimpleJobRunner.__init__(self,*args,**kws)
        # Build the pipeline
        out_file = os.path.join(self.working_dir,"out.txt")
        ppl = Pipeline()
        ppl.add_runner("test_runner1")
        ppl.add_runner("test_runner2")
        task1 = Echo("Echo item1",
                     f=out_file,
                     s="item1")
        task2 = Echo("Echo item2",
                     f=out_file,
                     s="item2")
        ppl.add_task(task1,
                     runner=ppl.runners["test_runner1"])
        ppl.add_task(task2,
                     requires=(task1,),
                     runner=ppl.runners["test_runner2"])
        # Run the pipeline setting the default runner
        # and only one of the two runners
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1,
                              default_runner=DefaultJobRunner(),
                              runners={ 'test_runner1':
                                        TestJobRunner(), })
        # Check the outputs
        self.assertEqual(exit_status,0)
        self.assertTrue(os.path.exists(out_file))
        self.assertEqual(open(out_file,'r').read(),"item1\nitem2\n")

    @unittest.skipIf(not envmod.__ENVMODULES__,
                     "Environment modules not available")
    def test_pipeline_with_envmodules(self):
        """
        Pipeline: define and run pipeline with environment modules
        """
        # Set up mock Fastqc
        bin_dir = os.path.join(self.working_dir,"apps","bin")
        os.mkdir(os.path.join(self.working_dir,"apps"))
        os.mkdir(bin_dir)
        with io.open(os.path.join(bin_dir,"fastqc"),'wt') as fp:
            fp.write(u"""#!/bin/bash
echo $1
exit 0
""")
        os.chmod(os.path.join(bin_dir,"fastqc"),0o775)
        # Set up mock environment module
        modules_dir = os.path.join(self.working_dir,"modulefiles")
        os.mkdir(modules_dir)
        modules = "apps/fastqc/1.0"
        os.mkdir(os.path.join(modules_dir,"apps"))
        os.mkdir(os.path.join(modules_dir,"apps","fastqc"))
        with io.open(os.path.join(modules_dir,"apps","fastqc","1.0"),'wt') \
             as fp:
            fp.write(u"""#%%Module1.0
prepend-path PATH %s
""" % bin_dir)
        os.environ['MODULEPATH'] = modules_dir
        # Define a task
        class RunFastqc(PipelineTask):
            def init(self,*files):
                self.add_output('files',list())
            def setup(self):
                for f in self.args.files:
                    self.add_cmd(
                        PipelineCommandWrapper(
                            "Run fastqc for %s" % f,
                            "fastqc",f))
            def finish(self):
                for f in self.args.files:
                    self.output.files.append(f)
        # Build the pipeline
        ppl = Pipeline()
        ppl.add_envmodules("fastqc")
        task = RunFastqc("Run Fastqc",
                         "sample1.fastq","sample2.fastq")
        ppl.add_task(task,
                     envmodules=ppl.envmodules["fastqc"])
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              envmodules={
                                  'fastqc': modules,
                              },
                              poll_interval=0.1,
                              verbose=True)
        # Check the outputs
        self.assertEqual(exit_status,0)

    @unittest.skipIf(not envmod.__ENVMODULES__,
                     "Environment modules not available")
    def test_pipeline_fails_with_missing_modules_environment(self):
        """
        Pipeline: check pipeline fails for missing 'modules' environment
        """
        # Missing module file
        modules = "apps/fastqc/1.0"
        # Define a task
        class RunFastqc(PipelineTask):
            def init(self,*files):
                self.add_output('files',list())
            def setup(self):
                for f in self.args.files:
                    self.add_cmd(
                        PipelineCommandWrapper(
                            "Run fastqc for %s" % f,
                            "fastqc",f))
            def finish(self):
                for f in self.args.files:
                    self.output.files.append(f)
        # Build the pipeline
        ppl = Pipeline()
        ppl.add_envmodules("fastqc")
        task = RunFastqc("Run Fastqc",
                         "sample1.fastq","sample2.fastq")
        ppl.add_task(task,
                     envmodules=ppl.envmodules["fastqc"])
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              envmodules={
                                  'fastqc': modules,
                              },
                              poll_interval=0.1,
                              verbose=True)
        # Check the pipeline failed (non-zero exit)
        self.assertNotEqual(exit_status,0)

    @unittest.skipIf(not envmod.__ENVMODULES__,
                     "Environment modules not available")
    def test_pipeline_add_envmodules_twice_raises_exception(self):
        """
        Pipeline: 'add_envmodules' raises exception when environment is added twice
        """
        # Make an empty pipeline
        ppl = Pipeline()
        # Add a environment definition
        self.assertFalse('test_env' in ppl.envmodules)
        ppl.add_envmodules('test_env')
        self.assertTrue('test_env' in ppl.envmodules)
        self.assertRaises(KeyError,
                          ppl.add_envmodules,
                          'test_env')

    def test_pipeline_define_outputs(self):
        """
        Pipeline: test defining pipeline outputs
        """
        # Define a reusable task
        # Appends item to a string
        class AppendString(PipelineTask):
            def init(self,s1,s2):
                self.add_output('string',PipelineParam(type=str))
            def setup(self):
                self.output.string.set(str(self.args.s1) + str(self.args.s2))
        # Build the pipeline
        ppl = Pipeline()
        task1 = AppendString("Append 1","This ","is ")
        task2 = AppendString("Append 2",task1.output.string,"the full string")
        ppl.add_task(task2,requires=(task1,))
        # Define outputs
        ppl.add_output('result',task2.output.string)
        # Run the pipeline
        exit_status = ppl.run(working_dir=self.working_dir,
                              poll_interval=0.1)
        # Check the outputs
        self.assertEqual(exit_status,0)
        self.assertTrue(isinstance(task1.output.string,PipelineParam))
        self.assertEqual(task1.output.string.value,"This is ")
        self.assertTrue(isinstance(task2.output.string,PipelineParam))
        self.assertEqual(task2.output.string.value,"This is the full string")
        self.assertEqual(ppl.output.result,"This is the full string")

    def test_pipeline_dont_finalize_outputs(self):
        """
        Pipeline: test not finalizing pipeline outputs
        """
        # Define a reusable task
        # Appends item to a string
        class AppendString(PipelineTask):
            def init(self,s1,s2):
                self.add_output('string',PipelineParam(type=str))
            def setup(self):
                self.output.string.set(str(self.args.s1) + str(self.args.s2))
        # Build the pipeline
        ppl = Pipeline()
        task1 = AppendString("Append 1","This ","is ")
        task2 = AppendString("Append 2",task1.output.string,"the full string")
        ppl.add_task(task2,requires=(task1,))
        # Define outputs
        ppl.add_output('result',task2.output.string)
        # Run the pipeline with output finalization turned off
        exit_status = ppl.run(finalize_outputs=False,
                              working_dir=self.working_dir,
                              poll_interval=0.1)
        # Check the outputs
        self.assertEqual(exit_status,0)
        self.assertTrue(isinstance(task1.output.string,PipelineParam))
        self.assertEqual(task1.output.string.value,"This is ")
        self.assertTrue(isinstance(task2.output.string,PipelineParam))
        self.assertEqual(task2.output.string.value,"This is the full string")
        self.assertTrue(isinstance(ppl.output.result,PipelineParam))
        self.assertEqual(ppl.output.result.value,"This is the full string")

    def test_pipeline_method_task_list(self):
        """
        Pipeline: test the 'task_list' method
        """
        # Define a reusable task
        # Appends item to a list
        class Append(PipelineTask):
            def init(self,l,s):
                self.add_output('list',list())
            def setup(self):
                for item in self.args.l:
                    self.output.list.append(item)
                self.output.list.append(self.args.s)
        # Make an empty pipeline
        ppl = Pipeline()
        self.assertEqual(ppl.task_list(),[])
        # Add a task
        task1 = Append("Append 1",(),"item1")
        task2 = Append("Append 2",task1.output.list,"item2")
        ppl.add_task(task2,requires=(task1,))
        # Check the task list
        task_list = ppl.task_list()
        self.assertEqual(len(task_list),2)
        self.assertTrue(task1.id() in task_list)
        self.assertTrue(task2.id() in task_list)

    def test_pipeline_method_get_task(self):
        """
        Pipeline: test the 'get_task' method
        """
        # Define a reusable task
        # Appends item to a list
        class Append(PipelineTask):
            def init(self,l,s):
                self.add_output('list',list())
            def setup(self):
                for item in self.args.l:
                    self.output.list.append(item)
                self.output.list.append(self.args.s)
        # Make a pipeline
        ppl = Pipeline()
        task1 = Append("Append 1",(),"item1")
        task2 = Append("Append 2",task1.output.list,"item2")
        ppl.add_task(task2,requires=(task1,))
        # Fetch task data
        task1_data = ppl.get_task(task1.id())
        self.assertEqual(task1_data[0],task1)
        self.assertEqual(task1_data[1],())
        self.assertEqual(task1_data[2],{})
        task2_data = ppl.get_task(task2.id())
        self.assertEqual(task2_data[0],task2)
        self.assertEqual(task2_data[1],(task1,))
        self.assertEqual(task2_data[2],{})

    def test_pipeline_method_rank_tasks(self):
        """
        Pipeline: test the 'rank_tasks' method
        """
        # Define a reusable task
        # Appends item to a list
        class Append(PipelineTask):
            def init(self,l,s):
                self.add_output('list',list())
            def setup(self):
                for item in self.args.l:
                    self.output.list.append(item)
                self.output.list.append(self.args.s)
        # Make a pipeline
        ppl = Pipeline()
        task1 = Append("Append 1",(),"item1")
        task2 = Append("Append 2",task1.output.list,"item2")
        task3 = Append("Append 3",task1.output.list,"item3")
        task4 = Append("Append 4",task3.output.list,"item4")
        ppl.add_task(task2,requires=(task1,))
        ppl.add_task(task3,requires=(task1,))
        ppl.add_task(task4,requires=(task3,))
        # Rank the tasks
        ranked_tasks = ppl.rank_tasks()
        # Should be 3 ranks
        self.assertEqual(len(ranked_tasks),3)
        # Check the ranks
        self.assertEqual(ranked_tasks[0],[task1.id()])
        self.assertEqual(sorted(ranked_tasks[1]),
                         sorted([task2.id(),task3.id()]))
        self.assertEqual(ranked_tasks[2],[task4.id()])

    def test_pipeline_method_get_dependent_tasks(self):
        """
        Pipeline: test the 'get_dependent_tasks' method
        """
        # Define a reusable task
        # Appends item to a list
        class Append(PipelineTask):
            def init(self,l,s):
                self.add_output('list',list())
            def setup(self):
                for item in self.args.l:
                    self.output.list.append(item)
                self.output.list.append(self.args.s)
        # Make a pipeline
        ppl = Pipeline()
        task1 = Append("Append 1",(),"item1")
        task2 = Append("Append 2",task1.output.list,"item2")
        task3 = Append("Append 3",task1.output.list,"item3")
        task4 = Append("Append 4",task3.output.list,"item4")
        ppl.add_task(task2,requires=(task1,))
        ppl.add_task(task3,requires=(task1,))
        ppl.add_task(task4,requires=(task3,))
        # Check the dependent tasks
        self.assertEqual(sorted(ppl.get_dependent_tasks(task1.id())),
                         sorted([task2.id(),task3.id(),task4.id()]))
        self.assertEqual(ppl.get_dependent_tasks(task2.id()),[])
        self.assertEqual(ppl.get_dependent_tasks(task3.id()),[task4.id()])
        self.assertEqual(ppl.get_dependent_tasks(task4.id()),[])

    def test_pipeline_append_pipeline(self):
        """
        Pipeline: append one pipeline to another
        """
        # Define a reusable task
        # Appends item to a list
        class Append(PipelineTask):
            def init(self,l,s):
                self.add_output('list',list())
            def setup(self):
                for item in self.args.l:
                    self.output.list.append(item)
                self.output.list.append(self.args.s)
        # Make first pipeline
        ppl1 = Pipeline()
        ppl1.add_param("param1")
        ppl1.add_runner("runner1")
        task1 = Append("Append 1",(),"item1")
        task2 = Append("Append 2",task1.output.list,"item2")
        task3 = Append("Append 3",task1.output.list,"item3")
        task4 = Append("Append 4",task3.output.list,"item4")
        ppl1.add_task(task2,requires=(task1,))
        ppl1.add_task(task3,requires=(task1,))
        ppl1.add_task(task4,requires=(task3,))
        self.assertEqual(len(ppl1.task_list()),4)
        # Make second pipeline
        ppl2 = Pipeline()
        ppl2.add_param("param2")
        ppl2.add_runner("runner2")
        task5 = Append("Append 5",task1.output.list,"item5")
        task6 = Append("Append 6",task3.output.list,"item6")
        task7 = Append("Append 7",task3.output.list,"item7")
        ppl2.add_task(task6,requires=(task5,))
        ppl2.add_task(task7,requires=(task6,))
        self.assertEqual(len(ppl2.task_list()),3)
        # Append second pipeline to the first
        ppl1.append_pipeline(ppl2)
        self.assertEqual(len(ppl1.task_list()),7)
        # Check requirements on first task of pipeline 2
        # have been updated
        self.assertEqual(
            sorted(ppl1.get_task(task5.id())[1],key=lambda t: t.id()),
            sorted([task2,task4,],key=lambda t: t.id())
        )
        # Check params from both pipelines are defined
        self.assertTrue('param1' in ppl1.params)
        self.assertTrue('param2' in ppl1.params)
        # Check runners from both pipelines are defined
        self.assertTrue('runner1' in ppl1.runners)
        self.assertTrue('runner2' in ppl1.runners)

    def test_pipeline_merge_pipeline(self):
        """
        Pipeline: merge one pipeline into another
        """
        # Define a reusable task
        # Appends item to a list
        class Append(PipelineTask):
            def init(self,l,s):
                self.add_output('list',list())
            def setup(self):
                for item in self.args.l:
                    self.output.list.append(item)
                self.output.list.append(self.args.s)
        # Make first pipeline
        ppl1 = Pipeline()
        ppl1.add_param("param1")
        ppl1.add_runner("runner1")
        task1 = Append("Append 1",(),"item1")
        task2 = Append("Append 2",task1.output.list,"item2")
        task3 = Append("Append 3",task1.output.list,"item3")
        task4 = Append("Append 4",task3.output.list,"item4")
        ppl1.add_task(task2,requires=(task1,))
        ppl1.add_task(task3,requires=(task1,))
        ppl1.add_task(task4,requires=(task3,))
        self.assertEqual(len(ppl1.task_list()),4)
        # Make second pipeline
        ppl2 = Pipeline()
        ppl2.add_param("param2")
        ppl2.add_runner("runner2")
        task5 = Append("Append 5",task1.output.list,"item5")
        task6 = Append("Append 6",task3.output.list,"item6")
        task7 = Append("Append 7",task3.output.list,"item7")
        ppl2.add_task(task6,requires=(task5,))
        ppl2.add_task(task7,requires=(task6,))
        self.assertEqual(len(ppl2.task_list()),3)
        # Merge second pipeline into the first
        ppl1.merge_pipeline(ppl2)
        self.assertEqual(len(ppl1.task_list()),7)
        # Check params from both pipelines are defined
        self.assertTrue('param1' in ppl1.params)
        self.assertTrue('param2' in ppl1.params)
        # Check runners from both pipelines are defined
        self.assertTrue('runner1' in ppl1.runners)
        self.assertTrue('runner2' in ppl1.runners)

class TestPipelineTask(unittest.TestCase):

    def setUp(self):
        # Set up a scheduler
        self.sched = SimpleScheduler(poll_interval=0.01)
        self.sched.start()
        # Make a temporary working dir
        self.working_dir = tempfile.mkdtemp(
            suffix='TestPipeline')

    def tearDown(self):
        # Stop the scheduler
        if self.sched is not None:
            self.sched.stop()
        # Remove temp dir
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)

    def _user(self):
        # Internal function to determine user
        return getpass.getuser()

    def _hostname(self):
        # Internal function to determine hostname
        try:
            return os.environ['HOSTNAME']
        except KeyError:
            # HOSTNAME not defined in the
            # environment, try 'platform'
            # module instead
            return platform.node()

    def test_pipelinetask_invocations(self):
        """
        PipelineTask: check task methods are invoked
        """
        # Define a simplistic task which does nothing
        class CheckInvocations(PipelineTask):
            def init(self):
                self.add_output('invocations',list())
                self.output.invocations.append("init")
            def setup(self):
                self.output.invocations.append("setup")
            def finish(self):
                self.output.invocations.append("finish")
        # Make a task instance
        task = CheckInvocations("Check method invocations")
        # Check initial state
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertEqual(task.output.invocations,
                         ["init"])
        # Run the task
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertEqual(task.exit_code,0)
        self.assertEqual(task.output.invocations,
                         ["init","setup","finish"])

    def test_pipelinetask_init(self):
        """
        PipelineTask: check task 'init' invocations
        """
        # Define a task for testing
        class CheckInit(PipelineTask):
            def init(self,a,b,c='hello',d=13,e=None):
                self.add_output('results',list())
            def setup(self):
                result = "a=%s b=%s c=%s d=%s e=%s" \
                         % (self.args.a,
                            self.args.b,
                            self.args.c,
                            self.args.d,
                            self.args.e)
                self.output.results.append(result)
        # Make a task instance with minimal arglist
        task = CheckInit("Minimal arglist","a","b")
        self.assertEqual(task.args.a,"a")
        self.assertEqual(task.args.b,"b")
        self.assertEqual(task.args.c,"hello")
        self.assertEqual(task.args.d,13)
        self.assertEqual(task.args.e,None)
        # Make a task instance with named minimal arglist
        task = CheckInit("Named minimal arglist",a="a",b="b")
        self.assertEqual(task.args.a,"a")
        self.assertEqual(task.args.b,"b")
        self.assertEqual(task.args.c,"hello")
        self.assertEqual(task.args.d,13)
        self.assertEqual(task.args.e,None)
        # Make a task instance with named minimal arglist (reversed)
        task = CheckInit("Named minimal arglist reversed",
                         b="a",a="b")
        self.assertEqual(task.args.a,"b")
        self.assertEqual(task.args.b,"a")
        self.assertEqual(task.args.c,"hello")
        self.assertEqual(task.args.d,13)
        self.assertEqual(task.args.e,None)
        # Make a task instance with args and subset of keywords
        task = CheckInit("Args and subset of keywords",
                         "a","b",e=True,d=12)
        self.assertEqual(task.args.a,"a")
        self.assertEqual(task.args.b,"b")
        self.assertEqual(task.args.c,"hello")
        self.assertEqual(task.args.d,12)
        self.assertEqual(task.args.e,True)
        # Make a task instance with full arglist with keywords
        task = CheckInit("Full arglist with keywords",
                         "a","b",c="goodbye",d=12,e=True)
        self.assertEqual(task.args.a,"a")
        self.assertEqual(task.args.b,"b")
        self.assertEqual(task.args.c,"goodbye")
        self.assertEqual(task.args.d,12)
        self.assertEqual(task.args.e,True)
        # Make a task instance with full arglist no keywords
        task = CheckInit("Full arglist no keywords",
                         "a","b","goodbye",12,True)
        self.assertEqual(task.args.a,"a")
        self.assertEqual(task.args.b,"b")
        self.assertEqual(task.args.c,"goodbye")
        self.assertEqual(task.args.d,12)
        self.assertEqual(task.args.e,True)
        # Check task raises exception if init fails
        # Define a task for testing
        class FailInit(PipelineTask):
            def init(self,a,b,c='hello',d=13,e=None):
                raise Exception("Forced init to fail")
            def setup(self):
                result = "a=%s b=%s c=%s d=%s e=%s" \
                         % (self.args.a,
                            self.args.b,
                            self.args.c,
                            self.args.d,
                            self.args.e)
                self.output.results.append(result)
        self.assertRaises(Exception,
                          FailInit,
                          "This will fail on init",
                          "a",
                          "b")

    def test_pipelinetask_no_commands(self):
        """
        PipelineTask: run task with no commands
        """
        # Define a task with no commands
        class Add(PipelineTask):
            def init(self,x,y):
                self.add_output('result',list())
            def setup(self):
                self.output.result.append(self.args.x+self.args.y)
        # Make a task instance
        task = Add("Add two numbers",1,2)
        # Check initial state
        self.assertEqual(task.args.x,1)
        self.assertEqual(task.args.y,2)
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertEqual(task.output.result,[])
        # Run the task
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertEqual(task.exit_code,0)
        self.assertEqual(task.output.result,[3])
        self.assertEqual(task.stdout,"")

    def test_pipelinetask_with_commands(self):
        """
        PipelineTask: run task with shell command
        """
        # Define a task with a command
        # Echoes text via shell command
        class Echo(PipelineTask):
            def init(self,s):
                pass
            def setup(self):
                self.add_cmd(
                    PipelineCommandWrapper(
                        "Echo text","echo",self.args.s))
        # Make a task instance
        task = Echo("Echo string","Hello!")
        # Check initial state
        self.assertEqual(task.args.s,"Hello!")
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertFalse(task.output)
        # Run the task
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertEqual(task.exit_code,0)
        self.assertFalse(task.output)
        # Check stdout
        # Should look like:
        # #### COMMAND Echo text
        # #### HOSTNAME popov
        # #### USER pjb
        # #### START Thu Aug 17 08:38:14 BST 2017
        # Hello!
        # #### END Thu Aug 17 08:38:14 BST 2017
        # #### EXIT_CODE 0
        stdout = task.stdout.split("\n")
        self.assertEqual(len(stdout),8) # 8 = 7 + trailing newline
        self.assertEqual(stdout[0],"#### COMMAND Echo text")
        self.assertEqual(stdout[1],"#### HOSTNAME %s" % self._hostname())
        self.assertEqual(stdout[2],"#### USER %s" % self._user())
        self.assertTrue(stdout[3].startswith("#### START "))
        self.assertEqual(stdout[4],"Hello!")
        self.assertTrue(stdout[5].startswith("#### END "))
        self.assertEqual(stdout[6],"#### EXIT_CODE 0")

    def test_pipelinetask_with_multiple_commands(self):
        """
        PipelineTask: run task with multiple shell commands
        """
        # Define a task with a command
        # Echoes text via shell command
        class EchoMany(PipelineTask):
            def init(self,*s):
                pass
            def setup(self):
                for s in self.args.s:
                    self.add_cmd(
                        PipelineCommandWrapper(
                            "Echo text","echo",s))
        # Make a task instance
        task = EchoMany("Echo string","Hello!","Goodbye!")
        # Check initial state
        self.assertEqual(task.args.s,("Hello!","Goodbye!"))
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertFalse(task.output)
        # Run the task
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertEqual(task.exit_code,0)
        self.assertFalse(task.output)
        # Check stdout
        # Should look like:
        # #### COMMAND Echo text
        # #### HOSTNAME popov
        # #### USER pjb
        # #### START Thu Aug 17 08:38:14 BST 2017
        # Hello!
        # #### END Thu Aug 17 08:38:14 BST 2017
        # #### EXIT_CODE 0
        # #### COMMAND Echo text
        # #### HOSTNAME popov
        # #### USER pjb
        # #### START Thu Aug 17 08:38:14 BST 2017
        # Goodbye!
        # #### END Thu Aug 17 08:38:14 BST 2017
        # #### EXIT_CODE 0
        stdout = task.stdout.split("\n")
        self.assertEqual(len(stdout),15) # 15 = 14 + trailing newline
        self.assertEqual(stdout[0],"#### COMMAND Echo text")
        self.assertEqual(stdout[1],"#### HOSTNAME %s" % self._hostname())
        self.assertEqual(stdout[2],"#### USER %s" % self._user())
        self.assertTrue(stdout[3].startswith("#### START "))
        self.assertEqual(stdout[4],"Hello!")
        self.assertTrue(stdout[5].startswith("#### END "))
        self.assertEqual(stdout[6],"#### EXIT_CODE 0")
        self.assertEqual(stdout[7],"#### COMMAND Echo text")
        self.assertEqual(stdout[8],"#### HOSTNAME %s" % self._hostname())
        self.assertEqual(stdout[9],"#### USER %s" % self._user())
        self.assertTrue(stdout[10].startswith("#### START "))
        self.assertEqual(stdout[11],"Goodbye!")
        self.assertTrue(stdout[12].startswith("#### END "))
        self.assertEqual(stdout[13],"#### EXIT_CODE 0")

    def test_pipelinetask_with_batched_commands(self):
        """
        PipelineTask: run task with batched shell commands
        """
        # Define a task with a command
        # Echoes text via shell command
        class EchoMany(PipelineTask):
            def init(self,*s):
                pass
            def setup(self):
                for s in self.args.s:
                    self.add_cmd(
                        PipelineCommandWrapper(
                            "Echo text","echo",s))
        # Make a task instance
        task = EchoMany("Echo string","Hello!","Goodbye!")
        # Check initial state
        self.assertEqual(task.args.s,("Hello!","Goodbye!"))
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertFalse(task.output)
        # Run the task with batches
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 batch_size=2,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertEqual(task.exit_code,0)
        self.assertFalse(task.output)
        # Check stdout
        # Should look like:
        # #### COMMAND Batch commands for Echo string
        # #### HOSTNAME popov
        # #### USER pjb
        # #### START Thu Aug 17 08:38:14 BST 2017
        # Hello!
        # Goodbye!
        # #### END Thu Aug 17 08:38:14 BST 2017
        # #### EXIT_CODE 0
        stdout = task.stdout.split("\n")
        self.assertEqual(len(stdout),9) # 9 = 8 + trailing newline
        self.assertEqual(stdout[0],
                         "#### COMMAND Batch commands for Echo string")
        self.assertEqual(stdout[1],"#### HOSTNAME %s" % self._hostname())
        self.assertEqual(stdout[2],"#### USER %s" % self._user())
        self.assertTrue(stdout[3].startswith("#### START "))
        self.assertEqual(stdout[4],"Hello!")
        self.assertEqual(stdout[5],"Goodbye!")
        self.assertTrue(stdout[6].startswith("#### END "))
        self.assertEqual(stdout[7],"#### EXIT_CODE 0")

    def test_pipelinetask_with_failing_command(self):
        """
        PipelineTask: run task with failing shell command
        """
        # Define a task with a command
        # Attempts to run a non-existant shell command
        class Nonexistant(PipelineTask):
            def init(self):
                pass
            def setup(self):
                self.add_cmd(
                    PipelineCommandWrapper(
                        "Nonexistant","./non_existant --help"))
        # Make a task instance
        task = Nonexistant("Will fail")
        # Check initial state
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertFalse(task.output)
        # Run the task
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertNotEqual(task.exit_code,0)
        self.assertFalse(task.output)
        # Check stdout
        # Should look like:
        # #### COMMAND Nonexistant
        # #### HOSTNAME popov
        # #### USER pjb
        # #### START Thu Aug 17 08:38:14 BST 2017
        # #### END Thu Aug 17 08:38:14 BST 2017
        # #### EXIT_CODE 127
        stdout = task.stdout.split("\n")
        self.assertEqual(len(stdout),7) # 7 = 6 + trailing newline
        self.assertEqual(stdout[0],"#### COMMAND Nonexistant")
        self.assertEqual(stdout[1],"#### HOSTNAME %s" % self._hostname())
        self.assertEqual(stdout[2],"#### USER %s" % self._user())
        self.assertTrue(stdout[3].startswith("#### START "))
        self.assertTrue(stdout[4].startswith("#### END "))
        self.assertEqual(stdout[5],"#### EXIT_CODE 127")

    def test_pipelinetask_stdout(self):
        """
        PipelineTask: check stdout recovered from task
        """
        # Define a task with a command
        # Echoes text multiple times via shell command
        class MultipleEcho(PipelineTask):
            def init(self,s,n=1):
                pass
            def setup(self):
                for i in range(self.args.n):
                    self.add_cmd(
                        PipelineCommandWrapper(
                            "Echo text","echo",self.args.s))
        # Make a task instance
        task = MultipleEcho("Echo string 3 times","Hello!",3)
        # Check initial state
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertFalse(task.output)
        # Run the task
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertEqual(task.exit_code,0)
        self.assertFalse(task.output)
        # Check stdout
        # Should look like:
        # #### COMMAND Echo text
        # #### HOSTNAME popov
        # #### USER pjb
        # #### START Thu Aug 17 08:38:14 BST 2017
        # Hello!
        # #### END Thu Aug 17 08:38:14 BST 2017
        # #### EXIT_CODE 0
        # ...x three times
        print(task.stdout)
        stdout = task.stdout.split("\n")
        self.assertEqual(len(stdout),22) # 22 = 21 + trailing newline
        for i in range(3):
            self.assertEqual(stdout[0+i*7],"#### COMMAND Echo text")
            self.assertEqual(stdout[1+i*7],"#### HOSTNAME %s" % self._hostname())
            self.assertEqual(stdout[2+i*7],"#### USER %s" % self._user())
            self.assertTrue(stdout[3+i*7].startswith("#### START "))
            self.assertEqual(stdout[4+i*7],"Hello!")
            self.assertTrue(stdout[5+i*7].startswith("#### END "))
            self.assertEqual(stdout[6+i*7],"#### EXIT_CODE 0")

    def test_pipelinetask_invoke_fail(self):
        """
        PipelineTask: check task invoking 'fail' method
        """
        # Define a task which invokes 'fail'
        class FailingTask(PipelineTask):
            def init(self):
                pass
            def setup(self):
                self.fail(message="Invoked fail method",
                          exit_code=123)
        # Make a task instance
        task = FailingTask("This will fail")
        # Check initial state
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertFalse(task.output)
        # Run the task
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 poll_interval=0.5,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertEqual(task.exit_code,123)
        self.assertFalse(task.output)
        self.assertEqual(task.stdout,"")

class TestPipelineFunctionTask(unittest.TestCase):

    def setUp(self):
        # Set up a scheduler
        self.sched = SimpleScheduler(poll_interval=0.5)
        self.sched.start()
        # Make a temporary working dir
        self.working_dir = tempfile.mkdtemp(
            suffix='TestPipeline')

    def tearDown(self):
        # Stop the scheduler
        if self.sched is not None:
            self.sched.stop()
        # Remove temp dir
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)

    def test_pipelinefunctiontask(self):
        """
        PipelineFunctionTask: run task wrapping function call
        """
        # Define a task with a function call
        class Hello(PipelineFunctionTask):
            def init(self,name):
                pass
            def setup(self):
                self.add_call("Emit greeting",
                              self.hello,
                              self.args.name)
            def hello(self,name):
                return "Hello %s!" % name
        # Make a task instance
        task = Hello("Hello world","World")
        # Check initial state
        self.assertEqual(task.args.name,"World")
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertEqual(task.result(),None)
        self.assertFalse(task.output)
        # Run the task
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 poll_interval=0.1,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertEqual(task.exit_code,0)
        self.assertEqual(task.result(),["Hello World!"])
        self.assertFalse(task.output)

    def test_pipelinefunctiontask_with_failing_call(self):
        """
        PipelineFunctionTask: run task with failing function call
        """
        # Define a task with a function call
        # that raises an exception
        class RaisesException(PipelineFunctionTask):
            def init(self):
                pass
            def setup(self):
                self.add_call("Raises an exception",
                              self.raises_exception)
            def raises_exception(self):
                raise Exception("Exception is raised")
        # Make a task instance
        task = RaisesException("Will raise exception")
        # Check initial state
        self.assertFalse(task.completed)
        self.assertEqual(task.exit_code,None)
        self.assertEqual(task.result(),None)
        self.assertFalse(task.output)
        # Run the task
        task.run(sched=self.sched,
                 working_dir=self.working_dir,
                 poll_interval=0.1,
                 asynchronous=False)
        # Check final state
        self.assertTrue(task.completed)
        self.assertNotEqual(task.exit_code,0)
        self.assertEqual(task.result(),None)
        self.assertFalse(task.output)

class TestPipelineCommand(unittest.TestCase):

    def setUp(self):
        # Make a temporary working dir
        self.working_dir = tempfile.mkdtemp(
            suffix='TestPipelineCommand')

    def tearDown(self):
        # Remove temp dir
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)

    def test_pipelinecommand(self):
        """
        PipelineCommand: check command and wrapper script
        """
        # Subclass PipelineCommand
        class EchoCmd(PipelineCommand):
            def init(self,txt):
                self._txt = txt
            def cmd(self):
                return Command(
                    "echo",
                    self._txt)
        # Make an instance
        cmd = EchoCmd("hello there")
        # Check name
        self.assertEqual(cmd.name(),"echocmd")
        # Check command
        self.assertEqual(str(cmd.cmd()),"echo hello there")
        # Check wrapper script file
        script_file = cmd.make_wrapper_script(
            scripts_dir=self.working_dir)
        self.assertTrue(os.path.isfile(script_file))
        self.assertEqual(os.path.dirname(script_file),
                         self.working_dir)
        self.assertEqual(open(script_file,'r').read(),
                         "#!/bin/bash\n"
                         "echo \"#### COMMAND EchoCmd\"\n"
                         "echo \"#### HOSTNAME $HOSTNAME\"\n"
                         "echo \"#### USER $USER\"\n"
                         "echo \"#### START $(date)\"\n"
                         "echo 'hello there'\n"
                         "exit_code=$?\n"
                         "echo \"#### END $(date)\"\n"
                         "echo \"#### EXIT_CODE $exit_code\"\n"
                         "exit $exit_code")

    def test_pipelinecommand_with_modules(self):
        """
        PipelineCommand: check command and wrapper script with modules
        """
        # Subclass PipelineCommand
        class EchoCmd(PipelineCommand):
            def init(self,txt):
                self._txt = txt
            def cmd(self):
                return Command(
                    "echo",
                    self._txt)
        # Make an instance
        cmd = EchoCmd("hello there")
        # Check name
        self.assertEqual(cmd.name(),"echocmd")
        # Check command
        self.assertEqual(str(cmd.cmd()),"echo hello there")
        # Check wrapper script file
        script_file = cmd.make_wrapper_script(
            scripts_dir=self.working_dir,
            envmodules=('apps/fastq-screen/0.13.0',
                        'apps/fastqc/0.11.8',))
        self.assertTrue(os.path.isfile(script_file))
        self.assertEqual(os.path.dirname(script_file),
                         self.working_dir)
        self.assertEqual(open(script_file,'r').read(),
                         "#!/bin/bash --login\n"
                         "echo \"#### COMMAND EchoCmd\"\n"
                         "echo \"#### HOSTNAME $HOSTNAME\"\n"
                         "echo \"#### USER $USER\"\n"
                         "echo \"#### START $(date)\"\n"
                         "module load apps/fastq-screen/0.13.0\n"
                         "module load apps/fastqc/0.11.8\n"
                         "echo 'hello there'\n"
                         "exit_code=$?\n"
                         "echo \"#### END $(date)\"\n"
                         "echo \"#### EXIT_CODE $exit_code\"\n"
                         "exit $exit_code")

class TestPipelineCommandWrapper(unittest.TestCase):

    def test_piplinecommandwrapper(self):
        """
        PipelineCommandWrapper: check generated command
        """
        # Make a pipeline command wrapper
        cmd = PipelineCommandWrapper("Echo text","echo","hello")
        # Check name and generated command
        self.assertEqual(cmd.name(),"echo_text")
        self.assertEqual(str(cmd.cmd()),"echo hello")
        # Add argument and check updated command
        cmd.add_args("there")
        self.assertEqual(str(cmd.cmd()),"echo hello there")

class TestPipelineParam(unittest.TestCase):

    def test_pipelineparam_no_type(self):
        """
        PipelineParam: no type specified
        """
        # No initial value
        p = PipelineParam()
        self.assertEqual(p.value,None)
        p.set("abc")
        self.assertEqual(p.value,"abc")
        p.set(123)
        self.assertEqual(p.value,123)

    def test_pipelineparam_with_initial_value(self):
        """
        PipelineParam: initial value supplied
        """
        # Specify an initial value
        p = PipelineParam("abc")
        self.assertEqual(p.value,"abc")
        p = PipelineParam(value="def")
        self.assertEqual(p.value,"def")

    def test_pipelineparam_with_type(self):
        """
        PipelineParam: type function supplied
        """
        # Specify type function as 'str'
        p = PipelineParam(type=str)
        p.set("abc")
        self.assertEqual(p.value,"abc")
        p.set(123)
        self.assertEqual(p.value,"123")
        # Specify type function as 'int'
        p = PipelineParam(type=int)
        p.set(123)
        self.assertEqual(p.value,123)
        p.set("123")
        self.assertEqual(p.value,123)
        # Exception for bad value
        p.set("abc")
        self.assertRaises(ValueError,lambda: p.value)
        # Specify type function as 'float'
        p = PipelineParam(type=float)
        p.set(1.23)
        self.assertEqual(p.value,1.23)
        p.set("1.23")
        self.assertEqual(p.value,1.23)
        # Exception for bad value
        p.set("abc")
        self.assertRaises(ValueError,lambda: p.value)

    def test_pipelineparam_with_default(self):
        """
        PipelineParam: default function supplied
        """
        # Specify type function as 'str'
        p = PipelineParam(default=lambda: "default")
        self.assertEqual(p.value,"default")
        p.set("abc")
        self.assertEqual(p.value,"abc")

    def test_pipelineparam_with_name(self):
        """
        PipelineParam: name supplied
        """
        # Specify a name
        p = PipelineParam(name="my_param")
        self.assertEqual(p.name,"my_param")

class TestFileCollector(unittest.TestCase):

    def setUp(self):
        # Make a temporary working dir
        self.working_dir = tempfile.mkdtemp(
            suffix='TestFileCollector')

    def tearDown(self):
        # Remove temp dir
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)

    def test_filecollector(self):
        """
        FileCollector: collects files matching pattern
        """
        # Set up collectors
        all_files = FileCollector(self.working_dir,"*")
        txt_files = FileCollector(self.working_dir,"*.txt")
        # Put some files in
        file_list = [os.path.join(self.working_dir,f)
                     for f in ["test1.txt","test.fq",
                               "test.r1.fastq","test.r2.fastq"]]
        file_list.sort()
        for f in file_list:
            with open(os.path.join(self.working_dir,f),'w') as fp:
                fp.write("")
        # Check each collection
        self.assertEqual(len(all_files),4)
        for f1,f2 in zip(all_files,file_list):
            self.assertEqual(f1,f2)
        self.assertEqual(len(txt_files),1)
        self.assertEqual(list(txt_files),
                         [os.path.join(self.working_dir,"test1.txt")])

class TestDispatcher(unittest.TestCase):

    def setUp(self):
        # Make a temporary working dir
        self.working_dir = tempfile.mkdtemp(
            suffix='TestDispatcher')

    def tearDown(self):
        # Remove temp dir
        if os.path.exists(self.working_dir):
            shutil.rmtree(self.working_dir)

    def test_dispatcher_subprocess(self):
        """
        Dispatcher: runs a function via subprocess module
        """
        dispatcher_wd = os.path.join(self.working_dir,
                                     "test_dispatcher")
        d = Dispatcher(working_dir=dispatcher_wd)
        def hello(name):
            return "Hello %s!" % name
        cmd = d.dispatch_function_cmd(hello,"World")
        exit_code = cmd.run_subprocess(log=os.path.join(self.working_dir,
                                                        "dispatcher.log"))
        self.assertEqual(exit_code,0)
        result = d.get_result()
        self.assertEqual(result,"Hello World!")

    def test_dispatcher_simplejobrunner(self):
        """
        Dispatcher: runs a function via SimpleJobRunner
        """
        dispatcher_wd = os.path.join(self.working_dir,
                                     "test_dispatcher")
        d = Dispatcher(working_dir=dispatcher_wd)
        def hello(name):
            return "Hello %s!" % name
        cmd = d.dispatch_function_cmd(hello,"World")
        runner = SimpleJobRunner(log_dir=self.working_dir)
        job_id = runner.run("Hello world",
                            self.working_dir,
                            cmd.command,
                            cmd.args)
        while runner.isRunning(job_id):
            time.sleep(0.1)
        exit_code = runner.exit_status(job_id)
        self.assertEqual(exit_code,0)
        result = d.get_result()
        self.assertEqual(result,"Hello World!")
