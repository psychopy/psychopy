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
from .gitignore import gitIgnoreText

rootURL = "https://gitlab.pavlovia.org"
client_id = '4bb79f0356a566cd7b49e3130c714d9140f1d3de4ff27c7583fb34fbfac604e0'
scopes = []
redirect_url = 'https://gitlab.pavlovia.org/'

knownUsers = DictStorage(filename=os.path.join(prefs.paths['userPrefsDir'],
                                               'pavlovia', 'users.json'))

# knownProjects is a dict stored by id ("namespace/name")
knownProjects = DictStorage(filename=os.path.join(prefs.paths['userPrefsDir'],
                                                  'pavlovia', 'projects.json'))
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
    logging.debug('pavloviaTokensCurrently: {}'.format(knownUsers))
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
                      localRoot=''):
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

        # TODO: add avatar option?
        # TODO: add namespace option?
        gitlabProj = self.gitlab.projects.create(projDict)
        pavProject = PavloviaProject(gitlabProj, localRoot=localRoot)
        return pavProject

    def getProject(self, id):
        """Gets a Pavlovia project from an ID number or namespace/name

        Parameters
        ----------
        id a numerical

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

    .pavlovia will point to a gitlab project on gitlab.pavlovia.org
    .repo will will be a gitpython repo
    .id is the namespace/name (e.g. peircej/stroop)
    .idNumber is gitlab numeric id
    .title
    .tags
    .owner is technically the namespace. Get the owner from .attributes['owner']
    .localRoot is the path to the local root
    """

    def __init__(self, proj, localRoot=''):
        dict.__init__(self)
        self._storedAttribs = {}  # these will go into knownProjects file
        self['id'] = ''
        self['localRoot'] = ''
        self['remoteSSH'] = ''
        self['remoteHTTPS'] = ''
        self._lastKnownSync = 0
        self._newRemote = False  # False can also indicate 'unknown'
        if isinstance(proj, gitlab.v4.objects.Project):
            self.pavlovia = proj
        else:
            self.pavlovia = currentSession.gitlab.projects.get(proj)
        self.repo = None  # update with getRepo()
        self.localRoot = localRoot

    def __getattr__(self, name):
        if name == 'owner':
            return
        proj = self.__dict__['pavlovia']
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
        self['localRoot'] = localRoot
        # this is where we add a project to knownProjects:
        if localRoot:  # i.e. not set to None or ''
            knownProjects[self.id] = self

    @property
    def id(self):
        if 'id' in self.pavlovia.attributes:
            return self.pavlovia.attributes['path_with_namespace']

    @property
    def idNumber(self):
        return self.pavlovia.attributes['id']

    @property
    def owner(self):
        return self.pavlovia.attributes['namespace']['name']

    @property
    def attributes(self):
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
            if time.time() < self._lastKnownSync + 2:
                return 1
        # pull first then push
        t0 = time.time()
        if self.emptyRemote:  # we don't have a repo there yet to do a 1st push
            self.firstPush()
        else:
            self.pull(syncPanel=syncPanel, progressHandler=progressHandler)
            self.push(syncPanel=syncPanel, progressHandler=progressHandler)
        self._lastKnownSync = t1 = time.time()
        msg = ("Successful sync at: {}, took {:.3f}s"
               .format(time.strftime("%H:%M:%S", time.localtime()), t1 - t0))
        logging.info(msg)
        if syncPanel:
            syncPanel.setStatus(msg)
            time.sleep(0.5)

    def pull(self, syncPanel=None, progressHandler=None):
        """Pull from remote to local copy of the repository

        Parameters
        ----------
        syncPanel
        progressHandler

        Returns
        -------

        """
        if syncPanel:
            syncPanel.setStatus("Pulling changes from remote...")
        origin = self.repo.remotes.origin
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
        origin = self.repo.remotes.origin
        origin.push(progress=progressHandler)

    def getRepo(self, syncPanel=None, progressHandler=None, forceRefresh=False,
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
            self.newRepo(progressHandler)
        elif gitRoot != self.localRoot:
            # this indicates that the requested root is inside another repo
            raise AttributeError("The requested local path for project\n\t{}\n"
                                 "sits inside another folder, which git will "
                                 "not permit. You might like to set the "
                                 "project local folder to be \n\t{}"
                                 .format(repr(self.localRoot), repr(gitRoot)))
        else:
            repo = git.Repo(gitRoot)
        self.repo = repo
        self.writeGitIgnore()

    def writeGitIgnore(self):
        """Check that a .gitignore file exists and add it if not"""
        gitIgnorePath = os.path.join(self.localRoot, '.gitignore')
        if not os.path.exists(gitIgnorePath):
            with open(gitIgnorePath, 'w') as f:
                f.write(gitIgnoreText)

    def newRepo(self, progressHandler=None):
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
        if localFiles and self._newRemote:  # existing folder
            self.repo = git.Repo.init(self.localRoot)
            # add origin remote and master branch (but no push)
            self.repo.create_remote('origin', url=self['remoteHTTPS'])
            self.repo.git.checkout(b="master")
            self.writeGitIgnore()
            self.stageFiles(['.gitignore'])
            self.commit(['Create repository (including .gitignore)'])
            self._newRemote = True
        else:
            # no files locally so safe to try and clone from remote
            self.cloneRepo(progressHandler)
            # TODO: add the further case where there are remote AND local files!

    def firstPush(self):
        self.repo.git.push('-u', 'origin', 'master')

    def cloneRepo(self, progressHandler=None):
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
        if not self.localRoot:
            raise AttributeError("Cannot fetch a PavloviaProject until we have "
                                 "chosen a local folder.")
        if progressHandler:
            progressHandler.setStatus("Cloning from remote...")
            progressHandler.syncPanel.Refresh()
            progressHandler.syncPanel.Layout()
        repo = git.Repo.clone_from(
            self.remoteHTTPS,
            self.localRoot,
            progress=progressHandler)
        self._lastKnownSync = time.time()
        self.repo = repo
        self._newRemote = False

    def forkTo(self, username=None):
        if username:
            # fork to a specific namespace
            fork = self.pavlovia.forks.create({'namespace': 'myteam'})
        else:
            fork = self.pavlovia.forks.create({})  # uses the current logged-in user
        return fork

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
                raise (
                    "Found an unexpected change_type '{}' in gitpython Diff"
                    .format(this.change_type))
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
            self.repo.git.add(files)
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

    def save(self):
        """Saves the metadata to gitlab.pavlovia.org"""
        self.pavlovia.save()


def getGitRoot(p):
    """Return None or the root path of the repository"""
    if not os.path.isdir(p):
        p = os.path.split(p)[0]
    if subprocess.call(["git", "branch"],
                       stderr=subprocess.STDOUT, stdout=open(os.devnull, 'w'),
                       cwd=p) != 0:
        return None
    else:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"],
                                      cwd=p)
        return out.strip().decode('utf-8')


def getProject(filename):
    """Will try to find (locally synced) pavlovia Project for the filename"""
    gitRoot = getGitRoot(filename)
    if gitRoot in knownProjects:
        return knownProjects[gitRoot]
    elif gitRoot:
        # Existing repo but not in our knownProjects. Investigate
        logging.info("Investigating repo at {}".format(gitRoot))
        localRepo = git.Repo(gitRoot)
        for remote in localRepo.remotes:
            for url in remote.urls:
                if "gitlab.pavlovia.org/" in url:
                    namespaceName = url.split('gitlab.pavlovia.org/')[1]
                    namespaceName = namespaceName.replace('.git', '')
                    try:
                        proj = currentSession.getProject(namespaceName)
                    except gitlab.exceptions.GitlabGetError as e:
                        if "404 Project Not Found" in e.error_message:
                            continue
                    proj.localRoot = gitRoot
                    return proj
        # if we got here then we have a local git repo but not a
        # TODO: we have a git repo, but not on gitlab.pavlovia
        # Could help user that we add a remote called pavlovia but for now
        # just print a message!
        print("We found a git repository at {} but it doesn't point to "
              "gitlab.pavlovia.org. You could create that as a remote to "
              "sync from PsychoPy.")


# create an instance of that
currentSession = PavloviaSession()
