/**
 * I/O component of psychoJS
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
psychoJS.io = {}


/**
 * Create a new resource manager.
 * 
 * <p>The resource manager synchronously or asynchronously uploads resources
 * to and from a local or distant data repository, possibly via an experiment server.</p>
 * <p>Note: The parameters are set in the [set function]{@link psychoJS.io.ResourceManager#set}.</p>
 * 
 * @constructor
 */
psychoJS.io.ResourceManager = function() {
	if (psychoJS.debug) console.log("ResourceManager created");
	
	psychoJS.visual.MinimalStim.call(this, {'name' : 'resourceManager', 'autoLog' : false});
}
psychoJS.io.ResourceManager.prototype = Object.create(psychoJS.visual.MinimalStim.prototype);


/**
 * Set the parameters of the resource manager.
 * 	
 * @param {Object} attribs - associative array used to store the following parameters:
 * @param {psychoJS.visual.Window} attribs.win - the psychoJS [Window]{@link psychoJS.visual.Window}
 * @param {('OSF'|'EXPERIMENT_SERVER')} attribs.downloadFrom - type of repository from which the data is downloaded
 * @param {String} attribs.projectId - ID of the project on OSF
 * @param {('PUBLIC'|'PRIVATE')} attribs.projectStatus - status of the project
 * @param {psychoJS.core.Clock} attribs.clock - clock
 * @param {String} [attribs.projectName] - name of the project on OSF
 * @param {String} [attribs.projectContributor] - name of the project contributor on OSF
 * @param {String} [attribs.username] - username of the project contributor on OSF
 * @param {String} [attribs.password] - password of the project contributor on OSF
 */
psychoJS.io.ResourceManager.prototype.set = function(attribs) {
	var errorPrefix = '{ "function" : "io.ResourceManager.set", "context" : "when setting the parameters of the resource manager", '
		+ '"error" : ';
		
	this.win = psychoJS.getAttrib(attribs, 'win');
	this.downloadFrom = psychoJS.getAttrib(attribs, 'downloadFrom');
	this.projectName = psychoJS.getAttrib(attribs, 'projectName');
	this.projectId = psychoJS.getAttrib(attribs, 'projectId');
	this.projectContributor = psychoJS.getAttrib(attribs, 'contributor');
	this.projectStatus = psychoJS.getAttrib(attribs, 'projectStatus');
	this.username = psychoJS.getAttrib(attribs, 'username');
	this.password = psychoJS.getAttrib(attribs, 'password');
	this.clock = psychoJS.getAttrib(attribs, 'clock');
	
	// check arguments:
	if (['PUBLIC', 'PRIVATE'].indexOf(this.projectStatus) == -1) {
		throw errorPrefix + '"unknown project status: ' + this.projectStatus + '", "stack" : ' + getErrorStack() + ' }';
	}
	if (['OSF', 'EXPERIMENT_SERVER'].indexOf(this.downloadFrom) == -1) {
		throw errorPrefix + '"unknown type of repository: ' + this.downloadFrom + '", "stack" : ' + getErrorStack() + ' }';
	}

	// status of the resource manager ('READY'|'REGISTERING'|'BUSY'|'ERROR'):
	this._status = 'READY';
	this._statusCallback = undefined;
	
	// default resource callback function does nothing
	this._resourceCallback = function(message) {};
	
	// resources:
	this._experimentServerResourceDirectory = undefined;
	this._resources = {};

	// OSF specific:
	this._OsfUrl = 'https://api.osf.io/v2/';
	this._CorsProxyUrl = ''; // e.g. 'https://cors-anywhere.herokuapp.com/'
	this._OsfAjaxSettings = {type: "GET", async: true, crossDomain: true, dataType: 'json'};
}


/**
 * Get the resource manager status.
 * 
 * @return {('READY'|'REGISTERING'|'BUSY'|'ERROR')} status
 */
psychoJS.io.ResourceManager.prototype.getStatus = function() {
	return this._status;
}


/**
 * Set the resource manager status.
 *
 * <p> Note: the status callback function is called, if it has been previously set with
 * [setStatusCallback]{@link psychoJS.io.ResourceManager#setStatusCallback}.</p>
 * @param {('READY'|'REGISTERING'|'BUSY'|'ERROR')} newStatus - the new status
 */
psychoJS.io.ResourceManager.prototype.setStatus = function(newStatus) {
	var errorPrefix = '{ "function" : "io.ResourceManager.setStatus", "context" : "when changing the status of the resource manager", '
		+ '"error" : ';
	if (['READY', 'REGISTERING', 'BUSY', 'ERROR'].indexOf(newStatus) == -1) {
		throw errorPrefix + '"unknown status: ' + newStatus + '", "stack" : ' + getErrorStack() + ' }';
	}
	
	this._status = newStatus;
	
	if (undefined !== this._statusCallback)
		this._statusCallback(this._status);
}


/**
 * Set the status change call back function.
 * 
 * @param {Object} callback - the function called whenever the resource manager's status changes
 */
psychoJS.io.ResourceManager.prototype.setStatusCallback = function(callback) {
	this._statusCallback = callback;
}


/**
 * Reset the resource manager status to 'READY'.
 * 
 * @return {'READY'} the new status
 */
psychoJS.io.ResourceManager.prototype.resetStatus = function() {
	this.setStatus('READY');
	return this._status;
}


/**
 * Set the callback function for all resource registration and download events.
 * 
 * <p>Note: the callback function is passed a stringified json message.</p>
 * 
 * @param {Object} callbackFunction - the function called each time
 * a resource registration or download event is fired
 */
psychoJS.io.ResourceManager.prototype.setResourceCallback = function(callbackFunction) {
	this._resourceCallback = callbackFunction;
}


/**
 * Schedule the registration of all available resources for this experiment.
 * 
 * <p>Note: The scheduler will wait for the registration to complete before moving onto the next task.</p>
 * 
 * @param {psychoJS.Scheduler} scheduler - the registration [scheduler] {@link psychoJS.Scheduler}
 */
psychoJS.io.ResourceManager.prototype.scheduleRegistration = function(scheduler) {
	this._RegistrationComponent = [];
	scheduler.add(this.Loop(this, this._RegistrationComponent, psychoJS.io.ResourceManager.prototype.registerAvailableResources));
}


/**
 * Register all available resources for this experiment.
 * 
 * <p>registerAvailableResources first queries the list of resources from either
 * the OSF server or the experiment server, before registering each of them
 * with this resource manager.</p>
 * 
 * <p>Note: We assume that the server.php file is in the same directory on the 
 * experiment server as the experiment html file itself.</p>
 * 
 * @param {psychoJS.io.ResourceManager} resourceManager - the [resource manager]{@link psychoJS.io.ResourceManager}
 * @param {Object} component - dummy component used by the [Loop function]{@link psychoJS.io.ResourceManager#Loop} to block
 * the scheduler passed to [scheduleRegistration]{@link psychoJS.io.ResourceManager#scheduleRegistration} until the registration has completed
 * @param {Object} [arg] - argument (currently unused)
 * 
 * @throws {String} Throws a JSON string exception if the registration failed.
 */
psychoJS.io.ResourceManager.prototype.registerAvailableResources = function(resourceManager, component, arg) {
	var errorPrefix = '{ "function" : "io.ResourceManager.registerAvailableResources", "context" : "when registering all available resources", '
		+ '"error" : ';
	resourceManager._resourceCallback('{ "message" : "resource registration started" }');
	resourceManager.setStatus('REGISTERING');
	
	// query the list of resources directly from the OSF server:
	if (resourceManager.downloadFrom === 'OSF') {
		// TODO
	}
		
	// query the list of resources from the experiment server:
	else if (resourceManager.downloadFrom === 'EXPERIMENT_SERVER') {
		$.post('./server.php',
			{'command' : 'LIST_RESOURCES'})
		.then(
			function (result) {
				try {
					var json = JSON.parse(result);
				} catch (exception) {
					resourceManager.setStatus('ERROR');
					// JSON.parse will throw a SyntaxError if result is not a JSON string
					// this might happens if php is not available on the server running server.php,
					// in which case an HTTP POST request to server.php returns the code of server.php
					throw errorPrefix + '"unexpected answer from the experiment server", "stack" : ' + getErrorStack() + ' }';
				}
				
				if ('resources' in json) {
					
					resourceManager._experimentServerResourceDirectory = json.resourceDirectory;
					
					var nbResource = json.resources.length;
					for (var i = 0; i < nbResource; i++) {
						resourceManager.registerResource(json.resources[i]);
					}
					resourceManager._resourceCallback('{ "message" : "all resources registered", "number" : ' + nbResource.toString() + ' }');
					resourceManager.setStatus('READY');
						
					if (component !== undefined) {
						// leave the generic loop:
						component.status = psychoJS.FINISHED;
					}
				} else {
					resourceManager.setStatus('ERROR');
					throw errorPrefix + $.trim(result) + ', "stack" : ' + getErrorStack() + ' }';
				}
			}, 
			function (error){
				resourceManager.setStatus('ERROR');
				if ('statusText' in error)
					throw errorPrefix + '"' + $.trim(error.statusText) + '", "stack" : ' + getErrorStack() + ' }';
				else
					throw errorPrefix + error + ', "stack" : ' + getErrorStack() + ' }';
			}
		);
	}
}


/**
 * Register a resource.
 * 
 * <p>Note: the [callback function]{@link psychoJS.io.ResourceManager#setResourceCallback} is called with
 * the following stringified json object: <blockquote>{"message" : "resource registered", "resource" : "&lt;resource name&gt;"}</blockquote></p>
 * 
 * @param {string} resourceName - name of the resource to be registered
 */
psychoJS.io.ResourceManager.prototype.registerResource = function(resourceName) {
	this._resources[resourceName] = undefined;
	this._resourceCallback('{ "message" : "resource registered", "resource" : "' + resourceName + '" }');
}


/**
 * Query the value of a resource.
 * 
 * @param {string} name of the requested resource
 * @return {Object} value of the resource or exception if resource is unknown
 */
psychoJS.io.ResourceManager.prototype.getResource = function(resourceName) {
	var errorPrefix = '{ "function" : "io.ResourceManager.getResource", "context" : "when getting resource", "error" : ';
	if (!this._resources.hasOwnProperty(resourceName)) {
		throw errorPrefix + '"unknown resource: ' + resourceName + '", "stack" : ' + getErrorStack() + ' }';
	}
	
	return this._resources[resourceName];
}


/**
 * Schedule the asynchronous download of the registered resources.
 * 
 * <p>Note: The scheduler will wait for the download of all registered
 * resources to complete before moving onto the next task.</p>
 * 
 * @param {Object} scheduler - the [resource scheduler]{@link psychoJS.Scheduler}
 **/
