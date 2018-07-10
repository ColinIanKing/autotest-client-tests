import os
import re
import sys
import platform

from autotest.client import test
from autotest.client.shared import utils


class ipv6connect(test.test):
    version = 1

    preserve_srcdir = True

    def setup(self, src='ipv6connect.c'):
        self.install_required_pkgs()
        os.chdir(self.srcdir)
        utils.system('gcc ipv6connect.c -o ipv6connect -lpthread -static -s')

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
        self.job.require_gcc()
        self.results = []

    def run_once(self, dir=None, nprocs=None, args=''):
        (lower, upper) = utils.get_ip_local_port_range()
        utils.set_ip_local_port_range(4096, 65535)
        try:
            result = utils.run(os.path.join(self.srcdir, 'ipv6connect'),
                               None, False,
                               stdout_tee=sys.stdout, stderr_tee=sys.stderr)
        finally:
            utils.set_ip_local_port_range(lower, upper)
        self.results.append(result.stderr)

    def postprocess(self):
        pattern = re.compile(r'\nTotal time = ([0-9.]+)s\n')
        for duration in pattern.findall('\n'.join(self.results)):
            self.write_perf_keyval({'time': duration})
