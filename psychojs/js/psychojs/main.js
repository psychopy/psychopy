/**
 * Main component of psychoJS
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
var psychoJS = {}


/**
 * Initialise PsychoJS
 * 
 * <p>Note: 'init' must be called once the document is ready:</p>
 * <code>$(document).ready(function() {<br>
 * ...<br>
 * psychoJS.init();</code>
 *
 * @param {psychoJS.visual.Window} window - the psychoJS [Window]{@link psychoJS.visual.Window}
 * 
 */
psychoJS.init = function(window) {
	// component states:
	psychoJS.NOT_STARTED = "NOT_STARTED";
	psychoJS.STARTED = "STARTED";
	psychoJS.FINISHED = "FINISHED";

	// debugging:
	psychoJS.debug = true;
	if (psychoJS.debug) console.log("init PsychoJS");
	
	psychoJS.frameCount = 0;
	
	// note: we create the resource manager here, but its parameters
	// will be set in the psychopy generated .html code
	psychoJS.resourceManager = new psychoJS.io.ResourceManager();
	
	psychoJS.window = window;
	
		
	// get IP info of participant
	// note: since we make a GET call to http://ipinfo.io to get IP info,
	// these will most certainly not be available immediately after the call
	// to psychoJS.init. 
	psychoJS._IP = {};
	psychoJS.getParticipantIPInfo();
}


/**
 * Get the IP information of the participant, asynchronously.
 * 
 * <p>Note: we use http://ipinfo.io</p>
 */
psychoJS.getParticipantIPInfo = function() {
	$.ajax({
		type: "GET",
		url: 'http://ipinfo.io',
		dataType: 'json',
	}).then(
		function (response) {
			psychoJS._IP['IP'] = response.ip;
			psychoJS._IP['hostname'] = response.hostname;
			psychoJS._IP['city'] = response.city;
			psychoJS._IP['region'] = response.region;
			psychoJS._IP['country'] = response.country;
			psychoJS._IP['location'] = response.loc;
		},
		function (error) {
			throw '{ "function" : "psychoJS.getParticipantIPInfo", "context" : "when getting the IP information of the participant", "error" : "' + error.statusText + '", "stack" : ' + getErrorStack() + ' }';
		}
	);
}


/**
 * Set up the keyboard and window callback functions.
 */
psychoJS.setupCallbacks = function() {
	// key events:
	document.addEventListener("keydown", psychoJS.event._keyDownHandler, false);
	
	// resize events:
	$(window).on("resize", psychoJS.onResize);
	$(window).on("orientationchange", psychoJS.onResize);
	
	return psychoJS.NEXT;
}


/**
 * Define the canvas's aspect ratio
 */
var STAGE_WIDTH = 480;
var STAGE_HEIGHT = 320;


/**
 * Window resize callback
 */
psychoJS.onResize = function(event) {
	var width = $(window).width();
	var height = $(window).height();
	
	// maintain aspect ratio:
	var ratioWidth = width / STAGE_WIDTH;
	var ratioHeight = height / STAGE_HEIGHT;
	if (ratioWidth < ratioHeight) {
	    var ratio = ratioWidth;
	} else {
	    ratio = ratioHeight;
	}
	var ratioWidth = Math.floor(STAGE_WIDTH * ratio);
	var ratioHeight = Math.floor(STAGE_HEIGHT * ratio);
	
	psychoJS.window._renderer.view.style.width = ratioWidth + 'px';
	psychoJS.window._renderer.view.style.height = ratioHeight + 'px';
	psychoJS.window._renderer.view.style.left = width/2 - ratioWidth/2 + "px";
	psychoJS.window._renderer.view.style.top = height/2 - ratioHeight/2 + "px";
	
	psychoJS.window._renderer.resize(ratioWidth, ratioHeight);
	
	psychoJS.window._container.position.x = ratioWidth/2;
	psychoJS.window._container.position.y = ratioHeight/2;
	// positive values of y are to the top:
	psychoJS.window._container.scale.y = -1;
}


/**
 * Update the canvas on each frame
 */
psychoJS.onUpdate = function()
{
	++psychoJS.frameCount;
	if (psychoJS.debug) console.log("frame " + psychoJS.debug);
	
	stats.begin();
	
	renderer.render(stage);
	requestAnimationFrame(psychoJS.onUpdate);
	
	stats.end();
}

