
class BuildException(Exception):
    def __init__(self, status, log):
        self.msg = 'Build failed with %d:\n%s' % (status, log)

    def __str__(self):
        return self.msg
