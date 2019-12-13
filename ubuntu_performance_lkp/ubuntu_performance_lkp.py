#
#
import os
from autotest.client import test, utils
from math import sqrt
import platform
import time
import json
import socket
import subprocess
import resource

#
# Number of test iterations to get min/max/average stats
#
test_iterations = 3
commit='7078336702a53c99f3a17ad1ca2af9a3323a818c'

class ubuntu_performance_lkp(test.test):
    version = 7

    systemd_services = [
        "smartd.service",
        "iscsid.service",
        "apport.service",
        "cron.service",
        "anacron.timer",
        "apt-daily.timer",
        "apt-daily-upgrade.timer",
        "fstrim.timer",
        "logrotate.timer",
        "motd-news.timer",
        "man-db.timer",
    ]
    systemctl = "systemctl"

    def stop_services(self):
        stopped_services = []
        for service in self.systemd_services:
            cmd = "%s is-active --quiet %s" % (self.systemctl, service)
            result = subprocess.Popen(cmd, shell=True)
            result.communicate()
            if result.returncode == 0:
                cmd = "%s stop %s" % (self.systemctl, service)
                result = subprocess.Popen(cmd, shell=True)
                result.communicate()
                if result.returncode == 0:
                    stopped_services.append(service)
                else:
                    print "WARNING: could not stop %s" % (service)
        return stopped_services

    def start_services(self, services):
        for service in services:
            cmd = "%s start %s" % (self.systemctl, service)
            result = subprocess.Popen(cmd, shell=True)
            result.communicate()
            if result.returncode != 0:
                print "WARNING: could not start %s" % (service)

    def set_rlimit_nofile(self, newres):
        oldres = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, newres)
        return oldres

    def restore_rlimit_nofile(self, res):
        resource.setrlimit(resource.RLIMIT_NOFILE, res)

    def is_number(self, s):
        try:
            f = float(s)
            return True
        except:
            return False

    def install_required_pkgs(self):
        arch   = platform.processor()
        series = platform.dist()[2]

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('5.5.5.5', 1))
            ipaddr = s.getsockname()[0]
        except:
            ipaddr = '127.0.0.1'
        finally:
            s.close()
        return ipaddr

    def setup(self, lkp_jobs):
        self.install_required_pkgs()
        self.job.require_gcc()

        if "192.168." not in self.get_ip():
            os.environ["https_proxy"] = "http://squid.internal:3128"
            os.environ["http_proxy"] = "http://squid.internal:3128"

        utils.system_output('apt-get install --yes --force-yes git', retain_output=True)

        os.chdir(self.srcdir)

        if not os.path.isdir("lkp-tests"):
            self.results += utils.system_output('git clone https://github.com/intel/lkp-tests', retain_output=True)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            self.results += utils.system_output('git checkout -b stable ' + commit, retain_output=True)
            #
            # New distros use libarchive-tools and not bsdtar so edit the package name
            # https://github.com/intel/lkp-tests/issues/50
            #
            self.results += utils.system_output('find distro -type f -exec sed -i "s/bsdtar/libarchive-tools/" {} \;')

        utils.system_output('make install', retain_output=True)
        utils.system_output('yes "" | lkp install', retain_output=True)

        for lkp_job in lkp_jobs:
            print "setting up " + lkp_job
            print utils.system_output('yes "" | lkp install jobs/%s || true' % lkp_job, retain_output=True)
            print utils.system_output('lkp split jobs/%s || true' % lkp_job, retain_output=True)

    def run_aim9(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, find ops/sec in fields as follows:
            #
            # ------------------------------------------------------------------------------------------------------------
            #   Test        Test        Elapsed  Iteration    Iteration          Operation
            #  Number       Name      Time (sec)   Count   Rate (loops/sec)    Rate (ops/sec)
            #  ------------------------------------------------------------------------------------------------------------
            #       1 brk_test           300.00      42763  142.54333      2423236.67 System Memory Allocations/second
            # ------------------------------------------------------------------------------------------------------------
            found_dashes = False;
            for line in self.results.splitlines():
                print line
                chunks = line.split()
                if len(chunks) > 0 and '---------' in chunks[0]:
                    found_dashes = True;
                elif found_dashes and len(chunks) > 5 and chunks[0] == '1' and self.is_number(chunks[5]):
                    values.append(float(chunks[5]))
                    found_dashes = False

        print "%s_bogoops" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('bogoops', values) ]

    def run_cassandra(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, find ops/sec in fields as follows:
            #
            # Row rate                  :   21,376 row/s [insert: 15,345 row/s, simple1: 6,031 row/s]
            #
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) >= 4 and chunks[0] == "Row" and chunks[1] == "rate" \
                   and chunks[2] == ':':
                    val = chunks[3].replace(",", "")
                    if (self.is_number(val)):
                        values.append(float(val))

        print "%s_rows_per_second" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('rows_per_sec', values) ]

    def run_dbench(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, find throughput in fields as follows:
            #
            # Throughput 1154.73 MB/sec  4 clients  4 procs  max_latency=2606.696 ms
            #
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) >= 3 and chunks[0] == "Throughput" and chunks[2] == "MB/sec" \
                   and self.is_number(chunks[1]):
                    values.append(float(chunks[1]))

        print "%s_throughput_mb_per_second" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('throughput', values) ]

    def run_hackbench(self, lkp_job, lkp_jobs, test_name):
        values = []
        print "Testing %s: 1 of 1" % lkp_job
        os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
        cmd = 'sudo lkp run %s' % lkp_job
        self.results = utils.system_output(cmd, retain_output=True)
        #
        # parse text, find Time: fields in multiple repeats of results such as:
        #
        # 2018-12-18 10:57:33 /usr/bin/hackbench -g 32 --process threads -l 3750
        # Running in process mode with 32 groups using 40 file descriptors each (== 1280 tasks)
        # Each sender will pass 3750 messages of 100 bytes
        # Time: 29.915
        #
        for line in self.results.splitlines():
            chunks = line.split()
            if len(chunks) == 2 and chunks[0] == "Time:":
                values.append(float(chunks[1]))

        print "%s_seconds" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('duration', values) ]

    def run_iperf(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            idx1 = self.results.find("{")
            idx2 = self.results.rfind("}")

            intervals = []
            if idx1 > -1 and idx2 > 0:
                data = self.results[idx1:idx2+1]
                j = json.loads(data)
                n = len(j['intervals'])
                for i in range(n):
                    intervals.append(float(j['intervals'][i]['sum']['bits_per_second']))

            values.append(sum(intervals) / len(intervals))

        #print "%s_bits_per_second_second" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('bitrate', values) ]

    def run_linpack(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # Allow CPU to cool before next try
            #
            time.sleep(45)
            #
            # parse text, find ops/sec in fields as follows:
            #
            # Maximum memory requested that can be used=1449646096, at the size=13460
            # 
            # =================== Timing linear equation system solver ===================
            # 
            # Size   LDA    Align. Time(s)    GFlops   Residual     Residual(norm) Check
            # 13460  13460  4      9.851      165.0621 1.255759e-10 2.452756e-02   pass
            # 
            # Performance Summary (GFlops)
            # 
            # Size   LDA    Align.  Average  Maximal
            # 13460  13460  4       165.0621 165.0621
            # 
            # Residual checks PASSED
            #
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) == 8 and chunks[7] == "pass" and self.is_number(chunks[0]) \
                   and self.is_number(chunks[1]) and self.is_number(chunks[2]) \
                   and self.is_number(chunks[3]) and self.is_number(chunks[4]) \
                   and self.is_number(chunks[5]) and self.is_number(chunks[6]):
                    values.append(float(chunks[4]))


        print "%s_gflops" % (test_name), "%.4f " * len(values) % tuple(values)
        return [ ('gflops', values) ]

    def run_perf_bench_futex(self, lkp_job, lkp_jobs, test_name):
        values = []
        print "Testing %s: 1 of 1" % lkp_job
        os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
        cmd = 'sudo lkp run %s' % lkp_job
        self.results = utils.system_output(cmd, retain_output=True)

        #
        # parse text, find KB/s data in fields as follows:
        #
        # [thread  0] futexes: 0x56007a705030 ... 0x56007a70602c [ 2267037 ops/sec ]
        # [thread  1] futexes: 0x56007a706fe0 ... 0x56007a707fdc [ 2199947 ops/sec ]
        # [thread  2] futexes: 0x56007a707ff0 ... 0x56007a708fec [ 2166125 ops/sec ]
        # [thread  3] futexes: 0x56007a709000 ... 0x56007a709ffc [ 2194377 ops/sec ]
        #
        # or:
        #
        # [thread   0] futex: 0x555f99164140 [ 1866 ops/sec ]
        # [thread   1] futex: 0x555f99164140 [ 1866 ops/sec ]
        # [thread   2] futex: 0x555f99164140 [ 1866 ops/sec ]
        # [thread   3] futex: 0x555f99164140 [ 1866 ops/sec ]
        #
        for line in self.results.splitlines():
            chunks = line.split()
            if len(chunks) == 10 and chunks[0] == "[thread" and chunks[2] == "futexes:" \
               and chunks[8] == "ops/sec" and self.is_number(chunks[7]):
                values.append(float(chunks[7]))
            elif len(chunks) == 8 and chunks[0] == "[thread" and chunks[2] == "futex:" \
               and chunks[6] == "ops/sec" and self.is_number(chunks[5]):
                values.append(float(chunks[5]))

        print "%s_ops_per_sec" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('futex_rate', values) ]

    def run_pxz(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, find throughput in fields as follows:
            #
            # throughput: 25116233.198712446
            #
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) >= 2 and chunks[0] == "throughput:" and self.is_number(chunks[1]):
                    values.append(float(chunks[1]))

        print "%s_throughput" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('throughput', values) ]

    def run_schbench(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, we are interested in the 99th percentile:
            #
            # *99.0000th: 103296
            #
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) >= 2 and chunks[0] == "*99.0000th:" and self.is_number(chunks[1]):
                    values.append(float(chunks[1]))

        print "%s_99th_percentile" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('99th_percentile', values) ]

    def run_sockperf(self, lkp_job, lkp_jobs, test_name):
        filters = [
            ("subcommand under-load UDP",
              [ ("percentile 90.00", 5, "UDP-under-load-90%-percentile"),
                ("Summary: Latency", 4, "UDP-under-load-latency") ]),
            ("subcommand under-load TCP",
              [ ("percentile 90.00", 5, "TCP-under-load-90%-percentile"),
                ("Summary: Latency", 4, "TCP-under-load-latency") ]),
            ("subcommand ping-pong UDP",
              [ ("percentile 90.00", 5, "UDP-ping-pong-90%-percentile"),
                ("Summary: Latency", 4, "UDP-ping-pong-latency") ]),
            ("subcommand ping-pong TCP",
              [ ("percentile 90.00", 5, "TCP-ping-pong-90%-percentile"),
                ("Summary: Latency", 4, "TCP-ping-pong-latency") ]),
            ("subcommand throughput UDP",
              [ ("Summary: Message Rate", 5, "UDP-throughput-rate"),
                ("Summary: BandWidth", 4, "UDP-bandwidth") ]),
            ("subcommand throughput TCP",
              [ ("Summary: Message Rate", 5, "TCP-throughput-rate"),
                ("Summary: BandWidth", 4, "TCP-bandwidth") ]),
        ]

        data = {}
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            metrics = []
            for line in self.results.splitlines():
                for filter in filters:
                    if filter[0] in line:
                        metrics = filter[1]
                        break

                chunks = line.split()
                for metric in metrics:
                    if metric[0] in line and len(chunks) >= metric[1] and self.is_number(chunks[metric[1]]):
                        label = metric[2]
                        if label not in data:
                            data[label] = []
                        data[label].append(float(chunks[metric[1]]))

        values = []
        for d in data:
            values.append((d, data[d]))

        return values

    def run_sysbench_threads(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, we are interested in the 95th percentile:
            #
            # 95th percentile:                        0.45
            #
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) >= 3 and chunks[0] == "95th" and self.is_number(chunks[2]):
                    values.append(float(chunks[2]))

        print "%s_95th_percentile" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('95th_percentile', values) ]

    def run_thrulay(self, lkp_job, lkp_jobs, test_name):
        values_throughput = []
        values_latency = []
        print "Testing %s: 1 of 1" % (lkp_job)
        os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
        cmd = 'sudo lkp run %s' % lkp_job
        self.results = utils.system_output(cmd, retain_output=True)

        #
        # parse text, find throughput in fields as follows:
        #
        # ( 0)  249.000  250.000 59896.294    0.068    0.004
        #
        for line in self.results.splitlines():
            chunks = line.split()
            if len(chunks) == 7 and chunks[0] == "(" and chunks[1] == "0)" and \
               self.is_number(chunks[4]) and self.is_number(chunks[5]):
                values_throughput.append(float(chunks[4]))
                values_latency.append(float(chunks[5]))

        #print "%s_throughput" % (test_name), "%.3f " * len(values_throughput) % tuple(values_throughput)
        #print "%s_latency" % (test_name), "%.3f " * len(values_latency) % tuple(values_latency)
        return [ ('throughput', values_throughput), ('latency', values_latency) ]

    def run_ebizzy(self, lkp_job, lkp_jobs, test_name):
        values = []
        print "Testing %s: 1 of 1" % lkp_job
        os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
        cmd = 'sudo lkp run %s' % lkp_job
        self.results = utils.system_output(cmd, retain_output=True)

        #
        # parse text, find KB/s data in fields as follows:
        #
        # 46348 records/s 5652 5731 6011 5844 5852 5640 6055 5560
        #
        for line in self.results.splitlines():
            chunks = line.split()
            if len(chunks) >= 2 and chunks[1] == "records/s" and self.is_number(chunks[0]):
                values.append(float(chunks[0]))

        print "%s_records_per_sec" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('record_rate', values) ]

    def run_unixbench(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, find index score in fields as follows:
            #
            # System Benchmarks Index Score (Partial Only)                          275.3
            #
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) == 7 and chunks[0] == "System" and chunks[1] == "Benchmarks" and \
                   chunks[2] == "Index" and chunks[3] == "Score" and chunks[4] == "(Partial" and \
                   chunks[5] == "Only)" and self.is_number(chunks[6]):
                    values.append(float(chunks[6]))

        print "%s_score" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('score', values) ]

    def run_vm_scalability(self, lkp_job, lkp_jobs, test_name):
        values = []
        for i in range(test_iterations):
            print "Testing %s: %d of %d" % (lkp_job, i + 1, test_iterations)
            os.chdir(os.path.join(self.srcdir, 'lkp-tests'))
            cmd = 'sudo lkp run %s' % lkp_job
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # parse text, find KB/s data in fields as follows:
            #
            # 53614772232 bytes / 300627955 usecs = 174162 KB/s
            # 53358395400 bytes / 300632043 usecs = 173327 KB/s
            # 56508841992 bytes / 300632313 usecs = 183561 KB/s
            # 56203182088 bytes / 300632709 usecs = 182568 KB/s
            #
            for line in self.results.splitlines():
                chunks = line.split()
                if len(chunks) >= 8 and chunks[1] == "bytes" and chunks[4] == "usecs" and chunks[7] == "KB/s":
                    values.append(float(chunks[6]))

        print "%s_kb_per_sec" % (test_name), "%.3f " * len(values) % tuple(values)
        return [ ('rate', values) ]

    def get_sysinfo(self):
        print 'date_ctime "' + time.ctime() + '"'
        print 'date_ns %-30.0f' % (time.time() * 1000000000)
        print 'kernel_version ' + platform.uname()[2]
        print 'hostname ' + platform.node()
        print 'virtualization ' + utils.system_output('systemd-detect-virt || true', retain_output=True)
        print 'cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True)
        print 'cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True)
        print 'page_size ' + utils.system_output('getconf PAGE_SIZE', retain_output=True)
        print 'pages_available ' + utils.system_output('getconf _AVPHYS_PAGES', retain_output=True)
        print 'pages_total ' + utils.system_output('getconf _PHYS_PAGES', retain_output=True)

    def run_once(self, lkp_job, sub_job, lkp_jobs):
        if lkp_job == 'setup':
            self.get_sysinfo()
            self.setup(lkp_jobs)
            return

        job_funcs = {
            'aim9.yaml':             self.run_aim9,
            'cassandra.yaml':        self.run_cassandra,
            'dbench.yaml':           self.run_dbench,
            'ebizzy.yaml':           self.run_ebizzy,
            'hackbench.yaml':        self.run_hackbench,
            'iperf.yaml':            self.run_iperf,
            'linpack.yaml':          self.run_linpack,
            'perf-bench-futex.yaml': self.run_perf_bench_futex,
            'pxz.yaml':              self.run_pxz,
            'schbench.yaml':         self.run_schbench,
            'sockperf.yaml':         self.run_sockperf,
            'sysbench-threads.yaml': self.run_sysbench_threads,
            'thrulay.yaml':          self.run_thrulay,
            'unixbench.yaml':        self.run_unixbench,
            'vm-scalability.yaml':   self.run_vm_scalability,
        }

        test_name = sub_job
        test_name = test_name.replace("-", "_").replace(".yaml", "")
        test_pass = True
        test_run  = False

        print
        if lkp_job in job_funcs:
            self.stopped_services = self.stop_services()
            self.oldres = self.set_rlimit_nofile((500000, 500000))

            ret_values = job_funcs[lkp_job](sub_job, lkp_jobs, test_name)

            self.set_rlimit_nofile(self.oldres)
            self.start_services(self.stopped_services)
        else:
            print "Cannot find running/parser for %s, please fix ubuntu_performance_lkp.py" % lkp_job
            return

        for (label, values) in ret_values:
            if len(values) == 0:
                    continue
            minimum = min(values)
            maximum = max(values)
            average = sum(values) / len(values)
            max_err = (maximum - minimum) / average * 100.0 if average > 0 else 0.0

            test_run = True

            if len(values) > 1:
                stddev = sqrt(float(reduce(lambda x, y: x + y, map(lambda x: (x - average) ** 2, values))) / (len(values) - 1))
            else:
                stddev = 0.0
            percent_stddev = (stddev / average) * 100.0 if average > 0 else 0.0
            print "%s_%s_minimum %.3f" % (test_name, label, minimum)
            print "%s_%s_maximum %.3f" % (test_name, label, maximum)
            print "%s_%s_average %.3f" % (test_name, label, average)
            print "%s_%s_maximum_error %.3f%%" % (test_name, label, max_err)
            print "%s_%s_stddev %.3f" % (test_name, label, stddev)
            print "%s_%s_percent_stddev %.3f" % (test_name, label, percent_stddev)

            if max_err > 5.0:
                print "FAIL: maximum error is greater than 5%"
                test_pass = False

        if test_run:
            if test_pass:
                print "PASS: test passes specified performance thresholds"
                print
        else:
                print "NOTRUN: test not run on this sytem"
                print

# vi:set ts=4 sw=4 expandtab syntax=python:
