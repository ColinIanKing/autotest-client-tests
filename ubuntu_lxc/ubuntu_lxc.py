#
#
from autotest.client                        import test, utils
import multiprocessing
import os
import platform
import shutil

class ubuntu_lxc(test.test):
    version = 1

    def install_required_pkgs(self):
        arch  = platform.processor()
        if self.series in ['precise', 'trusty', 'xenial', 'artful']:
            pkgs = [
                'lxc-tests'
            ]
        else:
            pkgs = [
                'autoconf',
                'build-essential',
                'dirmngr',
                'libapparmor-dev',
                'libcap-dev',
                'libtool',
                'lxc',
                'pkg-config',
                'python3-lxc',
            ]
            gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
            pkgs.append(gcc)

        pkgs.append('liblxc1')
        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        utils.system_output(cmd, retain_output=True)

    def initialize(self, test_name):
        try:
            self.series = platform.dist()[2]
        except AttributeError:
            import distro
            self.series = distro.codename()

        if test_name != 'setup':
            return

        self.install_required_pkgs()
        if self.series not in ['precise', 'trusty', 'xenial']:
            os.chdir('/tmp')
            shutil.rmtree('lxc-pkg-ubuntu', ignore_errors=True)
            cmd = 'git clone --depth=1 https://github.com/lxc/lxc-pkg-ubuntu.git -b dpm-{}'.format(self.series)
            utils.system(cmd)
            os.chdir('/tmp/lxc-pkg-ubuntu')
            gcc_multiarch = utils.system_output('gcc -print-multiarch',  retain_output=False)
            utils.system('autoreconf -f -i')
            cmd = '--enable-tests --disable-rpath --disable-doc --with-distro=ubuntu \
                   --prefix=/usr --sysconfdir=/etc --localstatedir=/var \
                   --libdir=\${{prefix}}/lib/{0} \
                   --libexecdir=\${{prefix}}/lib/{0} \
                    --with-rootfs-path=\${{prefix}}/lib/{0}/lxc'.format(gcc_multiarch)
            utils.configure(cmd)
            try:
                nprocs = '-j' + str(multiprocessing.cpu_count())
            except:
                nprocs = ''
            utils.make(nprocs)

        # Override the GPG server
        fn = '/usr/share/lxc/templates/lxc-download'
        cmd = "grep -q 'DOWNLOAD_KEYSERVER=\"hkp://keyserver.ubuntu.com:80\"' {0} || sed -i '/^DOWNLOAD_URL=$/a DOWNLOAD_KEYSERVER=\"hkp://keyserver.ubuntu.com:80\"' {0}".format(fn)
        utils.system(cmd)

        # Workaround for broken gpg2
        if os.environ.get('http_proxy') and os.path.isfile('/usr/bin/dirmngr'):
            cmd = 'dpkg-divert --divert /usr/bin/dirmngr.orig --rename --add /usr/bin/dirmngr'
            utils.system(cmd)
            with open('/usr/bin/dirmngr', 'w') as f:
                f.write('#!/bin/sh\n')
                f.write('exec /usr/bin/dirmngr.orig --honor-http-proxy $@\n')
            cmd = 'chmod +x /usr/bin/dirmngr'
            utils.system(cmd)


    def run_once(self, test_name):
        if test_name == 'setup':
            return

        # Destroy the "reboot" container which might have been left
        # behind (LP#1788574)
        if test_name == 'lxc-test-api-reboot':
            cmd = 'lxc-destroy reboot &> /dev/null'
            utils.system(cmd, ignore_status=True)

        if self.series in ['precise', 'trusty', 'xenial']:
            fpath = '/usr/bin/'
        else:
            fpath = '/tmp/lxc-pkg-ubuntu/src/tests/'

        # Override the path for Python3 API test
        if test_name == 'api_test.py':
            fpath = 'python3 /usr/share/doc/python3-lxc/examples/'

        cmd = fpath + test_name
        utils.system_output(cmd, retain_output=True)

# vi:set ts=4 sw=4 expandtab syntax=python:
