#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Helper functions in PsychoPy for interacting with Pavlovia.org
"""
import glob
import json
import pathlib
import os
import re
import time
import subprocess
import traceback

import pandas
from packaging.version import Version

from psychopy import logging, prefs, exceptions
from psychopy.tools.filetools import DictStorage, KnownProjects
from psychopy import app
from psychopy.localization import _translate
import wx

from ..app.errorDlg import exceptionCallback
from ..tools.apptools import SortTerm

try:
    import git  # must import psychopy constants before this (custom git path)
    haveGit = True
except ImportError:
    haveGit = False

import requests
import gitlab
import gitlab.v4.objects

# for authentication
from . import sshkeys
from uuid import uuid4

from .gitignore import gitIgnoreText

from urllib import parse
urlencode = parse.quote

# TODO: test what happens if we have a network initially but lose it
# TODO: test what happens if we have a network but pavlovia times out

pavloviaPrefsDir = os.path.join(prefs.paths['userPrefsDir'], 'pavlovia')
rootURL = "https://gitlab.pavlovia.org"
client_id = '944b87ee0e6b4f510881d6f6bc082f64c7bba17d305efdb829e6e0e7ed466b34'
code_challenge = None
code_verifier = None
scopes = []
redirect_url = 'https://gitlab.pavlovia.org/'

knownUsers = DictStorage(
        filename=os.path.join(pavloviaPrefsDir, 'users.json'))

# knownProjects is a dict stored by id ("namespace/name")
knownProjects = KnownProjects(
        filename=os.path.join(pavloviaPrefsDir, 'projects.json'))
# knownProjects stores the gitlab id to check if it's the same exact project
# We add to the knownProjects when project.local is set (ie when we have a
# known local location for the project)

permissions = {  # for ref see https://docs.gitlab.com/ee/user/permissions.html
    'guest': 10,
    'reporter': 20,
    'developer': 30,  # (can push to non-protected branches)
    'maintainer': 30,
    'owner': 50}

MISSING_REMOTE = -1
OK = 1


def getAuthURL():
    # starting state
    state = str(uuid4())  # create a private "state" based on uuid
    # code challenge and verifier need to be global so we can access them later
    global code_challenge, code_verifier
    # generate code challenge and corresponding verifier
    code_verifier, code_challenge = generateCodeChallengePair()
    # construct auth url
    auth_url = ('https://gitlab.pavlovia.org/oauth/authorize?client_id={}'
                '&redirect_uri={}&response_type=code&state={}&code_challenge={}&code_challenge_method=S256'
                .format(client_id, redirect_url, state, code_challenge))

    return auth_url, state


def generateCodeChallengePair():
    """
    Create a unique random string and its corresponding encoded challenge.

    Returns
    -------
    str
        A code verifier - a random collection of characters
    str
        A code challenge - the code verifier transformed using a particular algorithm
    """
    from numpy.random import randint, choice as randchoice
    import hashlib
    import base64
    # characters valid for a code verifier...
    validChars = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~")
    # first make the answer - pick random alphanumeric chars
    code_verifier = ""
    for n in range(randint(44, 127)):
        code_verifier += randchoice(validChars)
    # transform to make code_challenge
    code_challenge = code_verifier
    # SHA-256 digest
    code_verifier_hash = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    # Base64 urlsafe encode without padding
    code_challenge = base64.urlsafe_b64encode(code_verifier_hash).decode("utf-8").rstrip("=")

    return code_verifier, code_challenge


def login(tokenOrUsername, rememberMe=True):
    """Sets the current user by means of a token

    Parameters
    ----------
    token
    """
    currentSession = getCurrentSession()
    if not currentSession:
        exceptionCallback(exc_type=requests.exceptions.ConnectionError)
        return
    # would be nice here to test whether this is a token or username
    logging.debug('pavloviaTokensCurrently: {}'.format(knownUsers))
    if tokenOrUsername in knownUsers:
        token = knownUsers[tokenOrUsername]  # username so fetch token
    else:
        token = tokenOrUsername
    # it might still be a dict that *contains* the token
    if type(token) == dict and 'token' in token:
        token = token['token']

    # try actually logging in with token
    currentSession.setToken(token)
    if currentSession.user is not None:
        user = currentSession.user
        prefs.appData['projects']['pavloviaUser'] = user['username']
    # update Pavlovia button(s)
    appInstance = app.getAppInstance()
    if appInstance:
        for btn in appInstance.pavloviaButtons['user'] + appInstance.pavloviaButtons['project']:
            btn.updateInfo()


def logout():
    """Log the current user out of pavlovia.

    NB This function does not delete the cookie from the wx mini-browser
    if that has been set. Use pavlovia_ui for that.

     - set the user for the currentSession to None
     - save the appData so that the user is blank
    """
    # create a new currentSession with no auth token
    global _existingSession
    _existingSession = None
    # set appData to None
    prefs.appData['projects']['pavloviaUser'] = None
    prefs.saveAppData()
    for frameWeakref in app.openFrames:
        frame = frameWeakref()
        if hasattr(frame, 'setUser'):
            frame.setUser(None)
    # update Pavlovia button(s)
    for btn in app.getAppInstance().pavloviaButtons['user'] + app.getAppInstance().pavloviaButtons['project']:
        btn.updateInfo()


class User(dict):
    """Class to combine what we know about the user locally and on gitlab

    (from previous logins and from the current session)"""

    def __init__(self, id, rememberMe=True):
        # Get info from Pavlovia
        if isinstance(id, (float, int, str)):
            # If given a number or string, treat it as a user ID / username
            self.info = self.session.session.get(
                "https://pavlovia.org/api/v2/designers/" + str(id)
            ).json()['designer']
            # Make sure self.info has necessary keys
            assert 'gitlabId' in self.info, _translate(
                "Could not retrieve user info for user {}, server returned:\n"
                "{}"
            ).format(id,self.info)
        elif isinstance(id, dict) and 'gitlabId' in id:
            # If given a dict from Pavlovia rather than an ID, store it rather than requesting again
            self.info = id
        else:
            raise TypeError(f"ID must be either an integer representing the user's numeric ID or a string "
                            f"representing their username, not `{id}`.")
        # Store own ID
        self.id = int(self.info['gitlabId'])
        # Get user object from GitLab
        self.user = self.session.gitlab.users.get(self.id)
        # Add user email (mostly redundant but necessary for saving)
        self.user.email = self.info['email']
        # Init dict
        dict.__init__(self, self.info)
        # Update local
        if rememberMe:
            self.saveLocal()

    def __getitem__(self, key):
        # Get either from self or project.attributes
        try:
            value = dict.__getitem__(self, key)
        except KeyError:
            value = self.user.attributes[key]

        return value

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.user.__setattr__(key, value)

    def __str__(self):
        return "pavlovia.User <{}>".format(self['username'])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            # Compare gitlab ID for two User objects
            return int(self['id']) == int(other['id'])
        elif isinstance(other, (int, float)) or (isinstance(other, str) and other.isnumeric()):
            # Compare gitlab ID for an int or int-like
            return int(self['id']) == int(other)
        elif isinstance(other, str):
            # Compare username for a string
            return self['username'] == other

    @property
    def session(self):
        # Cache session if not cached
        if not hasattr(self, "_session"):
            self._session = getCurrentSession()
        # Return cached session
        return self._session

    def saveLocal(self):
        """Saves the data on the current user in the pavlovia/users json file"""
        knownUsers[self['username']] = self.user.attributes
        knownUsers[self['username']]['token'] = self.session.getToken()
        knownUsers.save()

    def save(self):
        self.user.save()


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
        self.userID = None  # populate when token property is set
        self.userFullName = None
        self.remember_me = remember_me
        self.authenticated = False
        self.setToken(token)
        logging.debug("PavloviaLoggedIn")

    @property
    def currentProject(self):
        if hasattr(self, "_currentProject"):
            return self._currentProject

    @currentProject.setter
    def currentProject(self, value):
        self._currentProject = PavloviaProject(value)

    def createProject(self, name, description="", tags=(), visibility='private',
                      localRoot='', namespace=''):
        """Returns a PavloviaProject object (derived from a gitlab.project)

        Parameters
        ----------
        name
        description
        tags
        visibility
        local

        Returns
        -------
        a PavloviaProject object

        """
        if not self.user:
            raise exceptions.NoUserError("Tried to create project with no user logged in")
        # NB gitlab also supports "internal" (public to registered users)
        if type(visibility) == bool and visibility:
            visibility = 'public'
        elif type(visibility) == bool and not visibility:
            visibility = 'private'

        projDict = {}
        projDict['name'] = name
        projDict['description'] = description
        projDict['issues_enabled'] = True
        projDict['visibility'] = visibility
        projDict['wiki_enabled'] = True
        if namespace and namespace != self.username:
            namespaceRaw = self.getNamespace(namespace)
            if namespaceRaw:
                projDict['namespace_id'] = namespaceRaw.id
            else:
                dlg = wx.MessageDialog(None, message=_translate(
                    "PavloviaSession.createProject was given a namespace ({namespace}) that couldn't be found "
                    "on gitlab."
                ).format(namespace=namespace), style=wx.ICON_WARNING)
                dlg.ShowModal()
                return
        # Create project on GitLab
        try:
            gitlabProj = self.gitlab.projects.create(projDict)
        except gitlab.exceptions.GitlabCreateError as e:
            if 'has already been taken' in str(e.error_message):
                # If name is taken, get instead of create
                gitlabProj = self.gitlab.projects.get(f"{self.username}/{name}")
            else:
                # Otherwise, raise original error
                raise e
            # Check for bare remote
            bareRemote = False
            try:
                gitlabProj.repository_tree()
            except gitlab.exceptions.GitlabGetError:
                # If we've made it thus far but can't get a tree, the remote is bare
                bareRemote = True
            # If remote is populated, handle and return
            if not bareRemote:
                dlg = wx.MessageDialog(None, message=_translate(
                    "Project `{namespace}/{name}` already exists, please choose another name."
                ).format(namespace=namespace, name=name), style=wx.ICON_WARNING)
                dlg.ShowModal()
                return
            # Otherwise, continue as normal (bare remote is fine to replace)

        # Create pavlovia project object
        pavProject = PavloviaProject(gitlabProj.get_id(), localRoot=localRoot)
        return pavProject

    def getProject(self, id, localRoot=""):
        """Gets a Pavlovia project from an ID number or namespace/name

        Parameters
        ----------
        id : float
            Numeric ID of the project
        localRoot : str or Path
            Path of the project root

        Returns
        -------
        pavlovia.PavloviaProject or None

        """
        if id:
            return PavloviaProject(id, localRoot=localRoot)
        else:
            return None

    def findProjects(self, search_str='', tags="psychopy"):
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
        rawProjs = self.gitlab.projects.list(
                search=search_str,
                as_list=False)  # iterator not list for auto-pagination
        projs = [PavloviaProject(proj) for proj in rawProjs if proj.id]
        return projs

    def listUserGroups(self, namesOnly=True):
        gps = self.gitlab.groups.list(member=True)
        if namesOnly:
            gps = [this.name for this in gps]
        return gps

    def findUserProjects(self, searchStr=''):
        """Finds all readable projects of a given user_id
        (None for current user)
        """
        try:
            own = self.gitlab.projects.list(owned=True, search=searchStr)
        except Exception as e:
            print(e)
            own = self.gitlab.projects.list(owned=True, search=searchStr)
        group = self.gitlab.projects.list(owned=False, membership=True,
                                          search=searchStr)
        projs = []
        projIDs = []
        for proj in own + group:
            if proj.id not in projIDs and proj.id not in projs:
                projs.append(PavloviaProject(proj.id))
                projIDs.append(proj.id)
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
        self.startSession(token)

    def getNamespace(self, namespace):
        """Returns a namespace object for the given name if an exact match is
        found
        """
        spaces = self.gitlab.namespaces.list(search=namespace)
        # might be more than one, with
        for thisSpace in spaces:
            if thisSpace.path == namespace:
                return thisSpace

    def startSession(self, token):
        """Start a gitlab session as best we can
        (if no token then start an empty session)"""
        self.session = requests.Session()
        if prefs.connections['proxy']:  # if we have a proxy then we'll need to use
            # the requests session to set the proxy
            self.session.proxies = {
                'https': prefs.connections['proxy'],
                'http': prefs.connections['proxy']
            }
        if token:
            if len(token) < 64:
                raise ValueError(
                        "Trying to login with token {} which is shorter "
                        "than expected length ({} not 64) for gitlab token"
                            .format(repr(token), len(token)))
            # Setup gitlab session
            self.gitlab = gitlab.Gitlab(rootURL, oauth_token=token,
                                        timeout=10, session=self.session,
                                        per_page=100)
            try:
                self.gitlab.auth()
            except gitlab.exceptions.GitlabParsingError as err:
                raise ConnectionError(
                    "Failed to authenticate with the gitlab.pavlovia.org server. "
                    "Received a string that could not be parsed by the gitlab library. "
                    "This may be caused by having an institutional proxy server but "
                    "not setting the proxy setting in PsychoPy preferences. If that "
                    "isn't the case for you, then please get in touch so we can work out "
                    "what the cause was in your case! support@opensciencetools.org")

            self.username = self.gitlab.user.username
            self.userID = self.gitlab.user.id  # populate when token property is set
            self.userFullName = self.gitlab.user.name
            self.authenticated = True
            # add the token (although this is also in the gitlab object)
            self.session.headers = {'OauthToken': token}
        else:
            self.gitlab = gitlab.Gitlab(rootURL,
                                        timeout=10, session=self.session,
                                        per_page=100)

    @property
    def user(self):
        if not hasattr(self, "_user") or self._user is None:
            try:
                self._user = User(self.gitlab.user.username)
            except AttributeError:
                return None
        return self._user

    @user.setter
    def user(self, value):
        if isinstance(value, User) or value is None:
            self._user = value
        else:
            self._user = User(value)


class PavloviaSearch(pandas.DataFrame):
    # List all possible sort terms
    sortTerms = [
        SortTerm("nbStars", dLabel=_translate("Most stars"), aLabel=_translate("Least stars"), ascending=False),
        SortTerm("nbForks", dLabel=_translate("Most forks"), aLabel=_translate("Least forks"), ascending=False),
        SortTerm("updateDate", dLabel=_translate("Last edited"), aLabel=_translate("Longest since edited"), ascending=False),
        SortTerm("creationDate", dLabel=_translate("Last created"), aLabel=_translate("First created"), ascending=False),
        SortTerm("name", dLabel=_translate("Name (Z-A)"), aLabel=_translate("Name (A-Z)"), ascending=True),
        SortTerm("pathWithNamespace", dLabel=_translate("Author (Z-A)"), aLabel=_translate("Author (A-Z)"), ascending=True),
    ]

    class FilterTerm(dict):
        # Map filter menu items to project columns
        filterMap = {
            "Author": "designer",
            "Status": "status",
            "Platform": "platform",
            "Visibility": "visibility",
            "Tags": "tags",
        }

        def __str__(self):
            # Start off with blank str
            terms = ""
            # Synonymise visibility unspecified with visibility all ticked (compensate for back-end being
            # exploration focussed)
            if "Visibility" not in self or not self['Visibility']:
                self['Visibility'] = ["owned", "private", "public"]
            # Iterate through values
            for key, value in self.items():
                # Ensure value is iterable and mutable
                if not isinstance(value, (list, tuple)):
                    value = [value]
                value = list(value)
                # Ensure each sub-value is a string
                for i in range(len(value)):
                    value[i] = str(value[i])
                # Skip empty terms
                if len(value) == 0:
                    continue
                # Alias keys
                if key in self.filterMap:
                    key = self.filterMap[key]
                # Add this term
                terms += f"&{key}={','.join(value)}"
            return terms

        def __bool__(self):
            return any(self.values())

    def __init__(self, term, sortBy=None, filterBy=None, mine=False):
        # Replace default filter
        if filterBy is None:
            filterBy = {}
        # Ensure filter is a FilterTerm
        filterBy = self.FilterTerm(filterBy)
        # Do search
        session = getCurrentSession()
        if mine:
            # Display experiments by current user
            data = session.session.get(
                f"https://pavlovia.org/api/v2/designers/{session.userID}/experiments?search={term}{filterBy}",
                timeout=10
            ).json()
        elif term or filterBy:
            data = session.session.get(
                f"https://pavlovia.org/api/v2/experiments?search={term}{filterBy}",
                timeout=10
            ).json()
        else:
            # Display demos for blank search
            data = session.session.get(
                "https://pavlovia.org/api/v2/experiments?search=demos&designer=demos",
                timeout=10
            ).json()
        # Construct dataframe
        pandas.DataFrame.__init__(self, data=data['experiments'])
        # Do any requested sorting
        if sortBy is not None:
            self.sort_values(sortBy)

    def sort_values(self, by, inplace=True, ignore_index=True, **kwargs):
        if isinstance(by, (str, int)):
            by = [str(by)]
        # Add mapped and selected menu items to sort keys list
        sortKeys = []
        ascending = []
        for item in by:
            if item.value in self.columns:
                sortKeys.append(item.value)
                ascending.append(item.ascending)
        # Add pavlovia score as final sort option
        sortKeys.append("pavloviaScore")
        ascending += [False]
        # Do actual sorting
        if sortKeys:
            pandas.DataFrame.sort_values(self, sortKeys,
                                         inplace=inplace, ascending=ascending, ignore_index=ignore_index,
                                         **kwargs)


class PavloviaProject(dict):
    """A Pavlovia project, with name, url etc

    .pavlovia will point to a gitlab project on gitlab.pavlovia.org
        - None if the session couldn't be opened
        - False if the session is open but the repo isn't there (deleted?)
    .repo will will be a local gitpython repo
    .localRoot is the path to the root of the repo
    .id is the namespace/name (e.g. peircej/stroop)
    .idNumber is gitlab numeric id
    .title
    .tags
    .group is technically the namespace. Get the owner from .attributes['owner']
    .localRoot is the path to the local root
    """

    # list of keys which we expect to be datetimes
    _datetimeKeys = ("created_at", "last_activity_at")

    def __init__(self, id, localRoot=None):
        # Cache whatever form of ID is given, to avoid unneccesary calls to Pavlovia/GitLab later
        if isinstance(id, int):
            # If created using a numeric ID...
            self.numericId = id
        elif isinstance(id, str):
            # If created using a "namespace/name" string...
            self.stringId = id
        else:
            # If created using a dict with info from Pavlovia...
            self._info = dict(id)
            if 'gitlabId' in self._info:
                self.numericId = int(self._info['gitlabId'])
            if 'pathWithNamespace' in self._info:
                self.stringId = self._info['pathWithNamespace']
        # Set local root
        if localRoot is not None:
            self.localRoot = localRoot

    def __getitem__(self, key):
        # Get either from self or project.attributes
        try:
            value = dict.__getitem__(self, key)
        except KeyError:
            # if no project, return None
            if self.project is None:
                return None
            # otherwise, get from attributes
            if key in self.project.attributes:
                value = self.project.attributes[key]
            elif hasattr(self, "_info") and key in self._info:
                return self._info[key]
            else:
                value = None
        # Transform datetimes
        if key in self._datetimeKeys:
            value = pandas.to_datetime(value, format=None, errors='coerce')

        return value

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.project.__setattr__(key, value)

    @property
    def id(self):
        """
        ID of this project - will be either a numeric ID or a "namespace/name" string depending
        on which is available. If both are available, "namespace/name" is prioritised.
        """
        if hasattr(self, "stringId"):
            return self.stringId
        elif hasattr(self, "numericId"):
            return self.numericId

    @property
    def info(self):
        """
        Returns the info about the project from Pavlovia API. This may have a delay after
        changes to the GitLab API calls, as the info filters through so use with caution.

        This can be updated with self.refresh()
        """
        if not self._info:
            self.refresh()
        return self._info

    def refresh(self):
        """
        Update the info about the project from Pavlovia API. This may have a delay after
        changes to the GitLab API calls, as the info filters through so use with caution.
        """
        # Update Pavlovia info
        start = time.time()
        self._info = None
        # for a new project it may take time for Pavlovia to register the new ID so try for a while
        while self._info is None and (time.time() - start) < 30:
            requestVal = self.session.session.get(
                f"https://pavlovia.org/api/v2/experiments/{self.id}",
            ).json()
            self._info = requestVal['experiment']
        if self._info is None:
            raise ValueError(f"Could not find project with id `{self.id}` on Pavlovia: {requestVal}")
        # Store received ID values from Pavlovia
        if 'gitlabId' in self._info:
            self.numericId = int(self._info['gitlabId'])
        if 'pathWithNamespace' in self._info:
            self.stringId = self._info['pathWithNamespace']
        if self.project is not None:
            # Reinitialise dict
            dict.__init__(self, self.project.attributes)
            # Convert datetime
            for key in self._info:
                if key in self._datetimeKeys:
                    self._info[key] = pandas.to_datetime(self._info[key], format=None, errors='coerce')
            # Update base dict
            self.update(self.project.attributes)

    @property
    def session(self):
        # If previous value is cached, return it
        if hasattr(self, "_session"):
            return self._session
        # Get and cache current session
        self._session = getCurrentSession()
        return self._session

    @property
    def project(self):
        # If previous value is cached, return it
        if hasattr(self, "_project"):
            return self._project
        # Get and cache gitlab project
        try:
            self._project = self.session.gitlab.projects.get(self.id)
            return self._project
        except gitlab.exceptions.GitlabGetError as e:
            # dlg = wx.MessageDialog(
            #     parent=None,
            #     message=_translate(
            #         "Could not find GitLab project with id {}.\n"
            #         "\n"
            #         "Please check that the project exists on Pavlovia, that you are logged in as the correct user in "
            #         "the PsychoPy app, and that your account has access to the project."
            #     ).format(self.id),
            #     style=wx.ICON_ERROR
            # )
            # dlg.ShowModal()
            return None

    @property
    def editable(self):
        """
        Whether or not the project is editable by the current user
        """
        # If previous value is cached, return it
        if hasattr(self, "_editable") and self._lastEditableCheckUser == self.session.user:
            return self._editable
        # Otherwise, figure it out
        if self.session.user:
            # Get current user id
            _id = self.session.user['id']
            # Get gitlab project users
            _users = self.project.users.list()
            # Return whether or not current user in in project users
            self._editable = _id in [user.id for user in _users]
        else:
            # If there's no user, they can't edit, so return False
            self._editable = False
        # Store user when last checked
        self._lastEditableCheckUser = self.session.user

        return self._editable

    @property
    def owned(self):
        """
        Whether or not the project is owned by the current user
        """
        if bool(self.session.user):
            # If there is a user, return True if they're the owner of this project
            return self['path_with_namespace'].split('/')[0] == self.session.user['username']
        else:
            # If there isn't a user, then they can't own this project, so return False
            return False

    @property
    def starred(self):
        """
        Star/unstar the project, or view starred status
        """
        # If previous value is cached, return it
        if hasattr(self, "_starred"):
            return self._starred
        # Otherwise, return whether this project is in the list of starred projects
        self._starred = bool(self.session.gitlab.projects.list(starred=True, search=str(self.id)))
        return self._starred

    @starred.setter
    def starred(self, value):
        # Enforce bool
        value = bool(value)
        # Store value
        self._starred = value
        # Set on gitlab
        if value:
            self.project.star()
        else:
            self.project.unstar()
        # Get info from Pavlovia again, as star count will have changed
        self.refresh()

    @property
    def remoteHTTPS(self):
        """
        The URL for the https access to thr git repo
        """
        return self.project.http_url_to_repo

    @property
    def remoteSSH(self):
        """
        The URL for the ssh access to the git repo
        """
        return self.project.ssh_url_to_repo

    @property
    def localRoot(self):
        if hasattr(self, "stringId") and self.stringId in knownProjects:
            # If project has known local store, return its root
            return knownProjects[self.stringId]['localRoot']
        elif hasattr(self, "_localRootStatic"):
            # If project has local root stored as static value, return it
            return self._localRootStatic
        else:
            # Otherwise, return blank
            return ""

    @localRoot.setter
    def localRoot(self, value):
        if hasattr(self, "stringId") and self.stringId in knownProjects:
            # If project has known local store, update its root
            knownProjects[self.stringId]['localRoot'] = str(value)
            knownProjects.save()
        elif hasattr(self, "stringId") and hasattr(self, "numericId"):
            # If project has no known local store and we are able to, create one
            knownProjects[self.stringId] = {
                'id': self.stringId,
                'idNumber': self.numericId,
                'localRoot': str(value),
                'remoteHTTPS': f"https://gitlab.pavlovia.org/{self.stringId}.git",
                'remoteSSH': f"git@gitlab.pavlovia.org:{self.stringId}.git"
            }
            knownProjects.save()
        else:
            # If we don't have enough info to save to knownProjects, just store the value given
            self._localRootStatic = value

    def sync(self, infoStream=None):
        """Performs a pull-and-push operation on the remote

        Will check for a local folder and whether that is already (in) a repo.
        If we have a local folder and it is not a git project already then
        this function will also clone the remote to that local folder

        Optional params infoStream is needed if you
        want to update a sync window/panel
        """
        # get info stream if not given
        if infoStream is None:
            infoStream = getInfoStream()
        # Error catch local root
        if not self.localRoot:
            dlg = wx.MessageDialog(self, message=_translate(
                "Can't sync project without a local root. Please specify a local root then try again."
            ), style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            return
        # Error catch logged out
        if not self.session.user:
            dlg = wx.MessageDialog(self, message=_translate(
                "You are not logged in to Pavlovia. Please log in to sync project."
            ), style=wx.ICON_ERROR | wx.OK)
            dlg.ShowModal()
            return
        if self.project is not None:
            # Jot down start time
            t0 = time.time()
            # make repo if needed
            if self.repo is None:
                repo = self.newRepo(infoStream)
                if repo is None:
                    return 0
            # If first commit (besides repo creation), do initial push
            if len(self.project.commits.list()) < 2:
                self.firstPush(infoStream=infoStream)
            # Pull and push
            self.pull(infoStream)
            self.push(infoStream)
            # Write updates
            t1 = time.time()
            msg = (
                "Successful sync at: {}, took {:.3f}s. View synced project here:\n"
                "{}\n".format(
                    time.strftime("%H:%M:%S", time.localtime()),
                    t1 - t0,
                    "https://pavlovia.org/" + self['path_with_namespace']
                )
            )
            logging.info(msg)
            if infoStream:
                infoStream.write(msg + "\n")
                time.sleep(0.5)
            # Refresh info
            self.refresh()
        else:
            # If project doesn't exist, tell the user
            infoStream.write(
                _translate("Sync failed - could not find project with id {}\n\n").format(self.id)
            )

        return 1

    def pull(self, infoStream=None):
        """Pull from remote to local copy of the repository

        Parameters
        ----------
        infoStream

        Returns
        -------
            1 if successful
            -1 if project is deleted on remote
        """
        # get info stream if not given
        if infoStream is None:
            infoStream = getInfoStream()

        if infoStream:
            infoStream.write("Pulling changes from remote...\n")
        if self.repo is None:
            self.cloneRepo(infoStream)
        try:
            info = self.repo.git.pull(self.remoteWithToken, 'master')
            if infoStream:
                infoStream.write("{}\n".format(info))
        except git.exc.GitCommandError as e:
            if ("The project you were looking for could not be found" in
                    traceback.format_exc()):
                    # pointing to a project at pavlovia but it doesn't exist
                    logging.warning("Project not found on gitlab.pavlovia.org")
                    return MISSING_REMOTE
            else:
                raise e

        logging.debug('pull complete: {}'.format(self.project.http_url_to_repo))
        if infoStream:
            infoStream.write("done\n")
        return 1

    def push(self, infoStream=None):
        """Push to remote from local copy of the repository

        Parameters
        ----------
        infoStream

        Returns
        -------
            1 if successful
            -1 if project deleted on remote
        """
        # get info stream if not given
        if infoStream is None:
            infoStream = getInfoStream()

        if infoStream:
            infoStream.write("Pushing changes to remote...\n")
        try:
            info = self.repo.git.push(self.remoteWithToken, 'master')
            if infoStream and len(info):
                infoStream.write("{}\n".format(info))
        except git.exc.GitCommandError as e:
            if ("The project you were looking for could not be found" in
                    traceback.format_exc()):
                    # pointing to a project at pavlovia but it doesn't exist
                    logging.warning("Project not found on gitlab.pavlovia.org")
                    return MISSING_REMOTE
            else:
                raise e

        logging.debug('push complete: {}'.format(self.project.http_url_to_repo))
        if infoStream:
            infoStream.write("done\n")
        return 1

    @property
    def repo(self):
        """Will always try to return a valid local git repo

        Will try to clone if local is empty and remote is not"""
        # If there's no local root, we can't find the repo
        if not self.localRoot:
            raise gitlab.GitlabGetError("Cannot fetch a PavloviaProject until we have chosen a local folder.")
        # If repo is cached, return it
        if hasattr(self, "_repo") and self._repo:
            return self._repo

        # Get git root
        gitRoot = getGitRoot(self.localRoot)

        if gitRoot is None:
            self._repo = self.newRepo()
        elif gitRoot not in [self.localRoot, str(pathlib.Path(self.localRoot).absolute())]:
            # this indicates that the requested root is inside another repo
            raise AttributeError("The requested local path for project\n\t{}\n"
                                 "sits inside another folder, which git will "
                                 "not permit. You might like to set the "
                                 "project local folder to be \n\t{}"
                                 .format(repr(self.localRoot), repr(gitRoot)))
        else:
            # If there's a git root, return the associated repo
            self._repo = git.Repo(gitRoot)
            self.configGitLocal()

        self.writeGitIgnore()

        return self._repo

    @repo.setter
    def repo(self, value):
        self._repo = value

    @property
    def remoteWithToken(self):
        """The remote for git sync using an oauth token (always as a bytes obj)
        """
        return f"https://oauth2:{self.session.token}@gitlab.pavlovia.org/{self['path_with_namespace']}"

    def writeGitIgnore(self):
        """Check that a .gitignore file exists and add it if not"""
        gitIgnorePath = os.path.join(self.localRoot, '.gitignore')
        if not os.path.exists(gitIgnorePath):
            with open(gitIgnorePath, 'w') as f:
                f.write(gitIgnoreText)

    def newRepo(self, infoStream=None):
        """Will either git.init and git.push or git.clone depending on state
        of local files.

        Use newRemote if we know that the remote has only just been created
        and is empty
        """
        # get info stream if not given
        if infoStream is None:
            infoStream = getInfoStream()

        localFiles = glob.glob(os.path.join(self.localRoot, "*"))
        # glob doesn't match hidden files by default so search for them
        localFiles.extend(glob.glob(os.path.join(self.localRoot, ".*")))

        # there's no project at all so create one
        if not self.localRoot:
            raise AttributeError("Cannot fetch a PavloviaProject until we have "
                                 "chosen a local folder.")
        if not os.path.exists(self.localRoot):
            os.makedirs(self.localRoot)

        # check if the remote repo is empty (if so then to init/push)
        if self.project:
            try:
                self.project.repository_tree()
                bareRemote = False
            except gitlab.GitlabGetError as e:
                if "Tree Not Found" in str(e):
                    bareRemote = True
                else:
                    bareRemote = False

        repo = None
        # if remote is new (or existed but is bare) then init and push
        if localFiles and bareRemote:  # existing folder
            repo = git.Repo.init(self.localRoot)
            self.configGitLocal()  # sets user.email and user.name
            # add origin remote and master branch (but no push)
            repo.create_remote('origin', url=self.project.http_url_to_repo)
            repo.git.checkout(b="master")
            self.writeGitIgnore()
            self.stageFiles(['.gitignore'])
            self.commit('Create repository (including .gitignore)')
            self._newRemote = False
        elif localFiles:
            # get project name
            if "/" in self.stringId:
                _, projectName = self.stringId.split("/")
            else:
                projectName = self.stringId
            # ask user if they want to clone to a subfolder
            msg = _translate(
                    "Folder '{localRoot}' is not empty, use '{localRoot}/{projectName}' instead?"
            )
            dlg = wx.MessageDialog(
                None,
                msg.format(localRoot=self.localRoot, projectName=projectName),
                style=wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
            resp = dlg.ShowModal()
            if resp == wx.ID_YES:
                # if yes, update local root
                self.localRoot = pathlib.Path(self.localRoot) / projectName
                # try again
                self.newRepo(infoStream=infoStream)
            elif resp == wx.ID_CANCEL:
                # if they cancelled, stop
                infoStream.write(
                    "Clone cancelled by user.\n"
                )
                repo = None
        else:
            # no files locally so safe to try and clone from remote
            repo = self.cloneRepo(infoStream=infoStream)

        return repo

    def firstPush(self, infoStream):
        # get info stream if not given
        if infoStream is None:
            infoStream = getInfoStream()
        if infoStream:
            infoStream.write("Pushing to Pavlovia for the first time...\n")
        # construct initial commit
        self.stageFiles(infoStream=infoStream)
        info = self.commit(
            _translate("Push initial project files")
        )
        if infoStream and len(info):
            infoStream.write("{}\n".format(info))
        # push
        info = self.repo.git.push('-u', self.remoteWithToken, 'master')
        self.project.attributes['default_branch'] = 'master'
        if infoStream:
            if len(info):
                infoStream.write("{}\n".format(info))
            infoStream.write("Success!\n".format(info))

    def cloneRepo(self, infoStream=None):
        """Gets the git.Repo object for this project, creating one if needed

        Will check for a local folder and whether that is already (in) a repo.
        If we have a local folder and it is not a git project already then
        this function will also clone the remote to that local folder

        Parameters
        ----------
        infoStream

        Returns
        -------
        git.Repo object

        Raises
        ------
        AttributeError if the local project is inside a git repo

        """
        # get info stream if not given
        if infoStream is None:
            infoStream = getInfoStream()
        if not self.localRoot:
            raise AttributeError("Cannot fetch a PavloviaProject until we have "
                                 "chosen a local folder.")

        if infoStream:
            infoStream.write("Cloning from remote...\n")
        repo = git.Repo.clone_from(
                self.remoteWithToken,
                self.localRoot,
        )
        # now change the remote to be the standard (without password token)
        repo.remotes.origin.set_url(self.project.http_url_to_repo)

        self._lastKnownSync = time.time()
        self._newRemote = False

        return repo

    def configGitLocal(self):
        """Set the local repo to have the correct name and email for user

        Returns
        -------
        None
        """
        localConfig = self.repo.git.config(l=True, local=True)  # list local
        if self.session.user['email'] in localConfig:
            return  # we already have it set up so can return
        # set the local config
        with self.repo.config_writer() as config:
            config.set_value("user", "email", self.session.user['email'])
            config.set_value("user", "name", self.session.user['name'])

    def fork(self, to=None):
        # Sub in current user if none given
        if to is None:
            to = self.session.user['username']
        # Do fork
        try:
            glProj = self.project.forks.create({'namespace': to})
        except gitlab.GitlabCreateError:
            raise gitlab.GitlabCreateError(f"Project {self.session.user['username']}/{self['name']} already exists!")
        # Get new project
        proj = PavloviaProject(glProj.id)
        # Return new project
        return proj

    def getChanges(self):
        """Find all the not-yet-committed changes in the repository"""
        changeDict = {}
        changeList = []
        # if we don't have a repo object, there's no changes
        if not hasattr(self, "_repo") or self._repo is None:
            return changeDict, changeList
        # get changes
        changeDict['untracked'] = self.repo.untracked_files
        changeDict['changed'] = []
        changeDict['deleted'] = []
        changeDict['renamed'] = []
        for this in self.repo.index.diff(None):
            # change type, identifying possible ways a blob can have changed
            # A = Added
            # D = Deleted
            # R = Renamed
            # M = Modified
            # T = Changed in the type
            if this.change_type == 'D':
                changeDict['deleted'].append(this.b_path)
            elif this.change_type == 'R':  # only if git rename had been called?
                changeDict['renamed'].append((this.rename_from, this.rename_to))
            elif this.change_type == 'M':
                changeDict['changed'].append(this.b_path)
            elif this.change_type == 'U':
                changeDict['changed'].append(this.b_path)
            else:
                raise ValueError("Found an unexpected change_type '{}' in gitpython Diff".format(this.change_type))
        for categ in changeDict:
            changeList.extend(changeDict[categ])
        return changeDict, changeList

    def stageFiles(self, files=None, infoStream=None):
        """Adds changed files to the stage (index) ready for commit.

        The files is a list and can include new/changed/deleted

        If files=None this is like `git add -u` (all files added/deleted)
        """
        # get info stream if not given
        if infoStream is None:
            infoStream = getInfoStream()

        if files:
            if type(files) not in (list, tuple):
                raise TypeError(
                        'The `files` provided to PavloviaProject.stageFiles '
                        'should be a list not a {}'.format(type(files)))
            try:
                for thisFile in files:
                    self.repo.git.add(thisFile)
            except git.exc.GitCommandError:
                if infoStream:
                    infoStream.SetValue(traceback.format_exc())
        else:
            diffsDict, diffsList = self.getChanges()
            if diffsDict['untracked']:
                self.repo.git.add(diffsDict['untracked'])
            if diffsDict['deleted']:
                self.repo.git.add(diffsDict['deleted'])
            if diffsDict['changed']:
                self.repo.git.add(diffsDict['changed'])

    def getStagedFiles(self):
        """Retrieves the files that are already staged ready for commit"""
        return self.repo.index.diff("HEAD")

    def unstageFiles(self, files):
        """Removes changed files from the stage (index) preventing their commit.
        The files in question can be new/changed/deleted
        """
        self.repo.git.reset('--', files)

    def commit(self, message):
        """Commits the staged changes"""
        info = self.repo.git.commit('-m', message)
        time.sleep(0.1)
        # then get a new copy of the repo
        self.repo = git.Repo(self.localRoot)

        return info

    def save(self):
        """Saves the metadata to gitlab.pavlovia.org"""
        try:
            self.project.save()
            return True
        except gitlab.GitlabUpdateError as err:
            msgRoot = "Could not sync project.\n\n"
            if err.response_code == 400:
                # Error: Avatar is too big
                msg = msgRoot + _translate("Avatar is too big, should be at most 200 KB.")
                dlg = wx.MessageDialog(None, msg, style=wx.ICON_ERROR)
                dlg.ShowModal()
                # Reset avatar
                self['avatar_url'] = ""
            return False

        # note that saving info locally about known projects is done
        # by the knownProjects DictStorage class

    @property
    def pavloviaStatus(self):
        return self.__dict__['pavloviaStatus']

    @pavloviaStatus.setter
    def pavloviaStatus(self, newStatus):
        url = 'https://pavlovia.org/server?command=update_project'
        data = {'projectId': self.id, 'projectStatus': 'ACTIVATED'}
        resp = requests.put(url, data)
        if resp.status_code == 200:
            self.__dict__['pavloviaStatus'] = newStatus
        else:
            print(resp)

    @property
    def permissions(self):
        """This returns the user's overall permissions for the project as int.
        Unlike the project.attribute['permissions'] which returns a dict of
        permissions for group/project which is sometimes also a dict and
        sometimes an int!

        returns
        ------------
        permissions as an int:
            -1 = probably not logged in?
            None = logged in but no permissions

        """
        if not getCurrentSession().user:
            return -1
        if 'permissions' in self.attributes:
            # collect perms for both group and individual access
            allPerms = []
            permsDict = self.attributes['permissions']
            if 'project_access' in permsDict:
                allPerms.append(permsDict['project_access'])
            if 'group_access' in permsDict:
                allPerms.append(permsDict['group_access'])
            # make ints and find the max permission of the project/group
            permInts = []
            for thisPerm in allPerms:
                # check if deeper in dict
                if type(thisPerm) == dict:
                    thisPerm = thisPerm['access_level']
                # we have a single value (but might still be None)
                if thisPerm is not None:
                    permInts.append(thisPerm)
            if permInts:
                perms = max(permInts)
            else:
                perms = None
        elif hasattr(self, 'project_access') and self.project_access:
            perms = self.project_access
            if type(perms) == dict:
                perms = perms['access_level']
        else:
            perms = None  # not sure if this ever occurs when logged in
        return perms


def getGitRoot(p):
    """Return None or the root path of the repository"""
    if not haveGit:
        raise exceptions.DependencyError(
                "gitpython and a git installation required for getGitRoot()")

    p = pathlib.Path(p).absolute()
    if not p.is_dir():
        p = p.parent  # given a file instead of folder?

    proc = subprocess.Popen('git branch --show-current',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd=str(p), shell=True,
                            universal_newlines=True)  # newlines forces stdout to unicode
    stdout, stderr = proc.communicate()
    if 'not a git repository' in (stdout + stderr):
        return None
    else:
        # this should have been possible with git rev-parse --top-level
        # but that sometimes returns a virtual symlink that is not the normal folder name
        # e.g. some other mount point?
        selfAndParents = [p] + list(p.parents)
        for thisPath in selfAndParents:
            if list(thisPath.glob('.git')):
                return str(thisPath)  # convert Path back to str


def getNameWithNamespace(p):
    """
    Return None or the root path of the repository
    """
    # Work out cwd
    if not haveGit:
        raise exceptions.DependencyError(
                "gitpython and a git installation required for getGitRoot()")

    p = pathlib.Path(p).absolute()
    if not p.is_dir():
        p = p.parent  # given a file instead of folder?
    # Open git process
    proc = subprocess.Popen('git config --get remote.origin.url',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd=str(p), shell=True,
                            universal_newlines=True)  # newlines forces stdout to unicode
    stdout, stderr = proc.communicate()
    # Find a gitlab url in the response
    url = re.match(r"https:\/\/gitlab\.pavlovia\.org\/\w*\/\w*\.git", stdout)
    if url:
        # Get contents of url from response
        url = url.string[url.pos:url.endpos]
        # Get namespace/name string from url
        path = url
        path = re.sub(r"\.git[.\n]*", "", path)
        path = re.sub(r"[.\n]*https:\/\/gitlab\.pavlovia\.org\/", "", path)
        return path
    else:
        return None


def getProject(filename):
    """Will try to find (locally synced) pavlovia Project for the filename
    """
    # Check that we have Git
    if not haveGit:
        raise exceptions.DependencyError(
                "gitpython and a git installation required for getProject()")
    # Get git root
    gitRoot = getGitRoot(filename)
    # Get name with namespace
    path = getNameWithNamespace(filename)
    # Get session
    session = getCurrentSession()
    # Start off with proj as None
    proj = None
    # If already found, return
    if (knownProjects is not None) and (path in knownProjects) and ('idNumber' in knownProjects[path]):
        # Make sure we are logged in
        nameSpace, projectName = path.split("/")
        # Try to log in if not logged in
        if not session.user:
            if nameSpace in knownUsers:
                # Log in if user is known
                login(nameSpace, rememberMe=True)
            else:
                # Check whether project repo is found in any of the known users accounts
                for user in knownUsers:
                    try:
                        login(user)
                    except requests.exceptions.ConnectionError:
                        break

        thisId = knownProjects[path]['id']
        # Check that project still exists on Pavlovia
        requestVal = session.session.get(
            f"https://pavlovia.org/api/v2/experiments/{thisId}",
        ).json()
        if requestVal['experiment'] is None:
            # If project has been deleted, return None
            return None
        # If project is still there, get it
        try:
            return PavloviaProject(thisId, localRoot=gitRoot)
        except LookupError as err:
            # If project not found, print warning and return None
            logging.warn(str(err))
            return None
    elif gitRoot:
        # Existing repo but not in our knownProjects. Investigate
        logging.info("Investigating repo at {}".format(gitRoot))
        localRepo = git.Repo(gitRoot)
        for remote in localRepo.remotes:
            for url in remote.urls:
                if "gitlab.pavlovia.org" in url:
                    # Get namespace from url
                    # could be 'https://gitlab.pavlovia.org/NameSpace/Name.git'
                    # or may be 'git@gitlab.pavlovia.org:NameSpace/Name.git'
                    namespaceName = url.split('gitlab.pavlovia.org')[1]
                    # remove the first char if it's : or /
                    if namespaceName[0] in ['/', ':']:
                        namespaceName = namespaceName[1:]
                    # Remove .git
                    namespaceName = namespaceName.replace(".git", "")
                    # Split to get namespace
                    nameSpace, projectName = namespaceName.split('/')
                    # Get current session
                    pavSession = getCurrentSession()
                    # Try to log in if not logged in
                    if not pavSession.user:
                        if nameSpace in knownUsers:
                            # Log in if user is known
                            login(nameSpace, rememberMe=True)
                        else:
                            # Check whether project repo is found in any of the known users accounts
                            for user in knownUsers:
                                try:
                                    login(user)
                                except requests.exceptions.ConnectionError:
                                    break
                                foundProject = False
                                for repo in pavSession.findUserProjects():
                                    if namespaceName in repo:
                                        foundProject = True
                                        logging.info("Logging in as {}".format(user))
                                        break
                                if not foundProject:
                                    logging.warning("Could not find {namespace} in your Pavlovia accounts. "
                                                    "Logging in as {user}.".format(namespace=namespaceName,
                                                                                   user=user))

                    if pavSession.user:
                        # Get PavloviaProject via id
                        proj = pavSession.getProject(namespaceName, localRoot=gitRoot)
                        proj.repo = localRepo
                    else:
                        # If we are still logged out, prompt user
                        logging.warning(_translate("We found a repository pointing to {} "
                                                   "but no user is logged in for us to check it".format(url)))
                    return proj

            if proj is None:
                # Warn user if still no project
                logging.warning("We found a repository at {} but it "
                                "doesn't point to gitlab.pavlovia.org. "
                                "You could create that as a remote to "
                                "sync from PsychoPy.".format(gitRoot))


global _existingSession
_existingSession = None


# create an instance of that
def getCurrentSession():
    """Returns the current Pavlovia session, creating one if not yet present

    Returns
    -------

    """
    global _existingSession
    if _existingSession:
        return _existingSession
    else:
        _existingSession = PavloviaSession()
    return _existingSession


def refreshSession():
    """Restarts the session with the same user logged in"""
    global _existingSession
    if _existingSession and _existingSession.getToken():
        _existingSession = PavloviaSession(
                token=_existingSession.getToken()
        )
    else:
        _existingSession = PavloviaSession()
    return _existingSession


def getInfoStream():
    """
    Get the Git output panel in the Runner frame, if any is active.

    Returns
    -------
    ScriptOutputCtrl
        Ctrl to write to
    """
    # attempt to get the Runner frame
    frame = app.getAppFrame("runner")
    # get ctrl from runner
    if frame is not None:
        return frame.getOutputPanel("git").ctrl
