class BadRequest(Exception):
    def __init__(self, message):
        super().__init__(message)

class Unauthorized(Exception):
    def __init__(self, message):
        super().__init__(message)

class Forbidden(Exception):
    def __init__(self, message):
        super().__init__(message)

class NotFound(Exception):
    def __init__(self, message):
        super().__init__(message)

class InternalServerError(Exception):
    def __init__(self, message):
        super().__init__(message)
