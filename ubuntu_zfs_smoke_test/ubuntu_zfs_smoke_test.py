#
#
import os
from autotest.client                        import test, utils
import platform

class ubuntu_zfs_smoke_test(test.test):
    version = 2

    def initialize(self):
	pass

    def setup(self):
        series = platform.dist()[2]

        pkgs = [ ]

        if series == 'xenial':
            pkgs.append('zfsutils-linux')
        elif series == 'wily':
            pkgs.append('zfs-dkms')
            pkgs.append('zfsutils-linux')
        else:
            utils.system_output('add-apt-repository ppa:zfs-native/stable -y', retain_output=True)
            utils.system_output('apt-get update || true', retain_output=True)
            pkgs.append('ubuntu-zfs')

        for pkg in pkgs:
                print "Installing package " + pkg
                utils.system_output('apt-get install ' + pkg + ' --yes --force-yes', retain_output=True)

        utils.system('modprobe zfs')


    def run_once(self, test_name):
	cmd = '%s/%s' % (self.bindir, test_name)
	self.results = utils.system_output(cmd, retain_output=True)
        #
        # FIXME: comment this out on production
        #
        print self.results

# vi:set ts=4 sw=4 expandtab syntax=python:
