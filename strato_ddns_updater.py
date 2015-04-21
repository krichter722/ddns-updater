#!/usr/bin/python
# -*- coding: utf-8 -*- 

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Dieses Programm ist Freie Software: Sie können es unter den Bedingungen
#    der GNU General Public License, wie von der Free Software Foundation,
#    Version 3 der Lizenz oder (nach Ihrer Wahl) jeder neueren
#    veröffentlichten Version, weiterverbreiten und/oder modifizieren.
#
#    Dieses Programm wird in der Hoffnung, dass es nützlich sein wird, aber
#    OHNE JEDE GEWÄHRLEISTUNG, bereitgestellt; sogar ohne die implizite
#    Gewährleistung der MARKTFÄHIGKEIT oder EIGNUNG FÜR EINEN BESTIMMTEN ZWECK.
#    Siehe die GNU General Public License für weitere Details.
#
#    Sie sollten eine Kopie der GNU General Public License zusammen mit diesem
#    Programm erhalten haben. Wenn nicht, siehe <http://www.gnu.org/licenses/>.

import plac
import urllib2
import base64
import logging
import time
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

@plac.annotations(hostname=("The DDNS hostname to be updated", "positional"),
    username=("The strato username", "positional"),
    password=("The strato DDNS password", "positional"),
    no_mx=("Setting MX entry is skipped if flag is set", "flag"),
    base_url=("Overwrite the base URL of the strato service", "option"),
    check_file_path=("Path to the file where the result of the last IP check is stored", "option"),
    check_interval=("The time in seconds between two checks of the current external IP (this is time your DDNS isn't reachable in the worst case) (don't set this value too low because the service to check for external IP (currently ipecho.net) might block you if you send too many requests)", "option")
)
def strato_ddns_updater(hostname, username, password, no_mx=False, base_url="https://dyndns.strato.com/nic/update", check_file_path="/tmp/strato-ddns-updater.dat", check_interval=60*15):
    try:
        check_interval_float = float(check_interval)
    except ValueError:
        raise ValueError("check interval '%s' could not be parsed as float" % (str(check_interval), ))
    while True:
        dyndns_response = urllib2.urlopen("http://ipecho.net/plain").readline().strip()
        external_ip = dyndns_response
        if os.path.exists(check_file_path):
            check_file = open(check_file_path)
            last_external_ip = check_file.readline().strip()
            if last_external_ip == external_ip:
                time.sleep(check_interval_float)
                continue
            check_file.close()
        check_file = open(check_file_path, "w")
        check_file.write(external_ip)
        check_file.flush()
        check_file.close()

        # Create an OpenerDirector with support for Basic HTTP Authentication...
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm='strato DDSN updater',
                                  uri=base_url,
                                  user=username,
                                  passwd=password)
        opener = urllib2.build_opener(auth_handler)
        # ...and install it globally so it can be used with urlopen.
        urllib2.install_opener(opener)

        if no_mx is False:
            mx_str = "&mx=%s" % (hostname, )
        else:
            mx_str = ""

        request = urllib2.Request("%s?hostname=%s%s&myip=%s&mxback=NO" % (base_url, hostname, mx_str, external_ip, ))
        # You need the replace to handle encodestring adding a trailing newline
        # (https://docs.python.org/2/library/base64.html#base64.encodestring)
        base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        result = urllib2.urlopen(request).readline().strip()
        logger.info("strato update site returned '%s'" % (result, ))
        if not result.startswith("good "):
            raise Error("request failed because response doesn't start with 'good'")

# necessary to allow setup of `setuptools` `entry_points`
def main():
    plac.call(strato_ddns_updater)

if __name__ == "__main__":
    main()
