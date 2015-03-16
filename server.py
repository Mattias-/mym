#!/usr/bin/env python

from contextlib import contextmanager
from functools import wraps
from os.path import join
from shutil import rmtree
from StringIO import StringIO
import tarfile
from tempfile import mkdtemp
import yaml

import docker
from requests.exceptions import ReadTimeout
from flask import Flask, request, Response
from werkzeug import secure_filename

CONTAINER_TIMEOUT = 60
CONFIG_FILE = 'config.yaml'

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

def get_config():
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f)
        return config

def get_user(username):
    config = get_config()
    for user in config['users']:
        if user['username'] == username:
            return user
    raise Exception('User not found')

def check_auth(username, password):
    try:
        user = get_user(username)
        return user['password'] == password
    except:
        return False

def check_image(username, image):
    try:
        user = get_user(username)
        return image in user['images']
    except:
        return False

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            header = {'WWW-Authenticate': 'Basic realm="Login Required"'}
            return Response('Please log in', 401, header)
        return f(*args, **kwargs)
    return decorated

def docker_build(archivedir, target, image):
    container = c.create_container(
        image=image,
        volumes=['/tmp/archivedir'],
        network_disabled=True,
        command='/tmp/build %s' % target
    )
    try:
        binds = {archivedir: {'bind': '/tmp/archivedir', 'ro': True}}
        c.start(container, binds=binds)
        result = c.wait(container, timeout=CONTAINER_TIMEOUT)
        log = c.logs(container, stdout=True, stderr=True)
        print log
        if result != 0:
            raise BuildException(result, log)
        tar_target = c.copy(container, '/tmp/%s' % target)
        tar = tarfile.open(fileobj=StringIO(tar_target.read()))
        return tar.extractfile(target)
    finally:
        c.remove_container(container, force=True)

@app.route('/', methods=['GET'])
def build_get():
    return app.send_static_file('index.html')

@app.route('/', methods=['POST'])
@app.route('/<image>/<target>', methods=['POST'])
@requires_auth
def build(image=None, target=None):
    image = request.form.get('image', image)
    target = request.form.get('target', target)
    archive = request.files['archive']
    if not image:
        return 'Missing image', 400
    if not target:
        return 'Missing target', 400
    if not archive:
        return 'Missing archive', 400
    if not check_image(request.authorization.username, image):
        return 'Image not allowed', 403
    with mktmpdir() as tempdir:
        archive.save(join(tempdir, secure_filename(archive.filename)))
        try:
            response = Response(docker_build(tempdir, target, image))
            cd = 'attachment; filename="%s"' % target
            response.headers['Content-Disposition'] = cd
            response.mimetype = 'application/octet-stream'
            return response
        except docker.errors.APIError as e:
            if 'could not find the file' in e.explanation.lower():
                err = 'Could not find file %s' % target
                return err, 400
            else:
                return e.explanation, 500
        except ReadTimeout as e:
            err = ('Timeout: Build did not complete after %d seconds' %
                   CONTAINER_TIMEOUT)
            return err, 400
        except BuildException as e:
            return str(e), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, debug=True)
