#
#
import os
import platform
import time
from autotest.client import test, utils

stream_iterations = 50

class ubuntu_performance_stream(test.test):
    version = 0

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'unzip',
            'gfortran',
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
        stream_10M = os.path.join(self.bindir, 'stream_10m')
        stream_100M = os.path.join(self.bindir, 'stream_100m')

        utils.system('cp %s/master.zip %s' % (self.bindir, self.srcdir))
        os.chdir(self.srcdir)
        utils.system('unzip %s/master.zip' % self.srcdir)
        utils.system('ls %s' % self.srcdir)
        master_path = os.path.join(self.srcdir, 'STREAM-master')

        os.chdir(master_path)

        utils.system('make clean')
        cmd = 'make CC=gcc FC=gfortran CFLAGS="-DSTREAM_ARRAY_SIZE=10000000 -DNTIMES=%d -mcmodel=large"' % stream_iterations
        self.results = utils.system_output(cmd, retain_output=True)
        utils.system('cp %s %s' % (os.path.join(master_path, 'stream_c.exe'), stream_10M))

        utils.system('make clean')
        cmd = 'make CC=gcc FC=gfortran CFLAGS="-DSTREAM_ARRAY_SIZE=100000000 -DNTIMES=%d -mcmodel=large"' % stream_iterations
        self.results = utils.system_output(cmd, retain_output=True)
        utils.system('cp %s %s' % (os.path.join(master_path, 'stream_c.exe'), stream_100M))

        os.chdir(self.srcdir)
        utils.system_output('rm -f /etc/*/S99autotest || true', retain_output=True)

    def run_stream(self, stream_exe, size):
        cmd = os.path.join(self.bindir, stream_exe)
        results = utils.system_output(cmd, retain_output=True)

        fields = [ 'Copy', 'Scale', 'Add', 'Triad' ]
        values = {}

        for line in results.splitlines():
            chunks = line.split()
            if len(chunks) > 2:
                for field in fields:
                    if chunks[0] == field + ':':
                        values[field] = chunks[2]

        for field in fields:
            print field.lower() + '_average_' + size, values[field]

    def get_sysinfo(self):
        print 'date_ctime "' + time.ctime() + '"'
        print 'date_ns %-30.0f' % (time.time() * 1000000000)
        print 'kernel_version ' + platform.uname()[2]
        print 'cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True)
        print 'cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True)
        print 'page_size ' + utils.system_output('getconf PAGE_SIZE', retain_output=True)
        print 'pages_availble ' + utils.system_output('getconf _AVPHYS_PAGES', retain_output=True)
        print 'pages_total ' + utils.system_output('getconf _PHYS_PAGES', retain_output=True)
        print 'stream_iterations %d' % stream_iterations

    def run_once(self, test_name):
        if test_name == 'setup':
            return

        print
        self.get_sysinfo()
        print
        self.run_stream('stream_10m', '10m')
        print
        self.run_stream('stream_100m', '100m')
        print

# vi:set ts=4 sw=4 expandtab syntax=python:
