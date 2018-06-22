#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Helper functions in PsychoPy for interacting with Pavlovia.org
"""

import glob
import os, sys, time
from psychopy import logging, prefs, constants
from psychopy.tools.filetools import DictStorage
import gitlab
import gitlab.v4.objects
import git
import subprocess
# for authentication
from uuid import uuid4
import io

rootURL = "https://gitlab.pavlovia.org"
client_id = '4bb79f0356a566cd7b49e3130c714d9140f1d3de4ff27c7583fb34fbfac604e0'
scopes = []
redirect_url = 'https://gitlab.pavlovia.org/'

knownUsers = DictStorage(filename=os.path.join(prefs.paths['userPrefsDir'],
                                    'pavlovia','users.json'))

# knownProjects is a dict stored by id ("namespace/name")
knownProjects = DictStorage(filename=os.path.join(prefs.paths['userPrefsDir'],
                                    'pavlovia','projects.json'))
# This also stores the numeric gitlab id to check if it's the same exact project
# We add to the knownProjects when project.local is set (ie when we have a
# known local location for the project)

# these are instantiated at bottom
# currentSession = PavloviaSession()

permissions = {  # for ref see https://docs.gitlab.com/ee/user/permissions.html
    'guest': 10,
    'reporter': 20,
    'developer': 30,  # (can push to non-protected branches)
    'maintainer': 30,
    'owner': 50}


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
    print('tokensCurrently:', knownUsers)
    if tokenOrUsername in knownUsers:
        token = knownUsers[tokenOrUsername]  # username so fetch token
    else:
        token = tokenOrUsername

    # try actually logging in with token
    currentSession.setToken(token)
    prefs.appData['projects']['pavloviaUser'] = currentSession.user.username
    knownUsers[currentSession.user.username] = token


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

    def createProject(self, name, description="", tags=(), visibility='private',
                      local=''):
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
        # NB gitlab also supports "internal" (public to registered users)
        if type(visibility)==bool and visibility:
            visibility = 'public'
        elif type(visibility)==bool and not visibility:
            visibility = 'private'

        projDict = {}
        projDict['name'] = name
        projDict['description'] = description
        projDict['issues_enabled'] = True
        projDict['visibility'] = visibility
        projDict['wiki_enabled'] = True

        #TODO: add avatar option?
        #TODO: add namespace option?
        gitlabProj = self.gitlab.projects.create(projDict)
        pavProject = PavloviaProject(gitlabProj)
        pavProject.local = local
        return pavProject

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

    def findUserProjects(self):
        """Finds all readable projects of a given user_id
        (None for current user)
        """
        own = self.gitlab.projects.list(owned=True)
        group = self.gitlab.projects.list(owned=False, membership=True)
        projs = []
        projIDs = []
        for proj in own+group:
            if proj.id and proj.id not in projIDs:
                projs.append(PavloviaProject(proj))
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

        if token and len(token) < 64:
            raise ValueError("Trying to login with token {} which is shorter "
                            "than expected length ({} not 64) for gitlab token"
                            .format(repr(token), len(token)))

        self.__dict__['token'] = token
        if token:
            self.gitlab = gitlab.Gitlab(rootURL, oauth_token=token)
            self.gitlab.auth()
            self.username = self.gitlab.user.username
            self.token = token
            # update stored tokens
            if self.remember_me:
                tokens = knownUsers
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


class PavloviaProject(dict):
    """A Pavlovia project, with name, url etc
    """

    def __init__(self, proj):
        dict.__init__(self)
        self._storedAttribs = {}  # these will go into knownProjects file
        self['id'] = ''
        self['local'] = ''
        self['remoteSSH'] = ''
        self['remoteHTTPS'] = ''
        if isinstance(proj, gitlab.v4.objects.Project):
            self._proj = proj
        else:
            self._proj = currentSession.gitlab.projects.get(proj)
        self.repo = None  # update with getRepo()
        self._lastKnownSync = None

    def __getattr__(self, name):
        if name == 'owner':
            return
        proj = self.__dict__['_proj']
        toSearch = [self, self.__dict__, proj._attrs]
        if 'attributes' in self._proj.__dict__:
            toSearch.append(self._proj.__dict__['attributes'])
        for attDict in toSearch:
            if name in attDict:
                return attDict[name]
        # error if none found
        if name == 'id':
            selfDescr = "PavloviaProject"
        else:
            selfDescr = repr(
                self)  # this includes self.id so don't use if id fails!
        raise AttributeError("No attribute '{}' in {}".format(name, selfDescr))

    @property
    def _proj(self):
        return self.__dict__['_proj']
    @_proj.setter
    def _proj(self, proj):
        global knownProjects
        self.__dict__['_proj'] = proj
        thisID = proj.attributes['path_with_namespace']
        if thisID in knownProjects:
            rememberedProj = knownProjects[thisID]
            if rememberedProj['idNumber'] != proj.attributes['id']:
                logging.warning("Project {} has changed gitlab ID since last "
                                "use (was {} now {})"
                                .format(thisID,
                                        rememberedProj['idNumber'],
                                        proj.attributes['id']))
            self.update(rememberedProj)
        else:
            self['local'] = ''
            self['id'] = proj.attributes['path_with_namespace']
            self['idNumber'] = proj.attributes['id']
        self['remoteSSH'] = proj.ssh_url_to_repo
        self['remoteHTTPS'] = proj.http_url_to_repo

    @property
    def local(self):
        return self['local']
    @local.setter
    def local(self, local):
        self['local'] = local
        # this is where we add a project to knownProjects:
        knownProjects[self.id] = self

    @property
    def id(self):
        if 'id' in self._proj.attributes:
            return self._proj.attributes['path_with_namespace']

    @property
    def idNumber(self):
        return self._proj.attributes['id']

    @property
    def owner(self):
        return self._proj.attributes['namespace']['name']

    @property
    def attributes(self):
        return self._proj.attributes

    @property
    def title(self):
        """The title of this project (alias for name)
        """
        return self.name

    @property
    def tags(self):
        """The title of this project (alias for name)
        """
        return self.tag_list

    def sync(self, syncPanel=None, progressHandler=None):
        """Performs a pull-and-push operation on the remote

        Will check for a local folder and whether that is already (in) a repo.
        If we have a local folder and it is not a git project already then
        this function will also clone the remote to that local folder

        Optional params syncPanel and progressHandler are both needed if you
        want to update a sync window/panel
        """
        if not self.repo:  # if we haven't been given a local copy of repo then find
            self.getRepo(progressHandler=progressHandler)
            # if cloned in last 2s then it was a fresh clone
            if time.time() < self._lastKnownSync+2:
                return 1
        # pull first then push
        self.pull(syncPanel, progressHandler)
        self.push(syncPanel, progressHandler)
        self._lastKnownSync =time.time()

    def pull(self, repo, syncPanel=None, progressHandler=None):
        """Pull from remote to local copy of the repository

        Parameters
        ----------
        syncPanel
        progressHandler

        Returns
        -------

        """
        syncPanel.setStatus("Pulling changes from remote...")
        syncPanel.Refresh()
        syncPanel.Layout()
        origin = self.remotes.origin
        origin.pull(progress=progressHandler)

    def push(self, syncPanel=None, progressHandler=None):
        """Pull from remote to local copy of the repository

        Parameters
        ----------
        syncPanel
        progressHandler

        Returns
        -------

        """
        syncPanel.setStatus("Pushing changes to remote...")
        syncPanel.Refresh()
        syncPanel.Layout()
        origin = self.remotes.origin
        origin.push(progress=progressHandler)

    def getRepo(self, syncPanel=None, progressHandler=None, forceRefresh=False):
        """Will always try to return a valid local git repo
        Underneath, this is stored as _repo. If .repo is requested then """
        if self.repo and not forceRefresh:
            return self.repo
        if not self.local:
            raise AttributeError("Cannot fetch a PavloviaProject until we have "
                                 "chosen a local folder.")
        gitRoot = getGitRoot(self.local)
        if gitRoot is None:
            # there's no project at all so create one
            progressHandler.setStatus("Cloning from remote...")
            progressHandler.syncPanel.Refresh()
            progressHandler.syncPanel.Layout()
            repo = git.Repo.clone_from(
                self.remoteHTTPS,
                self.local,
                progress=progressHandler)
            freshClone = 1
        elif gitRoot != self.local:
            # this indicates that the requested root is inside another repo
            raise AttributeError("The requested local path for project\n\t{}\n"
                                 "sits inside another folder, which git will "
                                 "not permit. You might like to set the "
                                 "project local folder to be \n\t{}"
                                 .format(repr(self.local), repr(gitRoot)))
        else:
            repo = git.Repo(gitRoot)
        self.repo = repo

    def cloneRepo(self, progressHandler):
        """Gets the git.Repo object for this project, creating one if needed

        Will check for a local folder and whether that is already (in) a repo.
        If we have a local folder and it is not a git project already then
        this function will also clone the remote to that local folder

        Parameters
        ----------
        progressHandler is subclassed from gitlab.remote.RemoteProgress

        Returns
        -------
        git.Repo object

        Raises
        ------
        AttributeError if the local project is inside a git repo

        """
        if not self.local:
            raise AttributeError("Cannot fetch a PavloviaProject until we have "
                                 "chosen a local folder.")
        progressHandler.setStatus("Cloning from remote...")
        progressHandler.syncPanel.Refresh()
        progressHandler.syncPanel.Layout()
        repo = git.Repo.clone_from(
            self.remoteHTTPS,
            self.local,
            progress=progressHandler)
        self._lastKnownSync = time.time()
        self._repo = repo
        # using wx process giving error about bad macbundle for 'git'
        #     command = ('/usr/local/bin/git clone --progress {} {}'
        #            .format(self.remoteHTTPS, self.local))
        #     proc = wx.Process(progressHandler)
        #     proc.Redirect()
        #     _opts = wx.EXEC_ASYNC | wx.EXEC_MAKE_GROUP_LEADER
        #     # launch the command
        #     print(command)
        #     pID = wx.Execute(command, _opts, proc)

        # using plain python subprocess (capture of stdout not working)
        #     command = ' '.join(['git', 'clone', '--progress', self.remoteHTTPS, self.local])
        #     print(command)
        #     process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        #     time.sleep(0.5)
        #     output, err = process.communicate()
        #     print(output)

    def save(self):
        self._proj.save()


def getGitRoot(p):
    """Return None or the root path of the repository"""
    if not os.path.isdir(p):
        p = os.path.split(p)[0]
    if subprocess.call(["git", "branch"],
                       stderr=subprocess.STDOUT, stdout=open(os.devnull, 'w'),
                       cwd=p) != 0:
        return None
    else:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=p)
        return out.strip()


def getProject(filename):
    """Will try to find (locally synced) pavlovia Project for the filename"""
    gitRoot = getGitRoot(filename)
    if gitRoot and gitRoot in knownProjects:
        return knownProjects[gitRoot]

# create an instance of that
currentSession = PavloviaSession()
