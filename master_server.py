from flask import Flask
import configparser
import paramiko

web_app = Flask(__name__)

configuration = configparser.ConfigParser()
with open('virtual_machines.ini') as config_file:
    configuration.read_file(config_file)


def get_available_vm():
    for section in configuration.sections():
        if configuration.get(section, 'reservation_status') == 'available':
            return section


def get_reserved_vm():
    for section in configuration.sections():
        if configuration.get(section, 'reservation_status') == 'reserved':
            return section


def update_reservation_status(vm, reservation_status):
    configuration.set(vm, 'reservation_status', reservation_status)
    with open('virtual_machines.ini', 'w') as config_file:
        configuration.write(config_file)


def vm_cleanup(ip_address):
    host = ip_address
    user = "admin"
    password = "123cba"

    try:
        print("attempting to connect to host: " + host)
        ssh_session = paramiko.SSHClient()
        ssh_session.load_system_host_keys()
        ssh_session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_session.connect(host, 22, user, password)

        ssh_session.exec_command('ls /tmp/*')
        ssh_session.exec_command('rm -fr /tmp/*')
    except TimeoutError:
        print("Error during VM cleanup for host: " + host)
    except paramiko.SSHException:
        print("Error during VM cleanup for host: " + host)


@web_app.route('/api/v1/checkout', methods=['GET'])
def check_out_vm():
    is_inventory_empty = True
    for section in configuration.sections():
        if configuration.get(section, 'reservation_status') == 'available':
            is_inventory_empty = False

    if is_inventory_empty:
        return "Your attempted checkin was rejected. There are no available VM's. \n Please try again later."
    else:
        available_vm = get_available_vm()
        update_reservation_status(available_vm, 'reserved')
        return "Your reservation was successful."


@web_app.route('/api/v1/checkin', methods=['POST'])
def check_in_vm():
    is_inventory_full = True
    for section in configuration.sections():
        if configuration.get(section, 'reservation_status') == 'reserved':
            is_inventory_full = False

    if is_inventory_full:
        return "Your return was rejected. There is no VM to check in."
    else:
        reserved_vm = get_reserved_vm()
        for section in configuration.sections():
            if section == reserved_vm:
                ip_address = section
                vm_cleanup(ip_address)

        update_reservation_status(reserved_vm, 'available')
        return "Your return was accepted"


if __name__ == "__main__":
    web_app.run()