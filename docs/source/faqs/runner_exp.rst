My experiment is crashing - how do I know where the problem is?
================================================================

If your experiment in PsychoPy is crashing, the most effective way to identify the issue is by checking the Runner window. This window displays real-time logs and error messages while your experiment runs. Follow these steps to use the Runner window for troubleshooting:

**Run Your Experiment:** 
Start your experiment as you normally would. If it crashes, the Runner window will capture and display relevant error messages.

**Locate the Error Message:** 
In the Runner window, look for messages that are marked as errors. These are typically highlighted in red for visibility and will usually contain details about the nature of the problem.

**Understand the Error Message:** 
The error message will often indicate where in your script or routine the problem occurred. It can provide clues such as the line number in your code or the specific component in your routine that caused the crash.

**Using the last_app_load.log file:**
The last_app_load.log file in PsychoPy is a log file that records information about the software's operations and events, particularly during the startup or loading phase of the application. It can be really useful if the error message you're receiving isn't too helpful, or if your experiment is causing the whole app to crash. It can be found by:

*Windows:*
- Opening a File Explorer window and typing %AppData% in the address bar. Open the folder called psychopy3 which should reveal the last_app_load.log file. You can open this in any text editor.
*Mac:*
- Open a Terminal and type cat ~/.psychopy3/last_app_load.log

**Suggested Troubleshooting Steps:**

* Syntax Errors: If the issue is a syntax error in your code, the error message will typically point to the exact line or command that needs correction.
* Resource Issues: If the error relates to missing files or resources, ensure all required files are in the correct location and properly linked in your script.
* Logical Errors: For logical errors, where the syntax is correct but the experiment does not behave as expected, re-check the logic of your code or experiment flow.
* Consult Documentation and Community: If the error message is unclear or you are unable to resolve the issue, consult the PsychoPy documentation for further guidance. `The PsychoPy forum <https://discourse.psychopy.org>`_ can also be a valuable resource for seeking help from other users who might have faced similar issues.