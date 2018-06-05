#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Helper functions in PsychoPy for interacting with Pavlovia.org
"""

# note that in this package we are using snake case for class methods so that
# methods have same names as OSF projects

import glob
import os
from psychopy import logging, prefs
import gitlab
# for authentication
from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session
from uuid import uuid4
projectsFolder = os.path.join(prefs.paths['userPrefsDir'], 'projects')

rootURL = "https://gitlab.pavlovia.org"
client_id = '4bb79f0356a566cd7b49e3130c714d9140f1d3de4ff27c7583fb34fbfac604e0'
scopes = []
redirect_url = 'https://gitlab.pavlovia.org/'

def getAuthURL():
    state = str(uuid4())  # create a private "state" based on uuid
    auth_url = ('https://gitlab.pavlovia.org/oauth/authorize?client_id={}'
                '&redirect_uri={}&response_type=token&state={}'
                .format(client_id, redirect_url, state))
    return auth_url, state


class PavloviaSession(gitlab.Gitlab):
    """A class to track a session with the OSF server.

    The session will store a token, which can then be used to authenticate
    for project read/write access
    """
    def __init__(self, username=None, password=None, token=None, otp=None,
                 remember_me=True):
        """Create a session to send requests with the pavlovia server

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
        self.token = token
        # placeholders for up/downloader threads
        self.syncThread = None

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

        # then populate self.userID and self.userName

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


    def apply_changes(self):
        """If threaded up/downloading is enabled then this begins the process
        """
        raise NotImplemented



class PavloviaProject:
    """A Pavlovia project, with name, url etc
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
