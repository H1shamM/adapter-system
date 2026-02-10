class AdapterError(Exception):
    """ Base adapter error"""

class AuthenticationError(AdapterError):
    pass

class FetchError(AdapterError):
    pass

class NormalizationError(AdapterError):
    pass