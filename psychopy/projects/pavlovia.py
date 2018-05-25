#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Helper functions in PsychoPy for interacting with projects (e.g. from pyosf)
"""
import glob
import os
from psychopy import logging
import gitlab

from psychopy import prefs

projectsFolder = os.path.join(prefs.paths['userPrefsDir'], 'projects')

rootURL = "https://gitlab.pavlovia.org"



class Session(gitlab.Gitlab):
    """A class to track a session with the OSF server.

    The session will store a token, which can then be used to authenticate
    for project read/write access
    """
    def __init__(self, username=None, password=None, token=None, otp=None,
                 remember_me=True, chunk_size=default_chunk_size):
        """Create a session to send requests with the OSF server

        Provide either username and password for authentication with a new
        token, or provide a token from a previous session, or nothing for an
        anonymous user
        """
        self.username = username
        self.password = password
        self.user_id = None  # populate when token property is set
        self.user_full_name = None
        self.remember_me = remember_me
        self.authenticated = False
        # set token (which will update session headers as needed)
        if token is not None:
            self.token = token
        elif username is not None:
            self.authenticate(username, password, otp)
        self.headers.update({'content-type': 'application/json'})
        # placeholders for up/downloader threads
        self.downloader = None
        self.uploader = None
        self.chunk_size = default_chunk_size

    def open_project(self, proj_id):
        """Returns a OSF_Project object or None (if that id couldn't be opened)
        """
        return PavloviaProject(session=self, id=proj_id)

    def create_project(self, title, descr="", tags=[], public=False,
                       category='project'):
        raise NotImplemented
        return project_node

    def find_projects(self, search_str, tags="psychopy"):
        """
        Parameters
        ----------
        search_str : str
            The string to search for in the title of the project
        tags : str
            Comma-separated string containing tags

        Returns
        -------
        A list of OSFProject objects

        """
        url = "{}/nodes/".format(constants.API_BASE)
        intro = "?"
        if tags:
            tagsList = tags.split(",")
            for tag in tagsList:
                tag = tag.strip()  # remove surrounding whitespace
                if tag == '':
                    continue
                url += "{}filter[tags][icontains]={}".format(intro, tag)
                intro = "&"
        if search_str:
            url += "{}filter[title][icontains]={}".format(intro, search_str)
            intro = "&"
        logging.info("Searching Pavlovia using: {}".format(url))
        t0 = time.time()
        logging.info("Download results took: {}s".format(time.time()-t0))
        return projs

    def find_users(self, search_str):
        """Find user IDs whose name matches a given search string
        """
        return users

    def find_user_projects(self, user_id=None):
        """Finds all readable projects of a given user_id
        (None for current user)
        """

        return projs

    @property
    def token(self):
        """The authorisation token for the current logged in user
        """
        return self.__dict__['token']

    @token.setter
    def token(self, token, save=None):
        """Set the token for this session and check that it works for auth
        """
        self.__dict__['token'] = token
        if token is None:
            headers = {}
        else:
            headers = {
                'Authorization': 'Bearer {}'.format(token),
            }
        self.headers.update(headers)
        # then populate self.userID and self.userName
        resp = self.get(constants.API_BASE+"/users/me/", timeout=10.0)
        if resp.status_code != 200:
            raise exceptions.AuthError("Invalid credentials trying to get "
                                       "user data:\n{}".format(resp.json()))
        else:
            logging.info("Successful authentication with token")
        json_resp = resp.json()
        self.authenticated = True
        data = json_resp['data']
        self.user_id = data['id']
        self.user_full_name = data['attributes']['full_name']
        # update stored tokens
        if save is None:
            save = self.remember_me
        if save and self.username is not None:
            tokens = TokenStorage()
            tokens[self.username] = token
            tokens.save()

    def authenticate(self, username, password=None, otp=None):
        """Authenticate according to username and password (if needed).

        If the username has been used already to create a token then that
        token will be reused (and no password is required). If not then the
        password will be sent (using https) and an auth token will be stored.
        """
        # try fetching a token first
        tokens = TokenStorage()
        if username in tokens:
            logging.info("Found previous auth token for {}".format(username))
            try:
                self.token = tokens[username]
                return 1
            except exceptions.AuthError:
                if password is None:
                    raise exceptions.AuthError("User token didn't work and no "
                                               "password has been provided")
        elif password is None:
            raise exceptions.AuthError("No auth token found and no "
                                       "password given")
        token_url = constants.API_BASE+'/tokens/'
        token_request_body = {
            'data': {
                'type': 'tokens',
                'attributes': {
                    'name': '{} - {}'.format(
                        constants.PROJECT_NAME, datetime.date.today()),
                    'scopes': constants.APPLICATION_SCOPES
                }
            }
        }
        headers = {'content-type': 'application/json'}

        if otp is not None:
            headers['X-OSF-OTP'] = otp
        resp = self.post(
            token_url,
            headers=headers,
            data=json.dumps(token_request_body),
            auth=(username, password), timeout=10.0,
            )
        if resp.status_code in (401, 403):
            # If login failed because of a missing two-factor authentication
            # code, notify the user to try again
            # This header appears for basic auth requests, and only when a
            # valid password is provided
            otp_val = resp.headers.get('X-OSF-OTP', '', timeout=10.0)
            if otp_val.startswith('required'):
                raise exceptions.AuthError('Must provide code for two-factor'
                                           'authentication')
            else:
                raise exceptions.AuthError('Invalid credentials')
        elif not resp.status_code == 201:
            raise exceptions.AuthError('Invalid authorization response')
        else:
            json_resp = resp.json()
            logging.info("Successfully authenticated with username/password")
            self.authenticated = True
            self.token = json_resp['data']['attributes']['token_id']
            return 1

    def download_file(self, url, local_path,
                      size=0, threaded=False, changes=None):
        """ Download a file with given object id

        Parameters
        ----------

        asset : str or dict
            The OSF id for the file or dict of info
        local_path : str
            The full path where the file will be downloaded

        """
        if threaded:
            if self.downloader is None or \
                    self.downloader.status != NOT_STARTED:  # can't re-use
                self.downloader = PushPullThread(
                    session=self, kind='pull',
                    finished_callback=self.finished_downloads,
                    changes=changes)
            self.downloader.add_asset(url, local_path, size)
        else:
            # download immediately
            reply = self.get(url, stream=True, timeout=30.0)
            if reply.status_code == 200:
                with open(local_path, 'wb') as f:
                    for chunk in reply.iter_content(self.chunk_size):
                        f.write(chunk)
                if changes:
                    changes.add_to_index(local_path)  # signals success

    def upload_file(self, url, update=False, local_path=None,
                    size=0, threaded=False, changes=None):
        """Adds the file to the OSF project.
        If containing folder doesn't exist then it will be created recursively

        update is used if the file already exists but needs updating (version
        will be incremented).
        """
        if threaded:
            if self.uploader is None or \
                    self.uploader.status != NOT_STARTED:  # can't re-use
                self.uploader = PushPullThread(
                    session=self, kind='push',
                    finished_callback=self.finished_uploads,
                    changes=changes)
            self.uploader.add_asset(url, local_path, size)
        else:
            with open(local_path, 'rb') as f:
                reply = self.put(url, data=f, timeout=30.0)
            with open(local_path, 'rb') as f:
                local_md5 = hashlib.md5(f.read()).hexdigest()
            if reply.status_code not in [200, 201]:
                raise exceptions.HTTPSError(
                    "URL:{}\nreply:{}"
                    .format(url, json.dumps(reply.json(), indent=2)))
            node = FileNode(self, reply.json()['data'])
            if local_md5 != node.json['attributes']['extra']['hashes']['md5']:
                raise exceptions.OSFError(
                    "Uploaded file did not match existing SHA. "
                    "Maybe it didn't fully upload?")
            logging.info("Uploaded (unthreaded): ".format(local_path))
            if changes:
                changes.add_to_index(local_path)  # signals success
            return node

    def finished_uploads(self):
        self.uploader = None

    def finished_downloads(self):
        self.downloader = None

    def apply_changes(self):
        """If threaded up/downloading is enabled then this begins the process
        """
        if self.uploader:
            self.uploader.start()
        if self.downloader:
            self.downloader.start()

    def get_progress(self):
        """Returns either:
                    {'up': [done, total],
                     'down': [done, total]}
                or:
                    1 for finished
        """
        done = True  # but we'll check for alive threads and set False
        if self.uploader is None:
            up = [0, 0]
        else:
            if self.uploader.isAlive():
                done = False
            up = [self.uploader.finished_size,
                  self.uploader.queue_size]

        if self.downloader is None:
            down = [0, 0]
        else:
            if self.downloader.isAlive():
                done = False
            down = [self.downloader.finished_size,
                    self.downloader.queue_size]

        if not done:  # at least one thread reported being alive
            return {'up': up, 'down': down}
        else:
            return 1



class PavloviaProject(Node):
    """
    """
    def __init__(self, session, id):
        if session is None:
            session = Session()  # create a default (anonymous Session)
        self.session = session

        if type(id) is dict:
            self.json = id
            id = self.json['id']
        elif id.startswith('https'):
            # treat as URL. Extract the id from the request data
            reply = self.session.get(id, timeout=10.0)
            if reply.status_code == 200:
                self.json = reply.json()['data']
                id = self.json['id']
            elif reply.status_code == 410:
                raise exceptions.OSFDeleted(
                    "OSF Project {} appears to have been deleted"
                    .format(id))
            else:
                raise exceptions.HTTPSError(
                    "Failed to fetch OSF Project with URL:\n{}"
                    .format(reply, id))
        else:
            # treat as OSF id and fetch the URL
            url = "{}/nodes/{}/".format(constants.API_BASE, id)
            reply = self.session.get(url, timeout=10.0)
            if reply.status_code == 200:
                self.json = reply.json()['data']
            elif reply.status_code == 410:
                raise exceptions.OSFDeleted(
                    "OSF Project {} appears to have been deleted"
                    .format(url))
            else:
                raise exceptions.HTTPSError(
                    "Failed to fetch OSF Project with ID:\n {}: {}\n"
                    .format(reply, url))

        self.id = id

        self.containers = {}  # a dict of Nodes and folders to contain files
        self.path = ""  # provided for consistency with FileNode
        self.name = ""  # provided for consistency with FileNode
        self._index = None
        self.uploader = None  # to cache asynchronous uploads
        self.downloader = None  # to cache asynchronous downloads

    def __repr__(self):
        return "PavloviaProject(%r)" % (self.id)

    @property
    def title(self):
        """The title of this node/project
        """
        raise NotImplemented

    @property
    def attributes(self):
        """The attribute (meta)data about this node
        """
        raise NotImplemented

    @property
    def links(self):
        """The links are the URLs the node has to download, upload etc
        """
        return self.json['links']

    @property
    def parent(self):
        """Returns a new Node of the parent object or None
        """
        raise NotImplemented

    @property
    def name(self):
        """Name of this file
        """
        raise NotImplemented

    @property
    def path(self):
        """The path to this folder/file from the root
        """
        raise NotImplemented

    @property
    def files(self):
        """A json representation of files at this level of the heirarchy
        """
        raise NotImplemented

    @property
    def info(self):
        raise NotImplemented

    def download(self, target_path, threaded=False):
        """Download (clone) the project
        """
        raise NotImplemented
