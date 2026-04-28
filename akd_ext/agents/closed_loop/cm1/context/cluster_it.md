# Cluster IT Context - Matrix (UAH HPC Cluster)

cluster_it_context = """3/25/26, 10:31 AM Matrix - UAH-NSSTC IT Wiki
Matrix
From UAH-NSSTC IT Wiki
Contents
1 Structure
2 How To Use The System
3 SLURM
3.1 Where to Begin
3.2 Commands
3.3 Queues
3.4 QOS
3.5 Pre-emption
3.6 GPUs
3.7 Scheduling jobs at
regular intervals
4 Applications
4.1 Python
4.2 IDL
4.3 MATLAB
5 Interactive Commands
6 Caveats
6.1 Using more Processors
is not always faster
6.2 IEEE 754 Floating-
Point Arithmetic
6.3 Illegal Instruction PGI
Compiler Error
6.4 Running a Multi-
threaded non MPICH job
7 References
Cluster Equipment Racks
Matrix is a Linux cluster designed for single and multi-threaded modeling jobs. It uses the SLURM queuing system. It
is IMPORTANT that you do not execute code in the same manner you would on a traditional Linux system. Please
read this page thoroughly. System paths are set using the modules software.
Structure
OS: Redhat Enterprise 7.9
2PB Disk
Supermicro Xeon Blade Servers
TBD Nodes
TBD Processor Cores
Infiniband high-performance I/O
https://it.nsstc.uah.edu/itwiki/Matrix.html#Queues 1/6
3/25/26, 10:31 AM Matrix - UAH-NSSTC IT Wiki
How To Use The System
Do NOT run code interactively on Matrix. You must use the SLURM queueing system to run all jobs (even cron jobs).
The system is optimized for non-interactive cpu intensive applications. It is recommended that you run graphical
applications on another machine.
Review documentation about the directory structure and disk quotas on the system.
See the modules Documentation page for information on application usage.
Modify your .tcshrc.matrix file if you are using a TCSH shell. or your .bashrc.matrix file if you are using
the BASH shell. These files are to be located in your top user directory in /rhome. Matrix uses a path management
utility to configure paths for all of programs used on the system. DO NOT manually set paths as you may have with
other Unix machines.
SLURM
Where to Begin
Create a SLURM shell script to call your executable (Example scripts here)
Keep in mind that any shell script must start either with #!/bin/csh or #!/bin/bash depending on your shell. Bash users
need to make sure to use #!/bin/bash instead of #!/bin/sh
type: sbatch <script> to submit
Output is placed in a log file in your working directory slurm-<jobid>.out
Errors are placed in slurm-<jobid>.err
Commands
sbatch <slurm script> Submit a job for execution
scancel <job id> Kill a running job
squeue -u <username> Show queue information about your jobs
scontrol show job <job id> Show detailed information about a running job
sproc Show system CPU usage
sinfo Show info about available queues
sacct sstat --format=JobID,JobName,AveRss,MaxRSS,Elapsed -j <jobid> --format=JobID,AveRss,MaxRSS -a -j <jobid> Show statistics on a completed job
Show statistics on a running job
Queues
Matrix has 3 queues with functionality outlined below. Click on a queue name to see an example. Maximum interactive
sessions are limited to 3.
Name
Max
Jobs
Max
Procs
Max Total
Memory
Max Memory per
Node
Notes
shared 20 64 400G 100G Use for single and low priority multi processor jobs.
Nodes are shared with other users.
https://it.nsstc.uah.edu/itwiki/Matrix.html#Queues 2/6
3/25/26, 10:31 AM Matrix - UAH-NSSTC IT Wiki
standard 30 256 1000G 100G Nodes are exclusive to users but are subject to pre-
emption by the special queue.
special 5 QOS QOS 100G Processors are allocated to special projects and limits are
based on a QOS parameter.
QOS
The special queue sets limits on resources using a Quality of Service (QOS) type. It is assigned to users based on the type of
research they are running on the cluster. By default, users do not have access to this partition. Check with your PI or IT for
availability.
Pre-emption
Pre-emption suspends a running job temporarily so that a higher priority process can execute. After that job is finished, the
pre-empted job resumes from the point it stopped. On Matrix, jobs running in the special queue have the potential to pre-empt
standard jobs if additional processors are not available.
GPUs
GPUs are available on select nodes with the shared queue.
4 NVIDIA A100 Tensor GPUs. Specs
module load cuda
GPU Example
Scheduling jobs at regular intervals
Configure your SLURM script as usual.
use the command crontab -e to edit your configuration file.
make sure the first two lines of the crontab file include the following:
BASH
_
ENV="$HOME/.bashrc"
SHELL="/bin/bash"
add: min hr day mon weekday sbatch /path/script >/dev/null 2>&1
use a * for "every" interval (eg every hour, every minute)
Crontab Fields
# Use the hash sign to prefix a comment
# +---------------- minute (0 - 59)
# | +------------- hour (0 - 23)
# | | +---------- day of month (1 - 31)
# | | | +------- month (1 - 12)
# | | | | +---- day of week (0 - 7) (Sunday=0 or 7)
https://it.nsstc.uah.edu/itwiki/Matrix.html#Queues 3/6
3/25/26, 10:31 AM # | | | | |
# * * * * * command to be executed
Matrix - UAH-NSSTC IT Wiki
Example crontab file. Use this format for executing both CSH and BASH SLURM scripts.
BASH
_
ENV="$HOME/.bashrc"
SHELL=/bin/bash
MAILTO=user@nsstc.uah.edu
30 * * * * sbatch /rstor/scottp/test.csh > /dev/null 2>&1
30 12,13 * * * sbatch /rhome/scottp/test2.bash > /dev/null 2>&1
The first job runs every 30 minutes. The second one runs at 12:30pm and 1:30pm every day.
Applications
Type module avail to see a list of available packages.
Python
Python V2 and V3 are both available with many standard packages by loading the relevant module.
module load python/v2
module load python/v3
To list installed Python packages (after loading module):
conda list
To install additional/custom packages, create your own Python environment as follows:
module load python/v3
conda create -n py3 python=3
conda activate py3
conda install <your packages>
To activate a custom Python environment the next time you log in or run a Slurm script:
module load python/v3
conda activate py3
Python Example
IDL
When running IDL on Matrix, be sure to use the queuing system. Do not run it interactively. Use a system other then Matrix if
you need an interactive graphical display. If you are generating graphical output that would normally output to the screen, you
must first run Xvfb within the SLURM script to simulate a connection to a display.
https://it.nsstc.uah.edu/itwiki/Matrix.html#Queues 4/6
3/25/26, 10:31 AM IDL Example
Matrix - UAH-NSSTC IT Wiki
MATLAB
To run a job on Matrix, write a Matlab script file (.m) and then call the script from within a SLURM script. Include -
singleCompThread -nodisplay -nosplash -nojvm directives with the Matlab executable to indicate that your code will not be
running interactively.
MATLAB Example
Interactive Commands
Code should not be interactively executed on matrix but for certain high CPU commands that must be run on the interactive
node, use the scmd command to offload the function to a compute node. Note that scmd will only run on a single processor.
examples:
scmd tar czf test.tgz testdir
scmd ftp ftp.uah.edu
scmd scp testdir aqua:/testdir
scmd du
scmd gzip testfile
scmd cp /rstor/testuser/test /rtmp/test
Caveats
Using more Processors is not always faster
Many commonly run multi-processor models do not always scale as you might expect. For example, you might expect that if
you ran a model with 32 processors instead of 16, it should run twice as fast. Depending on how the code was written, this
may or may not be the case. In fact, sometimes it may even run slower with more processors, due to the communications
overhead. The recommendation is to make test runs with a variety of processor sizes and determine what works best. It is
generally a waste to just assume the maximum processor size as it ties up resources and may not be faster then a much smaller
set. Also, if your job is not multi-threaded (eg designed to run on multiple processors), assigning it more then 1 processor will
not make it run faster.
IEEE 754 Floating-Point Arithmetic
By default, the PGI compiler does not fully adhere to the IEEE 754 standard for floating-point arithmetic. This could mean
that small round-off errors might occur as a trade-off for speed optimizations. Model results may vary as a function of the
number of processors chosen and/or CPU type. If your model or code requires very high precision floating-point arithmetic,
use the -Kieee compiler option to assure compliance.
Illegal Instruction PGI Compiler Error
https://it.nsstc.uah.edu/itwiki/Matrix.html#Queues 5/6
3/25/26, 10:31 AM Matrix - UAH-NSSTC IT Wiki
When running code compiled with the Portland Group Compiler, your executable crashes with an "Illegal Instruction" error.
Recompile adding -tp=p7 as a compiler option. Note that this only applies to PGI compilers, eg. pgf90 pgf77 pgcc pgc++
Running a Multi-threaded non MPICH job
When running a job that does not support MPICH but is multi-threaded, it will not span more then one node so the maximum
number of processor cores that can be used is 16. Your code must support multi-threading for it to use more then 1 processor
core. It is recommended that you run a test job with 1 thread and then again with 2 or more threads comparing the run times.
Multi Proc Non-MPICH Example
References
SLURM Documentation (http://slurm.schedmd.com/documentation.html)
Portland Group Documentation (http://www.pgroup.com/resources/docs.htm)
MPICH Guides (http://www.mpich.org/documentation/guides/)
NVIDIA CUDA Toolkit (https://docs.nvidia.com/cuda)
Retrieved from "https://it.nsstc.uah.edu/itwiki/Matrix"
https://it.nsstc.uah.edu/itwiki/Matrix.html#Queues 6/6
"""
