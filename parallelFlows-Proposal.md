####Project Proposal -- Adding Parallel Flows In PsychoPy "Builder" Interface
######Proposed by Sariya Siddiqui and Irina Rabkina

**_What is PsychoPy?_**

PsychoPy is “an open-source application to allow the presentation of stimuli and collection of data for a wide range of neuroscience, psychology and psychophysics experiments” (psychopy.org). According to its founders, it is meant as an open-source -- and therefore adaptable -- alternative to existing experimental programs such as e-Prime and Presentation. The code for PsychoPy is platform-independent, using easily accessible Python and C libraries to facilitate implementation of psychology experiments. The software itself provides a “coder” interface for experienced programmers to code their own experiment formats, as well as a “builder” mode that provides an intuitive graphical user interface for less experienced coders. 

**_Proposal_**

Our proposed plan is to add useful functionalities to the “builder” interface of PsychoPy, in order to facilitate easy access to functionalities currently only useable through coding. Specifically, we plan to add the ability to create forks in experimental flow that would allow for a participant's response to affect the screen that he or she sees next. Psychology experiments often include questionnaires or surveys, and using information input by a participant--whether it be a correct vs. incorrect answer to a question or a choice between proceeding to a task or taking a break--is an important functionality in experimental design. The fact that forking based on participant response is not currently an option in builder mode is a downfall of Psychopy, and the feature has been requested several times in the Psychopy Users Google group. Jon Peirce, the main developer of the project, has said that this is a functionality he might add in the future but does not have time to develop now. No other developers seem to have attempted the task, but we believe that it is feasible to complete over the next four weeks.

The most time-consuming element of adding the functionality will, without a doubt, be writing the actual code. Creating an experiment with parallel flows is easy enough in coder mode (e.g. if participant response is a: do x. else: do y), and we intend for it to be even easier in builder mode. The process of our writing code for this function can be broken down into two main parts: (i) altering the graphical user interface of the “builder” view to include the new function, and (ii) linking this interface to a change in the “last_run.py” file that the builder creates in order to run an experiment. 

In order to change the GUI, we will need to add a graphical option for the user to choose a parallel flows option for his experiment. To do this, we will change the keyResponse component dialog box to include an option to “fork on this response.” When this box is checked, the user will be able to type in answer:flow correspondences in the dialog box. This interface will be very similar to the interface currently used for capturing correct responses, and therefore will be intuitive to Psychopy users.

Altering the GUI would also involve changing the way the experimental flow appears in a “builder” view, so that experimenters can keep track of the experiment’s flow, as is usually done. Since code already exists within the PsychoPy project to create graphical representations of stimulus on this experiment viewer, it should not be difficult to create a new type of diagram that contains an additional fork of flow. However, this change to the GUI will by no means be trivial.

Finally, and perhaps most importantly, we will need to make sure that the code will be compiled properly in last_run.py (the file that is created by the builder in order to run the expriment). This will involve linking the presence of a certain component of the experiment builder with the actual production of a properly functional last_run.py file. Though the logic behind creating parallel flows is a simple if/then sequence (as mentioned before), there may be difficulty in implementing this from the builder.

To make our new function useable to the public, we plan to include proper documentation of our new feature. PsychoPy’s community has developed conventions in documenting code, encouraging the use of “doc strings, comments in the code, and demos to show an example of actual usage” (psychopy.org). We will include all these types of documentation, in order to make our development as accessible, easy to use, and improvable as possible. When writing our code, we will try to adhere as closely as possible to PsychoPy’s standard of a 0.28:1 ratio of comments to code. This will make it easy to catch potential bugs, and will also allow other members of the open-source community to edit code. Additionally, we plan to create a tutorial or screencast to demonstrate use of our function.

**_Project Timeline_**

The following timeline shows our proposed work schedule over the course of the semester:

|       | Task                                      | Developer(s)     |
|-------|-------------------------------------------|------------------|
| Week 1| Change keyResponse Component dialog box   | Sariya Siddiqui  |
|       | Test keyResponse Component dialog box     | Irina Rabkina    |
|       | Change keyResponse Component documentation| Developer(s)     |
|       | Research creating last_run.py properly    | Sariya Siddiqui  |
|       | Research how to change appearance of flow | Irina Rabkina    |
| Week 2| Pseudo Code last_run.py changes           | Sariya Siddiqui  |
|       | Begin coding last_run.py changes          | Sariya Siddiqui  |
|       | Pseudo Code flow appearance               | Irina Rabkina    |
|       | Begin coding flow appearance              | Irina Rabkina    |
| Week 3| Code last_run.py                          | Sariya Siddiqui  |
|       | Code flow appearance                      | Irina Rabkina    |
|       | Test/critique last_run.py                 | Irina Rabkina    |
|       | Test/critique flow appearance             | Sariya Siddiqu   |
| Week 4| Finish code touch-ups                     | Both             |
|       | Final testing of new version of PsychoPy  | Both             |
|       | Edit Docs                                 | Both             |
|       | Create Tutorial                           | Both             |

If time permits, we may also develop documentation  that outlines code snippets that can be used to perform common tasks through the “coder” interface. Many such functions are already discussed on the Google Users group for PsychoPy, and a compilation of this information would be useful to many implementers. This is apparent from the fact that similar questions have been asked numerous times on the forum.  Of course, this task would not include much coding, but would rather involve starting a precedential wiki page where users can add helpful code examples.

**_Resources_**






