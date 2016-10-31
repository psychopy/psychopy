/**
 * GUI component of psychoJS
 * 
 * 
 * This file is part of the PsychoJS javascript engine of PsychoPy.
 * Copyright (c) 2016 Ilixa Ltd. (www.ilixa.com)
 * 
 * Distributed under the terms of the GNU General Public License (GPL).
 */


/**
 * @namespace
 */
psychoJS.gui = {}


/**
 * Create a dialog box that (a) enables the participant to set some
 * experimental values (i.e. the session name), (b) shows progress of resource
 * download, and (c) enables the partipant to run or cancel the experiment.
 * 
 * <b>(a) Setting experiment values</b>
 * <p>DlgFromDict displays an input field for all values in the info.dictionary argument.
 * It is possible to specify default values e.g.:</p>
 * <code>expName = 'stroop';<br>
 * expInfo = {'participant':'', 'session':'01'};<br>
 * scheduler.add(psychoJS.gui.DlgFromDict({dictionary:expInfo, title:expName}));</code>
 * <p>If the participant cancels (by pressing Cancel or by closing the dialog box), then
 * the dictionary remains unchanged.</p>
 * <b>(b) Progress of resource download</b>
 * <p>The download of the experiment's resources is typically scheduled before this
 * dialog box, in a sub-scheduler. Progress is visualised in a progress bar at the bottom
 * of this dialog box:</p>
 * <code>scheduler = new psychoJS.Scheduler();<br>
 * ...<br>
 * resourceScheduler = new psychoJS.Scheduler();<br>
 * resourceScheduler.add(registerResources);<br>
 * resourceScheduler.add(downloadResources);<br>
 * scheduler.add(function() { resourceScheduler.start(win); });<br>
 * scheduler.add(psychoJS.gui.DlgFromDict({dictionary:expInfo, title:expName}));</code>
 * <b>(c) Running or cancelling the experiment</b>
 * <p>The flow of the experiment can be controlled by using
 * [addConditionalBranches]{@link psychoJS.Scheduler.addConditionalBranches} and the psychoJS.gui.dialogComponent.button
 * variable, e.g.:</p>
 * <code>scheduler.add(psychoJS.gui.DlgFromDict({dictionary:expInfo, title:expName}));<br>
 * dialogOKScheduler = new psychoJS.Scheduler();<br>
 * dialogCancelScheduler = new psychoJS.Scheduler();<br>
 * scheduler.addConditionalBranches(function() { return psychoJS.gui.dialogComponent.button === 'OK'; }, dialogOKScheduler, dialogCancelScheduler);</code>
 * 
 * <p>Note: DlgFromDict returns a component which can be scheduled, so the flow is blocked
 * until the user has pressed one of the dialog buttons.</p>
 * 
 * @param {Object} info - associative array used to store the following parameters:
 * @param {Object} info.dictionary - associative array of values for the participant to set
 * @param {String} info.title - name of the project
 * 
 */
psychoJS.gui.DlgFromDict = function(info) {
	psychoJS.gui.dialogComponent = [];
	psychoJS.gui.dialogComponent.status = psychoJS.NOT_STARTED;
	psychoJS.gui.dialogClock = new psychoJS.core.Clock();

	return function() {
		t = psychoJS.gui.dialogClock.getTime();
		if (t >= 0.0 && psychoJS.gui.dialogComponent.status === psychoJS.NOT_STARTED) {
			psychoJS.gui.dialogComponent.tStart = t;
			psychoJS.gui.dialogComponent.status = psychoJS.STARTED;
			psychoJS.gui._progressBarCurrentIncrement = undefined;

			// get notified of registration and download events:
			psychoJS.resourceManager.setResourceCallback(psychoJS.gui.resourceCallback);
			
			// prepare jquery UI dialog box:
			var keys = Object.keys(info.dictionary);
			var htmlCode = 
				'<div id="expDialog" title="' + info.title + '">' + 
				'<p class="validateTips">Fields marked with an asterisk (*) are required.</p>';
			for (var i = 0; i < keys.length; i++) {
				key = keys[i];
				value = info.dictionary[key];
				htmlCode = htmlCode + 
				'<label for="' + key + '">' + key + '</label>' +
				'<input type="text" name="' + key + '" id="' + key + '_id" value="' + value + '" class="text ui-widget-content ui-corner-all">';
			}
			htmlCode = htmlCode + '<hr><div id="progressMsg">&nbsp;</div>';
			htmlCode = htmlCode + '<div id="progressbar"></div></div>';
			var dialogElement = document.getElementById('dialogDiv');
			dialogElement.innerHTML = htmlCode;
			
			// init and open dialog box:
			psychoJS.gui.dialogComponent.button = 'Cancel';
			$("#expDialog").dialog({
				width: 400,
				modal: true,
				closeOnEscape: false,
				buttons: [
					{
						id: "buttonOk",
						text: "Ok",
						disabled: true,
						click: function() {
							
							// update dictionary:
							for (var i = 0; i < keys.length; i++) {
								value = document.getElementById(keys[i] + "_id").value;
								info.dictionary[keys[i]] = value;
							}
							
							psychoJS.gui.dialogComponent.button = 'OK';
							$(this).dialog( "close" );
						}
					},
					{
						id: "buttonCancel",
						text: "Cancel",
						click: function() {
							psychoJS.gui.dialogComponent.button = 'Cancel';
							$(this).dialog( "close" );
						}
					}
				],
				// close is called by both buttons and when the user clicks on the cross:
				close : function() {
					//$.unblockUI();
					psychoJS.gui.dialogComponent.status = psychoJS.FINISHED;
				}
			})
			// change colour of title bar
			.prev(".ui-dialog-titlebar").css("background", "green");

			// block UI until user has pressed dialog button:
			// note: block UI does not allow for text to be entered in the dialog form boxes, alas!
			//$.blockUI({ message: "", baseZ: 1});
			
			// show dialog box:
			$("#expDialog").dialog("open");
			$("#progressbar").progressbar({value: 0});
		}

		// the loop will return until the authentication is completed
		// at which point the status changes to FINISHED
		if (psychoJS.gui.dialogComponent.status === psychoJS.FINISHED) {
			return psychoJS.NEXT;
		} else {
			return psychoJS.FLIP_REPEAT;
		}
	}
}


/**
 * Callback function passed to the [resource manager]{@link psychoJS.io.ResourceManager}
 * to inform the [gui dialog box]{@link psychoJS.gui.DlgFromDict} of any registration
 * or download event.
 * 
 * @param {String} message - message to be displayed in the dialog box
 */
psychoJS.gui.resourceCallback = function(message) {
	var json = JSON.parse(message);
	
	// display message:
	var progressMsg = json.message;
	for (var field in json)
		if (field !== "message")
			progressMsg = progressMsg + ": " + json[field];
	$("#progressMsg").text(progressMsg);
	
	// once all the resources have been registered, we can start the
	// progress bar:
	if (json.message === "all resources registered") {
		var progressBarMax = json.number;
		if (psychoJS.resourceManager.repository === 'OSF') {
			progressBarMax += 3;
			if (psychoJS.resourceManager.projectStatus === 'PRIVATE') {
				++ progressBarMax;
			}
		}
		$("#progressbar").progressbar("option", "max", progressBarMax);
		
		psychoJS.gui._progressBarCurrentIncrement = -1;
	}
	
	// show the ok button only when all the resources have been downloaded:
	else if (json.message === "all resources downloaded") {
		$("#buttonOk").button({ disabled: false });
	}
	
	// update progress bar:
	else
	{
		if (psychoJS.gui._progressBarCurrentIncrement !== undefined) {
			++ psychoJS.gui._progressBarCurrentIncrement;
			$("#progressbar").progressbar("option", "value", psychoJS.gui._progressBarCurrentIncrement);
		}
	}
	
}


/**
 * Destroy the resource or message dialog boxes if they are open.
 */
psychoJS.gui.destroyDialog = function() {
	if ($("#expDialog").length) {
		$("#expDialog").dialog("destroy");
	}
	if ($("#msgDialog").length) {
		$("#msgDialog").dialog("destroy");
	}
}


/**
 * Show a message to the participant in a dialog box.
 * 
 * <p>This function can be used to display either a multi-level exception,
 * such as those thrown by the functions of io.js, or a warning message.</p>
 * 
 * @param {Object} info - associative array used to store the following parameters:
 * @param {string} info.error - a JSON string exception of the format: {"function" : &lt;function name&gt;, "context" : &lt;context&gt;, "error" : &lt;error&gt;}
 * @param {string} info.message - any kind of message
 * @param {string} info.warning - a warning message
 * @param {boolean} [info.showOK=true] - specifies whether to show the OK button
 * @param {boolean} [info.onOK] - function called when the participant presses the OK button
 * 
 */
psychoJS.gui.dialog = function(info) {
	var errorPrefix = '{ "function" : "psychoJS.gui.dialog", "context" : "when showing a dialog box", "error" :';
	
	// destroy previous dialog box:
	psychoJS.gui.destroyDialog();

	// we are displaying an error:
	if (info.hasOwnProperty('error')) {
		var htmlCode = '<div id="msgDialog" title="Error">';
			+ '<p class="validateTips">Unfortunately we encountered an error:</p>';
		
		// go through the exception levels:
		htmlCode = htmlCode + '<ul>';
		var json = JSON.parse(info['error']);
		while (undefined !== json) {
			htmlCode = htmlCode + '<li>' + json.context  + '</li>';
			if ('string' !==  typeof json.error)
				json = json.error;
			else {
				htmlCode = htmlCode + '<li><b>' + json.error  + '</b></li>';
				json = undefined;
			}
		}
		htmlCode = htmlCode + '</ul>';
		htmlCode = htmlCode + '<p>Please try to run the experiment again. An email has been sent to the experimenter.</p>';
		var titleColour = 'red';
	}
	// we are displaying a message:
	else if (info.hasOwnProperty('message')) {
		htmlCode = '<div id="msgDialog" title="Message">'
			+ '<p class="validateTips">' + info['message'] + '</p>';
		titleColour = 'green';
	}
	// we are displaying a warning:
	else if (info.hasOwnProperty('warning')) {
		htmlCode = '<div id="msgDialog" title="Warning">'
			+ '<p class="validateTips">' + info['warning'] + '</p>';
		titleColour = 'orange';
	}
	// error:
	else {
		throw errorPrefix + '"unexpected argument: ' + JSON.stringify(info) + '", "stack" : ' + getErrorStack() + ' }';
	}
	htmlCode = htmlCode + '</div>';
	var dialogElement = document.getElementById('dialogDiv');
	dialogElement.innerHTML = htmlCode;
	
	// init dialog box:
	$("#msgDialog").dialog({dialogClass: 'no-close', width: 400, modal: true, closeOnEscape: false})
	// change colour of title bar
	.prev(".ui-dialog-titlebar").css("background", titleColour);
	
	// add OK button if need be:
	if (info.hasOwnProperty('showOK'))
		var showOK = info['showOK'];
	else
		showOK = true;
	if (showOK) {
		$("#msgDialog").dialog("option", "buttons", [
			{
				id: "buttonOk",
				text: "Ok",
				click: function() {
					$(this).dialog("close");
					
					// execute callback function:
					if (info.hasOwnProperty('onOK')) {
						info['onOK']();
					}
				}
			}]);
	}

	// show dialog box:
	$("#msgDialog").dialog("open");
}