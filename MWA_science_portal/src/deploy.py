#
#    (c) University of Western Australia
#    International Centre of Radio Astronomy Research
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA,
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#

"""
Fabric file for installing NGAS portal servers

Test deployment on EC2 is simple as it only runs on one server
fab test_deploy

The tasks can be used individually and thus allow installations in very
diverse situations.

For a full deployment use the command

fab --set postfix=False -f machine-setup/deploy.py test_deploy

For a local installation under a normal user without sudo access

fab -u `whoami` -H <IP address> -f machine-setup/deploy.py user_deploy
"""
import glob

import boto
import os
import time

from fabric.api import run, sudo, put, env, require, local, task
from fabric.context_managers import cd, hide, settings, prefix
from fabric.contrib.console import confirm
from fabric.contrib.files import append, sed, comment, exists
from fabric.decorators import task, serial
from fabric.operations import prompt
from fabric.utils import puts, abort, fastprint

#Defaults
USERNAME = 'admin'
USERS = ['gavo']
GAVO_PACKAGE = 'python-gavodachs'
POSTFIX = False
AMI_ID = 'ami-50d9a439' # This is a Debian 7.1 image in US Virginia
INSTANCE_NAME = 'GAVO Portal'
INSTANCE_TYPE = 't1.micro'
INSTANCES_FILE = os.path.expanduser('~/.aws/aws_instances')
AWS_KEY = os.path.expanduser('~/.ssh/icrar_ngas.pem')
KEY_NAME = 'icrar_ngas'
ELASTIC_IP = 'False'
SECURITY_GROUPS = ['icrar_gavo'] # Security group allows SSH
PORTAL_DIR = 'gavo_portal' #NGAS runtime directory
NGAS_PYTHON_VERSION = '2.7'
NGAS_PYTHON_URL = 'http://www.python.org/ftp/python/2.7.5/Python-2.7.5.tar.bz2'
NGAS_DEF_DB = '/home/ngas/NGAS/ngas.sqlite'

YUM_PACKAGES = [
   'autoconf',
   'python27-devel',
   'git',
   'readline-devel',
   'sqlite-devel',
   'make',
   'wget.x86_64',
   'gcc',
   'patch',
   'postgresql9-devel.x86_64',
]

APT_PACKAGES = [
        'libreadline-dev',
        'sqlite3',
        'libsqlite3-dev',
        'python-dev',
        'git',
        ]


PUBLIC_KEYS = os.path.expanduser('~/.ssh')
# WEB_HOST = 0
# UPLOAD_HOST = 1
# DOWNLOAD_HOST = 2

def set_env():
    # set environment to default for EC2, if not specified on command line.

    # puts(env)
    if not env.has_key('instance_name') or not env.instance_name:
        env.instance_name = INSTANCE_NAME
    if not env.has_key('USERS') or not env.instance_name:
        env.USERS = USERS
    if not env.has_key('postfix') or not env.postfix:
        env.postfix = POSTFIX
    if not env.has_key('use_elastic_ip') or not env.use_elastic_ip:
        env.use_elastic_ip = ELASTIC_IP
    if not env.user or not env.user:
        env.user = USERNAME
    if not env.has_key('key_filename') or not env.key_filename:
        env.key_filename = AWS_KEY
    require('hosts', provided_by=[test_env])
    if not env.has_key('PORTAL_DIR_ABS') or not env.PORTAL_DIR_ABS:
        env.PORTAL_DIR_ABS = '{0}/{1}'.format(run('echo $PWD'), PORTAL_DIR)
    # puts('Environment: {0} {1} {2} {3} {4} {5}'.format(env.user, env.key_filename, env.hosts,
    #                                               env.host_string, env.postfix, env.PORTAL_DIR_ABS))


@task
def create_instance(names, use_elastic_ip, public_ips):
    """Create the EC2 instance

    :param names: the name to be used for this instance
    :type names: list of strings
    :param boolean use_elastic_ip: is this instance to use an Elastic IP address

    :rtype: string
    :return: The public host name of the AWS instance
    """

    puts('Creating instances {0} [{1}:{2}]'.format(names, use_elastic_ip, public_ips))
    number_instances = len(names)
    if number_instances != len(public_ips):
        abort('The lists do not match in length')

    # This relies on a ~/.boto file holding the '<aws access key>', '<aws secret key>'
    conn = boto.connect_ec2()

    if use_elastic_ip:
        # Disassociate the public IP
        for public_ip in public_ips:
            if not conn.disassociate_address(public_ip=public_ip):
                abort('Could not disassociate the IP {0}'.format(public_ip))

    reservations = conn.run_instances(AMI_ID, instance_type=INSTANCE_TYPE, key_name=KEY_NAME, security_groups=SECURITY_GROUPS, min_count=number_instances, max_count=number_instances)
    instances = reservations.instances
    # Sleep so Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)

    # Are we running yet?
    for i in range(number_instances):
        while not instances[i].update() == 'running':
            fastprint('.')
            time.sleep(5)

    # Sleep a bit more Amazon recognizes the new instance
    for i in range(4):
        fastprint('.')
        time.sleep(5)
    puts('.')

    # Tag the instance
    for i in range(number_instances):
        conn.create_tags([instances[i].id], {'Name': names[i]})

    # Associate the IP if needed
    if use_elastic_ip:
        for i in range(number_instances):
            puts('Current DNS name is {0}. About to associate the Elastic IP'.format(instances[i].dns_name))
            if not conn.associate_address(instance_id=instances[i].id, public_ip=public_ips[i]):
                abort('Could not associate the IP {0} to the instance {1}'.format(public_ips[i], instances[i].id))

    # Give AWS time to switch everything over
    time.sleep(10)

    # Load the new instance data as the dns_name may have changed
    host_names = []
    for i in range(number_instances):
        instances[i].update(True)
        puts('Current DNS name is {0} after associating the Elastic IP'.format(instances[i].dns_name))
        host_names.append(str(instances[i].dns_name))


    # The instance is started, but not useable (yet)
    puts('Started the instance(s) now waiting for the SSH daemon to start.')
    for i in range(12):
        fastprint('.')
        time.sleep(5)
    puts('.')

    return host_names


def to_boolean(choice, default=False):
    """Convert the yes/no to true/false

    :param choice: the text string input
    :type choice: string
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    choice_lower = choice.lower()
    if choice_lower in valid:
        return valid[choice_lower]
    return default

def check_command(command):
    """
    Check existence of command remotely

    INPUT:
    command:  string

    OUTPUT:
    Boolean
    """
    res = run('if command -v {0} &> /dev/null ;then command -v {0};else echo ;fi'.format(command))
    return res

def check_dir(directory):
    """
    Check existence of remote directory
    """
    res = run('if [ -d {0} ]; then echo 1; else echo ; fi'.format(directory))
    return res


def check_path(path):
    """
    Check existence of remote path
    """
    res = run('if [ -e {0} ]; then echo 1; else echo ; fi'.format(path))
    return res


def check_python():
    """
    Check for the existence of correct version of python

    INPUT:
    None

    OUTPUT:
    path to python binary    string, could be empty string
    """
    # Try whether there is already a local python installation for this user
    ppath = os.path.realpath(env.PORTAL_DIR_ABS+'/../python')
    ppath = check_command('{0}/bin/python{1}'.format(ppath, NGAS_PYTHON_VERSION))
    if ppath:
        return ppath
    # Try python2.7 first
    ppath = check_command('python{0}'.format(NGAS_PYTHON_VERSION))
    if ppath:
        env.PYTHON = ppath
        return ppath


def install_yum(package):
    """
    Install a package using YUM
    """
    errmsg = sudo('yum --assumeyes --quiet install {0}'.format(package),\
                   combine_stderr=True, warn_only=True)
    processCentOSErrMsg(errmsg)


def install_apt(package):
    """
    Install a package using APT

    NOTE: This requires sudo access
    """
    sudo('apt-get -qq -y install {0}'.format(package))


def check_yum(package):
    """
    Check whether package is installed or not

    NOTE: requires sudo access to machine
    """
    with hide('stdout','running','stderr'):
        res = sudo('yum --assumeyes --quiet list installed {0}'.format(package), \
             combine_stderr=True, warn_only=True)
    #print res
    if res.find(package) > 0:
        print "Installed package {0}".format(package)
        return True
    else:
        print "NOT installed package {0}".format(package)
        return False


def check_apt(package):
    """
    Check whether package is installed using APT

    NOTE: This requires sudo access
    """
    # TODO
    with hide('stdout','running'):
        res = sudo('dpkg -L | grep {0}'.format(package))
    if res.find(package) > -1:
        print "Installed package {0}".format(package)
        return True
    else:
        print "NOT installed package {0}".format(package)
        return False


def copy_public_keys():
    """
    Copy the public keys to the remote servers
    """
    env.list_of_users = []
    for file in glob.glob(PUBLIC_KEYS + '/*.pub'):
        filename = '.ssh/{0}'.format(os.path.basename(file))
        user, ext = os.path.splitext(filename)
        env.list_of_users.append(user)
        put(file, filename)


def virtualenv(command):
    """
    Just a helper function to execute commands in the virtualenv
    """
    env.activate = 'source {0}/bin/activate'.format(env.PORTAL_DIR_ABS)
    with cd(env.PORTAL_DIR_ABS):
        run(env.activate + '&&' + command)


def git_pull():
    """
    Updates the repository.
    TODO: This does not work outside iVEC. The current implementation
    is thus using a tar-file, copied over from the calling machine.
    """
    with cd(env.PORTAL_DIR_ABS):
        sudo('git pull', user=env.user)

def git_clone():
    """
    Clones the NGAS repository.
    """
    copy_public_keys()
    with cd(env.PORTAL_DIR_ABS):
        run('git clone {0}@{1}'.format(env.GITUSER, env.GITREPO))


@task
def git_clone_tar():
    """
    Clones the repository into /tmp and packs it into a tar file

    TODO: This does not work outside iVEC. The current implementation
    is thus using a tar-file, copied over from the calling machine.
    """
    set_env()
    with cd('/tmp'):
        local('cd /tmp && git clone {0}@{1}'.format(env.GITUSER, env.GITREPO))
        local('cd /tmp && tar -cjf {0}.tar.bz2 {0}'.format(PORTAL_DIR))
        tarfile = '{0}.tar.bz2'.format(PORTAL_DIR)
        put('/tmp/{0}'.format(tarfile), tarfile)
        local('rm -rf /tmp/{0}'.format(PORTAL_DIR))  # cleanup local git clone dir
        run('tar -xjf {0} && rm {0}'.format(tarfile))


def processCentOSErrMsg(errmsg):
    if (errmsg == None or len(errmsg) == 0):
        return
    if (errmsg == 'Error: Nothing to do'):
        return
    firstKey = errmsg.split()[0]
    if (firstKey == 'Error:'):
        abort(errmsg)


@task
def system_install_f():
    """
    Perform the system installation part.

    NOTE: Most of this requires sudo access on the machine(s)
    """
    set_env()

    # Install required packages
    re = run('cat /etc/issue')
    linux_flavor = re.split()
    if (len(linux_flavor) > 0):
        if linux_flavor[0] == 'CentOS' or linux_flavor[0] == 'Ubuntu' \
           or linux_flavor[0] == 'Debian':
            linux_flavor = linux_flavor[0]
        elif linux_flavor[0] == 'Amazon':
            linux_flavor = ' '.join(linux_flavor[:2])
    if (linux_flavor in ['CentOS','Amazon Linux']):
        # Update the machine completely
        errmsg = sudo('yum --assumeyes --quiet update', combine_stderr=True, warn_only=True)
        processCentOSErrMsg(errmsg)
        for package in YUM_PACKAGES:
            install_yum(package)

    elif (linux_flavor in ['Ubuntu', 'Debian']):
        errmsg = sudo('apt-get -qq -y update', combine_stderr=True, warn_only=True)
        for package in APT_PACKAGES:
            install_apt(package)
    else:
        abort("Unknown linux flavor detected: {0}".format(re))



@task
def system_check():
    """
    Check for existence of system level packages

    NOTE: This requires sudo access on the machine(s)
    """
    with hide('running','stderr','stdout'):
        set_env()

        re = run('cat /etc/issue')
    linux_flavor = re.split()
    if (len(linux_flavor) > 0):
        if linux_flavor[0] == 'CentOS':
            linux_flavor = linux_flavor[0]
        elif linux_flavor[0] == 'Amazon':
            linux_flavor = ' '.join(linux_flavor[:2])

    summary = True
    if (linux_flavor in ['CentOS','Amazon Linux']):
        for package in YUM_PACKAGES:
            if not check_yum(package):
                summary = False
    elif (linux_flavor == 'Ubuntu'):
        for package in APT_PACKAGES:
            if not check_apt(package):
                summary = False
    else:
        abort("Unknown linux flavor detected: {0}".format(re))
    if summary:
        print "\n\nAll required packages are installed."
    else:
        print "\n\nAt least one package is missing!"


@task
def postfix_config():
    """
    Setup the e-mail system for the NGAS
    notifications. It requires access to an SMTP server.
    """

    if 'gmail_account' not in env:
        prompt('GMail Account:', 'gmail_account')
    if 'gmail_password' not in env:
        prompt('GMail Password:', 'gmail_password')

    # Setup postfix
    sudo('service sendmail stop')
    sudo('service postfix stop')
    sudo('chkconfig sendmail off')
    sudo('chkconfig sendmail --del')

    sudo('chkconfig postfix --add')
    sudo('chkconfig postfix on')

    sudo('service postfix start')

    sudo('''echo "relayhost = [smtp.gmail.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_CAfile = /etc/postfix/cacert.pem
smtp_use_tls = yes

# smtp_generic_maps
smtp_generic_maps = hash:/etc/postfix/generic
default_destination_concurrency_limit = 1" >> /etc/postfix/main.cf''')

    sudo('echo "[smtp.gmail.com]:587 {0}@gmail.com:{1}" > /etc/postfix/sasl_passwd'.format(env.gmail_account, env.gmail_password))
    sudo('chmod 400 /etc/postfix/sasl_passwd')
    sudo('postmap /etc/postfix/sasl_passwd')

@task
def user_setup():
    """
    setup gavo user.

    TODO: sort out the ssh keys
    """
    set_env()

    if not env.user:
        env.user = USERNAME # defaults to ec2-user
    for user in env.USERS:
        sudo('useradd -m {0}'.format(user), warn_only=True)
        sudo('mkdir -p /home/{0}/.ssh'.format(user), warn_only=True)
        sudo('chmod 700 /home/{0}/.ssh'.format(user))
        sudo('chown -R {0}:{0} /home/{0}/.ssh'.format(user))
        sudo('cp /home/{0}/.ssh/authorized_keys /home/{1}/.ssh/authorized_keys'.format(env.user, user))
        sudo('chmod 700 /home/{0}/.ssh/authorized_keys'.format(user))
        sudo('chown {0}:{0} /home/{0}/.ssh/authorized_keys'.format(user))
        sudo('usermod -a -G sudo %s'.format(user)) # add gavo user to sudo to allow installation
    env.PORTAL_DIR_ABS = '/home/{0}/{1}'.format(env.USERS[0], PORTAL_DIR)


@task
def setup_gavo_repo():
    """
    Add the GAVO repository to the system
    """
    ari_repo = ["deb http://vo.ari.uni-heidelberg.de/debian stable main",
                "deb-src http://vo.ari.uni-heidelberg.de/debian stable main"]
    append('/etc/apt/sources.list', ari_repo, use_sudo=True)
    sudo("wget -qO - http://docs.g-vo.org/archive-key.asc | apt-key add -")
    sudo("aptitude update")

@task
def install_gavo():
    """
    Install the GAVO package

    NOTE: This requires the repository to be setup (setup_gavo_repo)
    """
    with prefix("LANG=en_US.UTF-8"):
        install_apt(GAVO_PACKAGE)


@task
def fix_gavo_install():
    with prefix("LANG=en_US.UTF-8"):
        sudo("export PGVERSION=9.1 && pg_dropcluster --stop $PGVERSION main && \
        pg_createcluster -d /usr/local/psql/data --locale=C -e UNICODE --lc-collate=C --lc-ctype=C $PGVERSION pgdata")
        install_apt(GAVO_PACKAGE)


@task
def python_setup():
    """
    Ensure that there is the right version of python available
    If not install it from scratch in user directory.

    INPUT:
    None

    OUTPUT:
    None
    """
    set_env()

    with cd('/tmp'):
        run('wget --no-check-certificate -q {0}'.format(NGAS_PYTHON_URL))
        base = os.path.basename(NGAS_PYTHON_URL)
        pdir = os.path.splitext(os.path.splitext(base)[0])[0]
        run('tar -xjf {0}'.format(base))
    ppath = run('echo $PWD') + '/python'
    with cd('/tmp/{0}'.format(pdir)):
        run('./configure --prefix {0};make;make install'.format(ppath))
        ppath = '{0}/bin/python{1}'.format(ppath,NGAS_PYTHON_VERSION)
    env.PYTHON = ppath


@task
def virtualenv_setup():
    """
    setup virtualenv with the detected or newly installed python
    """
    set_env()
    check_python()
    print "CHECK_DIR: {0}".format(check_dir(env.PORTAL_DIR_ABS))
    if check_dir(env.PORTAL_DIR_ABS):
        abort('{0} directory exists already'.format(env.PORTAL_DIR_ABS))

    with cd('/tmp'):
        run('wget --no-check-certificate -q https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.10.tar.gz')
        run('tar -xvzf virtualenv-1.10.tar.gz')
        run('cd virtualenv-1.10; {0} virtualenv.py {1}'.format(env.PYTHON, env.PORTAL_DIR_ABS))
    with cd(env.PORTAL_DIR_ABS):
        virtualenv('pip install zc.buildout')
        # make this installation self consistent
        virtualenv('pip install fabric')
        virtualenv('pip install boto')


@task
def content_install():
    """
    Install the content of the NGAS portal
    """
    set_env()
    #git_clone_tar()
    #run('cp /tmp/ngas_portal/data/NGAST.zexp {0}/ngas/import/')
    put('data/NGAST.zexp', '{0}/ngas/import/'.format(env.PORTAL_DIR_ABS))
    run('mkdir NGAS', warn_only=True)
    if not exists('{0}/..NGAS/ngas.sqlite'.format(env.PORTAL_DIR_ABS)):
        put('data/ngas.sqlite', '{0}/../NGAS/'.format(env.PORTAL_DIR_ABS))


@task
@serial
def test_env():
    """Configure the test environment on EC2

    Ask a series of questions before deploying to the cloud.

    Allow the user to select if a Elastic IP address is to be used
    """
    if 'use_elastic_ip' in env:
        use_elastic_ip = to_boolean(env.use_elastic_ip)
    else:
        use_elastic_ip = confirm('Do you want to assign an Elastic IP to this instance: ', False)

    public_ip = None
    if use_elastic_ip:
        if 'public_ip' in env:
            public_ip = env.public_ip
        else:
            public_ip = prompt('What is the public IP address: ', 'public_ip')

    if 'instance_name' not in env:
        prompt('AWS Instance name: ', 'instance_name')

    # Create the instance in AWS
    host_names = create_instance([env.instance_name], use_elastic_ip, [public_ip])
    env.hosts = host_names
    if not env.host_string:
        env.host_string = env.hosts[0]
    env.user = USERNAME
    env.key_filename = AWS_KEY
    env.roledefs = {
        'gavo' : host_names,
    }

@task
def user_deploy():
    """
    Deploy the system as a normal user WITH sudo access
    """
    env.hosts = ['localhost',]
    env.host_string = env.hosts[0]
    set_env()
#    ppath = check_python()
#    if not ppath:
#        python_setup()
#    else:
#        env.PYTHON = ppath
#    virtualenv_setup()
    setup_gavo_repo()
    puts('****** THIS IS CURRENTLY FAILING! ********')
    puts('****** WE JUST CATCH THE ERROR, FIX THE INSTALLATION ********')
    puts('****** AND RUN THE apt-get again ********')

    with settings(warn_only=True):
        install_gavo()
    puts('****** RUN apt-get again ********')
    fix_gavo_install()
    gavo_config()

    # content_install()



@task
def init_deploy():
    """
    Install the NGAS init script for an operational deployment
    """

    if not env.has_key('PORTAL_DIR_ABS') or not env.PORTAL_DIR_ABS:
        env.PORTAL_DIR_ABS = '{0}/{1}'.format('/home/ngas', PORTAL_DIR)

    sudo('cp {0}/src/ngamsStartup/ngamsServer.init.sh /etc/init.d/ngamsServer'.\
         format(env.PORTAL_DIR_ABS))
    sudo('chmod a+x /etc/init.d/ngamsServer')
    sudo('chkconfig --add /etc/init.d/ngamsServer')
    with cd(env.PORTAL_DIR_ABS):
        sudo('ln -s {0}/cfg/{1} {0}/cfg/ngamsServer.conf'.format(\
              env.PORTAL_DIR_ABS, NGAS_DEF_DB))



@task
@serial
def operations_deploy():
    """
    ** MAIN TASK **: Deploy the full NGAS operational environment.
    In order to install NGAS on an operational host go to any host
    where NGAS is already running or where you have git-cloned the
    NGAS software and issue the command:

    fab -u <super-user> -H <host> -f machine_setup/deploy.py operations_deploy

    where <super-user> is a user on the target machine with root priviledges
    and <host> is either the DNS resolvable name of the target machine or
    its IP address.
    """

    if not env.user:
        env.user = 'root'
    # set environment to default, if not specified otherwise.
    set_env()
    system_install()
    if env.postfix:
        postfix_config()
    user_setup()
    with settings(user='ngas'):
        ppath = check_python()
        if not ppath:
            python_setup()
        virtualenv_setup()
        # content_install()
    #init_deploy()



@task
@serial
def test_deploy():
    """
    ** MAIN TASK **: Deploy the full NGAS EC2 test environment.
    """

    test_env()
    # set environment to default for EC2, if not specified otherwise.
    set_env()
    setup_gavo_repo()
    puts('****** THIS IS CURRENTLY FAILING! ********')
    puts('****** WE JUST CATCH THE ERROR, FIX THE INSTALLATION ********')
    puts('****** AND RUN THE apt-get again ********')

    with settings(warn_only=True):
        install_gavo()
    puts('****** RUN apt-get again ********')
    fix_gavo_install()
    gavo_config()
#    system_install()
#    if env.postfix:
#        postfix_config()
#    user_setup()

        #content_install()
    #init_deploy()

@task
def gavo_config():
    """
    Write the default configuration file to make the server visible
    outside.
    """
    HOST = env.host_string
    if HOST.count('@') > 0:
        HOST = HOST.split('@')[1]
    config = [
              "[web]",
              "bindAddress: {0}".format(HOST),
              "serverPort: 80",
              "serverURL: http://{0}".format(HOST),
              ]
    append('/etc/gavo.rc', config, use_sudo=True)
    sudo("gavo --disable-spew serve restart")

@task
def uninstall():
    """
    Uninstall NGAS_portal, NGAS users and init script.
    """
    set_env()
    if env.user in ['ec2-user', 'root']:
        sudo('userdel -r ngas', warn_only=True)
#        sudo('rm /etc/init.d/ngamsServer', warn_only=True)
    else:
        run('rm -rf {0}'.format(env.PORTAL_DIR_ABS))
