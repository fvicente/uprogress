#
# _upload_limit.py
#
import os
import urllib
from mod_python import apache
from mod_python.Session import Session
from mod_python import util

UPLOAD_LIMIT = 10 * 1024 * 1024

class Storage(file):
    def __init__(self, directory, advisory_filename):
        self.advisory_filename = advisory_filename
        self.delete_on_close = False
        self.already_deleted = False
        self.real_filename = os.path.join(directory, os.path.split(advisory_filename)[1])
        super(Storage, self).__init__(self.real_filename, 'w+b')
    def close(self):
        if self.already_deleted:
            return
        super(Storage, self).close()
        if self.delete_on_close:
            self.already_deleted = True
            os.remove(self.real_filename)

class StorageFactory:
    def __init__(self, dir):
        self.dir = dir
    def create(self, advisory_filename):
        return Storage(self.dir, advisory_filename)

def fixuphandler(req):
    if req.method == 'POST':
        length = req.headers_in.get('Content-Length')
        if length is None:
            req.status = apache.HTTP_LENGTH_REQUIRED
            req.write("{ 'code': 5, 'desc': 'content length required' }")
            return apache.DONE
        elif int(length) > UPLOAD_LIMIT:
            req.status = apache.HTTP_REQUEST_ENTITY_TOO_LARGE
            req.write("{ 'code': 4, 'desc': 'upload maximum size exceeded' }")
            return apache.DONE
        elif req.uri.startswith('/upload_file'):
            # parse arguments
            args = dict([part.split('=') for part in (req.args or "").split('&')])
            filename = ""
            if args.get('id'):
                filename = urllib.unquote(os.path.split(args['id'])[1])
            if filename == "":
                req.write("{ 'code': 3, 'desc': 'id not supplied' }")
                return apache.DONE
            if not hasattr(req, "session"):
                req.session = Session(req, lock=False)
            session = req.session
            session.lock()
            if filename in os.listdir(session['outdir']):
                session.unlock()
                req.write("{ 'code': 1, 'desc': 'already exist' }")
                return apache.DONE
            session['temp_name_' + filename] = os.path.join(session['outdir'], filename)
            session['temp_size_' + filename] = int(length)
            session.save()
            file_factory = StorageFactory(session['outdir'])
            session.unlock()
            util.FieldStorage(req, keep_blank_values=False, file_callback=file_factory.create)
    return apache.OK
