#! python

from google.oauth2 import service_account
from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import os
from pathlib import Path
import datetime

# author: JWP
 
# Define the auth scopes to request.
scope = 'https://www.googleapis.com/auth/drive'

class GDrive:
    def __init__(self, drive_key):
        """
        Params:
            drive_key: json dict, or b64-encoded string, of the service account key
            drive_folder: id of the googledrive folder to store in
        """
        self.drive_key = drive_key
        # Authenticate and construct service.
        service = self._get_service(
            api_name='drive',
            api_version='v3',
            scopes=[scope],)
        self._files = service.files()
        
    def _get_service(self, api_name, api_version, scopes):
        """Get a service that communicates to a Google API.

        Params:
            api_name: The name of the api to connect to.
            api_version: The api version to connect to.
            scopes: A list auth scopes to authorize for the application.

        Returns:
            A service that is connected to the specified API.
        """
        credentials = service_account.Credentials.from_service_account_info(self.drive_key)
        scoped_credentials = credentials.with_scopes(scopes)
        # Build the service object.
        service = build(api_name, api_version, credentials=scoped_credentials)
        return service

    def list_files(self, 
                   query='', 
                   folder_id='', 
                   name_substr='', 
                   fulltxt_substr='', 
                   trashed='false'):
        """List files in a folder (optional) meeting various query criteria

        params: 
            query: the full query string for the listing (overrides other options)
            folder_id: the google id of the folder (from the URL)
            name_substr: a string that must be in the name
            fulltxt_substr: a string that must be in the full text of the document
            trashed: 'false' (,'true', None)
                ('false') the trash status of files to return
                NB. that 'true' returns ONLY trashed files. None returns all files
        """
        # see more query examples at
        #   https://developers.google.com/drive/api/guides/search-files#examples
        # set up the query
        if not query:
            queries = []
            if folder_id:
                queries.append(f"'{folder_id}' in parents")
            if name_substr:
                queries.append(f"name contains '{name_substr}'")
            if fulltxt_substr:
                queries.append(f"fullText contains '{fulltxt_substr}'")
            if trashed:
                queries.append(f"trashed = {trashed}")
            query = ' and '.join(queries)

        #list files
        files = []
        page_token = None
        while True:  # i.e. for each page in response
            # pylint: disable=maybe-no-member
            response = self._files.list(q=query,
                                supportsAllDrives='true',
                                includeItemsFromAllDrives='true',
                                spaces='drive',
                                corpora='allDrives',
                                fields='nextPageToken, files(id, name, parents)',
                                pageToken=page_token).execute()
            for file in response.get('files', []):
                print(f'Found: {file.get("name")}, {file.get("id")}, (parents={file.get("parents")})')

            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

    def upload_files(self, folder_id, filepath, 
                     glob_pattern="**/*",
                     ignore=['.DS_Store'],
                     suffix=""):
        """Upload 1 or more files using a filepath or a folder.

        NB Wildcards are not yet supported in the filepath/ignore params.

        params:
            folder_id : the folder ID on GDrive to which we upload
            filepath : the local path either to a file or a folder 
                       (uploads all files anywhere in that folder and subfolders)
            glob_pattern : if a folder is provided then can also give a glob 
                           pattern to match to (e.g '**/*.exe' for all exe files 
                           in all subfolders)
            ignore : list of files to ignore
        """
        p = Path(filepath)
        if p.is_dir():
            # we have a folder so find all files
            files = list(p.glob(glob_pattern))
        elif p.is_file():
            files = [p]
        else:  # not an actual file or folder but maybe a glob pattern?
            files = []
            print(f"No files found. The filepath should be either a valid"
                  " file or a folder to search")
        
        if len(list(files)) > 50:
            raise RuntimeError("There are more than 50 files there. "
                               "Zip them first or use glob_pattern to select files.")
        for f in files:
            if f.name not in ignore and f.is_file():

                name = f.stem + suffix + f.suffix
                print(f"uploading {str(f.absolute())} to {name}...",)
                self.upload_file(folder_id, filepath=f.absolute(), name=name)

    def upload_file(self, folder_id, filepath, name='', mimetype=''):
        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        print(f'Trying upload "{filepath}" to "{name}" (mimetype={mimetype})')
    
        if not name:
            name = Path(filepath).name
        if not mimetype:
            import mimetypes
            mimetype = mimetypes.guess_type(filepath)[0]
        # create a file
        file_metadata = {
            'name': name,
            'parents': [folder_id]
        }
        contents = MediaFileUpload(filepath, mimetype=mimetype,
                                   resumable=True)
        file = self._files.create(
            body=file_metadata, media_body=contents,
            supportsAllDrives='true',
            fields='id, name, parents'
        ).execute()
        print(f'File "{filepath}" has been uploaded to "{file.get("name")}" ({file.get("id")}) in https://drive.google.com/drive/u/0/folders/{file.get("parents")[0]}')
    
    def trash_file(self, file_id):
        """Set the 'trashed' flag for this body
        """
        body = {'trashed': True}
        updated_file = self._files.update(fileId=file_id, body=body).execute()

    @property
    def drive_key(self):
        return self._drive_key
    @drive_key.setter
    def drive_key(self, key):
        if type(key) is str:
            import json
            import base64
            key = json.loads(base64.b64decode( key ))
        self._drive_key = key

    
if __name__ == '__main__':
    import argparse
    # from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("drive_key", 
                        help="The base64-encoded key info for the authentication")
    parser.add_argument("--folder_id", 
                        help="The google ID of the folder to list or save the file in")
    parser.add_argument("-f", "--filepath", 
                        help="The full path/name of the local file")
    parser.add_argument("-n", "--name", 
                        help="The name for the new file (defaults to existing)")
    parser.add_argument("--suffix", 
                        help="The add something to filename (before extension)")
    parser.add_argument("--trash_file", 
                        help="The google ID of the file to trash")
    parser.add_argument("--glob_pattern", 
                        help="For folder uploads a glob pattern can be used e.g. **/*.exe")
    args = parser.parse_args()

    # check required args
    if not args.drive_key:
        raise ValueError("drive_key not defined")
    if not args.glob_pattern:
        glob_pattern = "**/*"  # all files in all subfolders
    else:
        glob_pattern = args.glob_pattern
    if args.suffix == 'date':
        suffix = datetime.datetime.now().strftime("_%Y-%m-%d_%H-%M")
    elif args.suffix:
        suffix = args.suffix
    else:
        suffix = ''
        
    folder_id = args.folder_id or ''
    # are we listing the folder or uploading a file?
    gdrive = GDrive(drive_key=args.drive_key)
    if args.filepath:
        gdrive.upload_files(filepath=args.filepath, 
                            folder_id=args.folder_id,
                            glob_pattern=glob_pattern,
                            suffix=suffix)
    elif args.trash_file:
        gdrive.trash_file(args.trash_file)
    else:
        gdrive.list_files(folder_id=args.folder_id)
