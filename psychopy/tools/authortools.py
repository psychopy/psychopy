class Author:
    """
    An easily referenceable author.

    Parameters
    ----------
    surname : str
        Author's surname, e.g. Peirce for Jon Peirce
    forenames : str, list
        Author's forename, e.g. "Jon" for Jon Peirce or ["Todd", "Ethan"] for Todd Ethan Parsons
    prefices : list
        Any prefices before the surname, e.g. ["of"] for Joan of Arc
        github : str
        Author's GitHub username, if they have one. e.g. peircej for Jon Peirce
    email : str
        Author's email address, if they have one. e.g. jon@opensciencetools.org for Jon Peirce
    other : dict
        Any other links or details the author may want included, such as a website link, ORCiD or Twitter username.
    """
    def __init__(
            self,
            forenames, surname, prefices=None,
            github=None, email=None, other=None
    ):
        # store surname
        self.surname = surname.lower().strip()
        # sanitize and store forenames
        forenames = forenames or []
        if isinstance(forenames, str):
            forenames = [forenames]
        self.forenames = [forename.lower().strip() for forename in forenames]
        # sanitize and store prefices
        prefices = prefices or []
        if prefices and isinstance(prefices, str):
            prefices = [prefices]
        self.prefices = [prefix.lower().strip() for prefix in prefices]

        # store basic details
        github = github or ""
        self.github = github.strip()
        email = email or ""
        self.email = email.lower().strip()
        # store other references
        other = other or {}
        self.other = {key: str(val).lower().strip() for key, val in other.items()}

    def __eq__(self, other):
        # comparing to another Author...
        if isinstance(other, self.__class__):
            # if both have a github username, use that
            if self.github and other.github:
                return self.github == other.github
            # if both have an orcid id, use that
            if 'orcid' in self.other:
                return self.other['orcid'] == other.other['orcid']
            # if both have an email, use that
            if self.email and other.email:
                return self.email == other.email
            # otherwise, compare fore and last names
            same = self.surname == other.surname
            for i in range(min(len(self.forenames), len(other.forenames))):
                same = same and self.forenames[i] == other.forenames[i]
            return same

        # comparing to a string
        if isinstance(other, str):
            # standardise and split
            other = other.lower().replace(".", "").replace(",", "")
            parts = other.split(" ")
            # if string is this Author's orcid, github or email, return True
            if 'orcid' in self.other and self.other['orcid'] in parts:
                return True
            if self.github.lower() in parts:
                return True
            if self.email in parts:
                return True
            # otherwise compare names
            same = parts[-1] == self.surname
            for i in range(min(len(self.forenames), len(parts))):
                isName = parts[i] == self.forenames[i]
                isPrefix = parts[i] in self.prefices
                isInitial = parts[i] == self.forenames[i][0]
                same = same and (isName or isPrefix or isInitial)
            return same

    @property
    def name(self):
        content = ""
        # full capitalized firstname
        content += self.forenames[0].capitalize()
        # initialized middlenames
        if len(self.forenames) > 1:
            content += " "
            content += " ".join([name[0].capitalize() + "." for name in self.forenames[1:]])
        # full lowercase prefices
        if len(self.prefices):
            content += " "
            content += " ".join(self.prefices)
        # full capitalized surname
        content += " "
        content += self.surname.capitalize()

        return content

    def __repr__(self):
        content = f"<Author: {self.name}"
        if self.github:
            content += f", @{self.github}"
        content += ">"

        return content

    def __str__(self):
        # start with name
        content = self.name
        # add details
        if self.github or self.email or self.other:
            other = []
            # github username
            if self.github:
                other.append(f"GitHub: @{self.github}")
            # email
            if self.email:
                other.append(f"Email: {self.email}")
            # other
            for key, val in self.other.items():
                other.append(f"{key}: {val}")
            content += " ("
            content += ", ".join(other)
            content += ")"

        return content
