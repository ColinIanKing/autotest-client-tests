#
#
import os
import platform
import re
from autotest.client                        import test, utils
from autotest.client.shared                 import error

class ubuntu_kernel_selftests(test.test):
    version = 1

    def install_required_pkgs(self):
        pkgs = [
            'bc',
            'build-essential',
            'devscripts',
            'fuse',
            'git',
            'jq',
            'kernel-wedge',
            'netsniff-ng',
            'net-tools',
            'pkg-config'
        ]
        if not (self.arch == 's390x' and self.series in ['precise', 'trusty', 'vivid', 'xenial']):
            pkgs.append('libnuma-dev')
            pkgs.append('libfuse-dev')
        gcc = 'gcc' if self.arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        if self.flavour in ['aws', 'azure', 'azure-fips', 'gcp', 'gcp-fips', 'gke', 'gkeop']:
            if not (self.flavour == 'aws' and self.series == 'trusty'):
                pkgs.append('linux-modules-extra-' + self.flavour + '*')

        if self.kv >= 415:
            # extra packages for building bpf tests
            pkgs.extend(['libcap-dev', 'libelf-dev'])
            if self.kv in [504, 503]:
                # special case for B-5.4 (lp:1882559) / B-5.3 (lp:1845860)
                # clang on F is clang-10 but we need clang-9 (see commit 95f91d59642)
                # clang on E is clang-9, so it's ok to just check kv here
                pkgs.extend(['clang-9', 'llvm-9'])
            elif self.kv == 506:
                # special case for F-oem-5.6 (lp:1879360)
                pkgs.extend(['clang-10', 'llvm-10'])
            elif self.kv >= 513:
                pkgs.extend(['clang-13', 'llvm-13'])
            else:
                pkgs.extend(['clang', 'llvm'])

        if self.kv >= 510:
            # python3-docutils is needed for bpf selftests build
            pkgs.extend(['python3-docutils'])

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        self.arch = platform.processor()
        self.flavour = re.split('-\d*-', platform.uname()[2])[-1]
        try:
            self.series = platform.dist()[2]
        except AttributeError:
            import distro
            self.series = distro.codename()
        self.kv = platform.release().split(".")[:2]
        self.kv = int(self.kv[0]) * 100 + int(self.kv[1])
        pass

    def download(self):
        cmd = "dpkg -S /lib/modules/" + platform.release() + "/kernel | cut -d: -f 1 | cut -d, -f 1"
        pkg = os.popen(cmd).readlines()[0].strip()
        utils.system("apt-get source --download-only " + pkg)

    def extract(self):
        os.system("rm -rf linux/")
        utils.system("dpkg-source -x linux*dsc linux")

    def summary(self, pattern):
        failures = list(re.finditer(pattern, self.results))
        if failures:
            for i in failures:
                print('Sub test case: {} failed.'.format(i.group('case')))
            return True
        return False

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

            # clean source tree so changes from debian.foo/reconstruct
            # (e.g. deleting files) are applied
            os.chdir('linux')
            cmd = 'fakeroot debian/rules clean'
            utils.system(cmd)
            os.chdir(self.srcdir)

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
            print("Updating CPU hotplug test")
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
                'kprobe/kprobe_module.tc',
            ]

            #
            # Ftrace 'Kprobe event user-memory access' test depends on
            # HAVE_FUNCTION_ARG_ACCESS_API, but ppc64 doesn't support it:
            # disable it to avoid an unresolved result (and thus a failure).
            #
            if self.arch in ['ppc64le', 's390x']:
                filenames.append('kprobe/kprobe_args_user.tc')

            for fn in filenames:
                fn = 'linux/tools/testing/selftests/ftrace/test.d/' + fn
                if os.path.exists(fn):
                    os.remove(fn)

            #
            # ptrace/vmaccess was introduced in 5.7-rc1 and is broken ATM,
            # see https://lkml.org/lkml/2020/4/9/648
            #
            fn = 'linux/tools/testing/selftests/ptrace/vmaccess.c'
            mk = 'linux/tools/testing/selftests/ptrace/Makefile'
            if os.path.exists(fn):
                print("Disabling ptrace/vmacces")
                cmd = 'sed -i "s/ vmaccess//" ' + mk
                utils.system(cmd)

            #
            # memory hotplug test will fail on arm platforms from 5.6+
            # as it was enabled in 5.6 but needs memory that does not
            # have boot time pages in the regions to be offlined and
            # current test hardware cannot guarantee that constraint
            # so disable it for arm platforms for now
            #
            if self.arch.startswith('arm') or self.arch == 'aarch64':
                print("Disabling memory hotplug test on ARM platform")
                fn = 'linux/tools/testing/selftests/memory-hotplug/mem-on-off-test.sh'
                if os.path.exists(fn):
                    cmd = 'chmod -x ' + fn
                    utils.system(cmd)

            # net/txtimestamp.sh is very fragile, disable it
            #
            fn = 'linux/tools/testing/selftests/net/Makefile'
            if os.path.exists(fn):
                cmd = 'sed -i "/^TEST_PROGS += txtimestamp.sh$/d" ' + fn
                utils.system(cmd)

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        cmd = "sudo sh -c 'echo 1 > /proc/sys/net/ipv4/conf/all/accept_local'"
        utils.system(cmd)

        os.chdir(self.srcdir)
        if test_name == "net" and self.kv >= 415:
            # net selftests use a module built by bpf selftests, bpf is available since bionic kernel
            if self.kv >= 513:
                os.environ["CLANG"] = "clang-13"
                os.environ["LLC"] = "llc-13"
                os.environ["LLVM_OBJCOPY"] = "llvm-objcopy-13"
                os.environ["LLVM_READELF"] = "llvm-readelf-13"
            elif self.kv == 506:
                os.environ["CLANG"] = "clang-10"
                os.environ["LLC"] = "llc-10"
                os.environ["LLVM_OBJCOPY"] = "llvm-objcopy-10"
                os.environ["LLVM_READELF"] = "llvm-readelf-10"
            elif self.kv in [504, 503]:
                os.environ["CLANG"] = "clang-9"
                os.environ["LLC"] = "llc-9"
                os.environ["LLVM_OBJCOPY"] = "llvm-objcopy-9"
                os.environ["LLVM_READELF"] = "llvm-readelf-9"
            cmd = "make -C linux/tools/testing/selftests TARGETS=bpf SKIP_TARGETS= KDIR=/usr/src/linux-headers-{}".format(platform.release())
            utils.system(cmd)
        cmd = "sudo make -C linux/tools/testing/selftests TARGETS=%s run_tests" % test_name
        self.results = utils.system_output(cmd, retain_output=True)

        print('========== Summary ===========')

        # Old pattern for Xenial
        pattern = re.compile('selftests: *(?P<case>[\w\-\.]+) \[FAIL\]\n')
        if self.summary(pattern):
            raise error.TestError('Test failed for ' + test_name)
        # If the test was not end by previous check, check again with new pattern
        pattern = re.compile('not ok [\d\.]* selftests: *({}.*: )?(?P<case>[\w\-\.]+)(?!.*SKIP)'.format(test_name))
        if self.summary(pattern):
            raise error.TestError('Test failed for ' + test_name)

        print('No failed cases reported')

# vi:set ts=4 sw=4 expandtab syntax=python:
