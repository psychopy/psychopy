/**
 * Core component of psychoJS
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
psychoJS.core = {}
psychoJS.clock = {}


/**
 * Close everything and exit nicely at the end of the experiment
 * 
 * <p>Note: if the resource manager is busy, we inform the participant
 * that he or she needs to wait for a bit.</p>
 */
psychoJS.core.quit = function() {
	
	// actual quit callback:
	var doQuit = function() {
		// we only actually quit if the resource manager is ready:
		if (psychoJS.resourceManager.getStatus() !== 'READY') return;

		// destroy dialog boxes:
		psychoJS.gui.destroyDialog();

		// close everything:
		if (psychoJS.debug) console.log("exiting psychoJS");
		var children = document.body.children;
		for(var i = 0; i < children.length; ++i) {
			document.body.removeChild(children[i]);
		}
		
		// flush logs and finish:
		psychoJS.logging.flush();
		psychoJS.finished = true;
		if (psychoJS.debug) console.log("Quit");
	}
	
	// if the resource manager is not ready, we inform
	// the participant that he or she needs to wait:
	if (psychoJS.resourceManager.getStatus() !== 'READY') {
		psychoJS.resourceManager.setStatusCallback(doQuit);
		psychoJS.gui.dialog({'warning' : 'The resource manager is busy. Please wait a few moments.', 'showOK' : false});
	} else
		doQuit();
}


psychoJS.core._coreLoadTime = new Date().getTime(); 


/**
 * Get the current time since the start of the context (if performance.now() is used)
 * or since psychoJS.core was loaded (if new Date().getTime() is used).
 * 
 * @return Time - elapsed in seconds.
 */
psychoJS.core.getTime = function () {
	if (false && performance && performance.now) {
		// returns monotonic time
		return performance.now() / 1000; 
	}
	else {
		// if performance.now() is not available, fall back to using Date which could be modified
		return (new Date().getTime() - psychoJS.core._coreLoadTime) / 1000; 
	}
}

psychoJS.clock.getTime = psychoJS.core.getTime;



/**
 * A convenient class to keep track of time in your experiments.
 * @constructor
 * 
 * @param startTime Origin time or undefined - The current time will be used in the later case.    
 */
psychoJS.core.MonotonicClock = function(startTime) {
	this._timeAtLastReset = startTime || psychoJS.core.getTime();		
}


/**
 * @return the current time on this clock in secs.
 */
psychoJS.core.MonotonicClock.prototype.getTime = function() {
	return psychoJS.core.getTime() - this._timeAtLastReset;
}


/**
 * @return the current offset being applied to the high resolution timebase used by Clock.
 */
psychoJS.core.MonotonicClock.prototype.getLastResetTime = function() {
	return this._timeAtLastReset;		
}

psychoJS.clock.monotonicClock = new psychoJS.core.MonotonicClock();
psychoJS.core.monotonicClock = psychoJS.clock.monotonicClock;


/**
 * A convenient class to keep track of time in your experiments.
 * You can have as many independent clocks as you like (e.g. one
 * to time responses, one to keep track of stimuli...)
 * This clock is identical to the class `psychoJS.core.MonotonicClock`
 * except that it can also be reset to 0 or another value at any point.
 */
psychoJS.core.Clock = function() {
	psychoJS.core.MonotonicClock.call(this);
}

psychoJS.core.Clock.prototype = Object.create(psychoJS.core.MonotonicClock.prototype);


/**
 * Reset the time on the clock. With no args time will be
 * set to zero. If a float is received this will be the new
 * time on the clock.
 */
psychoJS.core.Clock.prototype.reset = function(newT) {
	newT = newT || 0;
	this._timeAtLastReset = psychoJS.core.getTime() + newT;		
}


/**
 * Add more time to the clock's 'start' time (t0).
 * Note that, by adding time to t0, you make the current time
 * appear less. Can have the effect that getTime() returns a negative
 * number that will gradually count back up to zero.
 */
psychoJS.core.Clock.prototype.add = function(t) {
	this._timeAtLastReset += t;
}


/**
 * Similar to a class `psychoJS.core.Clock` except that time counts down
 * from the time of last reset.
 */
psychoJS.core.CountdownTimer = function(startTime) {
	startTime = startTime || 0;
	this._timeAtLastReset = psychoJS.core.getTime()
	this._countdown_duration = startTime;
	if (startTime) {
		this.add(startTime)
	}
}


/**
 * Add more time to the clock's 'start' time (t0).
 * Note that, by adding time to t0, you make the current time
 * appear less. Can have the effect that getTime() returns a negative
 * number that will gradually count back up to zero.
 * 
 */
psychoJS.core.CountdownTimer.prototype.add = function(t) {
	this._timeAtLastReset += t;
}


/**
 * Reset the time on the clock.
 * 
 * @param {number} t - if undefined time will be set to zero otherwise this will be the new time on the clock.
 */
psychoJS.core.CountdownTimer.prototype.reset = function(t) {
	if (t === undefined) {
		this._timeAtLastReset = psychoJS.core.getTime() + this._countdown_duration;
	}
	else {
		this._countdown_duration = t;
		this._timeAtLastReset = psychoJS.core.getTime() + t;
	}
}


/**
 * @return the current time left on this timer in secs.
 */
psychoJS.core.CountdownTimer.prototype.getTime = function() {
	return this._timeAtLastReset - psychoJS.core.getTime();
}


