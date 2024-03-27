from .versionchooser import *
from psychopy import logging
import warnings
from .versionchooser import psychopyVersion
from psychopy.localization import _translate


class DeprecationError(DeprecationWarning):
    pass


class Deprecated:
    # owner starts off as None until assigned
    owner = None

    def __init__(self, fcn, deprecation, removal=None, replacement=None):
        self.fcn = fcn
        self.deprecation = deprecation
        self.removal = removal
        self.replacement = replacement

    @property
    def removed(self):
        """
        Function is considered removed if its removal version is before or the same as the
        current version. If it has no removal version, then it isn't removed.
        """
        # if no removal version, not removed
        if self.removal is None:
            return False
        # return True if removal version is before or the same as current
        return Version(self.removal) <= psychopyVersion

    @property
    def deprecated(self):
        """
        Function is considered deprecated if its deprecation version is before or the same as the
        current version.
        """
        # return True if deprecation version is before or the same as current
        return Version(self.deprecation) <= psychopyVersion

    def makeMessage(self):
        """
        Create message for errors/warnings about this function.

        Returns
        -------
        str
            Constructed message
        """
        # root of the message
        msg = _translate(
            "%s.%s is deprecated as of version %s"
        ) % (self.fcn.__module__, self.fcn.__name__, self.deprecation)
        # additional statement about removal
        if self.removal is not None:
            # adjust tense according to future/past
            if self.removed:
                tense = _translate(" and was")
            else:
                tense = _translate(" and will be")
            msg += _translate(
                "%s removed in version %s"
            ) % (tense, self.removal)
        # end of first sentence
        msg += "."
        # additional statement about replacement
        if self.replacement is not None:
            msg += _translate(
                " Please use %s.%s instead."
            ) % (self.replacement.__module__, self.replacement.__name__)

        return msg

    def __call__(self, *args, **kwargs):
        """
        When a deprecated function is called, it either prints a warning (if depracated) or
        raises an error (if outright removed).
        """
        # if method should be removed, don't call at all - raise an error
        if self.removed:
            raise DeprecationError(
                self.makeMessage()
            )
        # if method is deprecated, log a warning
        if self.deprecated:
            warnings.warn(
                self.makeMessage(), DeprecationWarning
            )
            logging.warn(
                self.makeMessage()
            )
        # run
        if self.owner is None:
            self.fcn(*args, **kwargs)
        else:
            self.fcn(self.owner, *args, **kwargs)

    def __set_name__(self, owner, name):
        # store reference to owner
        self.owner = owner
        # set as normal
        setattr(owner, name, self)


class _Deprecator:
    def __init__(self, deprecation, removal=None, replacement=None):
        self.deprecation = deprecation
        self.removal = removal
        self.replacement = replacement

    def __call__(self, fcn):
        # make depracated object
        return Deprecated(
            fcn=fcn,
            deprecation=self.deprecation,
            removal=self.removal,
            replacement=self.replacement
        )


def deprecated(deprecation, removal=None, replacement=None):
    return _Deprecator(
        deprecation=deprecation,
        removal=removal,
        replacement=replacement
    )
