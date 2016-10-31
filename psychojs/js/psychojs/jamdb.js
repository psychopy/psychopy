psychoJS.jamdb = {}


/**
 * 
 * @constructor
 * @param 
 * 
 **/
psychoJS.jamdb.ResourceManager = function(attribs) {
	console.log("JamDB ResourceManager created");
	
	this.autoLog = false;
	this.win = psychoJS.getAttrib(attribs, 'win');
	this.target = psychoJS.getAttrib(attribs, 'target');
	this.namespace = psychoJS.getAttrib(attribs, 'namespace');
	this.collection = psychoJS.getAttrib(attribs, 'collection');
	this.projectStatus = psychoJS.getAttrib(attribs, 'projectStatus');
	this.username = psychoJS.getAttrib(attribs, 'username');
	this.password = psychoJS.getAttrib(attribs, 'password');
	this.clock = psychoJS.getAttrib(attribs, 'clock');

	this.status = undefined;
	
	this._resourceNames = [];
	this._resourceValues = [];


	// JamDB OSF specific:
	this._CorsProxyUrl = '';
	//this._CorsProxyUrl = 'https://cors-anywhere.herokuapp.com/';
	//this._CorsProxyUrl = 'https://psychocorsproxy.herokuapp.com'; //login at: https://id.heroku.com/login
	this._OsfJamDBURL = 'https://staging-metadata.osf.io/v1/';
	this._OsfAjaxSettings = {type: "GET", async: true, crossDomain: true, dataType: 'json'}; //headers: { 'Access-Control-Allow-Headers':'X-Requested-With', 'X-Requested-With' : 'XMLHttpRequest' }};


	psychoJS.visual.MinimalStim.call(this, attribs);
}
psychoJS.jamdb.ResourceManager.prototype = Object.create(psychoJS.visual.MinimalStim.prototype);


psychoJS.jamdb.ResourceManager.prototype.addResource = function(resourceName) {
	this._resourceNames.push(resourceName);
}


psychoJS.jamdb.ResourceManager.prototype.getResource = function(resourceName) {
	return resourceManager._resourceValues[resourceName];
}

/**
 * schedule the asynchronous upload of the resources
 * 
 **/
psychoJS.jamdb.ResourceManager.prototype.scheduleResources = function(resourceScheduler) {
	
	// prepare and show progress dialog box:
	this.showDialogBox();
	
	if (this.target === 'OSF') {
		
		// if project is private, we need to authenticate:
		if (this.projectStatus === 'PRIVATE') {
			// authenticate and get token:
			this._Authenticate = [];
			resourceScheduler.add(this.Loop(this, this._Authenticate, psychoJS.jamdb.ResourceManager.prototype.OSFAuthenticate));
		}
		/*
		// get project ID:
		this._ProjectIDComponent = [];
		resourceScheduler.add(this.Loop(this, this._ProjectIDComponent, psychoJS.jamdb.ResourceManager.prototype.OSFProjectID));
		
		// get storage provider:
		this._StorageProviderComponent = [];
		resourceScheduler.add(this.Loop(this, this._StorageProviderComponent, psychoJS.jamdb.ResourceManager.prototype.OSFStorageProvider));

		// get download links for all resources:
		this._downloadLinkDictionary = [];
		this._DowloadLinkComponent = [];
		resourceScheduler.add(this.Loop(this, this._DowloadLinkComponent, psychoJS.jamdb.ResourceManager.prototype.OSFDownloadLink));
		
		// download resources:
		this._DowloadResourceComponents = [];
		for (var i = 0; i < this._resourceNames.length; ++i) {
			this._DowloadResourceComponents[i] = [];
			resourceScheduler.add(this.Loop(this, this._DowloadResourceComponents[i], psychoJS.jamdb.ResourceManager.prototype.OSFDownloadResource, [i]));
		}*/
	}
	
	// schedule the closing of the dialog box:
	resourceScheduler.add(
		function() {
			$("#progressDialog").dialog("close");
			return psychoJS.NEXT;
		}
	);
}

/**
 * generic loop waiting for asynchronous resource operation to finish
 **/
psychoJS.jamdb.ResourceManager.prototype.Loop = function(resourceManager, component, resourceFunction, arguments) {
	component.status = psychoJS.NOT_STARTED;
	
	var localArguments = arguments;
	return function() {
				// get current time
				t = resourceManager.clock.getTime();
				frameN = frameN + 1;  // number of completed frames (so 0 is the first frame)

				if (t >= 0.0 && component.status === psychoJS.NOT_STARTED) {
					// keep track of start time/frame for later
					component.tStart = t;  // underestimates by a little under one frame
					component.frameNStart = frameN;  // exact frame index
					component.status = psychoJS.STARTED;

					resourceFunction(resourceManager, component, localArguments);
				}

				// check for quit (the Esc key)
				if (endExpNow || event.getKeys({keyList:["escape"]}).length > 0) {
					psychoJS.core.quit();
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


psychoJS.jamdb.ResourceManager.prototype.OSFAuthenticate = function(resourceManager, component, arguments) {
	
	resourceManager.incrementProgressBar("authenticating...");
	
	$.ajax({
		type: "POST",
		url: resourceManager._CorsProxyUrl + resourceManager._OsfJamDBURL + 'auth',
		async: true,
		data: JSON.stringify({data : { type: 'users' , attributes: { 'provider': 'osf', 'namespace': 'psychopy', 'collection': 'sys', 'username': 'root', 'password': 'password'} } }),
		//data: '{ "data" : { "type" : "users" , "attributes" : { "provider" : "osf", "namespace" : "' + resourceManager.namespace + '", "collection" : "' + resourceManager.collection + '", "username" : "' + resourceManager.username + '", "password": "' + resourceManager.password + '" } } }',
		contentType: 'application/json; charset=utf-8',
		dataType: 'json',
		crossDomain: true,
	}).then(
		function (result) {
			console.log(result);
			resourceManager._tokenID = result.data.attributes.token_id;
			console.log('\tgot token: ' + resourceManager._tokenID);
			
			// update ajax setting with token:
			this._OsfAjaxSettings = {type: "GET", async: true, headers: { "Authorization" : "Bearer " + resourceManager._tokenID }, crossDomain: true, dataType: 'json'};
	
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		},
		function (error){
			console.log('\terror obtaining token:');
			console.log(error);
		}
	);
}

psychoJS.jamdb.ResourceManager.prototype.OSFProjectID = function(resourceManager, component, arguments) {
	
	resourceManager.incrementProgressBar("getting project ID...");
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._OsfURL + 'nodes/?filter[title]=' + resourceManager.projectName;
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result) {
			console.log(result);
			resourceManager._projectID = result.data[0].id;
			console.log("\tgot project ID: " + resourceManager._projectID);
			
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		}, 
		function (error){
			console.log('\terror obtaining project ID:');
			console.log(error);
		}
	);
}


psychoJS.jamdb.ResourceManager.prototype.OSFStorageProvider = function(resourceManager, component, arguments) {

	resourceManager.incrementProgressBar("getting storage provider...");
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._OsfURL + 'nodes/' + resourceManager._projectID + '/files/';
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result){
			console.log(result);
			resourceManager._storageProviderURL = result.data[0].relationships.files.links.related.href;
			console.log("\tgot storage provider: " + resourceManager._storageProviderURL);
			
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		},
		function (error){
			console.log('\terror obtaining project storage provider:');
			console.log(error);
		}
  	);
}


psychoJS.jamdb.ResourceManager.prototype.OSFDownloadLink = function(resourceManager, component, arguments) {
	
	resourceManager.incrementProgressBar("getting download links...");
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._storageProviderURL;
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result){
			//console.log(result);
			for (var i = 0; i < result.data.length; i++) {
				var name = result.data[i].attributes.name;
				resourceManager._downloadLinkDictionary[name] = result.data[i].links.download;
				console.log("\tgot download link for resource '" + name + "' : " + resourceManager._downloadLinkDictionary[name]);
			}
			
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		},
		function (error){
			console.log('\terror obtaining download links:');
			console.log(error);
		}
  	);
}



psychoJS.jamdb.ResourceManager.prototype.OSFDownloadResource = function(resourceManager, component, arguments) {

	var resourceName = resourceManager._resourceNames[arguments[0]];
	resourceManager.incrementProgressBar("downloading resource '" + resourceName + "'...");
	
	resourceManager._OsfAjaxSettings.url = resourceManager._CorsProxyUrl + resourceManager._downloadLinkDictionary[resourceName];
	$.ajax(resourceManager._OsfAjaxSettings)
	.then(
		function (result){
			console.log(result);
		},
		// we get a parser error with cors-anywhere, but we still get the file in error.responseText
		function (error){
			//console.log(error);
			console.log('\tgot file:');
			resourceManager._resourceValues[resourceName] = error.responseText;
			console.log(resourceManager._resourceValues[resourceName]);
			
			// leave the generic loop:
			component.status = psychoJS.FINISHED;
		}
	);
}

psychoJS.jamdb.ResourceManager.prototype.showDialogBox = function() {
	
	// prepare dialog box:
	var htmlCode = 
		'<div id="progressDialog" title="Fetching resources">' + 
		'<form>' +
		'<fieldset>' +
		'<label id="progressLabel">Fetching resources...</label>' +
		'<div id="progressBarDiv"/>' +
		'</fieldset>' +
		'</form>' +
		'</div>';
	var element = document.createElement('div');
	element.innerHTML = htmlCode;
	document.body.appendChild(element);
	
	// init progress bar:
	this._progressBarTotalIncrements = 3 + this._resourceNames.length;
	if (this.projectStatus === 'PRIVATE') {
		++ this._progressBarTotalIncrements;
	}
	this._progressBarCurrentIncrement = -1;
	this.incrementProgressBar("initialising...");
	
	// init and show dialog box:
	$("#progressDialog").dialog({
		autoOpen: true,
		width: 400,
		modal: true,
		dialogClass: "no-close",
		buttons: [
			{
				text: "Abort",
				click: function() {
					$( this ).dialog( "close" );
					core.quit();
				}
			}
		]
	});
}

psychoJS.jamdb.ResourceManager.prototype.incrementProgressBar = function(message) {
	++ this._progressBarCurrentIncrement;
	var percentComplete = Math.round( this._progressBarCurrentIncrement / this._progressBarTotalIncrements * 100 );
	$("#progressBarDiv").progressbar({ value: percentComplete });
	$("#progressLabel").text(message);
}
