from contextlib import contextmanager
from io import StringIO
from shutil import rmtree
import tarfile
from tempfile import mkdtemp
import yaml

from .exceptions import BuildException


@contextmanager
def mktmpdir():
    try:
        tmpdir = mkdtemp()
        yield tmpdir
    finally:
        rmtree(tmpdir, ignore_errors=True)


def get_config():
    CONFIG_FILE = 'config.yaml'
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


def docker_build(c, inputdir_local, output, image):
    inputdir_container = '/tmp/inputdir'
    container = c.create_container(
        image=image,
        volumes=[inputdir_container],
        network_disabled=True,
        command='/tmp/build %s' % output
    )
    try:
        binds = {inputdir_local: {'bind': inputdir_container, 'ro': True}}
        c.start(container, binds=binds)
        result = c.wait(container, timeout=get_config['container_timeout'])
        log = c.logs(container, stdout=True, stderr=True)
        print log
        if result != 0:
            raise BuildException(result, log)
        tar_target = c.copy(container, '/tmp/%s' % output)
        tar = tarfile.open(fileobj=StringIO(tar_target.read()))
        return tar.extractfile(output)
    finally:
        c.remove_container(container, force=True)