psychoJS.io.ResourceManager.prototype.scheduleDownload = function(resourceScheduler) {
	// download resources from OSF:
	if (this.downloadFrom === 'OSF') {
		
		// if project is private, we need to authenticate:
		if (this.projectStatus === 'PRIVATE') {
			// authenticate and get token:
			this._Authenticate = [];
			resourceScheduler.add(this.Loop(this, this._Authenticate, psychoJS.io.ResourceManager.prototype.OSFAuthenticate));
			//this._Authenticate.status = psychoJS.NOT_STARTED;
			//resourceScheduler.add(psychoJS.io.ResourceManager.prototype.AuthenticateLoop(this));
		}
		
		/* DEPRECATED: we now use projectID by default
		// get project ID:
		this._ProjectIDComponent = [];
		resourceScheduler.add(this.Loop(this, this._ProjectIDComponent, psychoJS.io.ResourceManager.prototype.OSFProjectID));
		*/
		
		// get storage provider:
		this._StorageProviderComponent = [];
		resourceScheduler.add(this.Loop(this, this._StorageProviderComponent, psychoJS.io.ResourceManager.prototype.OSFStorageProvider));

		// get download links for all resources:
		this._downloadLinkDictionary = [];
		this._DowloadLinkComponent = [];
		resourceScheduler.add(this.Loop(this, this._DowloadLinkComponent, psychoJS.io.ResourceManager.prototype.OSFDownloadLink));
		
		// schedule download of resources:
		this._DowloadResourceComponents = {};
		for (resourceName in this._resources)
			if (this._resources.hasOwnProperty(resourceName)) {
				this._DowloadResourceComponents[resourceName] = [];
				resourceScheduler.add(this.Loop(this, this._DowloadResourceComponents[resourceName], psychoJS.io.ResourceManager.prototype.OSFDownloadResource, resourceName));
			}
	}
	// download resources from experiment server:
	else if (this.downloadFrom === 'EXPERIMENT_SERVER') {
		// schedule download of resources:
		this._DowloadResourceComponents = [];
		resourceScheduler.add(this.Loop(this, this._DowloadResourceComponents, psychoJS.io.ResourceManager.prototype.EXPDownloadResources));
	}
}


/**
 * Generic loop waiting for an asynchronous resource operation to finish
 *
 * @param {psychoJS.io.ResourceManager} resourceManager - the [resource manager]{@link psychoJS.io.ResourceManager}
 * @param {Object} component - dummy component used to block a scheduler, e.g. one passed to
 * [scheduleRegistration]{@link psychoJS.io.ResourceManager#scheduleRegistration}, until 'resourceFunction' has completed
 * @param {Object} resourceFunction - the potentially asynchronous function, the end of which Loop is waiting for
 * @param {Object} [arg] - argument passed to 'resourceFunction'
 **/
psychoJS.io.ResourceManager.prototype.Loop = function(resourceManager, component, resourceFunction, arg) {
	component.status = psychoJS.NOT_STARTED;
	
	var localArg = arg;
	return function() {
		// get current time
		t = resourceManager.clock.getTime();

		if (t >= 0.0 && component.status === psychoJS.NOT_STARTED) {
			// keep track of start time/frame for later
			component.tStart = t;  // underestimates by a little under one frame
			component.status = psychoJS.STARTED;

			resourceFunction(resourceManager, component, localArg);
		}

		// check for quit (the Esc key)
		if (endExpNow || psychoJS.event.getKeys({keyList:["escape"]}).length > 0) {
			resourceManager.resetStatus();
			psychoJS.core.quit('The "Escape" key was pressed. Goodbye!');
		}

		// the loop will return until the authentication is completed
		// at which point the status changes to FINISHED
		if (component.status === psychoJS.FINISHED) {
			return psychoJS.NEXT;
		} else {
			return psychoJS.FLIP_REPEAT;
		}
	};
}


/**
 * Get the experimenter's authentication token for the project on OSF
 * 
 * @param {psychoJS.io.ResourceManager} resourceManager - the [resource manager]{@link psychoJS.io.ResourceManager}
 * @param {Object} component - dummy component used by the [Loop function]{@link psychoJS.io.ResourceManager#Loop} to block
 * the scheduler passed to [scheduleRegistration]{@link psychoJS.io.ResourceManager#scheduleRegistration} until the download has completed
 * @param {Object} [arg] - argument (currently unused)
 */
psychoJS.io.ResourceManager.prototype.OSFAuthenticate = function(resourceManager, component, arg) {
	resourceManager._resourceCallback('{ "message" : "getting OSF authentication token" }');
	resourceManager.setStatus('BUSY');
	var errorPrefix = '{ "function" : "io.ResourceManager.OSFAuthenticate", "context" : "when getting authentication token from OSF", "error" : ';

	
	$.ajax({
		type: "POST",
		url: resourceManager._CorsProxyUrl + resourceManager._OsfUrl + 'tokens/',
		async: true,
		headers: {
			// see the following URL for the need for authentication details to be sent preemptively, in the headers:
			// http://stackoverflow.com/questions/5507234/how-to-use-basic-auth-with-jquery-and-ajax/11960692#11960692
			"Authorization" : "Basic " + btoa(resourceManager.username + ":" + resourceManager.password)
		},
		data: '{ "data" : {"type" : "tokens" , "attributes" : {"name" : "' + resourceManager.projectName + '", "scopes": "osf.full_write"} } }',
		contentType: 'application/json; charset=utf-8',
		dataType: 'json',
		crossDomain: true,
	}).then(
		function (result) {
			resourceManager._tokenID = result.data.attributes.token_id;
			if (psychoJS.debug) console.log('\tgot token: ' + resourceManager._tokenID);
			
			// update ajax setting with token:
			this._OsfAjaxSettings = {type: "GET", async: true, headers: { "Authorization" : "Bearer " + resourceManager._tokenID }, crossDomain: true, dataType: 'json'};
	
			resourceManager.setStatus('READY');
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		},
		function (error) {
			resourceManager.setStatus('ERROR');
			throw errorPrefix + '"' + error + '", "stack" : ' + getErrorStack() + ' }';
		}
	);
}


/**
 * Get the ID of the project on OSF
 * 
 * @param {psychoJS.io.ResourceManager} resourceManager - the [resource manager]{@link psychoJS.io.ResourceManager}
 * @param {Object} component - dummy component used by the [Loop function]{@link psychoJS.io.ResourceManager#Loop} to block
 * the scheduler passed to [scheduleRegistration]{@link psychoJS.io.ResourceManager#scheduleRegistration} until the download has completed
 * @param {Object} [arg] - argument (currently unused)
 */
psychoJS.io.ResourceManager.prototype.OSFProjectID = function(resourceManager, component, arg) {
	resourceManager._resourceCallback('{ "message" : "getting OSF project ID" }');
	resourceManager.setStatus('BUSY');
	var errorPrefix = '{ "function" : "io.ResourceManager.OSFProjectID", "context" : "when getting project ID from OSF", "error" : ';
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._OsfUrl + 'nodes/?filter[title]=' + resourceManager.projectName;
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result) {
			resourceManager._projectId = result.data[1].id;
			if (psychoJS.debug) console.log("\tgot project ID: " + resourceManager._projectId);
			this._resourceCallback('{ "message" : "got OSF project ID", "projectID" : "' + resourceManager._projectId + '" }');
			resourceManager.setStatus('READY');
			
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		}, 
		function (error) {
			resourceManager.setStatus('ERROR');
			throw errorPrefix + '"' + error + '", "stack" : ' + getErrorStack() + ' }';
		}
	);
}


/**
 * Get the storage provider of the project on OSF
 * 
 * @param {psychoJS.io.ResourceManager} resourceManager - the [resource manager]{@link psychoJS.io.ResourceManager}
 * @param {Object} component - dummy component used by the [Loop function]{@link psychoJS.io.ResourceManager#Loop} to block
 * the scheduler passed to [scheduleRegistration]{@link psychoJS.io.ResourceManager#scheduleRegistration} until the download has completed
 * @param {Object} [arg] - argument (currently unused)
 */
 psychoJS.io.ResourceManager.prototype.OSFStorageProvider = function(resourceManager, component, arg) {
	resourceManager._resourceCallback('{ "message" : "getting OSF storage provider" }');
	resourceManager.setStatus('BUSY');
	var errorPrefix = '{ "function" : "io.ResourceManager.OSFStorageProvider", "context" : "when getting storage provider from OSF", "error" : ';
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._OsfUrl + 'nodes/' + resourceManager.projectId + '/files/';
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result){
			resourceManager._storageProviderURL = result.data[0].relationships.files.links.related.href;
			if (psychoJS.debug) console.log("\tgot storage provider: " + resourceManager._storageProviderURL);
			resourceManager.setStatus('READY');
			
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		},
		function (error){
			resourceManager.setStatus('ERROR');
			throw errorPrefix + '"' + error + '", "stack" : ' + getErrorStack() + ' }';
		}
  	);
}


/**
 * Get the download links for the registered resources directly from OSF
 * (without going through the experiment server).
 * 
 * @param {psychoJS.io.ResourceManager} resourceManager - the [resource manager]{@link psychoJS.io.ResourceManager}
 * @param {Object} component - dummy component used by the [Loop function]{@link psychoJS.io.ResourceManager#Loop} to block
 * the scheduler passed to [scheduleRegistration]{@link psychoJS.io.ResourceManager#scheduleRegistration} until the download has completed
 * @param {Object} [arg] - argument (currently unused)
 */
 psychoJS.io.ResourceManager.prototype.OSFDownloadLink = function(resourceManager, component, arg) {
	resourceManager._resourceCallback('{ "message" : "getting OSF download links" }');
	resourceManager.setStatus('BUSY');
	var errorPrefix = '{ "function" : "io.ResourceManager.OSFDownloadLink", "context" : "when getting download links from OSF", "error" : ';
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._storageProviderURL;
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result){
			for (var i = 0; i < result.data.length; i++) {
				var name = result.data[i].attributes.name;
				resourceManager._downloadLinkDictionary[name] = result.data[i].links.download;
				if (psychoJS.debug) console.log("\tgot download link for resource '" + name + "' : " + resourceManager._downloadLinkDictionary[name]);
			}
			
			resourceManager.setStatus('READY');
			
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		},
		function (error){
			resourceManager.setStatus('ERROR');
			throw errorPrefix + '"' + error + '", "stack" : ' + getErrorStack() + ' }';
		}
  	);
}


/**
 * Download resources directly from OSF (without going through the experiment server).
 * 
 * <p>Note: we assume that the experiment server's resources subdirectory is in the same directory as
 * the experiment html file.</p>
 * 
 * @param {psychoJS.io.ResourceManager} resourceManager - the [resource manager]{@link psychoJS.io.ResourceManager}
 * @param {Object} component - dummy component used by the [Loop function]{@link psychoJS.io.ResourceManager#Loop} to block
 * the scheduler passed to [scheduleDownload]{@link psychoJS.io.ResourceManager#scheduleDownload} until the download has completed
 * @param {Object} arg - index of the resource in the resource name array
 */
psychoJS.io.ResourceManager.prototype.OSFDownloadResource = function(resourceManager, component, arg) {
	var resourceName = arg;
	resourceManager._resourceCallback('{ "message" : "downloading resource", "resource" : "' + resourceName + '" }');
	resourceManager.setStatus('BUSY');
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._downloadLinkDictionary[resourceName];
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result){
			console.log(result);
		},
		// we get a parser error with cors-anywhere, but we still get the file in error.responseText
		function (error){
			resourceManager._resources[resourceName] = error.responseText;
			resourceManager._resourceCallback('{ "message" : "resource downloaded", "resource" : "' + resourceName + '" }');
			resourceManager.setStatus('READY');
			if (psychoJS.debug) {
				console.log('\tgot file:');
				console.log(resourceManager._resources[resourceName]);
			}
			
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		}
	);
}


/**
 * Download resources from the experiment server.
 * 
 * <p>Note: we assume that the experiment server's resources subdirectory is in the same directory as
 * the experiment html file.</p>
 * 
 * @param {psychoJS.io.ResourceManager} resourceManager - the [resource manager]{@link psychoJS.io.ResourceManager}
 * @param {Object} component - dummy component used by the [Loop function]{@link psychoJS.io.ResourceManager#Loop} to block
 * the scheduler passed to [scheduleRegistration]{@link psychoJS.io.ResourceManager#scheduleRegistration} until the registration has completed
 * @param {Object} [arg] - argument (currently unused)
 */
psychoJS.io.ResourceManager.prototype.EXPDownloadResources = function(resourceManager, component, arg) {
	resourceManager.setStatus('BUSY');
	
	// set-up preload queue
	resourceManager._nbLoadedResources = 0;
	resourceManager.resourceQueue = new createjs.LoadQueue(true);
	
	resourceManager.resourceQueue.addEventListener("filestart", function(event) {
		resourceManager._resourceCallback('{ "message" : "downloading resource", "resource" : "' + event.item.id + '" }');
	});

	// note: strangely, possibly because of timing, the value of the resource
	// may not be available immediately upon the firing of "fileload", we have to
	// get it upon the firing of "complete", instead.
	resourceManager.resourceQueue.addEventListener("fileload", function(event) {
		++resourceManager._nbLoadedResources;
		resourceManager._resourceCallback('{ "message" : "resource downloaded", "resource" : "' + event.item.id + '" }');
	});
	
	// loading completed: we get the value of the resources and exit the generic Loop
	resourceManager.resourceQueue.addEventListener("complete", function(event) {
		
		// get the values of all resources:
		for (resourceName in resourceManager._resources)
			if (resourceManager._resources.hasOwnProperty(resourceName)) {
				resourceManager._resources[resourceName] = resourceManager.resourceQueue.getResult(resourceName, false); // true: load raw result
			}

		// clean house and leave Loop:
		resourceManager._resourceCallback('{ "message" : "all resources downloaded", "number" : ' + resourceManager._nbLoadedResources.toString() + ' }');
		resourceManager.resourceQueue.destroy();
		
		resourceManager.setStatus('READY');
		component.status = psychoJS.FINISHED;
	});
	
	// error: we throw an exception
	resourceManager.resourceQueue.addEventListener("error", function(event) {
		resourceManager.setStatus('ERROR');
		throw '{ "function" : "io.ResourceManager.EXPDownloadResources", "context" : "when downloading resource: ' + event.data.id + '", "error" : "' + event.title + '", "stack" : ' + getErrorStack() + ' }';
	});
	
	// queue the resources:
	for (resourceName in resourceManager._resources)
			if (resourceManager._resources.hasOwnProperty(resourceName)) {
				resourceManager.resourceQueue.loadFile({id : resourceName, src : resourceManager._experimentServerResourceDirectory + "/" + resourceName}, false);
			}
	
	// start loading:
	resourceManager.resourceQueue.load();
}


/**
 * Upload session information and experiment data to OSF via the experiment server.
 * 
 * <p>Sends the session information and experiment data to the experiment server using a POST
 *  request and instruct it to upload them to the OSF repository.</p>
 * 
 * <p>Note: we assume that the server.php file is in the same directory on the
 * experiment server as the experiment html file itself.</p>
 * 
 * @param {Object} session - session information (e.g. experiment name, participant name, etc.)
 * @param {{('RESULT'|'LOG')}} dataType - type of the data to be saved
 * @param {Object} data - data to be saved (e.g. a .csv string)
 * @return {Object} JSON string OSF representation of the file to which the data was saved
 */
psychoJS.io.ResourceManager.prototype.OSFEXPUploadData = function(session, dataType, data) {
	var errorPrefix = '{ "function" : "io.ResourceManager.OSFEXPUploadData", "context" : "when uploading data to OSF via the experiment server", '
		+ '"error" : ';
	this.setStatus('BUSY');
	
	if (['RESULT', 'LOG'].indexOf(dataType) == -1) {
		this.setStatus('ERROR');
		throw errorPrefix + '"unknown data type: ' + dataType + '", "stack" : ' + getErrorStack() + ' }';
	}
		
	var self = this;
	$.post('./server.php',
			{'command' : 'OSF_UPLOAD',
			'session' : JSON.stringify(session),
			'dataType' : dataType,
			'data' : data})
	.then(
		function (result) {
			try {
				var json = JSON.parse(result);
			} catch (exception) {
				self.setStatus('ERROR');
				// JSON.parse will throw a SyntaxError if result is not a JSON string
				// this might happens if php is not available on the server running server.php,
				// in which case an HTTP POST request to server.php returns the code of server.php
				// or if the experiment server ran into an error.
				if (psychoJS.debug) console.log(result);
				throw errorPrefix + '"unexpected answer from the experiment server", "stack" : ' + getErrorStack() + ' }';
			}

			if ('representation' in json) {
				self.setStatus('READY');
				return result;
			} else {
				self.setStatus('ERROR');
				throw errorPrefix + $.trim(result) + ', "stack" : ' + getErrorStack() + ' }';
			}
		}, 
		function (error) {
			self.setStatus('ERROR');
			if ('statusText' in error)
				throw errorPrefix + '"' + $.trim(error.statusText) + '", "stack" : ' + getErrorStack() + ' }';
			else
				throw errorPrefix + error + ', "stack" : ' + getErrorStack() + ' }';
		}
	);
}


/**
 * Upload session information and experiment data to the experiment server.
 * 
 * <p>Sends the session information and experiment data to the experiment server using a POST
 *  request.</p>
 * 
 * <p>Note: we assume that the server.php file is in the same directory on the
 * experiment server as the experiment html file itself.</p>
 * 
 * @param {Object} session - session information (e.g. experiment name, participant name, etc.)
 * @param {{('RESULT'|'LOG')}} dataType - type of the data to be saved
 * @param {Object} data - data to be saved (e.g. a .csv string)
 * @return {Object} JSON string representation of the file to which the data was saved
 */
psychoJS.io.ResourceManager.prototype.EXPUploadData = function(session, dataType, data) {
	var errorPrefix = '{ "function" : "io.ResourceManager.EXPUploadData", "context" : "when uploading data to OSF via the experiment server", '
		+ '"error" : ';
	this.setStatus('BUSY');
	
	if (['RESULT', 'LOG'].indexOf(dataType) == -1) {
		this.setStatus('ERROR');
		throw errorPrefix + '"unknown data type: ' + dataType + '", "stack" : ' + getErrorStack() + ' }';
	}
		
	var self = this;
	$.post('./server.php',
			{'command' : 'EXP_UPLOAD',
			'session' : JSON.stringify(session),
			'dataType' : dataType,
			'data' : data})
	.then(
		function (result) {
			try {
				var json = JSON.parse(result);
			} catch (exception) {
				self.setStatus('ERROR');
				// JSON.parse will throw a SyntaxError if result is not a JSON string
				// this might happens if php is not available on the server running server.php,
				// in which case an HTTP POST request to server.php returns the code of server.php
				throw errorPrefix + '"unexpected answer from the experiment server", "stack" : ' + getErrorStack() + ' }';
			}

			if ('representation' in json) {
				self.setStatus('READY');
				return result;
			} else {
				self.setStatus('ERROR');
				throw errorPrefix + $.trim(result) + ', "stack" : ' + getErrorStack() + ' }';
			}
		}, 
		function (error) {
			self.setStatus('ERROR');
			if ('statusText' in error)
				throw errorPrefix + '"' + $.trim(error.statusText) + '", "stack" : ' + getErrorStack() + ' }';
			else
				throw errorPrefix + error + ', "stack" : ' + getErrorStack() + ' }';
		}
	);
}

