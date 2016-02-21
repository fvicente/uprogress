# -*- coding: iso-8859-1 -*-
import os
import sys
import re
from mod_python import psp
from mod_python import apache
from mod_python import util
from mod_python.Session import Session

here = os.path.dirname(__file__)
libdir = os.path.abspath(os.path.join(here, '../lib'))
if not libdir in sys.path:
    sys.path.insert(0, libdir)

outdir = os.path.abspath(os.path.join(here, 'temp'))

from simplejson.encoder import JSONEncoder
from simplejson.decoder import JSONDecoder

##
# Decorators

def _session_getter(f):
    """
    Get current session
    You can modify this function to add login validations, etc.
    
    Important note: when this decorator is used the function must use req.session instead of Session(req)
    """
    def _wrapper(req, *args, **kwargs):
        if not hasattr(req, "session"):
            req.session = Session(req, lock=False)
        return f(req, *args, **kwargs)
    return _wrapper

##
# External functions. These can be accessed via URL's from
# outside.

def index(req):
    session = Session(req, lock=False)
    # output directory for uploaded files used in _upload_limit.py
    session.lock()
    session['outdir'] = outdir
    session.save()
    session.unlock()
    return psp.PSP(req, 'test.html', vars={})

@_session_getter
def upload_file(req, **kargs):
    return { 'code': 0, 'desc': 'success' }

@_session_getter
def get_upload_progress(req, files, **kargs):
    ret = {}
    files = JSONDecoder("UTF-8").decode(files)
    session = req.session
    session.lock()
    for (slot, upfile) in files.iteritems():
        upfile = os.path.split(upfile)[1]
        if session.get('temp_name_' + upfile):
            cursize = 0
            try:
                cursize = os.path.getsize(session['temp_name_' + upfile])
            except:
                pass
            ret[slot] = (cursize * 100) / (session.get('temp_size_' + upfile) or 1)
    session.unlock()
    req.content_type = 'application/json; charset=UTF-8'
    return JSONEncoder("UTF-8").encode(ret)

### The End ###
