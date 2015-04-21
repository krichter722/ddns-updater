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
)
def strato_ddns_updater(hostname, username, password, no_mx=False, base_url="https://dyndns.strato.com/nic/update"):
    dyndns_response = urllib2.urlopen("http://ipecho.net/plain").readline().strip()
    external_ip = dyndns_response

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

def main():
    plac.call(strato_ddns_updater)

if __name__ == "__main__":
    main()
