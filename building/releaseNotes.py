import requests
import re
from pathlib import Path
import json
from datetime import datetime
from copy import deepcopy
import argparse
import os


# make sure we have a folder to store the output in
outputDir = Path(__file__).parent / ".outputs"
outputDir.mkdir(parents=True, exist_ok=True)
# setup file to cache responses from GitHub
cachefile = outputDir / "_release_notes_cache.json"
# load cache if there is one
if cachefile.is_file():
    cache = json.loads(
        cachefile.read_text()
    )
else:
    cache = {}

# parse call args
argparser = argparse.ArgumentParser(
    prog="PsychoPy release notes generator",
    description="Run this script to generate a first draft of release notes from PR's since the last release"
)
argparser.add_argument(
    "--filter",
    help="Filter for a target branch",
    choices=[
        "dev",
        "release"
    ],
    default=None
)
argparser.add_argument(
    "--token",
    help=(
        "GitHub personal access token, used to avoid rate limiting. If not given, will use the "
        "GITHUB_TOKEN environment variable (if set)"
    ),
    default=os.environ.get("GITHUB_TOKEN", None)
)
args = argparser.parse_args()
# setup headers for requests (authenticating if we have a token)
headers = {}
if args.token:
    headers['Authorization'] = f"Bearer {args.token}"

def cacheget(url):
    """
    Like requests.get, but caches the result to avoid hitting GitHub's rate limiting

    Parameters
    ----------
    url : str
        URL to request
    """
    # if cached, use cache
    if url in cache:
        return deepcopy(cache[url])
    # print request
    print("REQUEST", url)
    # make request
    resp = requests.get(url, headers=headers).json()
    # rate limit?
    if resp.get("status", None) == "422" or "API rate limit exceeded" in resp.get("message", ""):
        raise ConnectionError(
            "You've hit GitHub API's rate limit, try again in about an hour"
        )
    # cache result
    cache[url] = resp
    # save
    cachefile.write_text(
        json.dumps(cache, indent=4)
    )

    return deepcopy(resp)


# choose repos
repos = {
    'psychopy/psychopy': "PsychoPy",
    'psychopy/psychopy-studio': "PsychoPy Studio",
    'psychopy/psychopy-app': "PsychoPy Standalone",
    'psychopy/psychopy-docs': "Documentation"
}
# dict to store prs in
prs = {
    'Improvements': { name: [] for name in repos },
    'Fixes': { name: [] for name in repos },
    'Breaking Changes': { name: [] for name in repos },
    'Documentation': { name: [] for name in repos },
    'Other': { name: [] for name in repos },
}
# map commit tags to release notes categories
categories = {
    # conventional commits
    'fix': "Fixes",
    'refactor': "Breaking Changes",
    'feat': "Improvements",
    'docs': "Documentation",
    'test': None,
    'chore': None,
    # legacy
    'RF': "Breaking Changes",
    'NF': "Improvements",
    'ENH': "Improvements",
    'BF': "Fixes",
    'FF': None,
    'DOC': None,
    'DOCS': None,
    'TEST': None,
    'TESTS': None,
    'SYS': None,
    'PKG': None,
}
# get last release
last = cacheget(
    "https://api.github.com/repos/psychopy/psychopy/releases/latest"
)
# for each repo...
for repo in repos:
    # for handling pagination...
    page = 1
    items = []
    total = 30
    # if total results >30, get subsequent pages
    while len(items) < total:
        # get PRs since last release
        resp = cacheget(
            f"https://api.github.com/search/issues?q=repo:{repo} is:pr merged:>{last['published_at'].replace(' ', 'T')}&page={page}"
        )
        # add to items
        items += resp['items']
        # update pagination details
        total = int(resp['total_count'])
        page += 1
    # iterate through PRs
    for pr in items:
        # ignore PRs from bots
        if pr['user']['type'] == "Bot":
            continue
        # parse title according to conventional commits spec
        pr['parts'] = re.match(
            pattern=r"^(?:(?P<tag>\w+)(?:\((?P<scope>[\w-]+)\))?(?P<breaking>!)?:\s*)?(?P<message>.+)$",
            string=pr['title']
        )
        # skip anything with regression scope
        if pr['parts'].group("scope") == "reg":
            continue
        # skip anything whose categ is hidden (e.g. sys admin stuff)
        if pr['parts'].group("tag") and categories.get(pr['parts'].group("tag"), None) is None:
            continue
        # if filtering for a specific target branch, get PR details
        if args.filter is not None:
            resp = cacheget(pr['pull_request']['url'])
            # if PR wasn't to target branch, ignore it
            if not resp['base']['ref'] == args.filter:
                continue
        # sort into appropriate category
        if pr['parts'].group("breaking"):
            # breaking change takes priority
            prs['Breaking Changes'][repo].append(pr)
        elif repo == "psychopy/psychopy-docs":
            # all PRs to psychopy-docs are Documentation
            prs["Documentation"][repo].append(pr)
        elif pr['parts'].group("tag") not in categories:
            # grab any with unrecognised tags
            prs["Other"][repo].append(pr)
        else:
            # anything else goes by category as normal
            prs[
                categories[pr['parts'].group("tag")]
            ][repo].append(pr)
# construct notes
notes = ""
# for each category...
for categ in prs:
    # skip docs
    if categ == "Documentation":
        continue
    # skip if there's no entries
    if all(len(prs[categ][repo]) == 0 for repo in prs[categ]):
        continue
    # category title
    notes += (
        f"## {categ}\n"
        f"\n"
    )
    for repo in repos:
        # skip if there's no PRs
        if not len(prs[categ][repo]):
            continue
        # add repo title
        notes += (
            f"### {repos[repo]}\n"
            f"\n"
        )
        # add PRs
        for pr in prs[categ][repo]:
            # write
            notes += (
                f"* {pr['parts'].group("message")} by {pr['user']['login']} in {repo}#{pr['number']}\n"
            )
        # add a newline after PRs
        notes += "\n"

# get first contribs
authors = {}
for categ in prs:
    for repo in repos:
        # skip docs
        if categ == "Documentation":
            continue
        # for each PR...
        for pr in prs[categ][repo]:
            # make sure there's an entry for this author
            if pr['user']['login'] not in authors:
                authors[pr['user']['login']] = {}
            # if already stored, get previous
            prev = authors[pr['user']['login']].get(repo, None)
            # datetime-ify timestamp so we can compare dates
            pr['closed_at'] = datetime.strptime(pr['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
            # if no previous, or newer previous, store this pr
            if prev is None or pr['closed_at'] < prev['closed_at']:
                authors[pr['user']['login']][repo] = pr
# add first contribs
notes += (
    "## New contributors\n"
    "\n"
)
for name, authprs in authors.items():
    for repo, pr in authprs.items():
        # check that first contrib is author's first contrib
        resp = cacheget(
            f"https://api.github.com/search/issues?q=repo:{repo} is:pr is:merged sort:created-asc author:{name}"
        )
        if not resp['items'][0]['number'] == pr['number']:
            continue
        # add
        notes += (
            f"* @{name} in {repo}#{pr['number']}\n"
        )
# add newline after new contribs
notes += "\n"

# get documentation authors
docs = set()
for repo in prs['Documentation']:
    for pr in prs['Documentation'][repo]:
        docs.add(
            f"@{pr['user']['login']}"
        )
# add documentation
notes += (
    f"## Documentation\n"
    f"\n"
    f"Contributions from: {', '.join(docs)}\n"
    f"\n"
)

# save
file = outputDir / "release_notes.md"
file.write_text(
    notes
)