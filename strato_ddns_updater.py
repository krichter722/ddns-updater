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

# There's currently no option to omit logging to file.
#
# Multiple invokations in a short range of time can cause the DDNS service
# (strato) to reject further update requests for a certain time. This is a
# mechanism by strato to prevent abuse. The caller is responsible to deal with
# this or use the built-in functions controlled by the settings
# `check_interval`, `loop` and `daemon`.

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
    check_interval=("The time in seconds between two checks of the current external IP (this is time your DDNS isn't reachable in the worst case) (don't set this value too low because the service to check for external IP (currently ipecho.net) might block you if you send too many requests)", "option"),
    loop=("Run as a loop with check_interval between runs (uses check_file to minimize requests to IP echo service)", "flag"),
    daemon=("Run as daemon (implies loop)", "flag"),
    log_dir=("The directory where to create log files (will be created if it doesn't exist) (expects permissions for creation and writing to be given)", "option"),
    debug=("Log debug information", "flag")
)
def strato_ddns_updater(hostname, username, password, no_mx=False, base_url="https://dyndns.strato.com/nic/update", check_file_path="/tmp/strato-ddns-updater.dat", check_interval=60*15, daemon=False, loop=False, log_dir="/var/log/strato-ddns-updater", debug=False):
    try:
        check_interval_float = float(check_interval)
    except ValueError:
        raise ValueError("check interval '%s' could not be parsed as float" % (str(check_interval), ))
    if not os.path.exists(log_dir):
        logger.info("creating inexisting log directory '%s'" % (log_dir,))
        os.makedirs(log_dir)
    elif os.path.isfile(log_dir):
        raise ValueError("log_dir '%s' is an existing file, but needs to be an existing directory or point to an inexisting path" % (log_dir,))
    logger_file_handler = logging.FileHandler(filename=os.path.join(log_dir, "strato-ddns-updater.log"), mode='a', encoding=None, delay=False)
    logger.addHandler(logger_file_handler)
    if debug:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)
        logger_file_handler.setLevel(logging.DEBUG)
    if daemon:
        loop = True
    # @return `True` if an actual request has been made, `False` if the stored last
    # result for the public IP query (in the check file) is identical to the current one (only run
    # if `use_check_file` is `True`).
    def __update__(use_check_file=loop):
        dyndns_response = urllib2.urlopen("http://ipecho.net/plain").readline().strip()
        external_ip = dyndns_response
        if use_check_file:
            # only check last result if loop is True (otherwise there's no last result stored anyway and sleeping doesn't make sense neither)
            if os.path.exists(check_file_path):
                check_file = open(check_file_path)
                last_external_ip = check_file.readline().strip()
                check_file.close()
                if last_external_ip == external_ip:
                    logger.debug("result of external IP check is identical to the last result, sleeping check interval (%s s)" % (str(check_interval_float),))
                    time.sleep(check_interval_float)
                    return False
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
        return True
    def __loop__():
        while True:
            # don't care about the return value of __update__ because it only
            # indicates whether a request has been made or not
            __update__()
    if not loop:
        __update__()
    else:
        if daemon:
            pid = os.fork()
            if pid == 0:
                __loop__()
            # don't care about parent
            os.exit(0)
        else:
            __loop__()

# necessary to allow setup of `setuptools` `entry_points`
def main():
    plac.call(strato_ddns_updater)

if __name__ == "__main__":
    try:
        main()
    except:
        logger.exception()
