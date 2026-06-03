import requests
import re
from pathlib import Path
import json

# setup file to cache responses from GitHub
cachefile = Path(__file__).parent / "_release_notes_cache.json"
# load cache if there is one
if cachefile.is_file():
    cache = json.loads(
        cachefile.read_text()
    )
else:
    cache = {}


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
        return cache[url]
    # print request
    print("REQUEST", url)
    # make request
    resp = requests.get(url).json()
    # rate limit?
    if resp.get("status", None) == "422":
        raise ConnectionError(
            "You've hit GitHub API's rate limit, try again in about an hour"
        )
    # cache result
    cache[url] = resp
    # save
    cachefile.write_text(
        json.dumps(cache, indent=4)
    )

    return resp


# choose repos
repos = {
    'psychopy/psychopy': "PsychoPy",
    'psychopy/psychopjs': "PsychoJS",
    'psychopy/psychopy-studio': "PsychoPy Studio",
    'psychopy/psychopy-app': "PsychoPy Standalone",
    'psychopy/psychopy-docs': "Documentation"
}
# dict to store prs in
prs = {
    'Highlights': { name: [] for name in repos },
    'Improvements': { name: [] for name in repos },
    'Fixes': { name: [] for name in repos },
    'Breaking Changes': { name: [] for name in repos },
    'Other': { name: [] for name in repos },
}
# get last release
last = cacheget(
    "https://api.github.com/repos/psychopy/psychopy/releases/latest"
)
# for each repo...
for repo in repos:
    # get PRs since last release
    resp = cacheget(
        f"https://api.github.com/search/issues?q=repo:{repo} is:pr merged:>{last['published_at'].replace(' ', 'T')}"
    )
    
    # iterate through PRs
    for pr in resp['items']:
        # sort PR titles
        if pr['title'].startswith("RF:") or re.match(r"^\w*?\!\:", pr['title']):
            prs['Breaking Changes'][repo].append(pr)
        elif pr['title'].startswith("NF:"):
            prs['Highlights'][repo].append(pr)
        elif pr['title'].startswith("ENH:"):
            prs['Improvements'][repo].append(pr)
        elif pr['title'].startswith("BF:"):
            prs['Fixes'][repo].append(pr)
        else:
            prs['Other'][repo].append(pr)

# construct notes
notes = ""
# for each category...
for categ in prs:
    # category title
    notes += (
        f"# {categ}\n"
        f"\n"
    )
    for repo in repos:
        # skip docs
        if repo == "psychopy-docs":
            continue
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
            # remove leading tag
            pr['title'] = re.sub(
                pattern=r"^[\w\!]*?\:\s*?", 
                string=pr['title'],
                repl=""
            )
            # remove trailing spaces
            pr['title'] = pr['title'].strip()
            # write
            notes += (
                f"* {pr['title']} by {pr['user']['login']} in {repo}#{pr['number']}\n"
            )
        # add a newline after PRs
        notes += "\n"

# get documentation authors
docs = set()
for categ in prs:
    for pr in prs[categ]['psychopy-docs']:
        docs.add(
            f"@{pr['user']['login']}"
        )
# add documentation
notes += (
    f"## Documentation\n"
    f"\n"
    f"Contributions from: {', '.join(docs)}"
)

# save
file = Path(__file__) / "release_notes.md"
file.write_text(
    notes
)