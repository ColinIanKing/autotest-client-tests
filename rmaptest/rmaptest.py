import os
import platform
from autotest.client import test, utils


# tests is a simple array of "cmd" "arguments"
tests = [["rmaptest", "-h -i100 -n100 -s100 -t100 -V10 -v file1.dat"],
         ["rmaptest", "-l -i100 -n100 -s100 -t100 -V10 -v file2.dat"],
         ["rmaptest", "-r -i100 -n100 -s100 -t100 -V10 -v file3.dat"],
         ]
name = 0
arglist = 1


class rmaptest(test.test):
    version = 1
    preserve_srcdir = True

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = []
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    def setup(self):
        os.chdir(self.srcdir)
        utils.system(utils.get_cc() + ' -Wall -o rmaptest rmap-test.c')

    def execute(self, args=''):
        os.chdir(self.tmpdir)
        for test in tests:
            cmd = '%s/%s %s %s' % (self.srcdir, test[name], args, test[arglist])
            utils.system(cmd)
