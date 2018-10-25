#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Helper functions in PsychoPy for interacting with Pavlovia.org
"""
from future.builtins import object
import glob
import os, time, socket
import traceback
import subprocess

from psychopy import logging, prefs, constants
from psychopy.tools.filetools import DictStorage
from psychopy import app
from psychopy.localization import _translate
import requests
import gitlab
import gitlab.v4.objects

import dulwich
import dulwich.porcelain as git

# for authentication
from . import sshkeys
from uuid import uuid4

from .gitignore import gitIgnoreText

if constants.PY3:
    from urllib import parse

    urlencode = parse.quote
else:
    import urllib

    urlencode = urllib.quote

# TODO: test what happens if we have a network initially but lose it
# TODO: test what happens if we have a network but pavlovia times out

pavloviaPrefsDir = os.path.join(prefs.paths['userPrefsDir'], 'pavlovia')
rootURL = "https://gitlab.pavlovia.org"
client_id = '4bb79f0356a566cd7b49e3130c714d9140f1d3de4ff27c7583fb34fbfac604e0'
scopes = []
redirect_url = 'https://gitlab.pavlovia.org/'

knownUsers = DictStorage(
        filename=os.path.join(pavloviaPrefsDir, 'users.json'))

# knownProjects is a dict stored by id ("namespace/name")
knownProjects = DictStorage(
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
    currentSession = getCurrentSession()
    if not currentSession:
        raise ConnectionError("Failed to connect to Pavlovia.org. No network?")
    # would be nice here to test whether this is a token or username
    logging.debug('pavloviaTokensCurrently: {}'.format(knownUsers))
    if tokenOrUsername in knownUsers:
        token = knownUsers[tokenOrUsername]  # username so fetch token
    else:
        token = tokenOrUsername
    # it might still be a dict that *contains* the token
    if type(token)==dict and 'token' in token:
        token = token['token']

    # try actually logging in with token
    currentSession.setToken(token)
    user = User(gitlabData=currentSession.user, rememberMe=rememberMe)
    prefs.appData['projects']['pavloviaUser'] = user.username


def logout():
    """Log the current user out of pavlovia.

    NB This function does not delete the cookie from the wx mini-browser
    if that has been set. Use pavlovia_ui for that.

     - set the user for the currentSession to None
     - save the appData so that the user is blank
    """
    # create a new currentSession with no auth token
    global _existingSession
    _existingSession = PavloviaSession()  # create an empty session (user is None)
    # set appData to None
    prefs.appData['projects']['pavloviaUser'] = None
    prefs.saveAppData()
    for frameWeakref in app.openFrames:
        frame = frameWeakref()
        if hasattr(frame, 'setUser'):
            frame.setUser(None)


class User(object):
    """Class to combine what we know about the user locally and on gitlab

    (from previous logins and from the current session)"""

    def __init__(self, localData={}, gitlabData=None, rememberMe=True):
        currentSession = getCurrentSession()
        self.data = localData
        self.gitlabData = gitlabData
        # try looking for local data
        if gitlabData and not localData:
            if gitlabData.username in knownUsers:
                self.data = knownUsers[gitlabData.username]


        # then try again to populate fields
        if gitlabData and not localData:
            self.data['username'] = gitlabData.username
            self.data['token'] = currentSession.getToken()
            self.avatar = gitlabData.attributes['avatar_url']
        elif 'avatar' in localData:
            self.avatar = localData['avatar']
        elif gitlabData:
            self.avatar = gitlabData.attributes['avatar_url']

        # check and/or create SSH keys
        sshIdPath = os.path.join(prefs.paths['userPrefsDir'],
                                 "ssh", self.username)
        if os.path.isfile(sshIdPath):
            self.publicSSH = sshkeys.getPublicKey(sshIdPath + ".pub")
        else:
            self.publicSSH = sshkeys.saveKeyPair(sshIdPath,
                                                 comment=gitlabData.email)
        # convert bytes to unicode if needed
        if type(self.publicSSH) == bytes:
            self.publicSSH = self.publicSSH.decode('utf-8')
        # push that key to gitlab.pavlovia if possible/needed
        if gitlabData:
            keys = gitlabData.keys.list()
            keyName = '{}@{}'.format(
                    self.username, socket.gethostname().strip(".local"))
            remoteKey = None
            for thisKey in keys:
                if thisKey.title == keyName:
                    remoteKey = thisKey
                    break
            if not remoteKey:
                remoteKey = gitlabData.keys.create({'title': keyName,
                                                    'key': self.publicSSH})
        if rememberMe:
            self.saveLocal()

    def __str__(self):
        return "pavlovia.User <{}>".format(self.username)

    def __getattr__(self, name):
        if name not in self.__dict__ and hasattr(self.gitlabData, name):
            return getattr(self.gitlabData, name)
        raise AttributeError(
                "No attribute '{}' in this PavloviaUser".format(name))

    @property
    def username(self):
        if 'username' in self.gitlabData.attributes:
            return self.gitlabData.username
        elif 'username' in self.data:
            return self.data['username']
        else:
            return None

    @property
    def url(self):
        return self.gitlabData.web_url

    @property
    def name(self):
        return self.gitlabData.name

    @name.setter
    def name(self, name):
        self.gitlabData.name = name

    @property
    def token(self):
        return self.data['token']

    @property
    def avatar(self):
        if 'avatar' in self.data:
            return self.data['avatar']
        else:
            return None

    @avatar.setter
    def avatar(self, location):
        if os.path.isfile(location):
            self.data['avatar'] = location

    def _fetchRemoteAvatar(self, url=None):
        if not url:
            url = self.avatar_url
        exten = url.split(".")[-1]
        if exten not in ['jpg', 'png', 'tif']:
            exten = 'jpg'
        avatarLocal = os.path.join(pavloviaPrefsDir, ("avatar_{}.{}"
                                                      .format(self.username,
                                                              exten)))

        # try to fetch the actual image file
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(avatarLocal, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            return avatarLocal
        return None

    def saveLocal(self):
        """Saves the data on the current user in the pavlovia/users json file"""
        # update stored tokens
        tokens = knownUsers
        tokens[self.username] = self.data
        tokens.save()

    def save(self):
        self.gitlabData.save()


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
        self.currentProject = None
        self.setToken(token)
        logging.debug("PavloviaLoggedIn")

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
            raise NoUserError("Tried to create project with no user logged in")
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
                raise ValueError("PavloviaSession.createProject was given a "
                                 "namespace that couldn't be found on gitlab.")
        # TODO: add avatar option?
        # TODO: add namespace option?
        try:
            gitlabProj = self.gitlab.projects.create(projDict)
        except gitlab.exceptions.GitlabCreateError as e:
            if 'has already been taken' in str(e.error_message):
                gitlabProj = "{}/{}".format(namespace, name)
            else:
                print('something bad happended!')
                raise e
        pavProject = PavloviaProject(gitlabProj, localRoot=localRoot)
        return pavProject

    def getProject(self, id, repo=None):
        """Gets a Pavlovia project from an ID number or namespace/name

        Parameters
        ----------
        id a numerical

        Returns
        -------
        pavlovia.PavloviaProject or None

        """
        if id:
            return PavloviaProject(id, repo=repo)
        elif repo:
            return PavloviaProject(repo=repo)
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
        own = self.gitlab.projects.list(owned=True, search=searchStr)
        group = self.gitlab.projects.list(owned=False, membership=True,
                                          search=searchStr)
        projs = []
        projIDs = []
        for proj in own + group:
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
        if token:
            if len(token) < 64:
                raise ValueError(
                        "Trying to login with token {} which is shorter "
                        "than expected length ({} not 64) for gitlab token"
                            .format(repr(token), len(token)))
            self.gitlab = gitlab.Gitlab(rootURL, oauth_token=token, timeout=2)
            self.gitlab.auth()
            self.username = self.user.username
            self.userID = self.user.id  # populate when token property is set
            self.userFullName = self.user.name
            self.authenticated = True
        else:
            self.gitlab = gitlab.Gitlab(rootURL, timeout=1)

    @property
    def user(self):
        if hasattr(self.gitlab, 'user'):
            return self.gitlab.user
        else:
            return None


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

    def __init__(self, proj=None, repo=None, localRoot=''):
        dict.__init__(self)
        self._storedAttribs = {}  # these will go into knownProjects file
        self['id'] = ''
        self['localRoot'] = ''
        self['remoteSSH'] = ''
        self['remoteHTTPS'] = ''
        self._lastKnownSync = 0

        # try to find the remote project through a connection to pavlovia
        if proj:  # we were given a proj or projID for the remote
            currentSession = getCurrentSession()
            self._newRemote = False  # False can also indicate 'unknown'
            if isinstance(proj, gitlab.v4.objects.Project):
                self.pavlovia = proj
            elif currentSession.gitlab is None:
                self.pavlovia = None
            else:
                try:
                    self.pavlovia = currentSession.gitlab.projects.get(proj)
                except gitlab.exceptions.GitlabGetError as e:
                    if "404 Project Not Found" in str(e):
                        self.pavlovia = False
                    else:
                        raise e
        else:
            self.pavlovia = None

        self.repo = repo

        # do we already have a local folder for this?
        if localRoot:
            self.localRoot = localRoot
        elif self.id in knownProjects:
            self.localRoot = knownProjects[self.id]['localRoot']
        elif self.repo:
            self.localRoot = repo.path
            self.configGitLocal()
        else:
            self.localRoot = localRoot  # which is probably ''

    def __getattr__(self, name):
        if name == 'owner':
            return
        proj = self.__dict__['pavlovia']
        if not proj:
            return
        toSearch = [self, self.__dict__, proj._attrs]
        if 'attributes' in self.pavlovia.__dict__:
            toSearch.append(self.pavlovia.__dict__['attributes'])
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
    def pavlovia(self):
        return self.__dict__['pavlovia']

    @pavlovia.setter
    def pavlovia(self, proj):
        global knownProjects
        self.__dict__['pavlovia'] = proj
        if not hasattr(proj, 'attributes'):
            return
        thisID = proj.attributes['path_with_namespace']
        if thisID in knownProjects \
                and os.path.exists(knownProjects[thisID]['localRoot']):
            rememberedProj = knownProjects[thisID]
            if rememberedProj['idNumber'] != proj.attributes['id']:
                logging.warning("Project {} has changed gitlab ID since last "
                                "use (was {} now {})"
                                .format(thisID,
                                        rememberedProj['idNumber'],
                                        proj.attributes['id']))
            self.update(rememberedProj)
        elif 'localRoot' in self:
            # this means the local root was set before the remote was known
            self['id'] = proj.attributes['path_with_namespace']
            self['idNumber'] = proj.attributes['id']
            knownProjects[self['id']] = self
        else:
            self['localRoot'] = ''
            self['id'] = proj.attributes['path_with_namespace']
            self['idNumber'] = proj.attributes['id']
        self['remoteSSH'] = proj.ssh_url_to_repo
        self['remoteHTTPS'] = proj.http_url_to_repo

    @property
    def emptyRemote(self):
        return not bool(self.pavlovia.attributes['default_branch'])

    @property
    def localRoot(self):
        return self['localRoot']

    @localRoot.setter
    def localRoot(self, localRoot):
        self['localRoot'] = localRoot.replace('\\', '/')
        # this is where we add a project to knownProjects
        # if we have both a
        if localRoot and self.id:  # i.e. not set to None or ''
            knownProjects[self.id] = self

    @property
    def id(self):
        if self.pavlovia and 'id' in self.pavlovia.attributes:
            return self.pavlovia.attributes['path_with_namespace']

    @property
    def idNumber(self):
        if self.pavlovia:
            return self.pavlovia.attributes['id']

    @property
    def remoteWithToken(self):
        """The remote for git sync using an oauth token
        """
        currentSession = getCurrentSession()
        rawHTTPS = self['remoteHTTPS']
        if rawHTTPS:
            remote = rawHTTPS.replace('https://gitlab.pavlovia.org/',
                                      'https://oauth2:{}@gitlab.pavlovia.org/'
                                      .format(currentSession.token))
        else:
            remote = None

        return remote
    @property
    def group(self):
        if self.pavlovia:
            namespaceName = self.id.split('/')[0]
            return namespaceName

    @property
    def attributes(self):
        if self.pavlovia:
            return self.pavlovia.attributes

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

    def sync(self, infoStream=None):
        """Performs a pull-and-push operation on the remote

        Will check for a local folder and whether that is already (in) a repo.
        If we have a local folder and it is not a git project already then
        this function will also clone the remote to that local folder

        Optional params infoStream is needed if you
        want to update a sync window/panel
        """
        self.repo = self.getRepo(forceRefresh=True, infoStream=infoStream)
        if not self.repo:  # if we haven't been given a local copy of repo then find
            self.getRepo(infoStream=infoStream)
            # if cloned in last 2s then it was a fresh clone
            if time.time() < self._lastKnownSync + 2:
                return 1
        # pull first then push
        t0 = time.time()
        if self.emptyRemote:  # we don't have a repo there yet to do a 1st push
            self.firstPush()
        else:
            status = self.pull(infoStream=infoStream)
            if status == MISSING_REMOTE:
                return -1
            self.repo = dulwich.repo.Repo(self.localRoot)  # get a new copy of repo (
            time.sleep(0.1)
            status = self.push(infoStream=infoStream)
            if status == MISSING_REMOTE:
                return -1

        self._lastKnownSync = t1 = time.time()
        msg = ("Successful sync at: {}, took {:.3f}s"
               .format(time.strftime("%H:%M:%S", time.localtime()), t1 - t0))
        logging.info(msg)
        if infoStream:
            infoStream.write("\n" + msg)
            time.sleep(0.5)
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
        if infoStream:
            infoStream.write("\nPulling changes from remote...")

        try:
            git.pull(self.repo, self.remoteWithToken,
                     outstream=infoStream,
                     errstream=infoStream)
        except Exception as e:
            if ("The project you were looking for could not be found" in
                    traceback.format_exc()):
                # we are pointing to a project at pavlovia but it doesn't exist
                # suggest we create it
                logging.warning("Project not found on gitlab.pavlovia.org")
                return MISSING_REMOTE
            else:
                raise e

        logging.debug('pull complete: {}'.format(self.remoteHTTPS))
        if infoStream:
            infoStream.write("done")
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
        if infoStream:
            infoStream.write("\nPushing changes to remote...")
        try:
            git.push(self.repo, self.remoteWithToken, 'master',
                     outstream=infoStream, errstream=infoStream)
        except Exception as e:
            if ("The project you were looking for could not be found" in
                    traceback.format_exc()):
                # we are pointing to a project at pavlovia but it doesn't exist
                # suggest we create it
                logging.warning("Project not found on gitlab.pavlovia.org")
                return MISSING_REMOTE
            else:
                raise e
        logging.debug('push complete: {}'.format(self.remoteHTTPS))
        if infoStream:
            infoStream.write("done")
        return 1

    def getRepo(self, infoStream=None, forceRefresh=False,
                newRemote=False):
        """Will always try to return a valid local git repo

        Will try to clone if local is empty and remote is not"""
        if self.repo and not forceRefresh:
            return self.repo
        if not self.localRoot:
            raise AttributeError("Cannot fetch a PavloviaProject until we have "
                                 "chosen a local folder.")
        gitRoot = getGitRoot(self.localRoot)

        if gitRoot is None:
            self.newRepo(infoStream=infoStream)
        elif gitRoot != self.localRoot:
            # this indicates that the requested root is inside another repo
            raise AttributeError("The requested local path for project\n\t{}\n"
                                 "sits inside another folder, which git will "
                                 "not permit. You might like to set the "
                                 "project local folder to be \n\t{}"
                                 .format(repr(self.localRoot), repr(gitRoot)))
        else:
            self.repo = git.Repo(gitRoot)
            self.configGitLocal()

        self.writeGitIgnore()
        return self.repo

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
        localFiles = glob.glob(os.path.join(self.localRoot, "*"))
        # there's no project at all so create one
        if not self.localRoot:
            raise AttributeError("Cannot fetch a PavloviaProject until we have "
                                 "chosen a local folder.")
        if not os.path.exists(self.localRoot):
            os.mkdirs(self.localRoot)
        if localFiles and self._newRemote:  # existing folder
            self.repo = dulwich.repo.Repo.init(self.localRoot)
            self.configGitLocal()  # sets user.email and user.name
            # add origin remote and master branch (but no push)
            git.remote_add(self.repo, name='origin', url=self['remoteHTTPS'])
            # self.repo.git.checkout(b="master")
            self.writeGitIgnore()
            self.stageFiles(['.gitignore'])
            self.commit('Create repository (including .gitignore)')
            self._newRemote = True
        else:
            # no files locally so safe to try and clone from remote
            self.cloneRepo(infoStream=infoStream)
            # TODO: add the further case where there are remote AND local files!

    def firstPush(self, infoStream):
        git.push(self.repo, self.remoteWithToken, 'master',
                 errstream=infoStream, outstream=infoStream)

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
        if not self.localRoot:
            raise AttributeError("Cannot fetch a PavloviaProject until we have "
                                 "chosen a local folder.")
        if infoStream:
            infoStream.SetValue("Cloning from remote...")
        repo = git.clone(
                source=self.remoteWithToken,
                target=self.localRoot,
                outstream=infoStream,
                errstream=infoStream,
        )
        config = repo.get_config()
        config.set(('remote','origin'), 'url', self.remoteHTTPS)
        config.write_to_path()
        self._lastKnownSync = time.time()
        self.repo = repo
        self._newRemote = False

    def configGitLocal(self):
        """Set the local repo to have the correct name and email for user

        Returns
        -------
        None
        """
        session = getCurrentSession()

        config = self.repo.get_config()

        # write any user entries that don't exist
        needSave = False
        try:
            email = config.get(('user',), 'email')
        except KeyError:
            config.set(('user',),'email', session.user.email)
            needSave = True
        try:
            name = config.get(('user',), 'name')
        except KeyError:
            config.set(('user',),'name', session.user.name)
            needSave = True
        if needSave:
            config.write_to_path()

    def forkTo(self, groupName=None, projectName=None):
        """forks this project to a new namespace and (potentially) project name"""
        newProjInfo = {}
        # if projectName:
        #    newProjInfo['name'] = projectName
        # if groupName:
        #     newProjInfo['namespace'] = groupName
        # make the fork
        fork = self.pavlovia.forks.create(newProjInfo)

        id = fork.id
        pavSession = refreshSession()
        proj = pavSession.getProject(id)
        return proj

    def getChanges(self):
        """Find all the not-yet-committed changes in the repository"""
        changeDict = {}

        # annoyingly in dulwich.status we get the type of file for changes once
        # staged but not for changes to be staged (those are just a flat list
        # irrespective of whether they're add/remove/modify)
        status = git.status(self.repo)
        # now to work out the type of change we need to stage the changes
        self.repo.stage(status.unstaged)

        # print(status.staged)
        # print(status.unstaged)
        # print(status.untracked)

        changeDict['untracked'] = status.staged['add']
        changeDict['changed'] = status.staged['modify']
        changeDict['deleted'] = status.staged['delete']
        changeList = []
        for categ in changeDict:
            changeList.extend(changeDict[categ])
        return changeDict, changeList

    def stageFiles(self, files=None):
        """Adds changed files to the stage (index) ready for commit.

        The files is a list and can include new/changed/deleted

        If files=None this is like `git add -u` (all files added/deleted)
        """
        if files:
            if type(files) not in (list, tuple):
                raise TypeError(
                        'The `files` provided to PavloviaProject.stageFiles '
                        'should be a list not a {}'.format(type(files)))
            git.add(self.repo, files)  # or could be self.repo.stage(files)
        else:
            diffsDict, diffsList = self.getChanges()
            if diffsDict['untracked']:
                git.add(self.repo, diffsDict['untracked'])
            if diffsDict['deleted']:
                git.add(self.repo, diffsDict['deleted'])
            if diffsDict['changed']:
                git.add(self.repo, diffsDict['changed'])

    def getStagedFiles(self):
        """Retrieves the files that are already staged ready for commit"""
        return git.status(self.repo).staged

    def unstageFiles(self, files):
        """Removes changed files from the stage (index) preventing their commit.
        The files in question can be new/changed/deleted
        """
        git.remove(self.repo, files)

    def commit(self, message):
        """Commits the staged changes"""
        git.commit(self.repo, message)
        time.sleep(0.1)
        # then get a new copy of the repo
        self.repo = dulwich.repo.Repo(self.localRoot)

    def save(self):
        """Saves the metadata to gitlab.pavlovia.org"""
        self.pavlovia.save()
        # note that saving info locally about known projects is done
        # by the knownProjects DictStorage class

    @property
    def pavloviaStatus(self):
        return self.__dict__['pavloviaStatus']

    @pavloviaStatus.setter
    def pavloviaStatus(self, newStatus):
        url = 'https://pavlovia.org/server?command=update_project'
        data = {'projectId': self.idNumber, 'projectStatus': 'ACTIVATED'}
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
    try:
        return dulwich.repo.Repo.discover(p).path
    except dulwich.errors.NotGitRepository:
        return None


def getProject(filename):
    """Will try to find (locally synced) pavlovia Project for the filename
    """

    gitRoot = getGitRoot(filename)
    if gitRoot in knownProjects:
        return knownProjects[gitRoot]
    elif gitRoot:
        # Existing repo but not in our knownProjects. Investigate
        logging.info("Investigating repo at {}".format(gitRoot))
        localRepo = git.Repo(gitRoot)
        proj = None
        config = localRepo.get_config()
        for sectionType in config:
            if sectionType[0] == 'remote':
                url = config.get(sectionType, 'url')
                if "gitlab.pavlovia.org/" in url:
                    namespaceName = url.split('gitlab.pavlovia.org/')[1]
                    namespaceName = namespaceName.replace('.git', '')
                    pavSession = getCurrentSession()
                    if pavSession.user:
                        proj = pavSession.getProject(namespaceName,
                                                     repo=localRepo)
                        if proj.pavlovia == 0:
                            logging.warning(
                                    _translate(
                                        "We found a repository pointing to {} "
                                        "but ") +
                                    _translate("no project was found there ("
                                               "deleted?)")
                                    .format(url))

                    else:
                        logging.warning(
                                _translate(
                                    "We found a repository pointing to {} "
                                    "but ") +
                                _translate(
                                    "no user is logged in for us to check "
                                    "it")
                                .format(url))
                    return proj
        if proj == None:
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


class NoUserError(Exception):
    pass


class ConnectionError(Exception):
    pass


class NoGitError(Exception):
    pass
