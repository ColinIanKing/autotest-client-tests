import os
import platform
from autotest.client import test, utils
from autotest.client.shared import error


class rtc(test.test):
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
        utils.system_output('apt-get install virt-what --assume-yes', retain_output=True)
        os.chdir(self.srcdir)
        utils.make('clobber')
        utils.make()

    def run_once(self, def_rtc="/dev/rtc0", maxfreq=64):
        virt = utils.system_output('virt-what', retain_output=True)
        if virt != '':
            print('Running inside ' + virt + ', not testing RTC')
        else:
            if not os.path.exists(def_rtc):
                raise error.TestNAError("RTC device %s does not exist" % def_rtc)
            os.chdir(self.srcdir)
            utils.system('./rtctest %s %s' % (def_rtc, maxfreq))
