class Repository(object):
    def __init__(self, session=None):
        self.session = session
        if self.session:
            self.query = self.session.query
        self.cursor = None

    def set_session(self, session):
        self.session = session
        if session:
            self.query = self.session.query
        return self

    def set_cursor(self, cursor):
        self.cursor = cursor
        return self
