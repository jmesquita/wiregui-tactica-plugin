import sys
import functools
#import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

__all__ = ['Session', 'dbsession']

#log = logging.getLogger(__name__)

Session = None
engine = None
_setup = False

def setupDB():
    """Setup the database accordingly"""
    if _setup:
        return
 #   log.debug("Setting up DB engine and session.")
    global Session
    global engine
    global _setup
    _setup = True
    engine = create_engine('mysql+pymysql://root:@192.168.200.2:3306/lateco?charset=utf8', pool_recycle=3600)
    Session = sessionmaker(bind=engine)
    

class dbsession(object):
    '''Decorator. Introduces a new parameter to the method called dbsession
    so that the method has access to the database.
    '''
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        try:
            dbsession = Session()
            kwargs['dbsession'] = dbsession
            return self.func(*args, **kwargs)
        except:
            raise
        finally:
            dbsession.close()
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)

setupDB()