requirejs(["js/Math2.js", "js/jquery-2.2.0.min.js", "js/stats.min.js", "js/pixi.min.js",
		  "psychopy/main.js",
		  "psychopy/core.js",
		  "psychopy/data.js",
		  "psychopy/events.js",
		  "psychopy/gui.js",
		  "psychopy/util.js",
		  "psychopy/scheduler.js",
		  "psychopy/visual.js"], 
		  function() {
			setupExperiment(); // not scheduled because we need a reference to window (win) to start the scheduler (though this could be set up in another way)

			scheduler = new PsychoPy.Scheduler();
			scheduler.add(experimentInit);
			scheduler.add(instructInit);
			scheduler.add(instructLoop);
			scheduler.add(instructEnd);
			scheduler.add(setupTrials);
			trialScheduler = new PsychoPy.Scheduler();
			scheduler.add(trialScheduler);
			scheduler.add(trialsEnd);
			scheduler.add(thanksInit);
			scheduler.add(thanksLoop);
			scheduler.add(thanksEnd);

			scheduler.start(win);
		  }
);
  
function setupExperiment() {
	with (PsychoPy) {
		debug = false;
		
	// 	# Ensure that relative paths start from the same directory as this script
	// 	_thisDir = os.path.dirname(os.path.abspath(__file__)).decode(sys.getfilesystemencoding())
	// 	os.chdir(_thisDir)
		
		// Store info about the experiment session
		expName = 'stroop';  // from the Builder filename that created this script
		expInfo = {'participant':'', 'session':'01'};
		dlg = gui.DlgFromDict({dictionary:expInfo, title:expName});
		if (dlg.OK == false) {
			core.quit(); // user pressed cancel
		}
		expInfo['date'] = data.getDateStr(); // add a simple timestamp
		expInfo['expName'] = expName;
		
	// 	# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
	// 	filename = _thisDir + os.sep + u'data' + os.sep + '%s_%s' %(expInfo['participant'], expInfo['date'])
		filename = "dummy_name"; // XXX
	// 
		// An ExperimentHandler isn't essential but helps with data saving
		thisExp = new data.ExperimentHandler({name:expName, version:'',
			extraInfo:expInfo, runtimeInfo:undefined,
			originPath:undefined,
			savePickle:true, saveWideText:true,
			/*dataFileName=filename*/});
	// 	#save a log file for detail verbose info
	// 	logFile = logging.LogFile(filename+'.log', level=logging.WARNING)
	// 	logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

		endExpNow = false; // flag for 'escape' or other condition => quit the exp

		// Start Code - component code to be run before the window creation
		
		// Setup the Window
		win = new visual.Window({size:[1080, 1920], fullsc:true, screen:0, allowGUI:false, allowStencil:false,
			monitor:'testMonitor', color:'black', colorSpace:'rgb',
			blendMode:'avg', useFBO:true,
			units:'norm'});
		// store frame rate of monitor if we can measure it successfully
		expInfo['frameRate']=win.getActualFrameRate();
		if (expInfo['frameRate']!=undefined) {
			frameDur = 1.0/Math.round(expInfo['frameRate']);
		}
		else {
			frameDur = 1.0/60.0; // couldn't get a reliable measure so guess
		}
		
		return NEXT;
	}
	
}
	
function experimentInit() {	
	with (PsychoPy) {
		// Initialize components for Routine "instruct"
		instructClock = new core.Clock();
		instrText = new visual.TextStim({win:win, ori:0, name:'instrText',
			text:'OK. Ready for the real thing?\n\nRemember, ignore the word itself; press:\nLeft for red LETTERS\nDown for green LETTERS\nRight for blue LETTERS\n(Esc will quit)\n\nPress any key to continue',    font:'Arial',
			pos:[0, 0], height:0.1, wrapWidth:undefined,
			color:[1, 1, 1], colorSpace:'rgb', opacity:1,
			depth:0.0});

		// Initialize components for Routine "trial"
		trialClock = new core.Clock();
		word = new visual.TextStim({win:win, ori:0, name:'word',
			text:'default text',    font:'Arial',
			pos:[0, 0], height:0.2, wrapWidth:undefined,
			color:1.0, colorSpace:'rgb', opacity:1,
			depth:0.0});
			
		
		// Initialize components for Routine "thanks"
		thanksClock = new core.Clock();
		thanksText = new visual.TextStim({win:win, ori:0, name:'thanksText',
			text:'This is the end of the experiment.\n\nThanks!',    font:'arial',
			pos:[0, 0], height:0.3, wrapWidth:undefined,
			color:[1, 1, 1], colorSpace:'rgb', opacity:1,
			depth:0.0});

		// Create some handy timers
		globalClock = new core.Clock();  // to track the time since experiment started
		routineTimer = new core.CountdownTimer();  // to track time remaining of each (non-slip) routine 
	}
	
	return NEXT;

}

function instructInit() {	
	with (PsychoPy) {
		//------Prepare to start Routine "instruct"-------
		t = 0;
		instructClock.reset(); // clock 
		frameN = -1;
		// update component parameters for each repeat
		ready = new event.BuilderKeyResponse(); // create an object of type KeyResponse
		ready.status = NOT_STARTED;
		// keep track of which components have finished
		instructComponents = [];
		instructComponents.push(instrText);
		instructComponents.push(ready);
		for(var i = 0; i < instructComponents.length; ++i) {
			thisComponent = instructComponents[i];
			if ('status' in thisComponent) {
				thisComponent.status = NOT_STARTED;
			}
		}	
		
		return NEXT;
	}
}

function instructLoop() {
	with (PsychoPy) {
		continueRoutine = true;
		
		// get current time
		t = instructClock.getTime();
		frameN = frameN + 1;  // number of completed frames (so 0 is the first frame)
		// update/draw components on each frame
		
		// *instrText* updates
		if (t >= 0 && instrText.status === NOT_STARTED) {
			// keep track of start time/frame for later
			instrText.tStart = t;  // underestimates by a little under one frame
			instrText.frameNStart = frameN;  // exact frame index
			instrText.setAutoDraw(true);
			console.log("------------ instrText set to autoDraw");
		}
		
		// *ready* updates
		if (t >= 0 && ready.status === NOT_STARTED) {
			// keep track of start time/frame for later
			ready.tStart = t;  // underestimates by a little under one frame
			ready.frameNStart = frameN;  // exact frame index
			ready.status = STARTED;
			// keyboard checking is just starting
			event.clearEvents({eventType:'keyboard'});
		}
		if (ready.status === STARTED) {
			theseKeys = event.getKeys();
			
			// check for quit:
			if ("escape" in theseKeys) {
				endExpNow = true;
			}
			if (theseKeys.length > 0) {  // at least one key was pressed
				// a response ends the routine
				continueRoutine = false;
			}
		}
		
		// check if all components have finished
		if (!continueRoutine) {  // a component has requested a forced-end of Routine
			return NEXT;
		}
		continueRoutine = false;  // will revert to True if at least one component still running
		for(var i = 0; i < instructComponents.length; ++i) {
			thisComponent = instructComponents[i];		
			if ('status' in thisComponent && thisComponent.status != FINISHED) {
				continueRoutine = true;
				break;
			}
		}	
			
		// check for quit (the Esc key)
		if (endExpNow || event.getKeys({keyList:["escape"]}).length > 0) {
			core.quit();
		}
		
		// refresh the screen
		if (continueRoutine) {  // don't flip if this routine is over or we'll get a blank screen
			return FLIP_REPEAT;
		}
		else {
			return NEXT;
		}
	}
}

function instructEnd() {
	with (PsychoPy) {
		//-------Ending Routine "instruct"-------
		for(var i = 0; i < instructComponents.length; ++i) {
			thisComponent = instructComponents[i];	
			if ("setAutoDraw" in thisComponent) {
				thisComponent.setAutoDraw(false);
			}
		}
		// the Routine "instruct" was not non-slip safe, so reset the non-slip timer
		routineTimer.reset();
		
		return NEXT;
	}
}


function setupTrials() {
	with (PsychoPy) {
		// set up handler to look after randomisation of conditions etc
		trials = new data.TrialHandler({nReps:5.0, method:'random', 
			extraInfo:expInfo, originPath:undefined,
			trialList:data.importConditions('trialTypes.xlsx'),
			seed:undefined, name:'trials'});
		// XXX cheat until we have importConditions:
		trials.trialList = [
			{text:'red', letterColor:'red', corrAns:'left', congruent:1},
			{text:'red', letterColor:'green', corrAns:'down', congruent:0},
			{text:'green', letterColor:'green', corrAns:'down', congruent:1},
			{text:'green', letterColor:'blue', corrAns:'right', congruent:0},
			{text:'blue', letterColor:'blue', corrAns:'right', congruent:1},
			{text:'blue', letterColor:'red', corrAns:'left', congruent:0}
			];
		thisExp.addLoop(trials); // add the loop to the experiment
		thisTrial = trials.trialList[0]; // so we can initialise stimuli with some values
		// abbreviate parameter names if possible (e.g. rgb=thisTrial.rgb)
		if (thisTrial != undefined) {
			for (paramName in thisTrial) {
				window[paramName] = thisTrial[paramName];
			}
		}
				
		for (var i = 0; i < trials.trialList.length; ++i) { // XXX Iterate on trials.trialList rather than trials???
			thisTrial = trials.trialList[i];
			trialScheduler.add(trialInit(thisTrial)); // XXX we could avoid parameterization by extracting the global variable trick into this loop
			trialScheduler.add(trialLoop); // XXX not parameterized by thisTrial because of usage of global variables
			trialScheduler.add(trialEnd); // XXX not parameterized by thisTrial because of usage of global variables
		}
		

		
		return NEXT;
	}
}

function trialInit(thisTrial) { // this one is a bit special: it returns a scheduler function
	return function() {
		with (PsychoPy) {
//console.log("trialInit : " + str(thisTrial)); 
			currentLoop = trials;
			// abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
			if (thisTrial != undefined) {
				for (paramName in thisTrial) {
					window[paramName] = thisTrial[paramName];
				}
			}	
			
			//------Prepare to start Routine "trial"-------
			t = 0;
			trialClock.reset();  // clock 
			frameN = -1;
			// update component parameters for each repeat
			word.setColor({color:letterColor, colorSpace:'rgb'});
			//word.setText(text);
			word.text = text;
			resp = new event.BuilderKeyResponse();  // create an object of type KeyResponse
			resp.status = NOT_STARTED;
			// keep track of which components have finished
			trialComponents = [];
			trialComponents.push(word);
			trialComponents.push(resp);
			for(var i = 0; i < trialComponents.length; ++i) {
				thisComponent = trialComponents[i];
				if ('status' in thisComponent) {
					thisComponent.status = NOT_STARTED;
				}
			}
			
			return NEXT;
		}
	}
}

function trialLoop() {
	with (PsychoPy) {
		continueRoutine = true;

		// get current time
		t = trialClock.getTime();
		frameN = frameN + 1;  // number of completed frames (so 0 is the first frame)
		// update/draw components on each frame
		
		// *word* updates
		if (t >= 0.5 && word.status === NOT_STARTED) {
			// keep track of start time/frame for later
			word.tStart = t;  // underestimates by a little under one frame
			word.frameNStart = frameN;  // exact frame index
			word.setAutoDraw(true);
		}
		
		// *resp* updates
		if (t >= 0.5 && resp.status === NOT_STARTED) {
			// keep track of start time/frame for later
			resp.tStart = t;  // underestimates by a little under one frame
			resp.frameNStart = frameN;  // exact frame index
			resp.status = STARTED;
			// keyboard checking is just starting
			resp.clock.reset();  // now t=0
			event.clearEvents({eventType:'keyboard'});
		}
		if (resp.status === STARTED) {
			theseKeys = event.getKeys({keyList:['left', 'down', 'right']})
			// check for quit:
			if ("escape" in theseKeys) {
				endExpNow = true;
			}
			if (theseKeys.length > 0) {  // at least one key was pressed
				resp.keys = theseKeys[theseKeys.length-1];  // just the last key pressed
				resp.rt = resp.clock.getTime();
				// was this 'correct'?
				if ((resp.keys === str(corrAns)) || (resp.keys === corrAns)) {
					resp.corr = 1;
				}
				else {
					resp.corr = 0;
				}
				// a response ends the routine
				continueRoutine = false;
			}
		}
		
		// check if all components have finished
		if (!continueRoutine) { // a component has requested a forced-end of Routine
			return NEXT;
		}
		continueRoutine = false;  // will revert to True if at least one component still running
		for(var i = 0; i < trialComponents.length; ++i) {
			thisComponent = trialComponents[i];		
			if ('status' in thisComponent && thisComponent.status != FINISHED) {
				continueRoutine = true;
				break;
			}
		}	
			
		// check for quit (the Esc key)
		if (endExpNow || event.getKeys({keyList:["escape"]}).length > 0) {
			core.quit();
		}
		
		// refresh the screen
		if (continueRoutine) {  // don't flip if this routine is over or we'll get a blank screen
			return FLIP_REPEAT;
		}
		else {
			return NEXT;
		}		
	}
}

function trialEnd() {
	with (PsychoPy) {
		//-------Ending Routine "trial"-------
		for(var i = 0; i < trialComponents.length; ++i) {
			thisComponent = trialComponents[i];	
			if ("setAutoDraw" in thisComponent) {
				thisComponent.setAutoDraw(false);
			}
		}
		// check responses
		if (['', [], undefined].indexOf(resp.keys) >= 0) {  // No response was made
			resp.keys=undefined;
			// was no response the correct answer?!
			if (str(corrAns).toLowerCase() === 'none') resp.corr = 1;  // correct non-response
			else resp.corr = 0;  // failed to respond (incorrectly)
		}
		// store data for trials (TrialHandler)
		trials.addData('resp.keys', resp.keys);
		trials.addData('resp.corr', resp.corr);
		if (resp.keys != undefined) {  // we had a response
			trials.addData('resp.rt', resp.rt);
		}
		// the Routine "trial" was not non-slip safe, so reset the non-slip timer
		routineTimer.reset();
		thisExp.nextEntry();
		
		return NEXT;
	}
}

function trialsEnd() {
	with (PsychoPy) {
		
		// completed 5.0 repeats of 'trials'

		// get names of stimulus parameters
		if (isEmpty(trials.trialList)) { // XXX equiv of : in ([], [None], None)
			params = [];
		}
		else {
			params = Object.keys(trials.trialList[0]);
		}
		// save data for this loop
		trials.saveAsExcel({fileName:filename + '.xlsx', sheetName:'trials',
			stimOut:params,
			dataOut:['n','all_mean','all_std', 'all_raw']});
		
		return NEXT;
	}
}


function thanksInit() {
	with (PsychoPy) {
		
		//------Prepare to start Routine "thanks"-------
		t = 0;
		thanksClock.reset();  // clock 
		frameN = -1;
		routineTimer.add(2.000000);
		// update component parameters for each repeat
		// keep track of which components have finished
		thanksComponents = [];
		thanksComponents.push(thanksText);
		for(var i = 0; i < thanksComponents.length; ++i) {
			thisComponent = thanksComponents[i];
			if ('status' in thisComponent) {
				thisComponent.status = NOT_STARTED;
			}
		}		
		
		return NEXT;
	}
}

function thanksLoop() {
	with (PsychoPy) {
		continueRoutine = true;
		
		// get current time
		t = thanksClock.getTime();
		frameN = frameN + 1;  // number of completed frames (so 0 is the first frame)
		// update/draw components on each frame
		
		// *thanksText* updates
		if (t >= 0.0 && thanksText.status === NOT_STARTED) {
			// keep track of start time/frame for later
			thanksText.tStart = t;  // underestimates by a little under one frame
			thanksText.frameNStart = frameN;  // exact frame index
			thanksText.setAutoDraw(true);
		}
		if (thanksText.status === STARTED && t >= (0.0 + (2.0-win.monitorFramePeriod*0.75))) { //most of one frame period left
			thanksText.setAutoDraw(false);
		}
		
		// check if all components have finished
		if (!continueRoutine) {  // a component has requested a forced-end of Routine
			return NEXT;
		}
		continueRoutine = false;  // will revert to True if at least one component still running
		for(var i = 0; i < thanksComponents.length; ++i) {
			thisComponent = thanksComponents[i];		
			if ('status' in thisComponent && thisComponent.status != FINISHED) {
				continueRoutine = true;
				break;
			}
		}	
		// check for quit (the Esc key)
		if (endExpNow || event.getKeys({keyList:["escape"]}).length > 0) {
			core.quit();
		}
		
		// refresh the screen
		if (continueRoutine && routineTimer.getTime() > 0) {  // don't flip if this routine is over or we'll get a blank screen
			return FLIP_REPEAT;
		}
		else {
			return NEXT;
		}
		
		
	}
}

function thanksEnd() {
	with (PsychoPy) {
		
		//-------Ending Routine "thanks"-------
		for(var i = 0; i < thanksComponents.length; ++i) {
			thisComponent = thanksComponents[i];	
			if ("setAutoDraw" in thisComponent) {
				thisComponent.setAutoDraw(false);
			}
		}
		win.close();
		core.quit();
		
		return QUIT;
	}
}




// setupExperiment(); // not scheduled because we need a reference to window (win) to start the scheduler (though this could be set up in another way)
// 
// scheduler = new PsychoPy.Scheduler();
// scheduler.add(experimentInit);
// scheduler.add(instructInit);
// scheduler.add(instructLoop);
// scheduler.add(instructEnd);
// scheduler.add(setupTrials);
// trialScheduler = new PsychoPy.Scheduler();
// scheduler.add(trialScheduler);
// scheduler.add(trialsEnd);
// scheduler.add(thanksInit);
// scheduler.add(thanksLoop);
// scheduler.add(thanksEnd);
// 
// scheduler.start(win);
	