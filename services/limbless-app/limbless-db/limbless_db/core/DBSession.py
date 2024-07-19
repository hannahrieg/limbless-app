from sqlalchemy.exc import IllegalStateChangeError

from .DBHandler import DBHandler


class DBSession():
    def __init__(self, db_handler: DBHandler, commit: bool = True):
        self.db_handler = db_handler
        self.commit = commit

    def __enter__(self):
        self.db_handler.open_session()
        print(self.db_handler._engine.pool.status(), flush=True)
        return self.db_handler

    def __exit__(self, *_):
        try:
            self.db_handler.close_session()
        except IllegalStateChangeError:
            pass
