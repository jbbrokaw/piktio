# Setup and install piktio, from the haus_site directory
# 1. Provision instance:
#       fab provision_instance
# 2. Update image, install packages
#       fab install_piktio
# 3. Setup Postgres database
#       fab setup_database
# 4. Start the server
#       fab start_server
# For utility
#       fab create_superuser
#       fab ssh
#       fab refresh_django_app
# The last restarts gunicorn (pulling in any changes you made since last
# starting it)
# Note that for actual deployment the settings file should be edited
# to turn off debug and set ALLOWED_HOSTS = ['127.0.0.1']

from fabric.api import task, cd, run, env, prompt, execute, sudo, open_shell
from fabric.api import settings, put
import fabric.contrib
import time
import os
# import io
import boto
import boto.ec2
from piktio import configure

env.hosts = ['localhost', ]
env["user"] = "ubuntu"
env["key_filename"] = "~/.ssh/fabric.pem"  # Update to user
env.aws_region = 'us-west-2'


@task
def host_type():
    run('uname -s')


def get_ec2_connection():
    if 'ec2' not in env:
        conn = boto.ec2.connect_to_region(env.aws_region)
        if conn is not None:
            env.ec2 = conn
            print "Connected to EC2 region %s" % env.aws_region
        else:
            msg = "Unable to connect to EC2 region %s"
            raise IOError(msg % env.aws_region)
    return env.ec2


@task
def provision_instance(wait_for_running=False, timeout=60,
                       interval=2):
    wait_val = int(interval)
    timeout_val = int(timeout)
    conn = get_ec2_connection()
    instance_type = 't2.micro'
    key_name = 'fabric'
    security_group = 'ssh-access'
    image_id = "ami-3d50120d"
    # subnet_id = create_network()  # Probably don't want to do this each time

    reservations = conn.run_instances(
        image_id,
        key_name=key_name,
        instance_type=instance_type,
        security_groups=[security_group, ],
    )
    new_instances = [i for i in reservations.instances
                     if i.state == u'pending']
    running_instance = []
    if wait_for_running:
        waited = 0
        while new_instances and (waited < timeout_val):
            time.sleep(wait_val)
            waited += int(wait_val)
            for instance in new_instances:
                state = instance.state
                print "Instance %s is %s" % (instance.id, state)
                if state == "running":
                    running_instance.append(
                        new_instances.pop(new_instances.index(i))
                    )
                instance.update()

    elastic_ip = conn.allocate_address(domain="vpc")
    conn.associate_address(instance_id=reservations.instances[0].id,
                           allocation_id=elastic_ip.allocation_id)


@task
def list_aws_instances(verbose=False, state='all'):
    conn = get_ec2_connection()

    reservations = conn.get_all_reservations()
    instances = []
    for res in reservations:
        for instance in res.instances:
            if state == 'all' or instance.state == state:
                instance = {
                    'id': instance.id,
                    'type': instance.instance_type,
                    'image': instance.image_id,
                    'state': instance.state,
                    'instance': instance,
                }
                instances.append(instance)
    env.instances = instances
    if verbose:
        import pprint
        pprint.pprint(env.instances)


def select_instance(state='running'):
    if env.get('active_instance', False):
        return

    list_aws_instances(state=state)

    prompt_text = "Please select from the following instances:\n"
    instance_template = " %(ct)d: %(state)s instance %(id)s\n"
    for idx, instance in enumerate(env.instances):
        ct = idx + 1
        args = {'ct': ct}
        args.update(instance)
        prompt_text += instance_template % args
    prompt_text += "Choose an instance: "

    def validation(input):
        choice = int(input)
        if not choice in range(1, len(env.instances) + 1):
            raise ValueError("%d is not a valid instance" % choice)
        return choice

    choice = prompt(prompt_text, validate=validation)
    env.active_instance = env.instances[choice - 1]['instance']


def run_command_on_selected_server(command):
    select_instance()
    selected_hosts = [
        env.user + '@' + env.active_instance.public_dns_name
    ]
    execute(command, hosts=selected_hosts)


def _install_piktio_requirements():
    sudo('apt-get update')
    sudo('apt-get -y upgrade')
    sudo('apt-get -y install python-pip')
    sudo('apt-get -y install python-dev')
    sudo('apt-get -y install postgresql-9.3')
    sudo('apt-get -y install postgresql-server-dev-9.3')
    sudo('apt-get -y install git')
    sudo('apt-get -y install nginx')
    sudo('pip install supervisor')

    if not fabric.contrib.files.exists('~/piktio/'):
        with settings(warn_only=True):
            sudo('git clone https://github.com/jbbrokaw/piktio.git')
    if not fabric.contrib.files.exists(
            '/etc/nginx/sites-enabled/amazonaws.com'):
        sudo('ln -s /home/ubuntu/piktio/piktio.conf '
             '/etc/nginx/sites-enabled/amazonaws.com')
    with cd('piktio'):
        with settings(warn_only=True):
            sudo('python setup.py install')
            sudo('python setup.py install')  # WTForms takes 2 tries
            sudo('python setup.py build')
    sudo('shutdown -r now')
    # TODO: Setup static files, serve w/ nginx


def _setup_database():
    configure.configure()
    password = os.environ['DATABASE_PASSWORD']
    create_user_command = """"
  create user piktio with password '%s';
  grant all on database piktio to piktio;"
""" % password
    with settings(warn_only=True):
        sudo('createdb piktio', user='postgres')
    sudo('psql -U postgres piktio -c %s' % create_user_command,
         user='postgres')
    with cd('piktio'):
        sudo('initialize_piktio_db development.ini')


def _get_secrets():
    if not fabric.contrib.files.exists(
            '~/piktio/piktio/configure.py'):
        secrets_file_name = \
            raw_input("Enter the name & path of the configure.py file: ")
        secrets_file_name = put(secrets_file_name, '.')[0]
        sudo('mv %s ~/piktio/piktio/configure.py' %
             secrets_file_name)
    if not fabric.contrib.files.exists('~/.boto'):
        secrets_file_name = \
            raw_input("Enter the name & path of the .boto file: ")
        secrets_file_name = put(secrets_file_name, '.')[0]
        sudo('chmod 400 ~/.boto')


def _start_server():
    _get_secrets()
    with cd('piktio'):
        sudo('python setup.py install')
        sudo('python setup.py build')
        sudo('/etc/init.d/nginx restart')
        sudo('supervisord -c supervisord.conf')


def _update_and_restart():
    with cd('piktio'):
        sudo('git pull origin master')
        sudo('kill -TERM $(cat supervisord.pid)')
    _start_server()


@task
def install_piktio():
    run_command_on_selected_server(_install_piktio_requirements)


@task
def setup_database():
    run_command_on_selected_server(_setup_database)


@task
def start_server():
    run_command_on_selected_server(_start_server)


@task
def update_and_restart():
    run_command_on_selected_server(_update_and_restart)


@task
def ssh():
    run_command_on_selected_server(open_shell)


@task
def stop_instance():
    select_instance()
    conn = get_ec2_connection()
    conn.stop_instances(instance_ids=[env.active_instance.id])


@task
def terminate_instance():
    select_instance(state="stopped")
    conn = get_ec2_connection()
    conn.terminate_instances(instance_ids=[env.active_instance.id])


@task
def release_address():
    conn = get_ec2_connection()
    prompt_text = "Please select from the following addresses:\n"
    address_template = " %(ct)d: %(id)s\n"
    addresses = conn.get_all_addresses()
    for idx, address in enumerate(addresses):
        ct = idx + 1
        args = {'ct': ct, 'id': str(address)}
        prompt_text += address_template % args
    prompt_text += "Choose an address: "

    def validation(input):
        choice = int(input)
        if not choice in range(1, len(addresses) + 1):
            raise ValueError("%d is not a valid instance" % choice)
        return choice

    choice = prompt(prompt_text, validate=validation)
    addresses[choice - 1].release()
