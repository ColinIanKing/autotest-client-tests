#
#
from autotest.client                        import test, utils
from autotest.client.shared                 import error

class ubuntu_sysdig_smoke_test(test.test):
    version = 99

    def install_required_pkgs(self):
        pkgs = [
            'sysdig', 'sysdig-dkms'
        ]

        cmd = 'apt-get install --yes ' + ' '.join(pkgs)
        self.results = utils.system_output(cmd, retain_output=True)

    def initialize(self):
        pass

    def setup(self):
        self.install_required_pkgs()
        cmd = 'dkms status -m sysdig | grep installed'
        try:
            utils.system(cmd)
        except error.CmdError:
            cmd = 'cat /var/lib/dkms/sysdig/*/build/make.log'
            utils.system(cmd)
            raise error.TestError('DKMS failed to install')

    def run_once(self, test_name):
        cmd = '%s/ubuntu_sysdig_smoke_test.sh' % (self.bindir)
        self.results = utils.system_output(cmd, retain_output=True)
        print(self.results)

    def cleanup(self):
        cmd = 'modprobe -r sysdig_probe || true'
        self.results = utils.system_output(cmd, retain_output=False)
        cmd = 'apt-get remove --purge sysdig-dkms -y'
        self.results = utils.system_output(cmd, retain_output=False)


# vi:set ts=4 sw=4 expandtab syntax=python:
