class DomainError(Exception):
    pass


class ClienteNotFound(DomainError):
    pass


class ClienteJaExiste(DomainError):
    pass


class DuplicateEvent(DomainError):
    pass
