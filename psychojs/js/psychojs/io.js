/**
 * I/O component of psychoJS
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
psychoJS.io = {}


/**
 * Create a new resource manager.
 * 
 * <p>The resource manager synchronously or asynchronously uploads resources
 * to and from a local or distant data repository, possibly via a local 
 * experiment server.</p>
 * <p>Note: The parameters are set in the [set function]{@link psychoJS.io.ResourceManager#set}.</p>
 * 
 * @constructor
 */
psychoJS.io.ResourceManager = function() {
	if (psychoJS.debug) console.log("OSF ResourceManager created");
	
	psychoJS.visual.MinimalStim.call(this, {'name' : 'resourceManager', 'autoLog' : false});
}
psychoJS.io.ResourceManager.prototype = Object.create(psychoJS.visual.MinimalStim.prototype);


/**
 * Set the parameters of the resource manager.
 * 
 * 
 * @param {Object} attribs - associative array used to store the following parameters:
 * @param {psychoJS.visual.Window} attribs.win - the psychoJS [Window]{@link psychoJS.visual.Window}
 * @param {('OSF'|'EXPERIMENT_SERVER')} attribs.repository - type of resource repository
 * @param {String} attribs.projectId - ID of the project on OSF
 * @param {String} attribs.projectName - name of the project on OSF
 * @param {('PUBLIC'|'PRIVATE')} attribs.projectStatus - status of the project
 * 
 */
psychoJS.io.ResourceManager.prototype.set = function(attribs) {
	this.win = getAttrib(attribs, 'win');
	this.repository = getAttrib(attribs, 'repository');
	this.projectName = getAttrib(attribs, 'projectName');
	this.projectId = getAttrib(attribs, 'projectId');
	this.projectContributor = getAttrib(attribs, 'contributor');
	this.projectStatus = getAttrib(attribs, 'projectStatus');
	this.username = getAttrib(attribs, 'username');
	this.password = getAttrib(attribs, 'password');
	this.clock = getAttrib(attribs, 'clock');

	// status of the resource manager ('READY'|'REGISTERING'|'BUSY'|'ERROR'):
	this._status = 'READY';
	this._statusCallback = undefined;
	
	// default callback function does nothing
	this._callbackFunction = function(message) {};
	
	// resources:
	this._resourceNames = [];
	this._resourceValues = [];

	// OSF specific:
	this._OsfUrl = 'https://api.osf.io/v2/';
	this._CorsProxyUrl = ''; // e.g. 'https://cors-anywhere.herokuapp.com/'
	this._OsfAjaxSettings = {type: "GET", async: true, crossDomain: true, dataType: 'json'};
}


/**
 * Get the resource manager status
 * 
 * @return {('READY'|'REGISTERING'|'BUSY'|'ERROR')} status
 */
psychoJS.io.ResourceManager.prototype.getStatus = function() {
	return this._status;
}


/**
 * Set the resource manager status
 * 
 * @return {('READY'|'REGISTERING'|'BUSY'|'ERROR')} the new status
 */
psychoJS.io.ResourceManager.prototype.setStatus = function(newStatus) {
	this._status = newStatus;
	if (undefined !== this._statusCallback)
		this._statusCallback(newStatus);
}


/**
 * Set the status change call back function
 * 
 * @param {Object} callback the function called whenever the resource manager's status changes
 */
psychoJS.io.ResourceManager.prototype.setStatusCallback = function(callback) {
	this._statusCallback = callback;
}


/**
 * Reset the resource manager status to 'READY'
 * 
 * @return {'READY'} the new status
 */
psychoJS.io.ResourceManager.prototype.resetStatus = function() {
	return this._status;
}


/**
 * Set the callback function for all resource registration and download events.
 * 
 * <p>Note: the callback function is passed a stringified json message</p>
 * 
 * @param {Object} callbackFunction the function called each time
 * a resource registration or download event is fired
 * 
 */
psychoJS.io.ResourceManager.prototype.setCallback = function(callbackFunction) {
	this._callbackFunction = callbackFunction;
}


/**
 * Schedule the registration of all available resources for this experiment.
 * 
 * <p>Note: The scheduler will wait for the registration to complete before moving onto the next task.</p>
 * 
 * @param {psychoJS.Scheduler} scheduler the registration [scheduler] {@link psychoJS.Scheduler}
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
 * <p>Note: We assume that the server.php file is in the same directory on the PHP
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
	resourceManager._callbackFunction('{ "message" : "resource registration started" }');
	resourceManager.setStatus('REGISTERING');
	
	// query the list of resources directly from the OSF server:
	if (resourceManager.repository === 'OSF') {
		// TODO
	}
	
	// query the list of resources from the PHP experiment server:
	else if (resourceManager.repository === 'EXPERIMENT_SERVER') {
		$.post('./server.php',
			{'command' : 'LIST_RESOURCES'})
		.then(
			function (result) {
				var json = JSON.parse(result);
				
				if ('resources' in json) {
					var nbResource = json.resources.length;
					for (var i = 0; i < nbResource; i++) {
						resourceManager.registerResource(json.resources[i]);
					}
					resourceManager._callbackFunction('{ "message" : "all resources registered", "number" : ' + nbResource.toString() + ' }');
					resourceManager.setStatus('READY');
					
					if (component !== undefined) {
						// leave the generic loop:
						component.status = psychoJS.FINISHED;
					}
				} else {
					resourceManager.setStatus('ERROR');
					throw '{ "function" : "io.ResourceManager.registerAvailableResources", "context" : "when registering all available resources", "error" : ' + $.trim(result) + ' }';
				}
			}, 
			function (error){
				resourceManager.setStatus('ERROR');
				throw '{ "function" : "io.ResourceManager.registerAvailableResources", "context" : "when registering all available resources", "error" : "' + $.trim(error) + '" }';
			}
		);
	}
}


/**
 * Register a resource.
 * 
 * <p>Note: the [callback function]{@link psychoJS.io.ResourceManager#setCallback} is called with
 * the following stringified json object: <blockquote>{"message" : "resource registered", "resource" : "&lt;resource name&gt;"}</blockquote></p>
 * 
 * @param {string} resourceName name of the resource to be registered
 */
psychoJS.io.ResourceManager.prototype.registerResource = function(resourceName) {
	this._resourceNames.push(resourceName);
	this._callbackFunction('{ "message" : "resource registered", "resource" : "' + resourceName + '" }');
}


/**
 * Query the value of a resource.
 * 
 * @param {string} name of the requested resource
 * @return {Object} value of the resource or exception if resource is unknown
 */
psychoJS.io.ResourceManager.prototype.getResource = function(resourceName) {
	if (this._resourceNames.indexOf(resourceName) == -1) {
		throw '{ "function" : "io.ResourceManager.getResource", "context" : "when getting resource: ' + resourceName + '", "error" : "unknown resource" }';
	}
	
	return this._resourceValues[resourceName];
}


/**
 * Schedule the asynchronous download of the registered resources.
 * 
 * <p>Note: The scheduler will wait for the download of all registered
 * resources to complete before moving onto the next task.</p>
 * 
 * @param {Object} scheduler the [resource scheduler]{@link psychoJS.Scheduler}
 * 
 **/
psychoJS.io.ResourceManager.prototype.scheduleDownload = function(resourceScheduler) {
	// download resources from OSF:
	if (this.repository === 'OSF') {
		
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
		this._DowloadResourceComponents = [];
		for (var i = 0; i < this._resourceNames.length; ++i) {
			this._DowloadResourceComponents[i] = [];
				resourceScheduler.add(this.Loop(this, this._DowloadResourceComponents[i], psychoJS.io.ResourceManager.prototype.OSFDownloadResource, [i]));
		}
	}
	// download resources from the PHP experiment server:
	else if (this.repository === 'EXPERIMENT_SERVER') {
		// schedule download of resources:
		this._DowloadResourceComponents = [];
		resourceScheduler.add(this.Loop(this, this._DowloadResourceComponents, psychoJS.io.ResourceManager.prototype.EXPDownloadResources));
	}
}


/**
 * Generic loop waiting for an asynchronous resource operation to finish
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
			core.quit();
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


psychoJS.io.ResourceManager.prototype.OSFAuthenticate = function(resourceManager, component, arg) {
	resourceManager._callbackFunction('{ "message" : "getting OSF authentication token" }');
	resourceManager.setStatus('BUSY');
	
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
			throw '{ "function" : "io.ResourceManager.OSFAuthenticate", "context" : "when getting token from OSF", "error" : "' + error + '" }';
		}
	);
}

psychoJS.io.ResourceManager.prototype.OSFProjectID = function(resourceManager, component, arg) {
	resourceManager._callbackFunction('{ "message" : "getting OSF project ID" }');
	resourceManager.setStatus('BUSY');
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._OsfUrl + 'nodes/?filter[title]=' + resourceManager.projectName;
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result) {
			resourceManager._projectId = result.data[1].id;
			if (psychoJS.debug) console.log("\tgot project ID: " + resourceManager._projectId);
			this._callbackFunction('{ "message" : "got OSF project ID", "projectID" : "' + resourceManager._projectId + '" }');
			resourceManager.setStatus('READY');
			
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		}, 
		function (error) {
			resourceManager.setStatus('ERROR');
			throw '{ "function" : "io.ResourceManager.OSFProjectID", "context" : "when getting project ID from OSF", "error" : "' + error + '" }';
		}
	);
}


psychoJS.io.ResourceManager.prototype.OSFStorageProvider = function(resourceManager, component, arg) {
	resourceManager._callbackFunction('{ "message" : "getting OSF storage provider" }');
	resourceManager.setStatus('BUSY');
	
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
			throw '{ "function" : "io.ResourceManager.OSFStorageProvider", "context" : "when getting storage provider from OSF", "error" : "' + error + '" }';
		}
  	);
}


psychoJS.io.ResourceManager.prototype.OSFDownloadLink = function(resourceManager, component, arg) {
	resourceManager._callbackFunction('{ "message" : "getting OSF download links" }');
	resourceManager.setStatus('BUSY');
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._storageProviderURL;
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result){
			for (var i = 0; i < result.data.length; i++) {
				var name = result.data[i].attributes.name;
				resourceManager._downloadLinkDictionary[name] = result.data[i].links.download;
				if (psychoJS.debug) console.log("\tgot download link for resource '" + name + "' : " + resourceManager._downloadLinkDictionary[name]);
			}
			
			// leave the generic loop:
			resourceManager.setStatus('READY');
			component.status = psychoJS.FINISHED;
		},
		function (error){
			resourceManager.setStatus('ERROR');
			throw '{ "function" : "io.ResourceManager.OSFStorageProvider", "context" : "when getting download links from OSF", "error" : "' + error + '" }';
		}
  	);
}



psychoJS.io.ResourceManager.prototype.OSFDownloadResource = function(resourceManager, component, arg) {
	var resourceName = resourceManager._resourceNames[arg[0]];
	resourceManager._callbackFunction('{ "message" : "downloading resource", "resource" : "' + resourceName + '" }');
	resourceManager.setStatus('BUSY');
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._downloadLinkDictionary[resourceName];
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result){
			console.log(result);
		},
		// we get a parser error with cors-anywhere, but we still get the file in error.responseText
		function (error){
			resourceManager._resourceValues[resourceName] = error.responseText;
			resourceManager._callbackFunction('{ "message" : "resource downloaded", "resource" : "' + resourceName + '" }');
			resourceManager.setStatus('READY');
			if (psychoJS.debug) {
				console.log('\tgot file:');
				console.log(resourceManager._resourceValues[resourceName]);
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
 * the scheduler passed to [scheduleRegistration]{@link psychoJS.io.ResourceManager#scheduleRegistration} until the download has completed
 * @param {Object} [arg] - argument (currently unused)
 */
psychoJS.io.ResourceManager.prototype.EXPDownloadResources = function(resourceManager, component, arg) {
	resourceManager.setStatus('BUSY');
	
	// set-up preload queue
	resourceManager._nbLoadedResources = 0;
	resourceManager.resourceQueue = new createjs.LoadQueue(true);
	
	resourceManager.resourceQueue.addEventListener("filestart", function(event) {
		resourceManager._callbackFunction('{ "message" : "downloading resource", "resource" : "' + event.item.id + '" }');
	});

	// note: strangely, possibly because of timing, the value of the resource
	// may not be available immediately upon the firing of "fileload", we have to
	// get it upon the firing of "complete", instead.
	resourceManager.resourceQueue.addEventListener("fileload", function(event) {
		++resourceManager._nbLoadedResources;
		resourceManager._callbackFunction('{ "message" : "resource downloaded", "resource" : "' + event.item.id + '" }');
	});
	
	// loading completed: we get the value of the resources and exit the generic Loop
	resourceManager.resourceQueue.addEventListener("complete", function(event) {
		
		// get the values of all resources:
		for (var i = 0; i < resourceManager._resourceNames.length; ++i) {
			var resourceName = resourceManager._resourceNames[i];
			resourceManager._resourceValues[resourceName] = resourceManager.resourceQueue.getResult(resourceName, false); // true: load raw result
		}

		// clean house and leave Loop:
		resourceManager._callbackFunction('{ "message" : "all resources downloaded", "number" : ' + resourceManager._nbLoadedResources.toString() + ' }');
		resourceManager.resourceQueue.destroy();
		
		resourceManager.setStatus('READY');
		component.status = psychoJS.FINISHED;
	});
	
	// error: we throw an exception
	resourceManager.resourceQueue.addEventListener("error", function(event) {
		resourceManager.setStatus('ERROR');
		throw '{ "function" : "io.ResourceManager.EXPDownloadResources", "context" : "when downloading resource: ' + event.data.id + '", "error" : "' + event.title + '" }';
	});
	
	// queue the resources:
	for (var i = 0; i < resourceManager._resourceNames.length; ++i) {
		var resourceURL = "resources/" + resourceManager._resourceNames[i];
		resourceManager.resourceQueue.loadFile({id : resourceManager._resourceNames[i], src : resourceURL}, false);
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
 * @param {Object} experimentServerUrl - URL of the experiment server
 * @param {Object} session - session information (e.g. experiment name, participant name, etc.)
 * @param {Object} data - data to be saved (e.g. a .csv string)
 * @return {Object} JSON string OSF representation of the file to which the data was saved
 */
psychoJS.io.ResourceManager.prototype.OSFEXPUploadData = function(experimentServerUrl, session, data) {
	this.setStatus('BUSY');
	
	var self = this;
	$.post('./server.php',
			{'command' : 'OSF_UPLOAD',
			'session' : JSON.stringify(session),
			'data' : data})
	.then(
		function (result) {
			json = JSON.parse(result);

			if ('representation' in json) {
				self.setStatus('READY');
				return result;
			} else {
				self.setStatus('ERROR');
				throw '{ "function" : "io.ResourceManager.OSFEXPUploadData", "context" : "when uploading data to OSF via the experiment server", "error" : ' + $.trim(result) + ' }';
			}
		}, 
		function (error) {
			self.setStatus('ERROR');
			throw '{ "function" : "io.ResourceManager.OSFEXPUploadData", "context" : "when uploading data to OSF via the experiment server", "error" : ' + $.trim(error) + ' }';
		}
	);
}

