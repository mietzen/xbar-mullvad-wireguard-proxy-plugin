#!/opt/homebrew/Caskroom/miniconda/base/bin/python
import string
import requests
import json
import subprocess
from io import StringIO
import base64
import pathlib
import platform
import re


def natural_sort(l: list) -> list:
    def convert(text): return int(text) if text.isdigit() else text.lower()
    def alphanum_key(key): return [convert(c)
                                   for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)


def auto_line_break(string: str, char_threshold=80) -> str:
    splitted_string = string.split(' ')
    line_broken_string = ''
    for i in range(len(splitted_string)):
        line_broken_string = ' '.join([line_broken_string, splitted_string[i]])
        if i < len(splitted_string)-1:
            if len(line_broken_string.split('\n')[-1]) + len(splitted_string[i+1]) >= char_threshold:
                line_broken_string += '\n'
    return line_broken_string


class MullvadSocksProxyMenu:
    with open(pathlib.Path(__file__).parent.resolve().joinpath('mullvad_icon.png'), 'rb') as icon:
        mullvad_icon = base64.b64encode(icon.read()).decode('utf-8')

    def __init__(self):
        self._secure = " "
        self._not_secure = " "
        self._no_connection = " "

        self._online = None
        self._mullvad_api_reachable = None
        self._am_i_mullvad_reachable = None

        self._status = None
        self._relays = None
        self._default_device_name = subprocess.check_output(
            "networksetup -listnetworkserviceorder | grep $(netstat -rn | grep default | awk '{ print $4 }' | head -n1 | xargs) | cut -d ':' -f 2 | cut -d ',' -f 1 | tr -d '[:space:]'", shell=True, text=True)
        self._check_if_online()
        self._load_mullvad_data()

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
                                and not x['status_messages'] and x['type'] == 'wireguard']
                self._mullvad_api_reachable = True
            except (requests.ConnectionError, requests.Timeout, AttributeError, json.JSONDecodeError):
                self._mullvad_api_reachable = False

            if self._mullvad_api_reachable:
                try:
                    self._status = json.loads(
                        (requests.get('https://am.i.mullvad.net/json', timeout=10).text))
                    self._am_i_mullvad_reachable = True
                    self._status['mullvad_server_type'].lower()
                except (requests.ConnectionError, requests.Timeout, AttributeError, json.JSONDecodeError):
                    # am.i.mullvad.net is sometimes unreachable, so we try to get gather some info
                    self._am_i_mullvad_reachable = False
                    external_ip = subprocess.check_output(
                        "dig +short myip.opendns.com @resolver1.opendns.com | tr -d '[:space:]'", shell=True, text=True)
                    self._status = {'ip': external_ip}
                    # Ping wireguard default dns to check if we might be connected to mullvad via wireguard
                    if subprocess.call(['ping', '-c', '1', '10.64.0.1']) == 0:
                        self._status['mullvad_exit_ip'] = True
                        self._relays = [
                            x for x in self._relays if x['type'] == 'wireguard']
                    else:
                        # We're probably not connected via mullvad
                        self._status['mullvad_exit_ip'] = False

    def _get_countries(self) -> list:
        return natural_sort(set([x['country_name'] for x in self._relays]))

    def _get_cities(self, country: str) -> list:
        return natural_sort(set([x['city_name'] for x in self._relays if x['country_name'] == country]))

    def _get_hostnames(self, city: str) -> list:
        return natural_sort(set([x['hostname'] for x in self._relays if x['city_name'] == city]))

    def _get_ip_v4_address(self, hostname: str) -> str:
        return [x['ipv4_addr_in'] for x in self._relays if x['hostname'] == hostname][0]

    def _get_ownership(self, hostname: str) -> str:
        if [x['owned'] for x in self._relays if x['hostname'] == hostname][0]:
            ownership = 'Owned'
        else:
            ownership = 'Rented'
        return ownership

    def _get_diskless(self, hostname: str) -> str:
        return [x['stboot'] for x in self._relays if x['hostname'] == hostname][0]

    def _deactivate_proxy(self) -> str:
        return 'shell=networksetup param1=-setsocksfirewallproxystate param2=' + self._default_device_name + ' param3=off'

    def _activate_proxy(self) -> str:
        return 'shell=networksetup param1=-setsocksfirewallproxystate param2=' + self._default_device_name + ' param3=on'

    def _get_proxy_url(self, hostname: str) -> str:
        return [x['socks_name'] for x in self._relays if x['hostname'] == hostname][0]

    def _set_proxy(self, proxy_url: str) -> str:
        return 'shell=networksetup param1=-setsocksfirewallproxy param2=' + self._default_device_name + ' param3=' + proxy_url + ' param4=1080'

    def _get_proxy_status(self) -> str:
        result = {}
        for i in subprocess.check_output('networksetup -getsocksfirewallproxy ' + self._default_device_name, shell=True, text=True)[:-1].split('\n'):
            key = i.split(': ')[0]
            value = i.split(': ')[1]
            result[key] = value
        if result.get('Enabled') == 'Yes':
            return result.get('Server')
        else:
            return 'Off'

    def print_menu(self):
        # Write menu to buffer before printing in case we run in to some errors
        fid = StringIO()
        if self._online and self._mullvad_api_reachable:
            if self._status.get('mullvad_exit_ip'):
                fid.write(
                    self._secure + " | font='FontAwesome5Free-Solid' | size=16 | trim=false | templateImage=" + self.mullvad_icon + '\n')
            else:
                fid.write(
                    self._not_secure + " | font='FontAwesome5Free-Solid' | size=16 | trim=false | templateImage=" + self.mullvad_icon + '\n')
            if self._status['mullvad_server_type'].lower() == 'wireguard':
                if self._am_i_mullvad_reachable and self._status.get('mullvad_exit_ip') and self._get_proxy_status() != 'Off':
                    proxies = {'https': 'socks5://' +
                               self._get_proxy_status() + ':1080'}
                    self._status = json.loads(
                        (requests.get('https://am.i.mullvad.net/json', proxies=proxies, timeout=10).text))
                fid.write('---' + '\n')
                fid.write('IP: 			' + self._status.get('ip') + '\n')
                if self._am_i_mullvad_reachable:
                    if self._status.get('mullvad_exit_ip'):
                        fid.write('Country: 		' +
                                  self._status.get('country') + '\n')
                    if self._status.get('city'):
                        fid.write('City: 		' + self._status.get('city') + '\n')
                    if self._status.get('mullvad_exit_ip'):
                        fid.write(
                            'Hostname:	' + self._status.get('mullvad_exit_ip_hostname') + '\n')
                        fid.write(
                            'Connection: 	' + self._status.get('mullvad_server_type') + '\n')
                        fid.write('Organization:	' +
                                  self._status.get('organization') + '\n')
                        fid.write(
                            'Ownership:	' + self._get_ownership(self._status.get('mullvad_exit_ip_hostname')) + '\n')
                        if self._get_diskless(self._status.get('mullvad_exit_ip_hostname')):
                            fid.write('Type:		Diskless\n')
                        else:
                            fid.write('Type:		Conventional\n')
                else:
                    fid.write('Connected via mullvad!' + '\n')
                    fid.write('Details are not available:' + '\n')
                    fid.write('am.i.mullvad.net unreachable' + '\n')
                fid.write('---' + '\n')
                proxy = self._get_proxy_status()
                if proxy == '10.64.0.1':
                    proxy = 'Mullvad default'
                fid.write('Proxy:		' + proxy + '\n')
                fid.write('Off | terminal=false | refresh=true | ' +
                          self._deactivate_proxy() + '\n')
                if self._status.get('mullvad_exit_ip'):
                    fid.write('Mullvad default | terminal=false | refresh=true | ' +
                              self._activate_proxy() + ' | ' + self._set_proxy('10.64.0.1') + '\n')
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
                                        if self._get_diskless(server):
                                            srv_typ = '-Diskless'
                                        else:
                                            srv_typ = ''
                                        fid.write('------' + server + ' (' + self._get_ownership(server) + srv_typ + ') | terminal=false | refresh=true | ' + self._activate_proxy(
                                        ) + ' | ' + self._set_proxy(self._get_proxy_url(server)) + '\n')
                fid.write('---' + '\n')
                fid.write(
                    'Open Mullvad VPN | terminal=false | refresh=true | shell=open param1=-a param2="Mullvad VPN"' + '\n')
            else:
                fid.write('---' + '\n')
                fid.write(
                    'SOCKS Proxy not available!\nYour connected via OpenVPN!' + '\n')
                fid.write('---')
                if self._default_device_name:
                    proxy = self._get_proxy_status()
                    if proxy == '10.64.0.1':
                        proxy = 'Mullvad default'
                    fid.write('Proxy:		' + proxy + '\n')
                    fid.write('Off | terminal=false | refresh=true | ' +
                              self._deactivate_proxy() + '\n')
                    fid.write('---' + '\n')
                    fid.write(
                        'Open Mullvad VPN | terminal=false | refresh=true | shell=open param1=-a param2="Mullvad VPN"' + '\n')
                else:
                    fid.write('No Interface available' + '\n')
                fid.write('---' + '\n')
        else:
            fid.write(self._no_connection +
                      " | font='FontAwesome5Free-Solid' | size=16 | trim=false | templateImage=" + self.mullvad_icon + '\n')
            fid.write('---' + '\n')
            if self._online == False:
                fid.write('Offline' + '\n')
                fid.write('---')
            if self._mullvad_api_reachable == False:
                fid.write('Mullvad API not reachable' + '\n')
                fid.write('---' + '\n')
            if self._default_device_name:
                proxy = self._get_proxy_status()
                if proxy == '10.64.0.1':
                    proxy = 'Mullvad default'
                fid.write('Proxy:		' + proxy + '\n')
                fid.write('Off | terminal=false | refresh=true | ' +
                          self._deactivate_proxy() + '\n')
                fid.write('---' + '\n')
                fid.write(
                    'Open Mullvad VPN | terminal=false | refresh=true | shell=open param1=-a param2="Mullvad VPN"' + '\n')
            else:
                fid.write('No Interface available' + '\n')
            fid.write('---' + '\n')
        fid.write('Refresh now | refresh=true')
        print(fid.getvalue())


if platform.system() == 'Darwin':
    try:
        mullvad_socks_proxy_menu = MullvadSocksProxyMenu()
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
