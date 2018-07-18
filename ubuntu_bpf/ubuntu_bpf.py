#
#
from autotest.client import test, utils
import platform
import os

class ubuntu_bpf(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()

        pkgs = [
            'build-essential',
            'clang',
            'git',
            'libcap-dev',
            'libelf-dev',
            'llvm',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        series = platform.dist()[2]
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
        if not os.path.exists('linux'):
            cmd = 'git clone --depth=1 https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/%s linux' % series
            utils.system(cmd)
        os.chdir(os.path.join(self.srcdir, 'linux'))
        # Assist local testing by restoring the linux repo to vanilla.
        cmd = 'git checkout -f;git clean -f -d;git ls-files --others --directory |xargs rm -rvf;rm -rf .git/rebase*'
        utils.system(cmd)
        cmd = 'git fetch origin master;git reset --hard FETCH_HEAD'
        utils.system(cmd)
        cmd = 'patch -p1 < %s/0001-selftests-just-build-bpf.patch' % self.bindir
        utils.system(cmd)
        os.chdir(os.path.join(self.srcdir, 'linux/tools/testing/selftests'))
        utils.make('clean')
        utils.make()

    def run_once(self, test_name):
        os.chdir(os.path.join(self.srcdir, 'linux/tools/testing/selftests'))
        cmd = '%s/ubuntu_bpf.sh' % self.bindir
        self.results = utils.system_output(cmd, retain_output=True)

        print(self.results)

# vi:set ts=4 sw=4 expandtab syntax=python:
