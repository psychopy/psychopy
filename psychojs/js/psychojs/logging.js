/**
 * Logging component of PsychoJS
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
psychoJS.logging = {};


psychoJS.logging.CRITICAL = 50;
psychoJS.logging.FATAL = psychoJS.logging.CRITICAL;
psychoJS.logging.ERROR = 40;
psychoJS.logging.WARNING = 30;
psychoJS.logging.WARN = psychoJS.logging.WARNING;
psychoJS.logging.DATA = 25;
psychoJS.logging.EXP = 22;
psychoJS.logging.INFO = 20;
psychoJS.logging.DEBUG = 10;
psychoJS.logging.NOTSET = 0;


psychoJS.logging._levelNames = {
    'CRITICAL': psychoJS.logging.CRITICAL,
    'ERROR': psychoJS.logging.ERROR,
    'DATA': psychoJS.logging.DATA,
    'EXP': psychoJS.logging.EXP,
    'WARN': psychoJS.logging.WARNING,
    'WARNING': psychoJS.logging.WARNING,
    'INFO': psychoJS.logging.INFO,
    'DEBUG': psychoJS.logging.DEBUG,
    'NOTSET': psychoJS.logging.NOTSET 
};
psychoJS.logging._levelNames[psychoJS.logging.CRITICAL] = 'CRITICAL';
psychoJS.logging._levelNames[psychoJS.logging.ERROR] = 'ERROR';
psychoJS.logging._levelNames[psychoJS.logging.DATA] = 'DATA';
psychoJS.logging._levelNames[psychoJS.logging.EXP] = 'EXP';
psychoJS.logging._levelNames[psychoJS.logging.WARNING] =  'WARNING';
psychoJS.logging._levelNames[psychoJS.logging.INFO] = 'INFO';
psychoJS.logging._levelNames[psychoJS.logging.DEBUG] = 'DEBUG';
psychoJS.logging._levelNames[psychoJS.logging.NOTSET] = 'NOTSET';

/**
 * Return the textual representation of logging level 'level'.
 * If the level is one of the predefined levels (CRITICAL, ERROR, WARNING,
 * INFO, DEBUG) then you get the corresponding string. If you have
 * associated levels with names using addLevelName then the name you have
 * associated with 'level' is returned.
 * If a numeric value corresponding to one of the defined levels is passed
 * in, the corresponding string representation is returned.
 * Otherwise, the string "Level %s" % level is returned.
 * @return the logging level.
 */
psychoJS.logging.getLevel = function(level) {
	var levelName = psychoJS.logging._levelNames[level];
	if (levelName) {
		return levelName;
	}
	else {
		return "Level " + level;
	}
}

/**
 * Associate 'levelName' with 'level'.
 * This is used when converting levels to text during message formatting.
 * @param {number} level - the numeric value of the error level.
 * @param {String} levelName - the name of the level used in message formatting.
 */
psychoJS.logging.addLevel = function(level, levelName) {
	psychoJS._levelNames[level] = levelName;
	psychoJS._levelNames[levelName] = level;
}

/**
 * Global defaultClock
 */
psychoJS.logging.defaultClock = psychoJS.clock.monotonicClock;

/**
 * Set the default clock to be used to reference all logging times.
 * 
 * <p>Beware that if you
 * reset the clock during the experiment then the resets will be
 * reflected here. That might be useful if you want your logs to be
 * reset on each trial, but probably not.</p>
 * 
 * @param {psychoJS.core.Clock} clock - the clock to be used to reference logging times.
 */
psychoJS.logging.setDefaultClock = function(clock) {
    psychoJS.logging.defaultClock = clock;
}


psychoJS.logging._LogEntry = function(attribs) {
	this.t = psychoJS.getAttrib(attribs, 't');
	this.t_ms = this.t * 1000;
	this.level = psychoJS.getAttrib(attribs, 'level');
	this.levelname = psychoJS.logging.getLevel(this.level);
	this.message = psychoJS.getAttrib(attribs, 'message');
	this.obj = psychoJS.getAttrib(attribs, 'obj');	
}

/**
 * @constructor
 * Maintains a set of log targets.
 * this.targets is a list of associative arrays {'stream':stream, 'level':level}
 * 
 * @param format {String} - the format log messages should use.
 */
psychoJS.logging._Logger = function(format) {
	this.targets = [];
	this.flushed = [];
	this.toFlush = [];
	this.format = format || "################ {t} \t{levelname} \t{message}";
	this.lowestTarget = 50;
}

/**
 * Add a target to the logger.
 * @param {psychoJS.logging.LogOutput} target - the target to be added.
 */
psychoJS.logging._Logger.prototype.addTarget = function(target) {
	this.targets.push(target);
	this._calcLowestTarget();
}

/**
 * Remove a target from the logger.
 * @param {psychoJS.logging.LogOutput} target - the target to removed added.
 */
psychoJS.logging._Logger.prototype.removeTarget = function(target) {
	var index = this.targets.indexOf(target);
	if (index >= 0) {
		this.targets.splice(index, 1);
	}
	this._calcLowestTarget();
}

psychoJS.logging._Logger.prototype._calcLowestTarget = function() {
	this.lowestTarget = 50;
	for(var i = 0; i < this.targets.length; ++i) {
		var target = this.targets[i];
		this.lowestTarget = Math.min(this.lowestTarget, target.level);
	}
}

/**
 * Add the `message` to the log stack at the appropriate `level`
 * If no relevant targets (files or console) exist then the message is
 * simply discarded.
 * 
 * @param {String} message - the message to be written to all targets of this Logger.
 * @param {number} level - the level of this message.
 * @param {number} t - the time of this message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging._Logger.prototype.log = function(message, level, t, obj) {
	// check for at least one relevant logger
	if (level < self.lowestTarget) {
		return;
	}
	
	// check time
	t = t || psychoJS.logging.defaultClock.getTime();

	// add message to list
	this.toFlush.push(new psychoJS.logging._LogEntry({t:t, level:level, message:message, obj:obj}));
}

/**
 * Process all current messages to each target.
 */
psychoJS.logging._Logger.prototype.flush = function() {
	if (psychoJS.debug) console.log("flushing logs");
	
	// loop through targets then entries in toFlush
	// so that stream.flush can be called just once
	for(var i = 0; i < this.targets.length; ++i) {
		var target = this.targets[i];
		if (psychoJS.debug) console.log("- target: " + target.getName() + ", flushing " + this.toFlush.length + " entries:");
		
		for (var j = 0; j < this.toFlush.length; ++j) {
			var thisEntry = this.toFlush[j];
			
			if (thisEntry.level >= target.level) {
				var formattedEntry = this.format.format(thisEntry);
				target.write(formattedEntry + '\n');
			}
		}
		
		target.flush();
	}
	
	// finished processing entries - move them to this.flushed
	this.flushed.concat(this.toFlush);
	this.toFlush = [];  // a new empty list
}


psychoJS.logging.root = new psychoJS.logging._Logger();


/**
 * Send current messages in the log to all targets.
 * 
 * @param {psychoJS.logging._Logger} logger - the logger to flush. By default this is psychoJS.logging.root.
 */
psychoJS.logging.flush = function(logger) {
	logger = logger || psychoJS.logging.root;
	logger.flush();
}

/**
 * Send the message to any receiver of logging info of level `CRITICAL` or higher.
 * 
 * @param {String} msg - the message to log.
 * @param {number} t - the time of the message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging.critical = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.CRITICAL, t, obj);
}

/**
 * Send the message to any receiver of logging info of level `FATAL` or higher.
 * 
 * @param {String} msg - the message to log.
 * @param {number} t - the time of the message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging.fatal = psychoJS.logging.critical;

/**
 * Send the message to any receiver of logging info of level `ERROR` or higher.
 * 
 * @param {String} msg - the message to log.
 * @param {number} t - the time of the message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging.error = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.ERROR, t, obj);
}

/**
 * Send the message to any receiver of logging info of level `WARNING` or higher.
 * 
 * @param {String} msg - the message to log.
 * @param {number} t - the time of the message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging.warning = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.WARNING, t, obj);
}

/**
 * Send the message to any receiver of logging info of level `DATA` or higher.
 * 
 * @param {String} msg - the message to log.
 * @param {number} t - the time of the message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging.data = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.DATA, t, obj);
}

/**
 * Send the message to any receiver of logging info of level `EXP` or higher.
 * 
 * @param {String} msg - the message to log.
 * @param {number} t - the time of the message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging.exp = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.EXP, t, obj);
}

/**
 * Send the message to any receiver of logging info of level `INFO` or higher.
 * 
 * @param {String} msg - the message to log.
 * @param {number} t - the time of the message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging.info = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.INFO, t, obj);
}

/**
 * Send the message to any receiver of logging info of level `DEBUG` or higher.
 * 
 * @param {String} msg - the message to log.
 * @param {number} t - the time of the message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging.debug = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.DEBUG, t, obj);
}

/**
 * Send the message to any receiver of logging info of level `level` or higher.
 * 
 * @param {String} msg - the message to log.
 * @param {number} level - the level of this message.
 * @param {number} t - the time of the message.
 * @param {Object} obj - the object this message concerns.
 */
psychoJS.logging.log = function(msg, level, t, obj) {
	psychoJS.logging.root.log(msg, level, t, obj);
}


/**
 * Parent LogOutput class
 */
psychoJS.logging.LogOutput = function(name, level, logger) {
	this.logger = logger || psychoJS.logging.root;
	this.logger.addTarget(this)
	this.level = level || psychoJS.logging.WARNING;
	this._name = name || 'Generic Log';
}

/**
 * 
 */
psychoJS.logging.LogOutput.prototype.setLevel = function(level) {
	this.level = level;
	this.logger._calcLowestTarget();
}	


/**
 * Write text to log output.
 *
 * @param {string} txt - text to be written
 */
psychoJS.logging.LogOutput.prototype.write = function(txt) {
	throw "Method write must be overriden.";
}	

/**
 * Flush the logs in this LogOutput. Behavior depends on the actual LogOutput implementation.
 * Some classes will withhold writes until flushing (eg. [ServerLogOutput]{@link psychoJS.logging.ServerLogOutput}).
 * Others will write immediately and flush will have no effect (eg. [ConsoleLogOutput]{@link psychoJS.logging.ConsoleLogOutput}).
 */
psychoJS.logging.LogOutput.prototype.flush = function() {
	// by default do nothing
}

/**
 * @return the name of this LogOutput.
 */
psychoJS.logging.LogOutput.prototype.getName = function() {
	return this._name;
}


/**
 * Create a logging output to the browser's console.
 *
 * @constructor
 */
psychoJS.logging.ConsoleLogOutput = function(level, logger) {
	psychoJS.logging.LogOutput.call(this, 'Console Log', level, logger);
}
psychoJS.logging.ConsoleLogOutput.prototype = Object.create(psychoJS.logging.LogOutput.prototype);

/**
 * Write text to log output.
 *
 * @param {string} txt - text to be written
 */
psychoJS.logging.ConsoleLogOutput.prototype.write = function(txt) {
	console.log(txt);
}

psychoJS.logging.console = new psychoJS.logging.ConsoleLogOutput();


/**
 * Create a persistent logging output to a server.
 *
 * <p>This logging output will upload the logs to a local or distant data repository,
 * possibly via an experiment server.</p>
 *
 * @constructor
 */
psychoJS.logging.ServerLogOutput = function(level, logger) {
	psychoJS.logging.LogOutput.call(this, 'Server Log', level, logger);
}
psychoJS.logging.ServerLogOutput.prototype = Object.create(psychoJS.logging.LogOutput.prototype);


/**
 * Set the parameters of the logging output.
 *
 * @param {Object} attribs - associative array used to store the following parameters:
 * @param {Object} attribs.level - logging level
 * @param {('OSF_VIA_EXPERIMENT_SERVER'|'EXPERIMENT_SERVER')}
 * attribs.saveTo - repository to which the data is saved
 * @param {Object} attribs.experimentInfo - information about the experiment
 */
psychoJS.logging.ServerLogOutput.prototype.set = function(attribs) {
	var errorPrefix = '{ "function" : "logging.ServerLogOutput.set", "context" : "when creating ServerLogOutput", "error" :';
	
	this._level = psychoJS.getAttrib(attribs, 'level');
	this._saveTo = psychoJS.getAttrib(attribs, 'saveTo');
	this._experimentInfo = psychoJS.getAttrib(attribs, 'experimentInfo');

	this.setLevel(this._level);
	if (['OSF_VIA_EXPERIMENT_SERVER', 'EXPERIMENT_SERVER'].indexOf(this._saveTo) == -1) {
		throw errorPrefix + '"unknown repository: ' + this._saveTo + '", "stack" : ' + getErrorStack() + ' }';
	}
}


/**
 * Write text to log output.
 *
 * <p>This method does nothing. The log entries are saved all at once upon call to the
 * [flush method]{@link psychoJS.logging.ServerLogOutput#flush}</p>
 *
 * @param {string} txt - text to be written
 */
psychoJS.logging.ServerLogOutput.prototype.write = function(txt) {}


/**
 * Flush the logs to the server.
 */
psychoJS.logging.ServerLogOutput.prototype.flush = function() {
	var errorPrefix = '{ "function" : "logging.ServerLogOutput.flush", "context" : "when flushing logs to server", "error" : ';
	
	try {
		// prepare session information:
		var session = {};
		session['experimentName'] = this._experimentInfo['expName'];
		session['participantName'] = this._experimentInfo['participant'];
		session['sessionName'] = this._experimentInfo['session'];
		 // note: we use getDateStr rather than this._experimentInfo['date'] since the latter
		 // may not have been set if the participant cancels the experiment at the initial dialog box
		session['sessionDate'] = psychoJS.data.getDateStr();
		for (property in psychoJS._IP)
		if (psychoJS._IP.hasOwnProperty(property)) {
			session[property] = psychoJS._IP[property];
		}
		
		// concatenate the logs:
		var concatenatedLogs = '';
		for (var j = 0; j < this.logger.toFlush.length; ++j) {
			var thisEntry = this.logger.toFlush[j];
				
			if (thisEntry.level >= this.level) {
				var formattedEntry = this.logger.format.format(thisEntry);
				concatenatedLogs = concatenatedLogs + formattedEntry + '\n';
			}
		}
		
		if (psychoJS.debug) console.log(concatenatedLogs);
		
		// upload log to the experiment server:
		if (this._saveTo === 'EXPERIMENT_SERVER') {
			psychoJS.resourceManager.EXPUploadData(session, 'LOG', concatenatedLogs);
		}	
		// upload log to OSF via the experiment server:
		else if (this._saveTo === 'OSF_VIA_EXPERIMENT_SERVER') {
			psychoJS.resourceManager.OSFEXPUploadData(session, 'LOG', concatenatedLogs);
		}
	}
	catch (exception) {
		throw errorPrefix + exception + ', "stack" : ' + getErrorStack() + ' }';
	}
}

psychoJS.logging.server = new psychoJS.logging.ServerLogOutput();
