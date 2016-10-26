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

# The fact that there's currently no support for reading from configuration file
# implies that the systemd setup is requires the file to be adjusted manually
# with the hostname, username and password arguments.

# @TODO: adjust everything to match with the setuptools handling of prefixes (including permissions of logging directories, etc.)

from setuptools import setup, find_packages, Command
from pkg_resources import parse_version
import os
import subprocess as sp
import logging
import pwd
import grp
from  setuptools.command.install  import  install as _install
import ddns_updater.ddns_updater_globals as ddns_updater_globals
import template_helper.template_helper as template_helper

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

# binaries
systemctl = "systemctl"
adduser = "adduser"
addgroup = "addgroup"

class SystemdServiceInstallCommand(Command):
    """setuptools Command"""
    description = "Create a systemd unit and necessary daemon system user and group"
    user_options = []

    def initialize_options(self):
        """init options"""
        pass

    def finalize_options(self):
        """finalize options"""
        pass

    def run(self):
        """runner"""
        logger.debug("running systemd service installation post-install hook")
        systemd_service_install()

def systemd_service_install():
    for name,user,group in [("strato","strato-ddns-updater","strato-ddns-updater"),
	("openafs","root","root") # has to be run as root in order to be able to create dummy interfaces
    ]:
        systemd_unit_name = "%s-ddns-updater" % (name,)

        # @TODO: adjust to deal with setuptools options
        systemd_service_file_path = "/lib/systemd/system/%s-ddns-updater.service" % (name,)
        config_file_dir_path = "/usr/local/%s-ddns-updater/etc/" % (name,)
        config_file_name = "%s-ddns-updater.conf" % (name,)
        config_file_path = os.path.join(config_file_dir_path, config_file_name)
        log_file_dir_path = "/var/log/%s-ddns-updater" % (name,)
        log_file_path = os.path.join(log_file_dir_path, ddns_updater_globals.log_file_name)

        sp.call([systemctl, "stop", systemd_unit_name]) # might fail if service doesn't exist
        from Cheetah.Template import Template
        t = Template(file="ddns-updater.service.tmpl")
        t.systemd_unit_name = systemd_unit_name
        t.app_name = ddns_updater_globals.app_name
        t.user = user
        t.group = group
        t.mode = name
        template_helper.write_template_file(str(t), systemd_service_file_path)
        logger.info("created systemd unit '%s'" % (systemd_service_file_path,))
        # pwd.getpwnam doesn't return a decent value if the user doesn't exist, but raises KeyError -> in order to express the condition in one line use a list aggreator
        if not user in [i.pw_name for i in pwd.getpwall()]:
            sp.check_call([adduser, "--system", user])
        if not group in [i.gr_name for i in grp.getgrall()]:
            sp.check_call([addgroup, "--system", group])
        if not os.path.exists(log_file_dir_path):
            os.makedirs(log_file_dir_path)
        os.chown(log_file_dir_path, pwd.getpwnam(user).pw_uid, grp.getgrnam(group).gr_gid)
        if os.path.exists(log_file_path):
            os.chown(log_file_path, pwd.getpwnam(user).pw_uid, grp.getgrnam(group).gr_gid)
        sp.check_call([systemctl, "daemon-reload"])
        sp.check_call([systemctl, "start", systemd_unit_name])

# create source files (use template helper in order to avoid overwriting changes)
from Cheetah.Template import Template
t = Template(file="ddns_updater/ddns_updater.py.tmpl")
t.log_file_dir_path = "/var/log"
template_helper.write_template_file(str(t), "ddns_updater/ddns_updater.py", check_output=True)

setup(
    name = ddns_updater_globals.app_name,
    version_command=('git describe --tags', "pep440-git-local"),
    packages = find_packages(),
    setup_requires = ["cheetah", "setuptools-version-command>=2.2", "template-helper"],
    install_requires = ["plac>=0.9.1"],
    entry_points={
        'console_scripts': [
            '%s = ddns_updater.ddns_updater:main' % (ddns_updater_globals.app_name, ),
        ],
    },
    cmdclass = {'systemd_service':SystemdServiceInstallCommand},

    # metadata for upload to PyPI
    author = "Karl-Philipp Richter",
    author_email = "krichter722@aol.de",
    url='https://github.com/krichter722/ddns-updater',
    description = "A python script which allows you to perform actions after a change of your DDNS IP has been detected",
    license = "GPLv3",
    keywords = "ddns"
)

