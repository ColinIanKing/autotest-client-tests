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
            #
            # newer kernels have the rtctest in the rtc subdirectory
            #
            fn = 'linux/tools/testing/selftests/rtc/Makefile'
            if os.path.exists(fn):
                cmd = 'sed -i "s/ rtctest//" ' + fn
                utils.system(cmd)
            #
            # systems without /dev/rtc0 should not run rtcpie test
            #
            fn = 'linux/tools/testing/selftests/timers/Makefile'
            if not os.path.exists("/dev/rtc0") and os.path.exists(fn):
                cmd = 'sed -i "s/ rtcpie//" ' + fn
                utils.system(cmd)

            #
            # update fix CPU hotplug test, new and old versions
            #
            print "Updating CPU hotplug test"
            fn="linux/tools/testing/selftests/cpu-hotplug/cpu-on-off-test.sh"
            if os.path.exists(fn) and 'present_cpus=' not in open(fn).read():
                cmd = 'cp %s/cpu-on-off-test.sh %s' % (self.bindir, fn)
                utils.system(cmd)
            else:
                fn="linux/tools/testing/selftests/cpu-hotplug/on-off-test.sh"
                if os.path.exists(fn) and 'present_cpus=' not in open(fn).read():
                    cmd = 'cp %s/cpu-on-off-test.sh %s' % (self.bindir, fn)
                    utils.system(cmd)

            #
            # Disable new ftrace tests that don't work reliably across
            # architectures because of various symbols being checked
            #
            filenames = [
                'ftrace/func_stack_tracer.tc',
                'ftrace/func-filter-glob.tc',
                'trigger/inter-event/trigger-inter-event-combined-hist.tc',
                'trigger/inter-event/trigger-synthetic-event-createremove.tc',
                'trigger/trigger-hist.tc',
                'trigger/trigger-trace-marker-hist.tc',
                'kprobe/probepoint.tc',
            ]
            for fn in filenames:
                fn = 'linux/tools/testing/selftests/ftrace/test.d/' + fn
                if os.path.exists(fn):
                    os.remove(fn)

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        cmd = "sudo sh -c 'echo 1 > /proc/sys/net/ipv4/conf/all/accept_local'"
        utils.system(cmd)

        os.chdir(self.srcdir)
        cmd = "sudo make -C linux/tools/testing/selftests TARGETS=%s run_tests" % test_name
        self.results = utils.system_output(cmd, retain_output=True)

        if self.results.rfind('[FAIL]\n') != -1:
            raise error.TestFail('Test failed for ' + test_name)


# vi:set ts=4 sw=4 expandtab syntax=python:
