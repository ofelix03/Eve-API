class PasswordMismatch(Exception):
    pass


class PasswordConfirmationMismatch(Exception):
    pass


class UserNotFound(Exception):
    pass

class UsedPasswordBefore(Exception):
    pass