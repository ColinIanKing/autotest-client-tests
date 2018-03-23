import os
import sys
import re
import platform
from autotest.client            import test, utils, os_dep
from autotest.client.shared     import error

class ubuntu_kvm_unit_tests(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential', 'cpu-checker', 'qemu-kvm', 'git',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

        try:
            utils.system('kvm-ok')
        except error.CmdError:
            raise error.TestError('Test skipped, this systems does not have KVM extension support')

    def initialize(self):
        self.install_required_pkgs()
        self.job.require_gcc()

    def setup(self):
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
                os.environ['https_proxy'] = 'https://' + proxy['addr'] + ':3128'
                break
            except:
                pass

        arch = platform.processor()
        opt = []
        os.chdir(self.srcdir)
        cmd = 'git clone --depth=1 https://git.kernel.org/pub/scm/virt/kvm/kvm-unit-tests.git'
        self.results = utils.system_output(cmd, retain_output=True)
        os.chdir('kvm-unit-tests')
        if arch == 'ppc64le':
            opt.append('--endian={}'.format(sys.byteorder))
        utils.configure(' '.join(opt))
        utils.make()

        # patch run_tests.sh to build our tests list
        utils.system('patch -p1 < %s/runtime_show.patch' % self.bindir)

    def run_once(self, test_name, cmd=''):
        os.chdir(self.srcdir + '/kvm-unit-tests')

        arch = platform.processor()
        if arch == 'ppc64le':
            # disable smt (simultaneous multithreading) on ppc for kvm
            utils.system('ppc64_cpu --smt=off')

        output = utils.system_output('./run_tests.sh -v', retain_output=True)

        if arch == 'ppc64le':
            # turn smt back on
            utils.system('ppc64_cpu --smt=on')

        if 'FAIL' in output:
            raise error.TestError('Test error, check debug logs for complete test output')

# vi:set ts=4 sw=4 expandtab:
