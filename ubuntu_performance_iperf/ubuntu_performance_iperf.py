#
#
import os
import platform
import time
import subprocess
import resource
from autotest.client import test, utils
from autotest.client.shared import error

#
# Number of test iterations to get min/max/average stats
#
test_iterations = 3

username = 'ubuntu'
#
# Temp hack for local testing
#
#os.environ['TEST_SERVER'] = 'mahobay.local'
#username = 'cking'

#
# Port range to exercise, 8 ports, from 5001 .. 5701
#
port_start=5001
port_step=100

class ubuntu_performance_iperf(test.test):
    version = 1
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
                    print "stopped service %s" % (service)
                else:
                    print "WARNING: could not stop %s" % (service)
        return stopped_services

    def start_services(self, services):
        for service in services:
            cmd = "%s start %s" % (self.systemctl, service)
            result = subprocess.Popen(cmd, shell=True)
            result.communicate()
            if result.returncode == 0:
                print "restarted service %s" % (service)
            else:
                print "WARNING: could not start %s" % (service)

    def set_rlimit_nofile(self, newres):
        oldres = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, newres)
        return oldres

    def restore_rlimit_nofile(self, res):
        resource.setrlimit(resource.RLIMIT_NOFILE, res)

    def set_cpu_governor(self, mode):
        cmd = "/usr/bin/cpupower frequency-set -g " + mode + " > /dev/null"
        result = subprocess.Popen(cmd, shell=True, stdout=None, stderr=None)
        result.communicate()
        if result.returncode != 0:
            print "WARNING: could not set CPUs to performance mode '%s'" % mode

    def set_swap_on(self, swap_on):
        cmd = "/sbin/swapon -a" if swap_on else "/sbin/swapoff -a"
        result = subprocess.Popen(cmd, shell=True, stdout=None, stderr=None)
        result.communicate()
        if result.returncode != 0:
            print "WARNING: could not set swap %s" % ("on" if swap_on else "off")

    def initialize(self):
        pass

    def get_setting(self, name):
        addr = os.environ.get(name)
        print "%s: %s" % (name, addr)
        if addr == None:
            raise error.TestError("ERROR: Environment variable '" + name +"' is not set")

        return addr

    #
    #  Get local inteface name and speed, assumes it's on 192.168.*.*
    #
    def get_interface_info(self):
        cmd = "/sbin/ip -o -br addr"
        result = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=None)
        out, err = result.communicate()

        interface=""
        for line in out.splitlines():
             words = line.split()
             if len(words) < 4:
                 continue
             if words[1] != 'UP':
                 continue
             if words[2].find("192.168.") != -1:
                 interface = words[0]
                 break

        if interface == "":
            raise error.TestError("ERROR: Interface and device bitrate not found")
            return ("NONE", 0)

        cmd = "/sbin/ethtool " + interface
        result = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=None)
        out, err = result.communicate()

        megabit_rates = [ ("Mb", 1), ("Gb", 1000) ]
        rate = -1.0
        for line in out.splitlines():
             words = line.split()
             if len(words) < 2:
                 continue
             if words[0] == "Speed:":
                 for r in megabit_rates:
                     n = words[1].find(r[0])
                     if n != -1:
                         rate = float(words[1][:n]) * r[1]

        if rate < 0.0:
            raise error.TestError("ERROR: Interface " + interface + " bitrate not found")
            return ("NONE", 0)

        print "Interface %s bitrate: %f Mb/sec" % (interface, rate)
        return (interface, rate)

    def setup(self):
        test_server = self.get_setting('TEST_SERVER')
        release = platform.release()

        pkgs = [
            'iperf3',
            'linux-tools-generic',
            'linux-tools-' + release
        ]
        cmd = 'apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

        cmd = "su " + username + " -c 'ssh " + username + "@" + test_server
        cmd += " sudo apt-get install --yes --force-yes " + " ".join(pkgs) + "'"
        self.results = utils.system_output(cmd, retain_output=True)

    def get_stats(self, results, fields):
        values = {}
        for line in results.splitlines():
            chunks = line.split()
            if len(chunks) > 2:
                for field in fields:
                    if chunks[0] == field + ':':
                        values[field] = chunks[2]
        return values

    def run_iperf_tcp(self, direction, interface, rate, clients):
        fields = [ 'sender_rate', 'receiver_rate' ]
        values = {}
        test_pass = True
        megabit_rates = [ ("Mbits", 1), ("Gbits", 1000) ]

        test_server = self.get_setting('TEST_SERVER')

        cmd = "su " + username + " -c 'ssh " + username + "@" + test_server
        cmd += " sudo /usr/bin/cpupower frequency-set -g performance'"
        utils.system_output(cmd, retain_output=True)

        if 'TEST_CONFIG' in os.environ:
            config = '_' + os.environ['TEST_CONFIG']
        else:
            config = ''

        for i in range(test_iterations):
            print "Test %d of %d:" % (i + 1, test_iterations)
            print "  Starting %d iperf3 instances on %s" % (clients, test_server)
            port_end = port_start + (port_step * clients)
            for port in xrange(port_start, port_end, port_step):
                cmd = "su " + username + " -c 'ssh " + username + "@" + test_server
                cmd += " nohup iperf3 -i 60 -D -s -p " + str(port) + "'"

                utils.system_output(cmd, retain_output=True)
            results = ""
            values[i] = self.get_stats(results, fields)

            proc = {}
            for port in xrange(port_start, port_end, port_step):
                cmd = "/usr/bin/iperf3 -t 60 -c %s -p %d -l256K -Z" % (test_server, port)
                if direction == 'reverse':
                    cmd += " -R"
                filename = "/tmp/port-%d.txt" % port
                if os.path.isfile(filename):
                    os.remove(filename)
                p = subprocess.Popen(cmd.split(), stdout=file(filename, "ab"))
                proc[port] = (p, filename)

            print "  Waiting for iperf3 to complete"
            for port in xrange(port_start, port_end, port_step):
                if proc[port][0].wait() > 0:
                    proc[port][0].wait()

            print "  Terminating iperf3 instances on %s" % test_server
            cmd = "su " + username + " -c 'ssh " + username + "@" + test_server
            cmd += " killall -9 iperf3'"
            self.results = utils.system_output(cmd, retain_output=True)

            #
            # 10:53:01 INFO | [ ID] Interval           Transfer     Bitrate         Retr
            # 10:53:01 INFO | [ 19]   0.00-10.00  sec   125 MBytes   105 Mbits/sec    0             sender
            # 10:53:01 INFO | [ 19]   0.00-10.00  sec   124 MBytes   104 Mbits/sec                  receiver
            #
            data = {}
            data['sender_rate'] = 0.0
            data['receiver_rate'] = 0.0

            for port in xrange(port_start, port_end, port_step):
                f = open(proc[port][1], "r")
                for line in f.readlines():
                    idx = line.find("]")
                    if idx == -1:
                        continue
                    words = line[idx + 1:].split()
                    if len(words) == 8 and words[7] == 'sender':
                        for r in megabit_rates:
                           n = words[5].find(r[0])
                           if n != -1:
                               data['sender_rate'] += (float(words[4]) * r[1])
                               break
                    if len(words) == 7 and words[6] == 'receiver':
                        for r in megabit_rates:
                           n = words[5].find(r[0])
                           if n != -1:
                               data['receiver_rate'] += (float(words[4]) * r[1])
                f.close()

            values[i] = data

        cmd = "su " + username + " -c 'ssh " + username + "@" + test_server
        cmd += " sudo /usr/bin/cpupower frequency-set -g powersave'"
        utils.system_output(cmd, retain_output=True)

        #
        #  Compute min/max/average:
        #
        print
        print "Collated Performance Metrics:"
        for field in fields:
            v = [ float(values[i][field]) for i in values ]
            maximum = max(v)
            minimum = min(v)
            average = sum(v) / float(len(v))
            max_err = (maximum - minimum) / average * 100.0

            print
            print "iperf3%s_clients%d_%s_%s_mbit_per_sec_minimum %.5f" % (config, clients, direction, field.lower(), minimum)
            print "iperf3%s_clients%d_%s_%s_mbit_per_sec_maximum %.5f" % (config, clients, direction, field.lower(), maximum)
            print "iperf3%s_clients%d_%s_%s_mbit_per_sec_average %.5f" % (config, clients, direction, field.lower(), average)
            print "iperf3%s_clients%d_%s_%s_mbit_per_sec_maximum_error %.2f%%" % (config, clients, direction, field.lower(), max_err)
            if max_err > 5.0:
                print "FAIL: maximum error is greater than 5%"
                test_pass = False

            threshold = rate * 0.90
            if average < threshold:
                print "FAIL: average bitrate of %.2f Mbit/sec is less than minimum threshold of %.2f Mbit/sec" % (average, threshold)
                test_pass = False
            else:
                print "bitrate of %.2f Mbit/sec is greater than minimum threshold of %.2f Mbit/sec" % (average, threshold)

        print
        if test_pass:
            print "PASS: test passes specified performance thresholds"

    def get_sysinfo(self):
        print 'date_ctime "' + time.ctime() + '"'
        print 'date_ns %-30.0f' % (time.time() * 1000000000)
        print 'kernel_version ' + platform.uname()[2]
        print 'hostname ' + platform.node()
        print 'virtualization ' + utils.system_output('systemd-detect-virt || true', retain_output=True)
        print 'cpus_online ' + utils.system_output('getconf _NPROCESSORS_ONLN', retain_output=True)
        print 'cpus_total ' + utils.system_output('getconf _NPROCESSORS_CONF', retain_output=True)
        return True

    def run_once(self, test_name, clients):
        if test_name == 'setup':
            return

        self.stopped_services = self.stop_services()
        self.oldres = self.set_rlimit_nofile((500000, 500000))
        self.set_cpu_governor('performance')
        self.set_swap_on(False)

        (interface, rate) = self.get_interface_info()

        self.run_iperf_tcp('forward', interface, rate, clients)
        self.run_iperf_tcp('reverse', interface, rate, clients)

        self.set_swap_on(True)
        self.set_cpu_governor('powersave')
        self.set_rlimit_nofile(self.oldres)
        self.start_services(self.stopped_services)
        print

# vi:set ts=4 sw=4 expandtab syntax=python:
