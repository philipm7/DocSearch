class DocumentNotFoundError(KeyError):
    pass


class VersionConflictError(RuntimeError):
    pass
