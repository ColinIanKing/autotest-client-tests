#
#
import logging, os
from time                                   import sleep
from urllib2                                import urlopen, URLError
import hashlib

from autotest.client                        import test
from autotest.client.shared                 import error
from autotest.client.ubuntu.network_manager import NetworkManager

class ubuntu_WiFi_SimpleConnection(test.test):
    version = 1

    def initialize(self):
        pass

    def start_authserver(self):
        # We want to be able to get to the real internet.
        pass

    def establish_connection(self, ssid, wpapsk):
        retval = False

        nm = NetworkManager()

        # If already connected to the specified ssid and the wireless device
        # has an IP address, we are good.
        #
        if nm.active_wifi_device_ip() is None:
            # If we don't have an IP address, try to hook up.
            #

            #------------------------------------------------------------------------------------------
            # Create/add a new wifi connection
            #
            condef = {
                'connection' : {
                    'type' : '802-11-wireless',
                    'id'   : ssid,
                },
                '802-11-wireless' : {
                    'ssid' : ssid,
                    'security' : '802-11-wireless-security',
                },
                '802-11-wireless-security' : {
                    'key-mgmt' : 'wpa-psk',
                    'psk' : wpapsk,
                },
                'ipv4' : {
                    'method' : 'auto',
                },
                'ipv6' : {
                    'method' : 'ignore',
                },
            }
            nm.create_wifi_connection(condef)
            nm.activate_wifi_connection(ssid)

            # Sleep for a bit to see if we can get an IP address
            #
            sleep(10)

            # If we still don't have an ip address, give up.
            #
            if nm.active_wifi_device_ip() is None:
                raise error.TestError('Failed to obtain an IP address after creating a new connection definition.')

        retval = True

        return retval

    def run_once(self, ssid=None, wpapsk='', test_time=10, exit_on_error=True, set_time=True):
        if not self.establish_connection(ssid, wpapsk):
            raise error.TestError('Unable to associate with an access point and obtain an IP address.')

        url = 'http://people.canonical.com/~bradf/1MB'
        actual_md5  = 'acf8d75153dd3e5965969cb593c6efef'  # This md5 obviously only works for the above file

        try:
            response = urlopen(url)
            content = response.read()

            content_md5 = hashlib.md5(content).hexdigest()
            if content_md5 != actual_md5:
                raise error.TestError('Unable to download the test file, the md5 sums do not match.')

        except URLError as e:
            raise error.TestErrror(e.reason)

# vi:set ts=4 sw=4 expandtab syntax=python:
