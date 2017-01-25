from contextlib import contextmanager
from StringIO import StringIO
from shutil import rmtree
import tarfile

from flask import current_app

from .exceptions import BuildException

import os
import uuid


@contextmanager
def mktmpdir():
    try:
        tmpdir = os.path.join(current_app.config['TMP_DIR'], uuid.uuid4())
        os.makedirs(tmpdir)
        yield tmpdir
    finally:
        rmtree(tmpdir, ignore_errors=True)


def get_user(username):
    for user in current_app.config['USERS']:
        if user['username'].lower() == username.lower():
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
        if 'allow_images' in user:
            return image in user['allow_images']
        else:
            return True
    except:
        return False


def docker_build(c, inputdir_local, output, image):
    inputdir_container = '/tmp/inputdir'
    container = c.create_container(
        image=image,
        volumes=[inputdir_container],
        host_config=c.create_host_config(binds=[
            ':'.join([inputdir_local, inputdir_container, 'rw'])]),
        network_disabled=True,
        command='/tmp/build %s' % output
    )
    try:
        c.start(container)
        result = c.wait(container, timeout=current_app.config['CONTAINER_TIMEOUT'])
        log = c.logs(container, stdout=True, stderr=True)
        print log
        if result != 0:
            raise BuildException(result, log)
        tar_target = c.copy(container, '/tmp/%s' % output)
        tar = tarfile.open(fileobj=StringIO(tar_target.read()))
        return tar.extractfile(output)
    finally:
        c.remove_container(container, force=True)
