#
#
import os
import platform
from autotest.client                        import test, utils

class ubuntu_futex(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'git',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    # setup
    #
    #    Automatically run when there is no autotest/client/tmp/<test-suite> directory
    #
    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        # Hacky way to use proxy settings, ideally this should be done on deployment stage
        #
        proxysets = [
                {'addr': 'squid.internal', 'desc': 'Running in the Canonical CI environment'},
                {'addr': '91.189.89.216',  'desc': 'Running in the Canonical enablement environment'},
                {'addr': '10.245.64.1',    'desc': 'Running in the Canonical enablement environment'}
            ]
        for proxy in proxysets:
            cmd = 'nc -w 2 ' + proxy['addr'] + ' 3128'
            try:
                utils.system_output(cmd, retain_output=False)
                print proxy['desc']
                os.environ['http_proxy'] = 'http://' + proxy['addr'] + ':3128'
                os.environ['https_proxy'] = 'http://' + proxy['addr'] + ':3128'
                break
            except:
                pass

        os.chdir(self.srcdir)
        cmd = 'git clone --depth=1 https://git.kernel.org/pub/scm/linux/kernel/git/dvhart/futextest.git'
        self.results = utils.system_output(cmd, retain_output=True)

        # Print test suite HEAD SHA1 commit id for future reference
        os.chdir(os.path.join(self.srcdir, 'futextest'))
        sha1 = utils.system_output('git rev-parse --short HEAD', retain_output=False, verbose=False)
        print("Test suite HEAD SHA1: {}".format(sha1))

        os.chdir(os.path.join(self.srcdir, 'futextest', 'functional'))
        cmd = 'sed -i s/lpthread/pthread/ Makefile'
        self.results = utils.system_output(cmd, retain_output=True)

        utils.make()

    # run_once
    #
    #    Driven by the control file for each individual test.
    #
    def run_once(self, test_name):
        os.chdir(os.path.join(self.srcdir, 'futextest', 'functional'))
        cmd = 'USE_COLOR=0 ./run.sh'

        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
