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
 *    - .pkl:  import from a pickle file as list of lists (header + row x col)
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
 * @param {psychoJS.io.ResourceManager} resourceManager the [resource manager]{@link psychoJS.io.ResourceManager}
 * @param {String} resourceName the name of the resource, registered with
 * the resource manager, containing the list of conditions
 * @return {Object} the parsed list of conditions
 * 
 * @throws {String} Throws a JSON string exception if importing the conditions failed.
 */
psychoJS.data.importConditions = function(resourceManager, resourceName) {
	try {
		var resourceValue = resourceManager.getResource(resourceName);
		
		console.log("got resource value:");
		console.log(resourceValue);
	
		// decode resource value based on resourceName extension:
		var parsingResult = Papa.parse(resourceValue, {header: true, dynamicsTyping: true});
		return parsingResult.data;
	}
	catch (exception) {
		throw '{ "function" : "data.importConditions", "context" : "when attempting to import condition: ' + resourceName + '", "error" : ' + exception + ' }';
	}
}


/**
 * 
 */
psychoJS.data.TrialHandler = function(attribs) {
	this.name = getAttrib(attribs, 'name', []);
	this.trialList = getAttrib(attribs, 'trialList', []);
	this.nReps = getAttrib(attribs, 'nReps', []);
	this.nTotal = this.nReps * this.trialList.length;
	this.nRemaining = this.nTotal // subtract 1 each trial
	this.method = getAttrib(attribs, 'method', 'random');
	this.thisRepN = 0;        // records which repetition or pass we are on
	this.thisTrialN = -1;    // records which trial number within this repetition
	this.thisN = -1;
	this.thisIndex = 0;        // the index of the current trial in the conditions list
	this.thisTrial = [];
	this.finished = false;
	this.extraInfo = getAttrib(attribs, 'extraInfo', []);
	this._warnUseOfNext = true;
	this.seed = getAttrib(attribs, 'seed', []);

	this.finished = false;
	this._experimentHandler = null;
}


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

/*
psychoJS.data.TrialHandler.prototype.saveAsExcel = function(attribs) {
}

psychoJS.data.TrialHandler.prototype.saveData = function(resourceManager, expInfo) {
	resourceManager.OSFUploadData(expInfo, this.data);
}
*/


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
 * @param {('LOCAL_EXCEL'|'OSF'|'OSF_VIA_EXPERIMENT_SERVER'|'EXPERIMENT_SERVER')} attribs.repository destination for long term data storage
 * 
 */
psychoJS.data.ExperimentHandler = function(attribs) {
	this.name = getAttrib(attribs, 'name', 'experiment');
	this.repository = getAttrib(attribs, 'repository', 'LOCAL_EXCEL');
	this.version = getAttrib(attribs, 'version', '1.0');
	this.extraInfo = getAttrib(attribs, 'extraInfo', undefined);
	this.dataFileName = getAttrib(attribs, 'dataFileName', 'defaultDataFile');
	this.experimentServerUrl = getAttrib(attribs, 'experimentServerUrl');

	// loop handlers:
	this._loops = [];
	this._unfinishedLoops = [];
	// session information (e.g. participant name, participant IP, experiment name)
	this._session = {};
	// data dictionaries (one per trial) and current data dictionary:
	this._trialsKeys = [];
	this._trialsData = [];
	this._currentTrialData = {};
	
	// get IP info of participant
	// note: since we make a GET call to http://ipinfo.io to get IP info,
	// these will most certainly not be available immediately after the call
	// to the ExperimentHandler constructor. 
	this.getParticipantIPInfo();
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

psychoJS.data.ExperimentHandler.prototype.save = function(attribs) {
	
	// collect session information:
	this._session['experimentName'] = expInfo['expName'];
	this._session['participantName'] = expInfo['participant'];
	this._session['sessionName'] = expInfo['session'];
	this._session['sessionDate'] = expInfo['date'];


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

	// upload data to OSF via the experiment server:
	if (this.repository === 'OSF_VIA_EXPERIMENT_SERVER') {
		psychoJS.resourceManager.OSFEXPUploadData(this.experimentServerUrl, this._session, csv);
	}
	// save data to a local excel file:
	else if (this.repository === 'LOCAL_EXCEL') {
		// TODO
	}
}


/**
 * Get the IP information of the participant
 * 
 * <p>Note: we use http://ipinfo.io</p>
 */
psychoJS.data.ExperimentHandler.prototype.getParticipantIPInfo = function() {
	var self = this;
	$.ajax({
		type: "GET",
		url: 'http://ipinfo.io',
		dataType: 'json',
	}).then(
		function (response) {
			self._session['IP'] = response.ip;
			self._session['hostname'] = response.hostname;
			self._session['city'] = response.city;
			self._session['region'] = response.region;
			self._session['country'] = response.country;
			self._session['location'] = response.loc;
		},
		function (error){
			console.log('Error obtaining IP info of participant:');
			console.log(error);
		}
	);
}


/**
 * Returns the attribute names and values for the current trial of a particular loop.
 * Does not return data inputs from the subject, only info relating to the trial
 * execution.
 * 
 * @param {Object} loop 
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
