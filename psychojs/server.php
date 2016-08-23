<?php

	/**
	 * PHP experiment server
	 * 
	 * 
	 * This file is part of the PsychoJS javascript engine of PsychoPy.
	 * Copyright (c) 2016 Ilixa Ltd. (www.ilixa.com)
	 * 
	 * Distributed under the terms of the GNU General Public License (GPL).
	 */


	/**
	 * Create a new Experiment Server
	 *
	 * <p>Note: The server requires the cURL PHP library to be installed.
	 * Under linux, that can usually be done using: <code>sudo apt-get install curl libcurl3 libcurl3-dev php5-curl</code></p>
	 * @class
	 */
	class ExperimentServer {
	
		/**
		 * @constructor
		 */
		function __construct() {
			// load the data.php, which contains the project ID, the user's project's OSF token, etc.
			include 'data.php';			
		}


		/**
		 * Process the HTTP POST request sent to this experiment server.
		 *
		 * <p>Get the 'command' variable passed to the experiment server via a HTTP POST method
		 * <ul>
		 * <li>if 'command' is not set, we show the server's synchronisation GUI</li>
		 * <li>if 'command' = 'OSF_UPLOAD', data contained in the 'data' variable passed via the
		 * POST method is saved locally on the local experiment server's data directory and
		 * uploaded to the remote OSF server</li>
		 * <li>if 'command' = 'SYNC', all of the project's resources are downloaded from the
		 * project's resource directory on the remote OSF server onto the local experiment
		 * server's resource directory</li>
		 * <li>if 'command= = 'LIST_RESOURCES', return the list of all available resource names
		 * in local resource directory as a stringified json array of resource names</li>
		 * </ul></p>
		 */
		public function processPOST() {

			try {
				// check whether cURL is installed:
				if (!extension_loaded('curl') || !is_callable('curl_init')) {
						throw new Exception("The experiment server requires the cURL PHP library to be installed.");
				}

				// no command - show synchronisation GUI:
				if (!isset($_POST['command'])) {
					$serverResponse = $this->showSynchronisationGUI();
				} else {
					// get POST command:
					$command = $_POST['command'];
					
					// OSF_UPLOAD - upload data to OSF server:
					if (0 === strcmp('OSF_UPLOAD', $command)) {
						$serverResponse = $this->OsfUpload();
					}
					
					// SYNC - get resources from OSF server:
					else if (0 === strcmp('SYNC', $command)) {
						$serverResponse = $this->OsfSync();
					}
					
					// LIST_RESOURCES - return list of resources from local resource directory:
					else if (0 === strcmp('LIST_RESOURCES', $command)) {
						$serverResponse = $this->listLocalResources();
					}
					
					// unknown command:
					else {
						throw new Exception('"Unknown command: ' . $command . '"');
					}
				}
			} catch (Exception $e) {
				$serverResponse = '{ "function" : "' . $this->data['projectId'] . ' experiment server", "context" : "when processing HTTP POST message", "error" : ' . $e->getMessage() . ' }';
			}
			
			echo $serverResponse;
		}


		/**
		 * Get storage provider and upload URL of project on OSF server
		 */
		private function getOsfStorageProvider() {
			try {
				$ch = curl_init();
				if (FALSE === $ch) {
					throw new Exception('"Unabled to initialize cURL"');
				}
				$resourceUrl = $this->data["OsfUrl"] . 'nodes/' . $this->data["projectId"] . '/files/?format=json';
				curl_setopt($ch, CURLOPT_URL, $resourceUrl);
				curl_setopt($ch, CURLOPT_HTTPHEADER, array('Authorization: Bearer ' . $this->data["token"]));
				curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
				
				$result = curl_exec($ch);
				$error = curl_error($ch);
				//$info = curl_getinfo($ch);
				curl_close($ch);
				
				if (FALSE === $result) {
					throw new Exception('"HTTP GET request failed: ' . $error . '"');
				} else {
					$json = json_decode($result);
					
					if (property_exists($json, "errors")) {
						throw new Exception('"' . $json->errors[0]->detail . '"');
					}
					
					$storageProviderUrl = $json->data[0]->relationships->files->links->related->href;
					$this->data["storageProviderUrl"] = substr($storageProviderUrl, 0, strpos($storageProviderUrl, "?")); // remove ?format=json
					
					$rootUploadUrl = $json->data[0]->links->upload;
					$this->data["rootUploadUrl"] = $rootUploadUrl;
				}
			} catch (Exception $e) {
				throw new Exception('{ "function" : "getOsfStorageProvider()", "context" : "when getting storage provider from OSF", "error" : ' . $e->getMessage() . ' }');
			}
		}


		/**
		 * Get project's data folder URL on OSF server
		 */
		private function getOsfDataDirectoryLink() {
			try {
				$ch = curl_init();
				if (FALSE === $ch) {
					throw new Exception('"Unabled to initialize cURL"');
				}
				curl_setopt($ch, CURLOPT_URL, $this->data["rootUploadUrl"]);
				curl_setopt($ch, CURLOPT_HTTPHEADER, array('Authorization: Bearer ' . $this->data["token"]));
				curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
				
				$result = curl_exec($ch);
				$error = curl_error($ch);
				//$info = curl_getinfo($ch);
				curl_close($ch);
				
				if (FALSE === $result) {
					throw new Exception('"HTTP GET request failed: ' . $error . '"');
				} else {
					$json = json_decode($result);
					
					if (property_exists($json, "errors")) {
						throw new Exception('"' . $json->errors[0]->detail . '"');
					}
					
					// look for data folder:
					$dataDirectory = $this->data["dataDirectory"];
					foreach ($json->data as $entity) {
						$name = $entity->attributes->name;
						
						if (0 === strcmp($dataDirectory, $name)) {
							$uploadLink = $entity->links->upload;
							$this->data["dataDirectoryUrl"] = substr($uploadLink, 0, strpos($uploadLink, "?")); // remove ?format=json
							return;
						}
					}
					
					// we could not find the data directory:
					throw new Exception('"Unabled to find data directory: ' . $dataDirectory . ' on OSF"');
				}
			} catch (Exception $e) {
				throw new Exception('{ "function" : "getOsfDataDirectoryLink()", "context" : "when getting data folder URL from OSF", "error" : ' . $e->getMessage() . ' }');
			}
		}
		
		
		/**
		 * Get project's resource directory URL on OSF server
		 */
		private function getOsfResourceDirectoryLink() {
			try {
				$ch = curl_init();
				if (FALSE === $ch) {
					throw new Exception('"Unabled to initialize cURL"');
				}
				curl_setopt($ch, CURLOPT_URL, $this->data["storageProviderUrl"]);
				curl_setopt($ch, CURLOPT_HTTPHEADER, array('Authorization: Bearer ' . $this->data["token"]));
				curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
				
				$result = curl_exec($ch);
				$error = curl_error($ch);
				//$info = curl_getinfo($ch);
				curl_close($ch);
				
				if (FALSE === $result) {
					throw new Exception('"HTTP GET request failed: ' . $error . '"');
				} else {
					$json = json_decode($result);
					
					if (property_exists($json, "errors")) {
						throw new Exception('"' . $json->errors[0]->detail . '"');
					}

					// look for resource folder:
					$resourceDirectory = $this->data["resourceDirectory"];
					foreach ($json->data as $entity) {
						$name = $entity->attributes->name;
						
						if (0 === strcmp($resourceDirectory, $name)) {
							$this->data["resourceDirectoryUrl"] = $this->data["storageProviderUrl"] . $entity->attributes->path;
							return;
						}
					}
					
					// we could not find a resource directory:
					throw new Exception('"Unabled to find resource directory: ' . $resourceDirectory . ' on OSF"');
				}
			} catch (Exception $e) {
				throw new Exception('{ "function" : "getOsfResourceDirectoryLink()", "context" : "when getting file/directory information from OSF", "error" : ' . $e->getMessage() . ' }');
			}
		}


		/**
		 * Get download links for all available resources in the project's OSF resource directory
		 */
		private function getOsfDownloadLinks() {
			try {
				$ch = curl_init();
				if (FALSE === $ch) {
					throw new Exception('"Unabled to initialize cURL"');
				}
				
				curl_setopt($ch, CURLOPT_URL, $this->data["resourceDirectoryUrl"]);
				curl_setopt($ch, CURLOPT_HTTPHEADER, array('Authorization: Bearer ' . $this->data["token"]));
				curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
				
				$result = curl_exec($ch);
				$error = curl_error($ch);
				//$info = curl_getinfo($ch);
				curl_close($ch);
				
				if (FALSE === $result) {
					throw new Exception('"HTTP GET request failed: ' . $error . '"');
				} else {
					$json = json_decode($result);
					
					if (property_exists($json, "errors")) {
						throw new Exception('"' . $json->errors[0]->detail . '"');
					}

					// look for resource folder:
					$resourceDirectory = $this->data["resourceDirectory"];
					
					// get all resources and their download links:
					foreach ($json->data as $entity) {
						$this->data["resources"][$entity->attributes->name] = $entity->links->download;
					}
				}
			} catch (Exception $e) {
				throw new Exception('{ "function" : "getOsfDownloadLinks()", "context" : "when getting resource download links", "error" : ' . $e->getMessage() . ' }');
			}
		}


		/**
		 * Get resource from OSF server
		 *
		 * <p>Download resource from OSF server onto local experiment server's resource directory</p>
		 * @param {String} $name name of the resource
		 */
		private function getOsfResource($name) {
			try {
				// open local file:
				$resourceLocalFile = $this->data["resourceDirectory"] . "/" . $name;
				$writeHandle = fopen($resourceLocalFile, 'wb');
				if (FALSE === $writeHandle) {
					throw new Exception('"Unabled to open local resource file: ' . $resourceLocalFile . '"');
				}
				
				$ch = curl_init();
				if (FALSE === $ch) {
					throw new Exception('"Unabled to initialize cURL"');
				}

				curl_setopt($ch, CURLOPT_URL, $this->data["resources"][$name]);
				curl_setopt($ch, CURLOPT_HTTPHEADER, array('Authorization: Bearer ' . $this->data["token"]));
				curl_setopt($ch, CURLOPT_FILE, $writeHandle); 
				curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
				curl_setopt($ch, CURLOPT_BINARYTRANSFER, true);
				
				$result = curl_exec($ch);
				$error = curl_error($ch);
				//$info = curl_getinfo($ch);
				curl_close($ch);
				fclose($writeHandle);
				
				if (FALSE === $result) {
					throw new Exception('"HTTP GET request failed: ' . $error . '"');
				}
			} catch (Exception $e) {
				throw new Exception('{ "function" : "getOsfResource()", "context" : "when getting resource: ' . $name . ' from OSF", "error" : ' . $e->getMessage() . ' }');
			}
		}


		/**
		 * Synchronise resources between the OSF server and the experiment server
		 *
		 * <p> Download all available resources from the resource directory of the
		 * project on the OSF server onto the experiment server's resource directory</p>
		 */
		function OsfSync() {
			try {
				$projectId = $this->data["projectId"];
				
				// create resource directory if need be:
				$resourceDirectory = $this->data["resourceDirectory"];
				if (FALSE === file_exists($resourceDirectory)) {
					if (FALSE === mkdir($resourceDirectory)) {
						throw new Exception('"Unabled to create local resource directory: ' . $resourceDirectory . ' on experiment server."');
					}
				}
				
				// get list of all available resources in the resource directory
				// of the project on OSF and their download links:
				$this->getOsfStorageProvider();
				$this->getOsfResourceDirectoryLink();
				$this->getOsfDownloadLinks();
				
				// download all resources and return stringified JSON array of resource names:
				$serverResponse = "[";
				$comma = FALSE;
				foreach ($this->data["resources"] as $name => $downloadLink) {
					$this->getOsfResource($name);
					
					if (TRUE === $comma) {
						$serverResponse = $serverResponse . ', ';
					} else {
						$comma = TRUE;
					}
					$serverResponse = $serverResponse . '"' . $name . '"';
				}
				$serverResponse = $serverResponse . "]";
				
				return $serverResponse;
			} catch (Exception $e) {
				throw new Exception('{ "function" : "OsfSync()", "context" : "when synchronising resources from OSF", "error" : ' . $e->getMessage() . ' }');
			}
		}
		
		
		/**
		 * Manually add a resource to the resource manager
		 * 
		 * @param {String} $name name of the resource
		 */
		private function addResource($name) {
			$this->data["resourceNames"][] = $name;
		}


		/**
		* Show the experiment server synchronisation GUI
		*
		* <p>The GUI gives the experimenter the ability to synchronise resources,
		* i.e. to download them from the project's resource directory on the remote
		* OSF server onto the local experiment server's resource directory, from
		* where they will be accessed by the html/javascript file running in the
		* participants' browsers.</p>
		*/
		private function showSynchronisationGUI() {
			$html = "<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>\n"
			. "<html>\n"
			. "<head><title>" . $this->data['projectId'] . " server</title>\n"
			. "<meta charset='UTF-8'>\n"
			. "<link href='js/vendors/jquery-ui-1.11.4.base/jquery-ui.min.css' rel='stylesheet'>\n"
			. "</head>\n"
			. "<body>\n"
			. "<script type='text/javascript' src='js/vendors/jquery-2.2.0.min.js'></script>\n"
			. "<script type='text/javascript' src='js/vendors/jquery-ui-1.11.4.base/jquery-ui.min.js'></script>\n";

			$html  = $html
			. "<div class='gui'><h1>PsychoJS Experiment Server</h1>"
			. "<div id='info'><ul><li><a href='#project'>" . $this->data['projectName'] . "</a></li></ul>"
			. "<div id='project'>Project ID: <b>" . $this->data['projectId'] . "</b></div><br>"
			. "<div id='actions' style='margin: 1em'><ul><li><a href='#sync'>Synchronisation</a></li></ul>"
			. "<div id='sync'><p>Press the Sync button to download all available project resources from the OSF server onto this PsychoJS experiment server:</p>"
			. "<input type='submit' value='Sync'>"
			. "<hr>"
			. "<div id='result'><p><b>...</b></p></div>"
			. "</div></div></div></div>";
			
			$html = $html
			. "<script>"
			// init tabs:
			. "$( '#info' ).tabs();"
			. "$( '#actions' ).tabs();"
			// init button:
			. "$( '.gui input[type=submit]' ).button();"
			// on click: post SYNC to server, get response and update result div:
			. "$( 'input' ).click( function( event ) {"
			. "document.getElementById('result').innerHTML = '<p><b>Synchronisation in progress...</b></p>';"
			. "$.post('" . $_SERVER['PHP_SELF'] . "',"
			. "{'command' : 'SYNC'})"
			. ".then("
			. "function (result) {"
			. "var json = JSON.parse(result);"
			. "var html = '<p><b><ul>';"
			. "for (var i = 0; i < json.length; i++) { html = html + '<li>successfully downloaded: ' + json[i] + '</li>'; }"
			. "html = html + '</ul></b></p>';"
			. "document.getElementById('result').innerHTML = html; },"
			. "function (error){ document.getElementById('result').innerHTML = '<p>Error: ' + JSON.stringify(error) + '</p>'; }"
			. ");"
			. "} );"
			. "</script>";
			
			$html = $html
			. "</body>\n"
			. "</html>\n";
			
			return $html;
		}
		
		
		/**
		 * List the resources available in the resource directory of the local experiment server
		 *
		 * <p>Note: the experimenter should have first synced the resource directory of the experiment
		 * server with that of the OSF server so that resources are available.</p>
		 *
		 * @return {String} list of available resources in the following JSON string format:
		 * { "function" : "project ID experiment server", "context" : "when listing resources
		 * available on the experiment server", "resources" : [ "resource name #1", "resource name #2", ... ] }
		 *
		 * @throws {String} Throws a JSON string exception if the listing failed.
		 */
		private function listLocalResources() {
			// look for resources in local resource directory on experiment server:
			set_error_handler(function($errno, $errstr) {}, E_WARNING); // suppress warnings
			$scanResults = scandir($this->data["resourceDirectory"]);
			restore_error_handler();
			if (FALSE === $scanResults) {
				throw new Exception('{ "function" : "listLocalResources()", "context" : "when listing resources available on the experiment server", "error" : "Unabled to scan resource directory: ' . $this->data["resourceDirectory"] . '" }');
			}
			
			$serverResponse = '{ "function" : "' . $this->data['projectId'] . ' experiment server", "context" : "when listing resources available on the experiment server", "resources": [';
			$comma = FALSE;
			foreach ($scanResults as $index => $resourceName ) {
				if (0 !== strcmp('.', $resourceName) && 0 !== strcmp('..', $resourceName)) {
					if (TRUE === $comma) {
						$serverResponse = $serverResponse . ',';
					} else {
						$comma = TRUE;
					}
					$serverResponse = $serverResponse . '"' . $resourceName . '"';
				}
			}
			$serverResponse = $serverResponse . ']}';
			return $serverResponse;
		}


		/**
		 * Upload a file from the local experiment server onto the OSF server
		 *
		 * @param {String} $localFileName the name of the file in the resource directory on the local experiment server
		 * @param {String} $OSFFileName the name of the file on the OSF server
		 *
		 * @return {String} JSON string OSF representation of the file
		 *
		 * TODO: if OSF server returns a 409 Conflict error response, we need to send another request: a file modification one, rather than a new one.
		 **/
		private function uploadLocalFileToOSF($localFileName, $OSFFileName) {
			try {
				// get upload URL:
				$this->getOsfStorageProvider();
				$this->getOsfDataDirectoryLink();
				$url = $this->data["dataDirectoryUrl"] . '?kind=file&name=' . $OSFFileName;
				
				// open local file and get its size:
				set_error_handler(function($errno, $errstr) {}, E_WARNING); // suppress warnings
				$handle =  fopen($localFileName, 'r');
				restore_error_handler();
				if (FALSE === $handle) {
					throw new Exception('"Unabled to open local file: ' . $localFileName . '"');
				}
				$fileSize = filesize($localFileName);
				
				// transfer local file to OSF server using a PUT request:
				$ch = curl_init();
				if (FALSE === $ch) {
					throw new Exception('"Unabled to initialize cURL"');
				}
				curl_setopt($ch, CURLOPT_URL, $url);
				curl_setopt($ch, CURLOPT_PUT, true);
				curl_setopt($ch, CURLOPT_HTTPHEADER, array('Authorization: Bearer ' . $this->data["token"]));
				curl_setopt($ch, CURLOPT_INFILESIZE, $fileSize);
				curl_setopt($ch, CURLOPT_INFILE, $handle);
				curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
				
				$return = curl_exec($ch);
				$error = curl_error($ch);
				//$info = curl_getinfo($ch);
				curl_close($ch);
				
				if (FALSE === $return) {
					throw new Exception('"HTTP PUT request failed: ' . $error . '"');
				}
				
				$json = json_decode($return);
				
				// if the PUT request to OSF succeeds the server responds with the file representation
				// therefore, if we don't find a data field in the json string, there must have been
				// an error:
				if (!property_exists($json, "data")) {
					throw new Exception('"' . $json->message_short . '"');
				}
				
				return $return;
			} catch (Exception $e) {
				throw new Exception('{ "function" : "uploadLocalFileToOSF()", "context" : "when uploading local file: ' . $localFileName . ' to OSF", "error" : ' . $e->getMessage() . ' }');
			}
		}


		/**
		 * Save data to the project's resource directory on the local experiment server
		 * and upload them to OSF
		 *
		 * <p>Note: the data are in the data variable of the POST request submitted
		 * to the experiment server.</p>
		 */
		private function OsfUpload() {
			try {
				if (!isset($_POST['session']) || !isset($_POST['data']) || !isset($_POST['dataType'])) {
					throw new Exception('"malformed HTTP POST request: missing session, data or dataType."');
				}
				
				$session = json_decode($_POST['session']);
				$postData = $_POST['data'];
				$postDataType = $_POST['dataType'];
				
				// create data directory if need be:
				set_error_handler(function($errno, $errstr) {}, E_WARNING); // suppress warnings
				$dataDirectory = $this->data["dataDirectory"];
				if (FALSE === file_exists($dataDirectory)) {
					if (FALSE === mkdir($dataDirectory)) {
						throw new Exception('"Unabled to create local data directory: ' . $dataDirectory . ' on experiment server."');
					}
				}
			
				// save data to local file to server as local copy:
				$fileID = $this->cleanString($session->participantName)
				. "_" . $this->cleanString($session->sessionName)
				. "_" . $this->cleanString($session->sessionDate)
				. "_" . $this->cleanString($session->IP);
				if (0 === strcmp('RESULT', $postDataType)) {
					$extension = '.csv';
				}
				else {
					$extension = '.log';
				}
				$localFileName = $dataDirectory . "/" . $fileID . $extension;
				$OSFFileName = $fileID . $extension;
				
				$handle = fopen($localFileName, "w");
				if (FALSE === $handle) {
					throw new Exception('"Unabled to open local file: ' . $localFileName . '"');
				}
				$return = fwrite($handle, $postData);
				if (FALSE === $return) {
					throw new Exception('"Unabled to write to local file: ' . $localFileName . '"');
				}
				fclose($handle);
				restore_error_handler();
				
				// upload local file to OSF:
				$OsfFileRepresentation = $this->uploadLocalFileToOSF($localFileName, $OSFFileName);
				
				$serverResponse = '{ "function" : "OsfUpload()", "context" : "when uploading data to OSF", "localFileName" : "' . $localFileName . '", "OSFFileName" : "' . $OSFFileName . '", "representation" : ' . $OsfFileRepresentation . ' }';
				return $serverResponse;
			} catch (Exception $e) {
				restore_error_handler();
				throw new Exception('{ "function" : "OsfUpload()", "context" : "when uploading data to OSF", "error" : ' . $e->getMessage() . ' }');
			}
		}

		
		/**
		 * Send email to experimenter.
		 *
		 * @param {String} $subject - subject of the email
		 * @param {String} $message - email message
		 *
		 */
		private function sendEmail($subject, $message) {
			$headers   = array();
			$headers[] = "MIME-Version: 1.0";
			$headers[] = "Content-type: text/plain; charset=iso-8859-1";
			$headers[] = "From: " . $this->data['projectId'] . " experiment server";
			$headers[] = "Subject: " . $subject;
			$headers[] = "X-Mailer: PHP/" . phpversion();

			mail($this->data["experimenterEmail"] , $subject, $message, implode("\r\n", $headers));
		}

		
		/**
		* Clean strings by removing all characters except A-Z, a-z, 0-9, dots, hyphens and spaces
		* and replacing sequences of spaces with underscore
		*
		* @param {String} $string string to be cleaned
		* @return {String} cleaned string
		*/
		private function cleanString($string) {
			$cleanedString = preg_replace('/[^A-Za-z0-9\. -]/', '', $string);
			$cleanedString = preg_replace('/  */', '_', $cleanedString);
			return $cleanedString;
		}

	}


	// process the HTTP POST request and return the server response:
	$experimentServer = new ExperimentServer();
	$experimentServer->processPOST();
	//echo $experimentServer->OsfSync();
?>

