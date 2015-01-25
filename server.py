#!/usr/bin/env python

from contextlib import contextmanager
from os.path import join
from shutil import rmtree
from StringIO import StringIO
import tarfile
from tempfile import mkdtemp

import docker
from requests.exceptions import ReadTimeout
from flask import Flask, request, Response
from werkzeug import secure_filename

TIMEOUT = 60

app = Flask(__name__)
c = docker.Client(base_url='unix://var/run/docker.sock')


@contextmanager
def mktmpdir():
    try:
        tmpdir = mkdtemp()
        yield tmpdir
    finally:
        rmtree(tmpdir, ignore_errors=True)


class BuildException(Exception):
    def __init__(self, status, log):
        self.msg =  'Build failed with %d:\n%s' % (status, log)

    def __str__(self):
        return self.msg


def docker_build(archivedir, filename):
    try:
        container = c.create_container(image='doc',
                                       volumes=['/tmp/archivedir'],
                                       network_disabled=True,
                                       command='./build %s' % filename)
                                       #command='false')
                                       #command='xxx')
                                       #command='sleep 60'); TIMEOUT=1
        c.start(container, binds={archivedir: {'bind': 'tmp/archivedir',
                                               'ro': True}})
        result = c.wait(container, timeout=TIMEOUT)
        log = c.logs(container, stdout=True, stderr=True)
        print log
        if result != 0:
            raise BuildException(result, log)
        target = c.copy(container, '/tmp/%s' % filename)
        tar = tarfile.open(fileobj=StringIO(target.read()))
        return tar.extractfile(filename)
    finally:
        c.remove_container(container, force=True)


@app.route('/build/', methods=['GET'])
def build_get():
    return app.send_static_file('index.html')


@app.route('/build/', methods=['POST'])
@app.route('/build/<filename>', methods=['POST'])
def build(filename=None):
    filename = request.form.get('filename', filename)
    archive = request.files['archive']
    if not filename:
        return 'Missing filename', 400
    if not archive:
        return 'Missing archive', 400
    with mktmpdir() as tempdir:
        archive.save(join(tempdir, secure_filename(archive.filename)))
        try:
            response = Response(docker_build(tempdir, filename))
            response.mimetype = 'application/octet-stream'
            response.headers['Content-Disposition'] = 'attachment; filename="%s"' % filename
            return response
        except docker.errors.APIError as e:
            if 'could not find the file' in e.explanation.lower():
                err = 'Could not find file %s' % filename
                return err, 400
            else:
                return e.explanation, 500
        except ReadTimeout as e:
            err = ('Timeout: Build did not complete after %d seconds' %
                   TIMEOUT)
            return err, 400
        except BuildException as e:
            return str(e), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, debug=False)
    #import sys
    #with mktmpdir() as tempdir:
    #    shutil.copy(sys.argv[1], tempdir)
    #    print docker_build(tempdir, sys.argv[2])