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
        '''Function to install necessary packages.'''
        pkgs = [
            'bc',
            'build-essential',
            'devscripts',
            'docutils-common',
            'ethtool',
            'fuse',
            'git',
            'iptables',
            'jq',
            'kernel-wedge',
            'netsniff-ng',
            'net-tools',
            'pkg-config',
            'uuid-runtime'
        ]
        if not (self.arch == 's390x' and self.series in ['trusty', 'xenial']):
            pkgs.append('libnuma-dev')
            pkgs.append('libfuse-dev')
        gcc = 'gcc' if self.arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        if any(x in self.flavour for x in ['aws', 'azure', 'gcp', 'gke']):
            if not (self.flavour == 'aws' and self.series == 'trusty'):
                pkgs.append('linux-modules-extra-' + platform.uname()[2])

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
            else:
                pkgs.extend(['clang', 'llvm'])

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        utils.system_output(cmd, retain_output=True)

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

    def download(self):
        '''Function to download kernel source.'''
        cmd = "dpkg -S /lib/modules/" + platform.release() + "/kernel | cut -d: -f 1 | cut -d, -f 1"
        pkg = os.popen(cmd).readlines()[0].strip()
        utils.system("apt-get source --download-only " + pkg)

    def extract(self):
        '''Function to extract kernel source.'''
        os.system("rm -rf linux/")
        utils.system("dpkg-source -x linux*dsc linux")

    def setup(self):
        '''Function to setup the test environment.'''
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
            # update fix CPU hotplug test, new and old versions
            #
            print("Updating CPU hotplug test")
            fn = "linux/tools/testing/selftests/cpu-hotplug/cpu-on-off-test.sh"
            if os.path.exists(fn) and 'present_cpus=' not in open(fn).read():
                cmd = 'cp %s/cpu-on-off-test.sh %s' % (self.bindir, fn)
                utils.system(cmd)
            else:
                fn = "linux/tools/testing/selftests/cpu-hotplug/on-off-test.sh"
                if os.path.exists(fn) and 'present_cpus=' not in open(fn).read():
                    cmd = 'cp %s/cpu-on-off-test.sh %s' % (self.bindir, fn)
                    utils.system(cmd)

            #
            # cpu hotplug test might fail on Azure instances because Hyper-V
            # does not allow it.
            #
            if self.flavour in ['azure', 'azure-fips']:
                print("Disabling CPU hotplug test")
                fn = 'linux/tools/testing/selftests/cpu-hotplug/cpu-on-off-test.sh'
                mk = 'linux/tools/testing/selftests/cpu-hotplug/Makefile'
                if os.path.exists(fn):
                    cmd = 'sed -i "s/ cpu-on-off-test.sh//" ' + mk
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
            # memory hotplug test will fail on arm and several cloud platforms from 5.6+
            # as it was enabled in 5.6 but needs memory that does not
            # have boot time pages in the regions to be offlined and
            # current test hardware cannot guarantee that constraint.
            # Except ARM, also all cloud platforms on amd64 seems to have unmovable
            # pages which makes memory hotplug failing.
            #
            if self.arch.startswith('arm') or self.arch == 'aarch64' or \
               self.flavour in ['aws', 'azure', 'azure-fips']:
                print("Disabling memory hotplug test")
                fn = 'linux/tools/testing/selftests/memory-hotplug/mem-on-off-test.sh'
                mk = 'linux/tools/testing/selftests/memory-hotplug/Makefile'
                if os.path.exists(fn):
                    cmd = 'sed -i "s/ mem-on-off-test.sh//" ' + mk
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
        if test_name.endswith('-build'):
            os.chdir(self.srcdir)
            if "net" in test_name:
                cmd = "sh -c 'echo 1 > /proc/sys/net/ipv4/conf/all/accept_local'"
                utils.system(cmd)
                if self.kv >= 415:
                    # net selftests use a module built by bpf selftests, bpf is available since bionic kernel
                    if self.kv == 506:
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
                    # keep running selftests/net, even if selftests/bpf build fails
                    utils.system(cmd, ignore_status=True)
            cmd = "make -C linux/tools/testing/selftests TARGETS={}".format(test_name.replace('-build', ''))
            utils.system_output(cmd, retain_output=True)
            return

        category = test_name.split(':')[0]
        sub_test = test_name.split(':')[1]
        dir_root = os.path.join(self.srcdir, 'linux', 'tools', 'testing', 'selftests')
        os.chdir(dir_root)
        cmd = "make run_tests -C {} TEST_PROGS={} TEST_GEN_PROGS='' TEST_CUSTOM_PROGS=''".format(category, sub_test)
        result = utils.system_output(cmd, retain_output=True)

        # The output of test_bpf.sh / test_blackhole_dev.sh test will be in the dmesg
        kernel_module_tests = {'test_bpf.sh': 'CONFIG_TEST_BPF',
                               'test_blackhole_dev.sh': 'CONFIG_TEST_BLACKHOLE_DEV'}
        if sub_test in kernel_module_tests.keys():
            output = utils.system_output('dmesg', retain_output=True)
            if not output:
                print("Looks like there's no dmesg output, checking for {}...".format(kernel_module_tests[sub_test]))
                cmd = "grep ^{} /boot/config-$(uname -r)".format(kernel_module_tests[sub_test])
                if not utils.system_output(cmd, verbose=False, ignore_status=True):
                    print("{} not enabled.".format(kernel_module_tests[sub_test]))

        # Old pattern for Xenial
        pattern = re.compile('selftests: *(?P<case>[\w\-\.]+) \[FAIL\]\n')
        if re.search(pattern, result):
            raise error.TestError(test_name + ' failed.')
        # If the test was not end by previous check, check again with new pattern
        pattern = re.compile('not ok [\d\.]* selftests: {}: {} # (?!.*SKIP)'.format(category, sub_test))
        if re.search(pattern, result):
            raise error.TestError(test_name + ' failed.')


# vi:set ts=4 sw=4 expandtab syntax=python:
