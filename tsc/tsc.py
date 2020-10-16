import os
import re
import logging
import platform
from autotest.client import test, utils
from autotest.client.shared import error


class tsc(test.test):
    version = 3

    preserve_srcdir = True

    def setup(self):
        self.install_required_pkgs()
        self.job.require_gcc()
        os.chdir(self.srcdir)
        utils.make()

    def install_required_pkgs(self):
        arch   = platform.processor()
        try:
            series = platform.dist()[2]
        except AttributeError:
            import distro
            series = distro.codename()

        pkgs = [
            'build-essential',
        ]
        gcc = 'gcc' if arch in ['ppc64le', 'aarch64', 's390x', 'riscv64'] else 'gcc-multilib'
        pkgs.append(gcc)

        cmd = 'yes "" | DEBIAN_FRONTEND=noninteractive apt-get install --yes --force-yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def run_once(self, args='-t 650'):
        result = utils.run(self.srcdir + '/checktsc ' + args,
                           stdout_tee=open(os.path.join(self.resultsdir,
                                                        'checktsc.log'), 'w'),
                           ignore_status=True)
        if result.exit_status != 0:
            logging.error('Program checktsc exit status is %s',
                          result.exit_status)
            default_reason = ("UNKNOWN FAILURE: rc=%d from %s" %
                              (result.exit_status, result.command))
            # Analyze result.stdout to see if it is possible to form qualified
            # reason of failure and to raise an appropriate exception.
            # For this test we qualify the reason of failure if the
            # following conditions are met:
            # (i) result.exit_status = 1
            # (ii) result.stdout ends with 'FAIL'
            # (iii) "FAIL" is preceded by one or more
            # lines in the following format:
            # CPU x - CPU y = <delta>
            # Set as a reason the line that contains max abs(delta)
            if result.exit_status == 1:
                if result.stdout.strip('\n').endswith('FAIL'):
                    # find all lines
                    # CPU x - CPU y = <delta>
                    # and parse out delta of max abs value
                    max_delta = 0
                    reason = ''
                    threshold = int(args.split()[1])
                    latencies = re.findall("CPU \d+ - CPU \d+ =\s+-*\d+",
                                           result.stdout)
                    for ln in latencies:
                        cur_delta = int(ln.split('=', 2)[1])
                        if abs(cur_delta) > max_delta:
                            max_delta = abs(cur_delta)
                            reason = ln
                    if max_delta > threshold:
                        reason = "Latency %s exceeds threshold %d" % (reason,
                                                                      threshold)
                        raise error.TestFail(reason)

            # If we are here, we failed to qualify the reason of test failre
            # Consider it as a test error
            raise error.TestError(default_reason)
