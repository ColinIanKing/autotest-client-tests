#
#
from autotest.client import test, utils
import platform
import os

class ubuntu_bpf(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
            'git',
            'libcap-dev',
            'libelf-dev',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        if series == 'focal':
            pkgs.extend(['clang-9', 'llvm-9'])
        else:
            pkgs.extend(['clang', 'llvm'])

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def download(self):
        kv = platform.release()
        cmd = "dpkg -S /lib/modules/" + kv + "/kernel | cut -d: -f 1 | cut -d, -f 1"
        pkg = os.popen(cmd).readlines()[0].strip()
        utils.system("apt-get source --download-only " + pkg)

    def extract(self):
        os.system("rm -rf linux/")
        utils.system("dpkg-source -x linux*dsc linux")

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()

        os.chdir(self.srcdir)
        if not os.path.exists('linux'):
            self.download()
        # Assist local testing by restoring the linux repo to vanilla.
        self.extract()
        os.chdir(self.srcdir)

        #
        # llvm10 breaks bpf test_maps, revert to llvm9 instead
        #
        series = platform.dist()[2]
        if series == 'focal':
            os.environ["CLANG"] = "clang-9"
            os.environ["LLC"] = "llc-9"
            os.environ["LLVM_OBJCOPY"] = "llvm-objcopy-9"
            os.environ["LLVM_READELF"] = "llvm-readelf-9"

        utils.make('-C linux/tools/testing/selftests TARGETS=bpf clean all')

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        os.chdir(os.path.join(self.srcdir, 'linux/tools/testing/selftests/bpf'))
        cmd = './%s' % test_name
        self.results = utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
