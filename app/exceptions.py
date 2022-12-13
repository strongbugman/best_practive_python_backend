class BaseException(Exception):
    http_status_code = 500

    def __init__(self, *args: object, http_status_code: int = 0) -> None:
        if http_status_code:
            self.http_status_code = http_status_code

        super().__init__(*args)


class ServerException(BaseException):
    http_status_code = 500


class ClientException(BaseException):
    http_status_code = 400


class RequestWrongException(ClientException):
    pass


class ForbiddenException(ClientException):
    http_status_code = 403
    pass


class SessionExpireException(ClientException):
    http_status_code = 401


class NotFound(ClientException):
    http_status_code = 404
