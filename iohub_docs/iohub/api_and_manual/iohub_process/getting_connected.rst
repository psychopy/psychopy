#################
Getting Connected 
#################

Running an experiment using the ioHub Event Framework utilizes two Python processes.
The first is for running the traditional PsychoPy coder experiment logic called the PsychoPy 
Process. The second is a separate process for device monitoring, event bundling, 
and data storage called the ioHub Process.

The PsychoPy Process is established by the Python interpreter executing
the experiment script. Therefore, the first thing that needs to be done when using
the ioHub Event Framework is to have the PsychoPy Process establish and connect
to a new ioHub Server process. 

The functionality for establishing and connecting to a new ioHub Process
is provided in the psychopy.iohub.ioHubConnection class.
The experiment script should **indirectly** create **one instance** of the 
ioHubConnection class using one of the two methods discussed in the next section.
That is, an instance of ioHubConnection should never be created *directly* by the 
experiment script.

The ioHubConnection Class
###############################


There are two ways to create an instance of the ioHubConnection class
to use with a PsychoPy experiment:
#. Calling the psychopy.iohub.client.quickStartHubServer function.
#. Extending the psychopy.iohub.client.ioHubExperimentRuntime class. 

Each approach to creating the ioHubConnection instance has strengths and weaknesses,
and the most appropriate approach for a given experiment depends
primarily on the ioHub Device types used in the experiment.
 
.. autoclass:: psychopy.iohub.client.ioHubConnection
	:member-order: bysource

