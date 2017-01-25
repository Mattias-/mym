from functools import wraps
from os.path import join

import docker
from requests.exceptions import ReadTimeout
from flask import current_app, request, Response, Blueprint
from werkzeug import secure_filename

from .exceptions import BuildException
from .utils import docker_build, check_auth, check_image, mktmpdir


c = docker.Client(base_url='unix://var/run/docker.sock')

build = Blueprint('build', __name__, static_folder='../static')


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            header = {'WWW-Authenticate': 'Basic realm="Login Required"'}
            return Response('Bad username or password', 401, header)
        return f(*args, **kwargs)
    return decorated


@build.route('/', methods=['GET'])
def index():
    return build.send_static_file('index.html')


@build.route('/', methods=['POST'])
@build.route('/<image>/<output>', methods=['POST'])
@requires_auth
def run_build(image=None, output=None):
    image = request.form.get('image', image)
    output = request.form.get('output', output)
    inputfile = request.files['input']
    if not image:
        return 'Missing image name', 400
    if not output:
        return 'Missing output file', 400
    if not inputfile:
        return 'Missing input file', 400
    if not check_image(request.authorization.username, image):
        return 'Image not allowed', 403
    with mktmpdir() as tempdir:
        inputfile.save(join(tempdir, secure_filename(inputfile.filename)))
        try:
            response = Response(docker_build(c, tempdir, output, image))
            cd = 'attachment; filename="%s"' % output
            response.headers['Content-Disposition'] = cd
            response.mimetype = 'application/octet-stream'
            return response
        except docker.errors.APIError as e:
            if 'could not find the file' in e.explanation.lower():
                err = 'Could not find file %s' % output
                return err, 400
            else:
                return e.explanation, 500
        except ReadTimeout as e:
            err = ('Timeout: Build did not complete after %d seconds' %
                   current_app.config['CONTAINER_TIMEOUT'])
            return err, 400
        except BuildException as e:
            return str(e), 400
