#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Helper functions in PsychoPy for interacting with Pavlovia.org
"""

import glob
import os
from psychopy import logging, prefs, constants
import gitlab
import gitlab.v4.objects
import json
# for authentication
from uuid import uuid4
projectsFolder = os.path.join(prefs.paths['userPrefsDir'], 'projects')

rootURL = "https://gitlab.pavlovia.org"
client_id = '4bb79f0356a566cd7b49e3130c714d9140f1d3de4ff27c7583fb34fbfac604e0'
scopes = []
redirect_url = 'https://gitlab.pavlovia.org/'

# these are instantiated at bottom
# currentSession = PavloviaSession()
# tokenStorage = PavloviaTokenStorage()

def getAuthURL():
    state = str(uuid4())  # create a private "state" based on uuid
    auth_url = ('https://gitlab.pavlovia.org/oauth/authorize?client_id={}'
                '&redirect_uri={}&response_type=token&state={}'
                .format(client_id, redirect_url, state))
    return auth_url, state


def login(tokenOrUsername, rememberMe=True):
    """Sets the current user by means of a token

    Parameters
    ----------
    token
    """
    global currentSession
    # would be nice here to test whether this is a token or username
    if tokenOrUsername in tokenStorage:
        token = tokenStorage[tokenOrUsername]
    else:
        token = tokenOrUsername
    # try actually logging in with token
    currentSession.setToken(token)
    prefs.appData['projects']['pavloviaUser'] = currentSession.user.username


class PavloviaSession:
    """A class to track a session with the server.

    The session will store a token, which can then be used to authenticate
    for project read/write access
    """
    def __init__(self, token=None, remember_me=True):
        """Create a session to send requests with the pavlovia server

        Provide either username and password for authentication with a new
        token, or provide a token from a previous session, or nothing for an
        anonymous user
        """
        self.username = None
        self.password = None
        self.userID = None  # populate when token property is set
        self.userFullName = None
        self.remember_me = remember_me
        self.authenticated = False
        self.currentProject = None
        self.gitlab = None
        self.setToken(token)

    def openProject(self, projID):
        """Returns a OSF_Project object or None (if that id couldn't be opened)
        """

        proj = PavloviaProject(session=self, id=projID)
        self.currentProject = proj
        return proj

    def createProject(self, title, descr="", tags=[], public=False,
                       category='project'):
        raise NotImplemented

    def projectFromID(self, id):
        """Gets a Pavlovia project from an ID (which in gitlab is a number
        indicating the number of the project since gitlab instantiation

        Parameters
        ----------
        id

        Returns
        -------
        pavlovia.PavloviaProject or None

        """
        if id:
            return PavloviaProject(id)
        else:
            return None

    def findProjects(self, search_str, tags="psychopy"):
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
        print('did fake search')
        return

    def findUserProjects(self, user_id=None):
        """Finds all readable projects of a given user_id
        (None for current user)
        """
        projs=[]
        for proj in self.gitlab.projects.list():
            if proj.id:
                projs.append(PavloviaProject(proj))
        return projs

    def findUsers(self, search_str):
        """Find user IDs whose name matches a given search string
        """
        return self.gitlab.users

    def getToken(self):
        """The authorisation token for the current logged in user
        """
        return self.__dict__['token']

    def setToken(self, token):
        """Set the token for this session and check that it works for auth
        """
        self.__dict__['token'] = token
        if token:
            self.gitlab = gitlab.Gitlab(rootURL, oauth_token=token)
            self.gitlab.auth()
            self.username = self.gitlab.user.username
            self.token = token
            # update stored tokens
            if self.remember_me:
                tokens = PavloviaTokenStorage()
                tokens[self.username] = token
                tokens.save()

    def applyChanges(self):
        """If threaded up/downloading is enabled then this begins the process
        """
        raise NotImplemented

    @property
    def user(self):
        if hasattr(self.gitlab, 'user'):
            return self.gitlab.user
        else:
            return None


class PavloviaTokenStorage(dict):
    """Dict-based class to store all the known tokens according to username
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.load()

    def load(self, filename=None):
        """Load all tokens from a given filename
        (defaults to ~/.PsychoPy3/pavlovia.json)
        """
        if filename is None:
            filename = os.path.join(prefs.paths['userPrefsDir'], 'pavlovia.json')
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                try:
                    self.update(json.load(f))
                except ValueError:
                    pass  # file didn't contain valid json data

    def save(self, filename=None):
        """Save all tokens from a given filename
        (defaults to ~/.PsychoPy3/pavlovia.json)
        """
        if filename is None:
            filename = os.path.join(prefs.paths['userPrefsDir'], 'pavlovia.json')
        if not os.path.isdir(prefs.paths['userPrefsDir']):
            os.makedirs(prefs.paths['userPrefsDir'])
        with open(filename, 'wb') as f:
            json_str = json.dumps(self)
            if constants.PY3:
                f.write(bytes(json_str, 'UTF-8'))
            else:
                f.write(json_str)

class PavloviaProject:
    """A Pavlovia project, with name, url etc
    """
    def __init__(self, proj):
        if isinstance(proj, gitlab.v4.objects.Project):
            self._proj = proj
        else:
            self._proj = self.gitlab.projects.get(id)
        #print(self.attributes)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            return getattr(self._proj, name)
        raise AttributeError("No attribute by the name {} in {}"
                             .format(name, self))


    def __repr__(self):
        return "PavloviaProject(%r)" % (self.id)

    def __str__(self):
        return "PavloviaProject {}: {}" % (self.id, self.attributes)

    @property
    def id(self):
        if 'id' not in self.attributes:
            return None
        else:
            return self.attributes['id']

    @property
    def owner(self):
        if 'owner' in self.attributes:
            print("own {}".format(self.attributes['owner'].username))
            return self.attributes['owner'].username
        else:
            print("namespace {}".format(self.namespace['name']))
            return self.namespace['name']

    # @property
    # def owner(self):
    #     """Name of this file
    #     """
    #     if 'owner' in self.attributes:
    #         owner = self.owner['username']
    #     else:
    #         owner = self.namespace['name']
    #     return str(owner)

    @property
    def title(self):
        """The title of this project (alias for name)
        """
        return self.name


# create an instance of that
tokenStorage = PavloviaTokenStorage()
currentSession = PavloviaSession()
