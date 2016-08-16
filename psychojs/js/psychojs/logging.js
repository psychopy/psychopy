/**
 * Logging component of psychoJS
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


psychoJS.logging.getLevel = function(level) {
	var levelName = psychoJS.logging._levelNames[level];
	if (levelName) {
		return levelName;
	}
	else {
		return "Level " + level;
	}
}

psychoJS.logging.addLevel = function(level, levelName) {
	psychoJS._levelNames[level] = levelName;
	psychoJS._levelNames[levelName] = level;
}


psychoJS.logging.defaultClock = psychoJS.clock.monotonicClock;
psychoJS.logging.setDefaultClock = function(clock) {
    psychoJS.logging.defaultClock = clock;
}


psychoJS.logging._LogEntry = function(attribs) {
	this.t = getAttrib(attribs, 't');
	this.t_ms = this.t * 1000;
	this.level = getAttrib(attribs, 'level');
	this.levelname = psychoJS.logging.getLevel(this.level);
	this.message = getAttrib(attribs, 'message');
	this.obj = getAttrib(attribs, 'obj');	
}


/**
 * Parent LogOutput class
 */
psychoJS.logging.LogOutput = function(level, logger) {
	this.logger = logger || psychoJS.logging.root;
	this.logger.addTarget(this)
	this.level = level || psychoJS.logging.WARNING;
}

psychoJS.logging.LogOutput.prototype.setLevel = function(level) {
	this.level = level;
	this.logger._calcLowestTarget();
}	

psychoJS.logging.LogOutput.prototype.write = function(txt) {
	throw "Method write must be overriden.";
}	

psychoJS.logging.LogOutput.prototype.flush = function() {
	// by default do nothing
}


/**
 * Console output
 */
psychoJS.logging.ConsoleLogOutput = function(level, logger) {
	psychoJS.logging.LogOutput.call(this, level, logger);
}
psychoJS.logging.ConsoleLogOutput.prototype = Object.create(psychoJS.logging.LogOutput.prototype);

psychoJS.logging.ConsoleLogOutput.prototype.write = function(txt) {
	console.log(txt);
}



psychoJS.logging._Logger = function(format) {
	this.targets = [];
	this.flushed = [];
	this.toFlush = [];
	this.format = format || "################ {t} \t{levelname} \t{message}";
	this.lowestTarget = 50;
}

psychoJS.logging._Logger.prototype.addTarget = function(target) {
	this.targets.push(target);
	this._calcLowestTarget();
}

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

psychoJS.logging._Logger.prototype.flush = function() {
console.log(">>>>>>>>>>> flushing log");
	// loop through targets then entries in toFlush
	// so that stream.flush can be called just once
	for(var i = 0; i < this.targets.length; ++i) {
		var target = this.targets[i];
console.log(">>>>>>>>>>> flushing " + this.toFlush.length + " entries");
		for (var j = 0; j < this.toFlush.length; ++j) {
			var thisEntry = this.toFlush[j];
			
			if (thisEntry.level >= target.level) {
				var formatted = this.format.format(thisEntry);
				target.write(formatted + '\n');
			}
		}
		
		target.flush();
	}
	// finished processing entries - move them to this.flushed
	this.flushed.concat(this.toFlush);
	this.toFlush = [];  // a new empty list
	
}


psychoJS.logging.root = new psychoJS.logging._Logger()
psychoJS.logging.console = new psychoJS.logging.ConsoleLogOutput()

psychoJS.logging.flush = function(logger) {
	logger = logger || psychoJS.logging.root;
	logger.flush();
}

psychoJS.logging.critical = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.CRITICAL, t, obj);
}
psychoJS.logging.fatal = psychoJS.logging.critical;

psychoJS.logging.error = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.ERROR, t, obj);
}

psychoJS.logging.warning = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.WARNING, t, obj);
}

psychoJS.logging.data = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.DATA, t, obj);
}

psychoJS.logging.exp = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.EXP, t, obj);
}

psychoJS.logging.info = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.INFO, t, obj);
}

psychoJS.logging.debug = function(msg, t, obj) {
	psychoJS.logging.root.log(msg, psychoJS.logging.DEBUG, t, obj);
}

psychoJS.logging.log = function(msg, level, t, obj) {
	psychoJS.logging.root.log(msg, level, t, obj);
}

