#
#
import os
import platform
from autotest.client                        import test, utils
from autotest.client.shared                 import error

class ubuntu_kernel_selftests(test.test):
    version = 1

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'bc', 'build-essential', 'git', 'pkg-config',
        ]
        if not (arch == 's390x' and series in ['precise', 'trusty', 'vivid', 'xenial']):
            pkgs.append('libnuma-dev')
            pkgs.append('libfuse-dev')
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

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

        # Use a local repo for manual testing. If it does not exist, then clone from the master
        # repository.
        #
        if not os.path.exists('linux'):
            self.download()
            self.extract()

            # tweak sleep wake alarm time to 30 seconds as 5 is a bit too small
            #
            fn = 'linux/tools/testing/selftests/breakpoints/step_after_suspend_test.c'
            if os.path.exists(fn):
               cmd = 'sed -i "s/tv_sec = 5;/tv_sec = 30;/" ' + fn
               utils.system(cmd)
            # currently disable step_after_suspend_test as this breaks ssh'd login
            # connections to the test VMs and real H/W
            fn = 'linux/tools/testing/selftests/breakpoints/Makefile'
            if os.path.exists(fn):
                cmd = 'sed -i "s/\(.* .\?= step_after_suspend_test\)/#\\1/" ' + fn
                utils.system(cmd)
                # LP #1680507
                cmd = 'sed -i /breakpoint_test_arm64/d ' + fn
                utils.system(cmd)

            #
            # disable rtctest, LP: #1659333
            #   this hangs xenial host servers when running in a VM,
            #   so for now disable this test. Urgh, dirty hack
            #
            fn = 'linux/tools/testing/selftests/timers/Makefile'
            if os.path.exists(fn):
                cmd = 'sed -i "s/threadtest rtctest/threadtest/" ' + fn
                utils.system(cmd)

                cmd = 'cat linux/tools/testing/selftests/timers/Makefile'
                utils.system(cmd)

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        os.chdir(self.srcdir)
        cmd = "sudo make -C linux/tools/testing/selftests TARGETS=%s run_tests" % test_name
        self.results = utils.system_output(cmd, retain_output=True)

        if self.results.find('[FAIL]') != -1:
            raise error.TestFail('Test failed for ' + test_name)


# vi:set ts=4 sw=4 expandtab syntax=python:
