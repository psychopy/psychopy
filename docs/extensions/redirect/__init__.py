from pathlib import Path
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


class RedirectDirective(SphinxDirective):
    """
    Redirect from one page to another.
    """

    has_content = True

    def run(self):
        self.assert_has_content()
        # iterate through lines in content
        for content in self.content:
            # get to and from locations
            from_raw, to_raw = content.split(" > ")
            # add redirect
            add_redirect(
                self.env, 
                from_raw=from_raw, 
                to_raw=to_raw
            )

        return []


class RedirectToDirective(SphinxDirective):
    """
    Redirect from the current page to a given page.
    """
    has_content = True

    def run(self):
        self.assert_has_content()
        # iterate through lines in content
        for content in self.content:
            # add redirect
            add_redirect(
                self.env, 
                from_raw=self.get_source_info()[0], 
                to_raw=content
            )

        return []


class RedirectFromDirective(SphinxDirective):
    """
    Redirect from a given page to the current page.
    """

    has_content = True

    def run(self):
        self.assert_has_content()
        # iterate through lines in content
        for content in self.content:
            # add redirect
            add_redirect(
                self.env, 
                from_raw=content, 
                to_raw=self.get_source_info()[0]
            )

        return []


def add_redirect(env, from_raw, to_raw):
    """
    Add a redirect from one location to another.

    Parameters
    ----------
    env : sphinx.environment.BuildEnvironment
        The current Sphinx build environment
    from_raw : str
        Raw content pointing to the document to redirect from
    to_raw : str
        Raw content pointing to the document to redirect to
    """
    # make sure environment has a value for redirects
    if not hasattr(env, 'redirects'):
        env.redirects = []
    # get document to redirect from
    from_doc = env.path2doc(
        env.relfn2path(from_raw)[0]
    )
    # get url to redirect to
    if to_raw.startswith("https:"):
        # if it's an external url, point to it as is
        to_url = to_raw
    else:
        # otherwise get a relative link
        to_doc = env.path2doc(
            env.relfn2path(to_raw)[0]
        )
        to_url = f"/{to_doc}"
    # append to list of redirects
    env.redirects.append(
        (from_doc, to_url)
    )

    
def create_redirect_pages(app):
    """
    Creates the redirect pages specified in `app.env.redirects` - indended for use as an event 
    callback for the `html-collect-pages` event.
    """
    # make sure environment has a value for redirects
    if not hasattr(app.env, 'redirects'):
        app.env.redirects = []
    # get path of template for a redirect page
    templatename = str((Path(__file__).parent / "redirect.html").absolute())
    # start off with no new pages
    pages = []
    # add a new page for every redirect
    for from_doc, to_url in app.env.redirects:
        # add parameters from given links
        pages.append(
            (from_doc, {'url': to_url}, templatename)
        )
    
    return pages


def setup(app):
    # add directives
    directives.register_directive('redirect', RedirectDirective)
    directives.register_directive('redirect-to', RedirectToDirective)
    directives.register_directive('redirect-from', RedirectFromDirective)
    # connect event callback
    app.connect('html-collect-pages', create_redirect_pages)

    return {
        'version': '0.1',
        'env_version': 1,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }