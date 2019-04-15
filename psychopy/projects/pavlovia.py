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
import subprocess
import traceback
from pkg_resources import parse_version

from psychopy import logging, prefs, constants, exceptions
from psychopy.tools.filetools import DictStorage, KnownProjects
from psychopy import app
from psychopy.localization import _translate

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
        raise exceptions.ConnectionError("Failed to connect to Pavlovia.org. No network?")
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
        # sshIdPath = os.path.join(prefs.paths['userPrefsDir'],
        #                          "ssh", self.username)
        # if os.path.isfile(sshIdPath):
        #     self.publicSSH = sshkeys.getPublicKey(sshIdPath + ".pub")
        # else:
        #     self.publicSSH = sshkeys.saveKeyPair(sshIdPath,
        #                                          comment=gitlabData.email)
        # # convert bytes to unicode if needed
        # if type(self.publicSSH) == bytes:
        #     self.publicSSH = self.publicSSH.decode('utf-8')
        # push that key to gitlab.pavlovia if possible/needed
        # if gitlabData:
        #     keys = gitlabData.keys.list()
        #     keyName = '{}@{}'.format(
        #             self.username, socket.gethostname().strip(".local"))
        #     remoteKey = None
        #     for thisKey in keys:
        #         if thisKey.title == keyName:
        #             remoteKey = thisKey
        #             break
        #     if not remoteKey:
        #         remoteKey = gitlabData.keys.create({'title': keyName,
        #                                             'key': self.publicSSH})
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
            if proj.id not in projIDs and proj.id not in projs:
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
            if parse_version(gitlab.__version__) > parse_version("1.4"):
                self.gitlab = gitlab.Gitlab(rootURL, oauth_token=token, timeout=2, per_page=100)
            else:
                self.gitlab = gitlab.Gitlab(rootURL, oauth_token=token, timeout=2)
            self.gitlab.auth()
            self.username = self.user.username
            self.userID = self.user.id  # populate when token property is set
            self.userFullName = self.user.name
            self.authenticated = True
        else:
            if parse_version(gitlab.__version__) > parse_version("1.4"):
                self.gitlab = gitlab.Gitlab(rootURL, timeout=1, per_page=100)
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
            self.localRoot = repo.working_dir
            self.configGitLocal()
        else:
            self.localRoot = localRoot  # which is probably ''

        # todo: we weren't given a url, but maybe we can deduce one?
        # if self.localRoot and not self.pavlovia:


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
        """The remote for git sync using an oauth token (always as a bytes obj)
        """
        currentSession = getCurrentSession()
        rawHTTPS = self['remoteHTTPS']
        if rawHTTPS:
            remote = rawHTTPS.replace('https://gitlab.pavlovia.org/',
                                      'https://oauth2:{}@gitlab.pavlovia.org/'
                                      .format(currentSession.token))
        else:
            remote = None
        # if remote and type(remote) != bytes:
        #     remote = remote.encode('utf-8')
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
            self.firstPush(infoStream=infoStream)
        else:
            status = self.pull(infoStream=infoStream)
            if status == MISSING_REMOTE:
                return -1
            # for gitpython we need to keep getting fresh copies!
            self.repo = git.Repo(self.localRoot)
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
            info = self.repo.git.pull(self.remoteWithToken, 'master')
            infoStream.write("\n{}".format(info))
        except git.exc.GitCommandError as e:
            if ("The project you were looking for could not be found" in
                    traceback.format_exc()):
                    # pointing to a project at pavlovia but it doesn't exist
                    logging.warning("Project not found on gitlab.pavlovia.org")
                    return MISSING_REMOTE
            else:
                raise e

        logging.debug('pull complete: {}'.format(self.remoteHTTPS))
        if infoStream:
            infoStream.write("\ndone")
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
            infoStream.write("\nPushing changes from remote...")
        try:
            info = self.repo.git.push(self.remoteWithToken, 'master')
            infoStream.write("\n{}".format(info))
        except git.exc.GitCommandError as e:
            if ("The project you were looking for could not be found" in
                    traceback.format_exc()):
                    # pointing to a project at pavlovia but it doesn't exist
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

        # refresh our representation of the local
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
        # also refresh our representation of the remote
        if self.pavlovia and forceRefresh:
            self.pavlovia = getCurrentSession().gitlab.projects.get(self.id)

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
        # glob doesn't match hidden files by default so search for them
        localFiles.extend(glob.glob(os.path.join(self.localRoot, ".*")))

        # there's no project at all so create one
        if not self.localRoot:
            raise AttributeError("Cannot fetch a PavloviaProject until we have "
                                 "chosen a local folder.")
        if not os.path.exists(self.localRoot):
            os.mkdirs(self.localRoot)

        # check if the remote repo is empty (if so then to init/push)
        if self.pavlovia:
            try:
                self.pavlovia.repository_tree()
                bareRemote = False
            except gitlab.GitlabGetError as e:
                if "Tree Not Found" in str(e):
                    bareRemote = True
                else:
                    bareRemote = False

        # if remote is new (or existed but is bare) then init and push
        if localFiles and (self._newRemote or bareRemote):  # existing folder
            self.repo = git.Repo.init(self.localRoot)
            self.configGitLocal()  # sets user.email and user.name
            # add origin remote and master branch (but no push)
            self.repo.create_remote('origin', url=self['remoteHTTPS'])
            self.repo.git.checkout(b="master")
            self.writeGitIgnore()
            self.stageFiles(['.gitignore'])
            self.commit('Create repository (including .gitignore)')
            self._newRemote = True
        else:
            # no files locally so safe to try and clone from remote
            self.cloneRepo(infoStream=infoStream)
            # TODO: add the further case where there are remote AND local files!

    def firstPush(self, infoStream):
        if infoStream:
            infoStream.write("\nPushing to Pavlovia for the first time...")
        info = self.repo.git.push('-u', self.remoteWithToken, 'master')
        if infoStream:
            infoStream.write("\n{}".format(info))
            infoStream.write("\nSuccess!".format(info))

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
        self.repo = git.Repo.clone_from(
                self.remoteWithToken,
                self.localRoot,
        )
        # now change the remote to be the standard (without password token)
        self.repo.remotes.origin.set_url(self.remoteHTTPS)

        self._lastKnownSync = time.time()
        self._newRemote = False

    def configGitLocal(self):
        """Set the local repo to have the correct name and email for user

        Returns
        -------
        None
        """
        session = getCurrentSession()
        localConfig = self.repo.git.config(l=True, local=True)  # list local
        if session.user.email in localConfig:
                return  # we already have it set up so can return
        # set the local config
        with self.repo.config_writer() as config:
            config.set_value("user", "email", session.user.email)
            config.set_value("user", "name", session.user.name)

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
            else:
                raise ValueError("Found an unexpected change_type '{}' in gitpython Diff".format(this.change_type))
        changeList = []
        for categ in changeDict:
            changeList.extend(changeDict[categ])
        return changeDict, changeList

    def stageFiles(self, files=None, infoStream=None):
        """Adds changed files to the stage (index) ready for commit.

        The files is a list and can include new/changed/deleted

        If files=None this is like `git add -u` (all files added/deleted)
        """
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
        self.repo.git.commit('-m', message)
        time.sleep(0.1)
        # then get a new copy of the repo
        self.repo = git.Repo(self.localRoot)

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
    if not haveGit:
        raise exceptions.DependencyError(
                "gitpython and a git installation required for getGitRoot()")

    if not os.path.isdir(p):
        p = [os.path.split(p)[0]
             if len(os.path.split(p)[0]) > 0
             else None].pop()
    if subprocess.call(["git", "branch"],
                       stderr=subprocess.STDOUT, stdout=open(os.devnull, 'w'),
                       cwd=p) != 0:
        return None
    else:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                      cwd=p)
        return out.strip().decode('utf-8')

def getProject(filename):
    """Will try to find (locally synced) pavlovia Project for the filename
    """
    if not haveGit:
        raise exceptions.DependencyError(
                "gitpython and a git installation required for getProject()")

    gitRoot = getGitRoot(filename)
    if gitRoot in knownProjects:
        return knownProjects[gitRoot]
    elif gitRoot:
        # Existing repo but not in our knownProjects. Investigate
        logging.info("Investigating repo at {}".format(gitRoot))
        localRepo = git.Repo(gitRoot)
        proj = None
        for remote in localRepo.remotes:
            for url in remote.urls:
                if "gitlab.pavlovia.org/" in url:
                    namespaceName = url.split('gitlab.pavlovia.org/')[1]
                    namespaceName = namespaceName.replace('.git', '')
                    pavSession = getCurrentSession()
                    if not pavSession.user:
                        nameSpace = namespaceName.split('/')[0]
                        if nameSpace in knownUsers:  # Log in if user is known
                            login(nameSpace, rememberMe=True)
                        else:  # Check whether project repo is found in any of the known users accounts
                            for user in knownUsers:
                                try:
                                    login(user)
                                except requests.exceptions.ConnectionError:
                                    break
                                foundProject = False
                                for repo in pavSession.findUserProjects():
                                    if namespaceName in repo['id']:
                                        foundProject = True
                                        logging.info("Logging in as {}".format(user))
                                        break
                                if not foundProject:
                                    logging.warning("Could not find {namespace} in your Pavlovia accounts. "
                                                    "Logging in as {user}.".format(namespace=namespaceName,
                                                                                   user=user))
                    if pavSession.user:
                        proj = pavSession.getProject(namespaceName,
                                                     repo=localRepo)
                        if proj.pavlovia == 0:
                            logging.warning(_translate("We found a repository pointing to {} "
                                                       "but no project was found there (deleted?)").format(url))
                    else:
                        logging.warning(_translate("We found a repository pointing to {} "
                                                   "but no user is logged in for us to check it".format(url)))
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

