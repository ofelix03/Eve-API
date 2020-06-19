import base64
from datetime import datetime


class BadCursorQuery(Exception):
    pass


class PaginationCursor(object):

    def __init__(self, cursor_before=None, cursor_limit=2, cursor_after=None):
        self.before = cursor_before
        self.after = cursor_after
        self.limit = cursor_limit
        self.has_more = False

    def set_limit(self, cursor_limit):
        self.limit = int(cursor_limit)

    def set_after(self, cursor_after):
        try:
            if isinstance(cursor_after, datetime):
                cursor_after = base64.b64encode(str(cursor_after.timestamp()).encode())
                self.after = cursor_after
            elif isinstance(cursor_after, str):
                self.after = cursor_after
            else:
                self.after = None
        except Exception:
            raise BadCursorQuery()

    def set_before(self, cursor_before):
        try:
            if isinstance(cursor_before, datetime):
                cursor_before = base64.b64encode(str(cursor_before.timestamp()).encode())
                self.before = cursor_before
            elif isinstance(cursor_before, str):
                self.before = cursor_before  # thi is the encoded value coming from the client
            else:
                self.before = None
        except Exception:
            raise BadCursorQuery()
        
    def set_has_more(self, has_more):
        self.has_more = has_more

    def get_after_as_float(self):
        if not self.after:
            return None
        timestamp = float(base64.b64decode(self.after))
        return timestamp

    def get_before_as_float(self):
        if not self.before:
            return None
        timestamp = float(base64.b64decode(self.before))
        return timestamp