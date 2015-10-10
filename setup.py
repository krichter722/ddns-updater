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
from  setuptools.command.install  import  install
<<<<<<< HEAD

git_default = "git"

def __app_version__(git=git_default, ):
    """Retrieves the version in form of a `StrictVersion` object from git by checking it HEAD is tagged and then returns the tag name or the output of `git describe --tags` otherwise. Uses `git` as git binary. See [PEP 386][1] for an overview over the quite smart attempt to deal with the version mess in this world - gently speaking.

    [1]:https://www.python.org/dev/peps/pep-0386/"""
    try:
        ret_value = parse_version(sp.check_output([git, "describe", "--tags", ], cwd=os.path.dirname(os.path.realpath(__file__))).strip())
        return ret_value
    except sp.CalledProcessError:
        ret_value = parse_version(sp.check_output([git, "describe", "--tags", "--long", ], cwd=os.path.dirname(os.path.realpath(__file__))).strip())
        return ret_value

from Cheetah.Template import Template
t = Template(file="strato_ddns_updater_globals.py.tmpl")
t.app_version = __app_version__()
t_file = open("strato_ddns_updater_globals.py", "w")
t_file.write(str(t))
t_file.flush()
t_file.close()

=======
>>>>>>> 57d1e130d6716b1f2034b030b9b52bbe56845c82
import strato_ddns_updater_globals

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

# binaries
systemctl = "systemctl"
adduser = "adduser"
addgroup = "addgroup"

systemd_unit_name = "strato-ddns-updater"
strato_ddns_updater_user = "strato-ddns-updater"
strato_ddns_updater_group = "strato-ddns-updater"

# @TODO: adjust to deal with setuptools options
systemd_service_file_path = "/lib/systemd/system/strato-ddns-updater.service"
config_file_dir_path = "/usr/local/strato-ddns-updater/etc/"
config_file_name = "strato-ddns-updater.conf"
config_file_path = os.path.join(config_file_dir_path, config_file_name)
log_file_dir_path = "/var/log/strato-ddns-updater"
log_file_path = os.path.join(log_file_dir_path, strato_ddns_updater_globals.log_file_name)

class SystemdServiceInstallCommand(Command):
    """setuptools Command"""
    description = "Create a systemd unit and necessary daemon system user and group"
    user_options = tuple()

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

class InstallOverwrite(install):
    def  run(self):
        install.run(self)
        create_default_config_file()
        # unclear how to initialize setuptools.Command (reported as https://bitbucket.org/pypa/setuptools/issues/423/document-setuptoolscommand__init__) -> use function
        systemd_service_install()

def create_default_config_file():
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.add_section("general")
    config.set('general', 'enabled', 'false')
    config.add_section('ddns')
    if not os.path.exists(config_file_dir_path):
        os.makedirs(config_file_dir_path)
    with open(config_file_path, 'wb') as configfile:
        config.write(configfile)

def systemd_service_install():
    sp.call([systemctl, "stop", systemd_unit_name]) # might fail if service doesn't exist
    from Cheetah.Template import Template
    t = Template(file="strato-ddns-updater.service.tmpl")
    t.systemd_unit_name = systemd_unit_name
    t.strato_ddns_updater_user = strato_ddns_updater_user
    t.strato_ddns_updater_group = strato_ddns_updater_group
    if os.getenv("STRATO_HOSTNAME") is None:
        raise ValueError("must specify STRATO_HOSTNAME environment variable") # workaround until configuration file works
    if os.getenv("STRATO_USERNAME") is None:
        raise ValueError("must specify STRATO_HOSTNAME environment variable") # workaround until configuration file works
    if os.getenv("STRATO_PASSWORD") is None:
        raise ValueError("must specify STRATO_PASSWORD environment variable") # workaround until configuration file works
    t.hostname = os.getenv("STRATO_HOSTNAME")
    t.username = os.getenv("STRATO_USERNAME")
    t.password = os.getenv("STRATO_PASSWORD")
    t_file = open(systemd_service_file_path, "w")
    t_file.write(str(t))
    t_file.flush()
    t_file.close()
    # pwd.getpwnam doesn't return a decent value if the user doesn't exist, but raises KeyError -> in order to express the condition in one line use a list aggreator
    if not strato_ddns_updater_user in [i.pw_name for i in pwd.getpwall()]:
        sp.check_call([adduser, "--system", strato_ddns_updater_user])
    if not strato_ddns_updater_group in [i.gr_name for i in grp.getgrall()]:
        sp.check_call([addgroup, "--system", strato_ddns_updater_group])
    if not os.path.exists(log_file_dir_path):
        os.makedirs(log_file_dir_path)
    os.chown(log_file_dir_path, pwd.getpwnam(strato_ddns_updater_user).pw_uid, grp.getgrnam(strato_ddns_updater_group).gr_gid)
    if os.path.exists(log_file_path):
        os.chown(log_file_path, pwd.getpwnam(strato_ddns_updater_user).pw_uid, grp.getgrnam(strato_ddns_updater_group).gr_gid)
    sp.check_call([systemctl, "daemon-reload"])
    sp.check_call([systemctl, "start", systemd_unit_name])

# create source files
from Cheetah.Template import Template
t = Template(file="strato_ddns_updater.py.tmpl")
t.log_file_dir_path = log_file_dir_path
t_file = open("strato_ddns_updater.py", "w")
t_file.write(str(t))
t_file.flush()
t_file.close()

setup(
    name = strato_ddns_updater_globals.app_name,
    version_command=('git describe --tags', "pep440-git-local"),
    packages = ["."],
    install_requires = ["cheetah", "plac>=0.9.1"],
    entry_points={
        'console_scripts': [
            '%s = strato_ddns_updater:main' % (strato_ddns_updater_globals.app_name, ),
        ],
    },
    cmdclass = {'systemd_service':SystemdServiceInstallCommand, 'install': InstallOverwrite},
    
    # metadata for upload to PyPI
    author = "Karl-Philipp Richter",
    author_email = "krichter722@aol.de",
    url='https://github.com/krichter722/strato-ddns-updater',
    description = "A python script which allows you to update your Dynamic DNS information for a strato domain",
    license = "GPLv3",
    keywords = "ddns"
)

