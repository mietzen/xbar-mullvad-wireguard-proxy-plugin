#!.venv/bin/python3

import base64
import ipaddress
import json
import os
import pathlib
import platform
import pypac
import re
import requests
import shlex
import subprocess
import sys

from io import StringIO


def gen_xbar_shell_cmd(call) -> str:
    cmd = ''
    if call:
        cmd = ' | terminal=false | refresh=true | '
        call_splited = shlex.split(call, posix=False)
        cmd += 'shell=' + call_splited[0]
        for j, y in enumerate(call_splited[1:], start=1):
            cmd += ' param{0}={1}'.format(j, y)
    return cmd.rstrip()


def natural_sort(unsorted_list: list) -> list:
    def convert(text): return int(text) if text.isdigit() else text.lower()
    def alphanum_key(key): return [convert(c)
                                   for c in re.split('([0-9]+)', key)]
    return sorted(unsorted_list, key=alphanum_key)


def auto_line_break(string: str, char_threshold=80) -> str:
    splitted_string = string.split(' ')
    line_broken_string = ''
    for i in range(len(splitted_string)):
        line_broken_string = ' '.join([line_broken_string, splitted_string[i]])
        if i < len(splitted_string)-1:
            if len(line_broken_string.split('\n')[-1]) + len(splitted_string[i+1]) >= char_threshold:
                line_broken_string += '\n'
    return line_broken_string


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class MullvadSocksProxyMenu(metaclass=Singleton):
    with open(pathlib.Path(__file__).parent.resolve().joinpath('assets/mullvad_icon.png'), 'rb') as icon:
        mullvad_icon = base64.b64encode(icon.read()).decode('utf-8')

    def __init__(self):
        self.__file = pathlib.Path(__file__)
        self.__base_dir = pathlib.Path(__file__).parent.resolve()
        self.__python = pathlib.Path.joinpath(
            self.__base_dir, '.venv', 'bin', 'python')
        self._secure = " "
        self._not_secure = " "
        self._no_connection = " "
        self._online = None
        self._mullvad_api_reachable = None
        self._am_i_mullvad_reachable = None
        self._proxy_bypass_str = None
        self._status = None
        self._relays = None
        self._default_device_name = subprocess.check_output(
            "networksetup -listnetworkserviceorder | grep -B 1 $(netstat -rn | grep default | grep -v tun | awk '{ print $4 }' | head -n1 | xargs) | head -n1 | sed -n 's/^([0-9])//p' | xargs | tr -d '\n'", shell=True, text=True)
        self._check_if_online()
        self._load_mullvad_data()

    def _call_self_cli(self, *nargs) -> str:
        cmd = ''
        if nargs:
            cmd = str(self.__python) + ' ' + \
                str(self.__file) + ' ' + ' '.join(nargs)
            cmd = gen_xbar_shell_cmd(cmd)
        return cmd

    def _check_if_online(self):
        try:
            _ = requests.head(url='https://www.google.com/', timeout=10)
            self._online = True
        except requests.ConnectionError:
            self._online = False

    def _load_mullvad_data(self):
        if self._online:
            try:
                self._relays = json.loads((requests.get(
                    'https://api.mullvad.net/www/relays/all/', timeout=10).text))
                self._relays = [x for x in self._relays if x['active']
                                and x['type'] == 'wireguard']
                self._mullvad_api_reachable = True
            except (requests.ConnectionError, requests.Timeout, AttributeError, json.JSONDecodeError):
                self._mullvad_api_reachable = False

            if self._mullvad_api_reachable:
                try:
                    pac_session = pypac.PACSession(pac_enabled=self._get_proxy_type() in [
                                                   'PAC', 'WPAD'], pac=pypac.get_pac(url=self._get_auto_proxy_url()))
                    self._status = json.loads(
                        (pac_session.get('https://am.i.mullvad.net/json', timeout=10).text))
                    self._am_i_mullvad_reachable = True
                    self._status['mullvad_server_type'].lower()
                except (requests.ConnectionError, requests.Timeout, AttributeError, json.JSONDecodeError):
                    # am.i.mullvad.net is sometimes unreachable, so we try to get gather some info
                    self._am_i_mullvad_reachable = False
                    external_ip = subprocess.check_output(
                        "dig +short myip.opendns.com @resolver1.opendns.com | tr -d '[:space:]'", shell=True, text=True)
                    self._status = {'ip': external_ip}
                    # Ping wireguard default dns to check if we might be connected to mullvad via wireguard
                    if subprocess.call(['ping', '-c', '1', '10.64.0.1'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0:
                        self._status['mullvad_exit_ip'] = True
                        self._status['mullvad_server_type'] = 'wireguard'
                        self._relays = [
                            x for x in self._relays if x['type'] == 'wireguard']
                    else:
                        # We're probably not connected via mullvad
                        self._status['mullvad_exit_ip'] = False
                except (Exception):
                    self._mullvad_api_reachable = False

    def _get_countries(self) -> list:
        return natural_sort(set([x['country_name'] for x in self._relays]))

    def _get_cities(self, country: str) -> list:
        return natural_sort(set([x['city_name'] for x in self._relays if x['country_name'] == country]))

    def _get_hostnames(self, city: str) -> list:
        return natural_sort(set([x['hostname'] for x in self._relays if x['city_name'] == city]))

    def _get_ip_v4_address(self, hostname: str) -> str:
        return [x['ipv4_addr_in'] for x in self._relays if x['hostname'] == hostname][0]

    def _get_ownership(self, hostname: str) -> str:
        ownership = 'Unknown'
        ownership_status = [x['owned']
                            for x in self._relays if x['hostname'] == hostname]
        if ownership_status:
            if ownership_status[0]:
                ownership = 'Owned'
            else:
                ownership = 'Rented'
        return ownership

    def _get_stboot(self, hostname: str) -> bool:
        stboot = None
        stboot_status = [x['stboot']
                         for x in self._relays if x['hostname'] == hostname]
        if stboot_status:
            stboot = stboot_status[0]

        return stboot

    def _deactivate_socks_proxy_str(self) -> str:
        proxy_type = self._get_proxy_type()
        deactivate_proxy_str = ''
        if proxy_type:
            if proxy_type == 'SOCKS5':
                deactivate_proxy_str = 'Deactivate SOCKS5 Proxy' + \
                    self._call_self_cli('deactivate_socks_proxy') + '\n'
            if proxy_type == 'PAC':
                with open(pathlib.Path.joinpath(self.__base_dir, '.pac_url'), 'w') as fid:
                    fid.write(self._get_auto_proxy_url())
                deactivate_proxy_str = 'Deactivate Proxy Auto-Configuration' + \
                    self._call_self_cli('deactivate_socks_proxy') + '\n'
            if proxy_type == 'WPAD':
                deactivate_proxy_str = 'Deactivate Web Proxy Auto-Discovery' + \
                    self._call_self_cli('deactivate_socks_proxy') + '\n'
        return deactivate_proxy_str

    def _get_proxy_bypass_str(self) -> str:
        if not self._proxy_bypass_str:
            net_info = self._query_networksetup('getinfo')
            network = str(ipaddress.IPv4Network(
                (net_info['IP address'], net_info['Subnet mask']), False))
            search_domain = '*.' + subprocess.check_output(
                "scutil --dns | grep -m 1 'search domain\[0\] : ' | cut -d':' -f2 | tr -d '[:space:]'", shell=True, text=True)

            self._proxy_bypass_str = ['127.0.0.1/8', '169.254.0.0/16', network, 'localhost', '*.local ', search_domain]
        return self._proxy_bypass_str

    def _pac_url(self) -> bool:
        pac_url = pathlib.Path("./.pac_url")
        return pac_url.is_file()

    def _get_proxy_url(self, hostname: str) -> str:
        return [x['socks_name'] for x in self._relays if x['hostname'] == hostname][0]

    def _get_auto_proxy_url(self) -> str | None:
        auto_proxy_url = None
        result = self._query_networksetup('getautoproxyurl')
        if result.get('Enabled') == 'Yes':
            auto_proxy_url = result.get('URL')
        return auto_proxy_url

    def _get_current_socks_proxy_server(self) -> str | None:
        proxy_server = None
        result = self._query_networksetup('getsocksfirewallproxy')
        if result.get('Enabled') == 'Yes':
            proxy_server = result.get('Server')
        return proxy_server

    def _get_proxy_type(self) -> str | None:
        type = None
        if self._query_networksetup('getautoproxyurl').get('Enabled') == 'Yes':
            type = 'PAC'
        else:
            if self._query_networksetup('getproxyautodiscovery').get('Auto Proxy Discovery') == 'On':
                type = 'WPAD'
            else:
                if self._query_networksetup('getsocksfirewallproxy').get('Enabled') == 'Yes':
                    type = 'SOCKS5'
        return type

    def _get_proxy_str(self) -> str:
        proxy_type = self._get_proxy_type()
        proxy_str = 'None'
        if proxy_type == 'SOCKS5':
            socks_proxy = self._get_current_socks_proxy_server()
            if socks_proxy:
                if socks_proxy == '10.64.0.1':
                    proxy_str = 'Mullvad default'
                else:
                    proxy_str = socks_proxy
        if proxy_type == 'PAC':
            proxy_str = 'PAC via: ' + self._get_auto_proxy_url()
        if proxy_type == 'WPAD':
            proxy_str = 'WPAD Proxy Auto Discovery'
        return proxy_str

    def _query_networksetup(self, command) -> dict:
        result = {}
        cmd_out = subprocess.check_output(
            'networksetup -' + command + ' "' + self._default_device_name + '"', shell=True, text=True)[:-1].split('\n')
        for i in cmd_out:
            if len(i.split(': ')) > 1:
                key = i.split(': ')[0]
                value = i.split(': ')[1]
                result[key] = value
        return result

    def print_menu(self):
        # Write menu to buffer before printing in case we run in to some errors
        fid = StringIO()
        if self._online and self._mullvad_api_reachable:
            if self._status['mullvad_exit_ip']:
                fid.write(
                    self._secure + " | font='FontAwesome5Free-Solid' | size=16 | trim=false | templateImage=" + self.mullvad_icon + '\n')
            else:
                fid.write(
                    self._not_secure + " | font='FontAwesome5Free-Solid' | size=16 | trim=false | templateImage=" + self.mullvad_icon + '\n')
            if 'wireguard' in self._status['mullvad_server_type'].lower():
                if self._am_i_mullvad_reachable and self._status['mullvad_exit_ip'] and self._get_proxy_type() == 'SOCKS5':
                    proxies = {'https': 'socks5://' +
                               self._get_current_socks_proxy_server() + ':1080'}
                    self._status = json.loads(
                        (requests.get('https://am.i.mullvad.net/json', proxies=proxies, timeout=10).text))
                fid.write('---' + '\n')
                fid.write('IP: 			' + self._status['ip'] + '\n')
                if self._am_i_mullvad_reachable:
                    if self._status['mullvad_exit_ip']:
                        fid.write('Country: 		' +
                                  self._status['country'] + '\n')
                        # Sometimes city is missing
                        if self._status['city']:
                            fid.write('City: 		' + self._status['city'] + '\n')
                        fid.write(
                            'Hostname:	' + self._status['mullvad_exit_ip_hostname'] + '\n')
                        fid.write(
                            'Connection: 	' + self._status['mullvad_server_type'] + '\n')
                        fid.write('Organization:	' +
                                  self._status['organization'] + '\n')
                        fid.write(
                            'Ownership:	' + self._get_ownership(self._status['mullvad_exit_ip_hostname']) + '\n')
                        if self._get_stboot(self._status['mullvad_exit_ip_hostname']):
                            fid.write('Type:		Diskless\n')
                        elif self._get_stboot(self._status['mullvad_exit_ip_hostname']) is None:
                            fid.write('Type:		Unknown\n')
                        else:
                            fid.write('Type:		Conventional\n')
                        if 'SOCKS' in self._status['mullvad_server_type']:
                            messages = [x['status_messages'] for x in self._relays if x['socks_name']
                                        == self._status['mullvad_exit_ip_hostname']]
                        else: 
                            messages = [x['status_messages'] for x in self._relays if x['hostname']
                                        == self._status['mullvad_exit_ip_hostname']][0]
                        if messages:
                            message = '\n'.join([x['message']
                                                for x in messages])
                            fid.write('---\nMessages:	!!! \n' +
                                      auto_line_break(message, 50) + '\n')
                        else:
                            fid.write('---\nMessages:	None\n')
                else:
                    fid.write('Connected via mullvad!' + '\n')
                    fid.write('Details are not available:' + '\n')
                    fid.write('am.i.mullvad.net unreachable' + '\n')
                fid.write('---' + '\n')
                fid.write('Proxy:		' + self._get_proxy_str() + '\n')
                if self._get_proxy_type():
                    fid.write(self._deactivate_socks_proxy_str())
                if self._status['mullvad_exit_ip'] and self._get_proxy_type() not in ['PAC', 'WPAD']:
                    if self._pac_url() and not self._get_proxy_type():
                        fid.write('Use Proxy Auto-Configuration' +
                                  self._call_self_cli('activate_pac') + '\n')
                    fid.write(
                        'Mullvad default' + self._call_self_cli('set_and_activate_socks_proxy', '10.64.0.1') + '\n')
                    fid.write('Countries:' + '\n')
                    for country in self._get_countries():
                        # Positive lookahead, do we have proxies in this country?
                        if [x for x in self._get_cities(country) if self._get_hostnames(x)]:
                            fid.write('--' + country + '\n')
                            for city in self._get_cities(country):
                                # Positive lookahead, do we have proxies in this city?
                                if self._get_hostnames(city):
                                    fid.write('----' + city + '\n')
                                    for server in self._get_hostnames(city):
                                        if self._get_stboot(server):
                                            srv_typ = '-Diskless'
                                        else:
                                            srv_typ = ''
                                        socks_proxy_url = self._get_proxy_url(server)
                                        if socks_proxy_url:
                                            fid.write('------' + server + ' (' + self._get_ownership(server) + srv_typ + ')' +
                                                    self._call_self_cli('set_and_activate_socks_proxy', socks_proxy_url) + '\n')
                fid.write('---' + '\n')
                fid.write(
                    'Open Mullvad VPN' + gen_xbar_shell_cmd("open -a 'Mullvad VPN'") + '\n')
            else:
                fid.write('---' + '\n')
                fid.write(
                    'SOCKS Proxy not available!\nYour connected via OpenVPN!' + '\n')
                fid.write('---')
                if self._default_device_name:
                    fid.write('Proxy:		' + self._get_proxy_str() + '\n')
                    if self._get_proxy_type():
                        fid.write(self._deactivate_socks_proxy_str())
                    fid.write('---' + '\n')
                    fid.write(
                        'Open Mullvad VPN' + gen_xbar_shell_cmd("open -a 'Mullvad VPN'") + '\n')
                else:
                    fid.write('No Interface available' + '\n')
                fid.write('---' + '\n')
        else:
            fid.write(self._no_connection +
                      " | font='FontAwesome5Free-Solid' | size=16 | trim=false | templateImage=" + self.mullvad_icon + '\n')
            fid.write('---' + '\n')
            if not self._online:
                fid.write('Offline' + '\n')
                fid.write('---')
            if not self._mullvad_api_reachable:
                fid.write('Mullvad API not reachable' + '\n')
                fid.write('---' + '\n')
            if self._default_device_name:
                fid.write('Proxy:		' + self._get_proxy_str() + '\n')
                if self._get_proxy_type():
                    fid.write(self._deactivate_socks_proxy_str())
                fid.write('---' + '\n')
                fid.write(
                    'Open Mullvad VPN' + gen_xbar_shell_cmd("open -a 'Mullvad VPN'") + '\n')
            else:
                fid.write('No Interface available' + '\n')
            fid.write('---' + '\n')
        fid.write('Refresh now | refresh=true')
        print(fid.getvalue())

    def deactivate_socks_proxy(self) -> None:
        proxy_type = self._get_proxy_type()
        if proxy_type:
            if proxy_type == 'SOCKS5':
                service = '-setsocksfirewallproxystate'
            if proxy_type == 'PAC':
                with open(pathlib.Path.joinpath(self.__base_dir, '.pac_url'), 'w') as fid:
                    fid.write(self._get_auto_proxy_url())
                service = '-setautoproxystate'
            if proxy_type == 'WPAD':
                service = '-setproxyautodiscovery'
            subprocess.call(['networksetup', service, self._default_device_name,
                            'off'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    def activate_pac(self) -> None:
        if self._pac_url:
            pac_url = ''
            with open(pathlib.Path.joinpath(self.__base_dir, '.pac_url'), 'r') as fid:
                pac_url = fid.read()
            subprocess.call(['networksetup', '-setautoproxyurl', self._default_device_name,
                            pac_url], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            subprocess.call(['networksetup', '-setproxybypassdomains', self._default_device_name,
                            ] + self._get_proxy_bypass_str(), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    def set_and_activate_socks_proxy(self, proxy_url: str) -> None:
        if proxy_url:
            subprocess.call(['networksetup', '-setsocksfirewallproxy', self._default_device_name,
                            proxy_url, '1080'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            subprocess.call(['networksetup', '-setproxybypassdomains', self._default_device_name,
                            ] + self._get_proxy_bypass_str(), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            subprocess.call(['networksetup', '--setsocksfirewallproxystate', self._default_device_name,
                            'on'], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def main():
    mullvad_socks_proxy_menu = MullvadSocksProxyMenu()
    if len(sys.argv) == 1:
        if "DEBUG" in os.environ:
            mullvad_socks_proxy_menu.print_menu()
        else:
            if platform.system() == 'Darwin':
                try:
                    mullvad_socks_proxy_menu.print_menu()
                except Exception as exception:
                    print('' + " | font='FontAwesome5Free-Solid' | size=16 | trim=false | templateImage=" +
                          MullvadSocksProxyMenu.mullvad_icon)
                    print('---')
                    print('Error')
                    print('---')
                    print(auto_line_break(str(exception), 30))
                    print('---')
                    print('Refresh now | refresh=true')
            else:
                print('' + " | font='FontAwesome5Free-Solid' | size=16 | trim=false | templateImage=" +
                      MullvadSocksProxyMenu.mullvad_icon)
                print('---')
                print('Error')
                print('---')
                print('Sorry atm macOS only')
                print('---')
                print('Refresh now | refresh=true')
    else:
        if sys.argv[1] == 'deactivate_socks_proxy':
            mullvad_socks_proxy_menu.deactivate_socks_proxy()
        if sys.argv[1] == 'activate_pac':
            mullvad_socks_proxy_menu.activate_pac()
        if sys.argv[1] == 'set_and_activate_socks_proxy' and len(sys.argv) > 2:
            mullvad_socks_proxy_menu.set_and_activate_socks_proxy(sys.argv[2])


main()
