import os
import time
import subprocess
import platform
from autotest.client import test
from autotest.client.shared import utils, error


class iosched_bugs(test.test):
    version = 1
    preserve_srcdir = True

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    def setup(self):
        os.chdir(self.srcdir)
        utils.make()

    def execute(self):
        os.chdir(self.tmpdir)
        (p1, _) = utils.run_bg('dd if=/dev/hda3 of=/dev/null')
        time.sleep(60)
        blah = os.path.join(self.tmpdir, 'blah')
        dirty_bin = os.path.join(self.srcdir, 'dirty')
        dirty_op = os.path.join(self.tmpdir, 'dirty')
        utils.system('echo AA > ' + blah)
        p2 = subprocess.Popen(dirty_bin + ' ' + blah + ' 1 > ' + dirty_op,
                              shell=True)
        time.sleep(600)
        if p2.poll() is None:
            utils.nuke_subprocess(p1)
            utils.nuke_subprocess(p2)
            raise error.TestFail('Writes made no progress')
# Commenting out use of utils.run as there is a timeout bug
#
#       try:
#           utils.run(dirty_bin + ' ' + blah + '1 > ' + dirty_op, 900, False,
#                     None, None)
#       except Exception:
#           utils.nuke_subprocess(p1)
#           raise error.TestFail('Writes made no progress')
        utils.nuke_subprocess(p1)
