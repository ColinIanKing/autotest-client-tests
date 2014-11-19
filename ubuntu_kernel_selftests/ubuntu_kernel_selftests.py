#
#
import os
from autotest.client                        import test

#
# Dictionary of kernel versions and releases for which self tests are supported.
#
releases = { '3.13':'trusty', '3.16':'utopic', '3.18':'vivid', '3.19':'vivid' };

#
# Each release has a unique set of tests that actually work. You can get the list of
# defined test targets from the TARGET macro of tools/testing/selftests/Makefile.
#
tests = {
          '3.2.':[ ],
          '3.13':[ 'breakpoints','cpu-hotplug','efivarfs','ipc','mount','powerpc','ptrace','timers' ],
          '3.16':[ ],
          '3.18':[ 'breakpoints','cpu-hotplug','efivarfs','memfd','memory-hotplug','mount','net','ptrace','timers','powerpc','user','ftrace' ],
          '3.19':[ ]
        };

TARGETS = 'breakpoints cpu-hotplug efivarfs kcmp memfd memory-hotplug mqueue mount net ptrace timers vm powerpc user sysctl firmware ftrace'

class ubuntu_kernel_selftests(test.test):
    version = 1

    def run_once(self, test_name):
        self.job.require_gcc()

        #
        # Extract the running kernel version and pair it with an Ubuntu release. Knowing
        # that allows us to pull the right repository.
        #
        release = os.uname()
        uname = release[2]
        version = uname[0:4]
        print(version)

        #
        # If there is no version in the releases dictionary, then just bail since this kernel
        # may not have had self tests (3.2 for example).
        #
        if not releases[version]:
            print("There are no self tests defined for kernel version %s" % version)

        #
        # Use a local repo for manual testing. If it does not exist, then clone from the master
        # repository.
        #
        repo = os.environ['HOME'] + '/ubuntu/ubuntu-%s' % releases[version]
        if os.path.exists(repo) == True:
            cmd = 'git clone -q %s linux' % repo
            print(cmd)
            if os.system(cmd) < 0:
                print("FAIL: Could not clone from local %s" % repo)
                return -1

        #
        # No local repository, so clone from the master repo.
        #
        if os.path.exists('linux') == False:
            cmd = 'git clone http://kernel.ubuntu.com/git-repos/ubuntu/ubuntu-%s.git linux' % releases[version]
            print(cmd)
            if os.system(cmd) < 0:
                print("FAIL: Could not clone ubuntu-%s" % releases[version])
                return -1

        for x in tests[version]:
            cmd = "sudo make -C linux/tools/testing/selftests/%s all run_tests" % x
            print(cmd)
            if os.system(cmd) < 0:
                print("FAIL: kernel self test %s failed" % x)
                return -1

        return 0

# vi:set ts=4 sw=4 expandtab syntax=python:
