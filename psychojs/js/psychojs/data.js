/**
 * Data component of psychoJS
 * 
 * 
 * This file is part of the psychoJS javascript engine of PsychoPy.
 * Copyright (c) 2016 Ilixa Ltd. (www.ilixa.com)
 * 
 * Distributed under the terms of the GNU General Public License (GPL).
 */


/**
 * @namespace
 */
psychoJS.data = {}


/**
 * Import a list of conditions from an .xlsx, .csv, or .pkl file
 * 
 * <p>The output is suitable as an input to 'TrialHandler', 'trialTypes' or
 * 'MultiStairHandler' as a 'conditions' list.
 *
 * If `fileName` ends with:
 *    - .csv:  import as a comma-separated-value file (header + row x col)
 *    - .xlsx: import as Excel 2007 (xlsx) files. Sorry no support for older (.xls) is planned.
 *
 * The file should contain one row per type of trial needed and one column
 * for each parameter that defines the trial type. The first row should give
 * parameter names, which should:
 *
 *    - be unique
 *    - begin with a letter (upper or lower case)
 *    - contain no spaces or other punctuation (underscores are permitted)
 *
 *
 * 'selection' is used to select a subset of condition indices to be used
 * It can be a list/array of indices, a python `slice` object or a string to
 * be parsed as either option.
 * e.g.:
 *    "1,2,4" or [1,2,4] or (1,2,4) are the same
 *    "2:5"       # 2,3,4 (doesn't include last whole value)
 *    "-10:2:"    #tenth from last to the last in steps of 2
 *    slice(-10,2,None) #the same as above
 *    random(5)*8 #5 random vals 0-8</p>
 * 
 * @param {String} resourceName - the name of the resource containing the list of conditions
 * It must be registered with the resource manager.
 * @param {Object} [selection] - the selection
 * @return {Object} the parsed list of conditions
 * 
 * @throws {String} Throws a JSON string exception if importing the conditions failed.
 */
psychoJS.data.importConditions = function(resourceName, selection) {
	try {
		var resourceValue = psychoJS.resourceManager.getResource(resourceName);
		
		// parse the selection:
		if (undefined !== selection) {
			// TODO
			throw 'selection currently not supported.';
		}
	
		// decode resource value based on resourceName extension:
		var resourceExtension = resourceName.split('.').pop();
		
		// comma separated file .csv:
		if (resourceExtension === 'csv') {
			// remove potential trailing line break:
			resourceValue = resourceValue.replace(/\n$/, "");
			
			// parse csv:
			var parsingResult = Papa.parse(resourceValue, {header: true, dynamicsTyping: true});
			
			// select the parsed results:
			// TODO
			
			return parsingResult.data;			
		}
		
		/*
		// Excel spreadsheet .xls or .xlsx:
		else if (resourceExtension === 'xls' || resourceExtension === 'xlsx') {
			
			JSZip.loadAsync(resourceValue).then(
				function (zip) {
					zip.forEach(function (relativePath, zipEntry) {
						console.log(relativePath + ":"); console.log(zipEntry);
						//var workbook = XLSX.read(resourceValue, {type:"binary"});
						//console.log(workbook);
					});
				},
				function (error) {
					throw '{ "function" : "JSZip", "context" : "when unzipping condition: ' + resourceName + '", "error" : ' + error + ' }';
				});

			console.log(resourceValue);
			var workbook = XLSX.read(resourceValue, {type: "binary"});
			console.log(workbook);
		}*/
		
		else {
			throw 'extension: ' + resourceExtension + ' currently not supported.';
		}
	}
	catch (exception) {
		throw '{ "function" : "data.importConditions", "context" : "when importing condition: ' + resourceName + '", "error" : ' + exception + ', "stack" : ' + getErrorStack() + ' }';
	}
}


/**
 * 
 */
psychoJS.data.TrialHandler = function(attribs) {
	this.name = psychoJS.getAttrib(attribs, 'name', []);
	this.trialList = psychoJS.getAttrib(attribs, 'trialList', []);
	this.nReps = psychoJS.getAttrib(attribs, 'nReps', []);
	this.nTotal = this.nReps * this.trialList.length;
	this.nRemaining = this.nTotal // subtract 1 each trial
	this.method = psychoJS.getAttrib(attribs, 'method', 'random');
	this.thisRepN = 0;        // records which repetition or pass we are on
	this.thisTrialN = -1;    // records which trial number within this repetition
	this.thisN = -1;
	this.thisIndex = 0;        // the index of the current trial in the conditions list
	this.thisTrial = [];
	this.finished = false;
	this.extraInfo = psychoJS.getAttrib(attribs, 'extraInfo', []);
	this._warnUseOfNext = true;
	this.seed = psychoJS.getAttrib(attribs, 'seed', []);

	this.finished = false;
	this._experimentHandler = null;
}


/**
 * Set the experiment handler.
 *
 * @param{} experimentHandler - the [experiment handler]{@link psychoJS.data.ExperimentHandler}
 */
psychoJS.data.TrialHandler.prototype.setExperimentHandler = function(experimentHandler) {
	this._experimentHandler = experimentHandler;
}


psychoJS.data.TrialHandler.prototype.addData = function(key, value) {
	this._experimentHandler.addData(key, value);
}


psychoJS.data.TrialHandler.prototype.updateAttributesAtBegin = function() {
	this.thisTrialN ++; 	// number of trial this pass
	this.thisN ++;			 	//number of trial in total
	this.nRemaining --;
	
	// start a new repetition:
	if (this.thisTrialN === this.trialList.length) {
		this.thisTrialN = 0;
		this.thisRepN ++;
	}
	
	/* TODO
	#fetch the trial info
        if self.method in ['random','sequential','fullRandom']:
            self.thisIndex = self.sequenceIndices[self.thisTrialN][self.thisRepN]
            self.thisTrial = self.trialList[self.thisIndex]
            self.data.add('ran',1)
            self.data.add('order',self.thisN)
        if self.autoLog:
            logging.exp('New trial (rep=%i, index=%i): %s' %(self.thisRepN, self.thisTrialN, self.thisTrial), obj=self.thisTrial)
	*/
}


/**
 * Create a new experiment handler.
 * 
 * <p>A container class for keeping track of multiple loops/handlers
 *
 *   Useful for generating a single data file from an experiment with many
 *   different loops (e.g. interleaved staircases or loops within loops
 *
 *   :usage:
 *
 *       exp = data.ExperimentHandler({'name' : 'Face Preference', 'version' = '0.1.0'})
 *  </p>
 * @constructor
 * 
 * @param {Object} attribs associative array used to store the following parameters:
 * @param {string} attribs.name - name of the experiment
 * @param {('LOCAL_EXCEL'|'OSF'|'OSF_VIA_EXPERIMENT_SERVER'|'EXPERIMENT_SERVER')}
 * attribs.saveTo - repository to which the data is saved
 * 
 */
psychoJS.data.ExperimentHandler = function(attribs) {
	var errorPrefix = '{ "function" : "data.ExperimentHandler", "context" : "when creating ExperimentHandler", "error" : ';

	this.name = psychoJS.getAttrib(attribs, 'name', 'experiment');
	this.saveTo = psychoJS.getAttrib(attribs, 'saveTo', 'LOCAL_EXCEL');
	if (['LOCAL_EXCEL', 'OSF', 'OSF_VIA_EXPERIMENT_SERVER', 'EXPERIMENT_SERVER'].indexOf(this.saveTo) == -1) {
		throw errorPrefix + '"unknown repository: ' + saveTo + '", "stack" : ' + getErrorStack() + ' }';
	}
	this.version = psychoJS.getAttrib(attribs, 'version', '1.0');
	this.extraInfo = psychoJS.getAttrib(attribs, 'extraInfo', undefined);
	this.dataFileName = psychoJS.getAttrib(attribs, 'dataFileName', 'defaultDataFile');

	// loop handlers:
	this._loops = [];
	this._unfinishedLoops = [];
	
	// data dictionaries (one per trial) and current data dictionary:
	this._trialsKeys = [];
	this._trialsData = [];
	this._currentTrialData = {};
}


/**
 * Add a loop such as a :class:`~psychopy.data.TrialHandler` or :class:`~psychopy.data.StairHandler`
 * Data from this loop will be included in the resulting data files.
 */
psychoJS.data.ExperimentHandler.prototype.addLoop = function(loop) {
	this._loops.push(loop);
	this._unfinishedLoops.push(loop);
	loop.setExperimentHandler(this);
}


/**
 * Informs the experiment handler that the loop is finished and not to
        include its values in further entries of the experiment.

        This method is called by the loop itself if it ends its iterations,
        so is not typically needed by the user.
 */
psychoJS.data.ExperimentHandler.prototype.loopEnded = function(loop) {
	var index = this._unfinishedLoops.indexOf(loop);
	if ( index !== -1) {
		this._unfinishedLoops.splice(index, 1);
	}
}

/**
 * Add the data with a given name to the current experiment.

        Typically the user does not need to use this function; if you added
        your data to the loop and had already added the loop to the
        experiment then the loop will automatically inform the experiment
        that it has received data.

        Multiple data name/value pairs can be added to any given entry of
        the data file and is considered part of the same entry until the
        nextEntry() call is made.

        e.g.::

            #add some data for this trial
            exp.addData('resp.rt', 0.8)
            exp.addData('resp.key', 'k')
            #end of trial - move to next line in data output
            exp.nextEntry()
*/
psychoJS.data.ExperimentHandler.prototype.addData = function(key, value) {
	if (this._trialsKeys.indexOf(key) === -1) {
		this._trialsKeys.push(key);
	};
	
	this._currentTrialData[key] = value;
}


/**
 * Calling nextEntry indicates to the ExperimentHandler that the
 * current trial has ended and so further addData() calls correspond
 * to the next trial.
 */
psychoJS.data.ExperimentHandler.prototype.nextEntry = function() {
	// fetch data from each (potentially-nested) loop
	for (var l = 0; l < this._unfinishedLoops.length; l++) {
		var loop = this._unfinishedLoops[l];
		
		var attributes = this.getLoopAttributes(loop);
		for (a in attributes)
			if (attributes.hasOwnProperty(a))
				this._currentTrialData[a] = attributes[a];
	}
	
	// add the extraInfo dict to the data
	for (a in this.extraInfo)
		if (this.extraInfo.hasOwnProperty(a))
			this._currentTrialData[a] = this.extraInfo[a];

	this._trialsData.push(this._currentTrialData);

	this._currentTrialData = {};
}


/**
 *
 */
psychoJS.data.ExperimentHandler.prototype.save = function(attribs) {
	// prepare session information:
	var session = {};
	session['experimentName'] = this.extraInfo['expName'];
	session['participantName'] = this.extraInfo['participant'];
	session['sessionName'] = this.extraInfo['session'];
	session['sessionDate'] = this.extraInfo['date'];
	for (property in psychoJS._IP)
		if (psychoJS._IP.hasOwnProperty(property)) {
			session[property] = psychoJS._IP[property];
		}

	// prepare the csv file:
	var csv = "";
	
	// (a) build the header:
	var header = this._trialsKeys;
	for (var l = 0; l < this._loops.length; l++) {
		var loop = this._loops[l];
		
		var loopAttributes = this.getLoopAttributes(loop);
		for (a in loopAttributes)
			if (loopAttributes.hasOwnProperty(a))
				header.push(a);
	}
	for (a in this.extraInfo) {
		if (this.extraInfo.hasOwnProperty(a))
			header.push(a);
	}

	for (var h = 0; h < header.length; h++) {
		if (h > 0)
			csv = csv + ', ';
		csv = csv + header[h];
	}
	csv = csv + '\n';
	
	// (b) build the records:
	for (var r = 0; r < this._trialsData.length; r++) {
		for (var h = 0; h < header.length; h++) {
			if (h > 0)
				csv = csv + ', ';
			csv = csv + this._trialsData[r][header[h]];
		}
		csv = csv + '\n';
	}


	// upload data to the experiment server:
	if (this.saveTo === 'EXPERIMENT_SERVER') {
		psychoJS.resourceManager.EXPUploadData(session, 'RESULT', csv);
	}	
	// upload data to OSF via the experiment server:
	else if (this.saveTo === 'OSF_VIA_EXPERIMENT_SERVER') {
		psychoJS.resourceManager.OSFEXPUploadData(session, 'RESULT', csv);
	}
	// save data to a local excel file:
	else if (this.saveTo === 'LOCAL_EXCEL') {
		// TODO
	}
}


/**
 * Returns the attribute names and values for the current trial of a particular loop.
 * Does not return data inputs from the subject, only info relating to the trial
 * execution.
 * 
 * @param {Object} loop - the loop
 */
psychoJS.data.ExperimentHandler.prototype.getLoopAttributes = function(loop) {
	var attributes = {};
	
	var loopName = loop['name'];
	
	// standard attributes:
	var properties = ['thisRepN', 'thisTrialN', 'thisN', 'thisIndex', 'stepSizeCurrent']; 
	for (var p = 0; p < properties.length; p++) {
		var property = properties[p];
		
		for (var loopProperty in loop)
			if (loop.hasOwnProperty(loopProperty) && loopProperty === property) {
				if (property === 'stepSizeCurrent')
					var key = loopName + '.stepSize';
				else
					key = loopName + '.' + property;
				
				attributes[key] = loop[property];
			}
	}
	
	/* TODO
	// method of constants
	if hasattr(loop, 'thisTrial'):
			trial = loop.thisTrial
			if hasattr(trial,'items'):#is a TrialList object or a simple dict
					for property,val in trial.items():
							if property not in self._paramNamesSoFar:
									self._paramNamesSoFar.append(property)
							names.append(property)
							vals.append(val)
			elif trial==[]:#we haven't had 1st trial yet? Not actually sure why this occasionally happens (JWP)
					pass
			else:
					names.append(loopName+'.thisTrial')
					vals.append(trial)
					
	// single StairHandler
	elif hasattr(loop, 'intensities'):
			names.append(loopName+'.intensity')
			if len(loop.intensities)>0:
					vals.append(loop.intensities[-1])
			else:
					vals.append(None)*/

	return attributes;
}


/**
 * Uses ``time.strftime()``_ to generate a string of the form
 * 2012_Apr_19_1531 for 19th April 3.31pm, 2012.
 * This is often useful appended to data filenames to provide unique names.
 * To include the year: getDateStr(format="%Y_%b_%d_%H%M") returns '2011_Mar_16_1307'
 * depending on locale, can have unicode chars in month names, so utf_8_decode them
 * For date in the format of the current localization, do:
 * data.getDateStr(format=locale.nl_langinfo(locale.D_T_FMT))
 */
psychoJS.data.getDateStr = function() {
	return new Date().toString();
}
