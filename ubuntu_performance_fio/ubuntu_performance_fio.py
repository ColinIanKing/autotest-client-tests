#
#
import os
import platform
import time
import re
from autotest.client import test, utils

file_size_mb=2048

class ubuntu_performance_fio(test.test):
    version = 0

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
            'libaio-dev',
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

        os.chdir(self.srcdir)
        self.results = utils.system_output('unxz < %s | tar xf - ' % os.path.join(self.bindir, 'fio-3.10.tar.xz'), retain_output=True)
        os.chdir(os.path.join(self.srcdir, 'fio-3.10'))
        self.results += utils.system_output('make', retain_output=True)

        print self.results

    def get_filesystem_free_mbytes(self):
        fd = os.open(self.bindir, os.O_RDONLY)
        statvfs = os.fstatvfs(fd)
        os.close(fd);
        return statvfs.f_bsize * statvfs.f_bavail / (1024.0 * 1024.0)


    def get_sysinfo(self):
        print
        print 'date_ctime "' + time.ctime() + '"'
        print 'date_ns %-30.0f' % (time.time() * 1000000000)
        print 'kernel_version ' + platform.uname()[2]
        print 'cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True)
        print 'cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True)
        print 'page_size ' + utils.system_output('getconf PAGE_SIZE', retain_output=True)
        print 'pages_availble ' + utils.system_output('getconf _AVPHYS_PAGES', retain_output=True)
        print 'pages_total ' + utils.system_output('getconf _PHYS_PAGES', retain_output=True)
        print 'free_disk_mb %.2f' % (self.get_filesystem_free_mbytes())
        print

    def print_stats(self, benchmark, results, fields):
        return

    def drop_cache(self):
        #
        #  Ensure cache won't affect test by dropping caches
        #  and ensuring data is sync'd
        #
        utils.system('sync')
        f = open("/proc/sys/vm/drop_caches", "w")
        f.write("3")
        f.close()

    def run_fio(self, testname):
        kb_scale = {
            "KiB":  1024.0 / 1000.0,
            "KB": 1000.0 / 1000.0,
            "MiB":  1024.0 * 1024.0 / 1000.0,
            "MB": 1000.0 * 1000.0 / 1000.0,
            "GiB":  1024.0 * 1024.0 * 1024.0 / 1000.0,
            "GB": 1000.0 * 1000.0 * 1000.0 / 1000.0,
        }

        usec_scale = {
            "(nsec)": 1.0 / 1000,
            "(usec)": 1.0,
            "(msec)": 1000.0,
            "(sec)" : 1000000.0,
        }

        #
        #  Edit various fio configs to use dynamic settings
        #  relevant to this test location and test size
        #
        file = testname + ".fio"
        fin = open(os.path.join(self.bindir, file), "r")
        fout = open(os.path.join(self.srcdir, file), "w")
        file_size = "%dM" % (file_size_mb)

        for line in fin:
            line = line.replace("DIRECTORY", self.srcdir)
            line = line.replace("SIZE", file_size)
            fout.write(line)
        fin.close()
        fout.close()

        self.drop_cache()

        #
        #  Run fio
        #
        cmd = os.path.join(self.srcdir, 'fio-3.10', 'fio') + " " + os.path.join(self.srcdir, file)
        results = utils.system_output(cmd, retain_output=True)
        bw = 0.0
        avg = 0.0
        stdev = 0.0

        #
        #  Extract pertinent factoids, bandwidth and latencies
        #
        for l in results.splitlines():
            for s in l.split():
                if s.startswith("BW="):
                    bw = float(re.findall(r"[-+]?\d*\.*\d+", s)[0])
                    for sc in kb_scale:
                        if sc in s:
                            bw = bw * kb_scale[sc]

            idx_avg = l.find("avg=")
            idx_stdev = l.find("stdev=")

            if " lat" in l and idx_avg > -1 and idx_stdev > -1:
                avg = float(re.findall("[-+]?\d*\.*\d+", l[idx_avg:])[0])
                stdev = float(re.findall("[-+]?\d*\.*\d+", l[idx_stdev:])[0])
                for sc in usec_scale:
                    if sc in l:
                        avg = avg * usec_scale[sc]

        testname = testname.replace("-","_")
        print
        print "%s_file_size_mb %s" % (testname, file_size_mb)
        print "%s_bandwidth_kb_per_sec %.2f" % (testname, bw)
        print "%s_latency_usec_average %.2f" % (testname, avg)
        print "%s_latency_stddev %.2f" % (testname, stdev)

    def run_once(self, test_name):
        if test_name == 'setup':
            self.setup()
            self.get_sysinfo()
            return

        #
        #  Drop cache to get a good idea of how much free memory can be used
        #
        self.drop_cache()
        page_size = float(utils.system_output('getconf PAGE_SIZE', retain_output=True))
        pages_available = float(utils.system_output('getconf _AVPHYS_PAGES', retain_output=True))
        mem_mb = page_size * pages_available / (1024.0 * 1024.0)

        if mem_mb > file_size_mb:
            print "\nWARNING: file size of %.2f MB should be at least twice the free memory size of %.2f MB" % (file_size_mb, mem_mb)

        free_mb = self.get_filesystem_free_mbytes()
        if free_mb > file_size_mb:
            self.run_fio(test_name)
        else:
            print 'cannot execute "%s", required %dMB, only got %dMB on disc' % (test_name, file_size_mb, free_mb)
        print


# vi:set ts=4 sw=4 expandtab syntax=python:
