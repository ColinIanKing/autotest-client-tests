#
#
import os
import platform
from autotest.client                        import test, utils
import platform

class ubuntu_zfs_xfs_generic(test.test):
    version = 4

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'acl',
            'attr',
            'autoconf',
            'automake',
            'autopoint',
            'bc',
            'build-essential',
            'dbench',
            'dump',
            'e2fsprogs',
            'fio',
            'gawk',
            'gdb',
            'gettext',
            'git',
            'kpartx',
            'ksh',
            'libtool',
            'libtool-bin',
            'pax',
            'pkg-config',
            'texinfo',
            'texlive',
            'quota',
            'git',
            'libblkid-dev'
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        if series in ['precise', 'trusty', 'utopic']:
            utils.system_output('add-apt-repository ppa:zfs-native/stable -y', retain_output=True)
            utils.system_output('apt-get update || true', retain_output=True)
            pkgs.append('ubuntu-zfs')
        elif series == 'wily':
            pkgs.append('zfs-dkms')
            pkgs.append('zfsutils-linux')
        else:
            pkgs.append('zfsutils-linux')

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    # if you change setup, be sure to increment version
    #
    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        utils.system_output('rm -f /etc/*/S99autotest || true', retain_output=True)

        utils.system_output('useradd fsgqa || true', retain_output=True)
        utils.system_output('grep -q fsgqa /etc/sudoers || echo \"fsgqa    ALL=(ALL)NOPASSWD: ALL\" >> /etc/sudoers', retain_output=True)

        # Hacky way to use proxy settings, ideally this should be done on deployment stage
        #
        print "Setup the http/https proxy"
        proxysets = [{'addr': 'squid.internal', 'desc': 'Running in the Canonical CI environment'},
                  {'addr': '91.189.89.216', 'desc': 'Running in the Canonical enablement environment'},
                  {'addr': '10.245.64.1', 'desc': 'Running in the Canonical enablement environment'}]
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

        print "Fetching xfstests.."
        os.chdir(self.srcdir)
        utils.system('git clone https://github.com/tytso/xfstests-bld')
        os.chdir(os.path.join(self.srcdir, 'xfstests-bld'))
        print "Using head commit d6e3c3559cf05b5ef078f91a97e9639c3688ead0"
        utils.system('git reset --hard d6e3c3559cf05b5ef078f91a97e9639c3688ead0')
        print "Patching git repo sources for xfstests-bld"
        utils.system('patch -p1 < %s/0002-config-use-http-https-protocol-for-firewall.patch' % self.bindir)
        print "Patching xfsprogs release version for lp:1753987"
        utils.system('patch -p1 < %s/0003-config-use-the-latest-xfsprogs-release.patch' % self.bindir)
        print "Patching xfstests-bld to add ARM64 xattr syscall support"
        utils.system('patch -p1 < %s/0004-Add-syscalls-for-ARM64-platforms-LP-1755499.patch' % self.bindir)
        print "Fetching all repos.."
        utils.system('./get-all')
        commit = "4cabd42a78d242650b1053520af308011061343e"
        print "Using xfs from known stable commit point " + commit
        os.chdir('xfstests-dev')
        utils.system('git reset --hard ' + commit)
        print "Patching xfstests.."
        utils.system('patch -p1 < %s/0001-xfstests-add-minimal-support-for-zfs.patch' % self.bindir)
        os.chdir(os.path.join(self.srcdir, 'xfstests-bld'))
        print "Building xfstests"
        utils.system('make')
        utils.system('modprobe zfs')

    def run_once(self, test_name):
        #
        #  We need to call setup first to trigger setup() being
        #  invoked, then we can run run_once per test
        #
        if test_name == 'setup':
                return
        os.chdir(os.path.join(self.srcdir, 'xfstests-bld', 'xfstests-dev'))
        cmd = '%s/ubuntu_zfs_xfs_generic.sh %s %s' % (self.bindir, test_name, self.srcdir)
        print "Running: " + cmd
        self.results = utils.system_output(cmd, retain_output=True)
        print self.results
        print "Done!"

# vi:set ts=4 sw=4 expandtab syntax=python:
