#!/opt/homebrew/Caskroom/miniconda/base/bin/python
import requests
import json
import subprocess
from io import StringIO


class MullvadSocksProxyMenu:
    mullvad_icon = "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HX+tCcx+kt7oaLEjYGAbuLjuaMoecLkDDD0Zsim7UpBKKBaB9zP6pjwweAv0rXlza5/j9AHI0qzSN8DBITBWoux1n3eHu+f27532/H4A01pyZ510YWkAAA0caVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOmQ0ZWY5MWViLTg3ODEtNDFlNi04OWQ4LWUxZTQxNDJlNWVhMCIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpkODFhYmRiOS1hMzI2LTQ4OTktYWRhNy0wMzlhNzQxNDg5ZTciCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDpjMmY5MTZhZC0zMzUwLTRlZGItODFkMi1jYmIyNTkwNzcxOGUiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJNYWMgT1MiCiAgIEdJTVA6VGltZVN0YW1wPSIxNjM4ODgwMzQ3MjkzMDI1IgogICBHSU1QOlZlcnNpb249IjIuMTAuMjgiCiAgIHRpZmY6T3JpZW50YXRpb249IjEiCiAgIHhtcDpDcmVhdG9yVG9vbD0iR0lNUCAyLjEwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6ODZiMWVmNDQtNjRlMS00ZWVlLThhM2UtNDZhMzVhNzIyMDg5IgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKE1hYyBPUykiCiAgICAgIHN0RXZ0OndoZW49IjIwMjEtMTItMDdUMTM6MzI6MjcrMDE6MDAiLz4KICAgIDwvcmRmOlNlcT4KICAgPC94bXBNTTpIaXN0b3J5PgogIDwvcmRmOkRlc2NyaXB0aW9uPgogPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4KICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgIAo8P3hwYWNrZXQgZW5kPSJ3Ij8+hjOjiAAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAAmcwAAJnMB82x1CgAAAAd0SU1FB+UMBwwgG8SB4QMAAAaiSURBVHja5ZttbJ5lFcd/V7uNlXZzg7mOFMIUxqZTw7I46qbBaHxZFo0lGHyJHyQRlxhiOqMgwRAjaTDq4gddJOrAELVoNBBxwkZ8iaBkhGim2YIC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"

    def __init__(self):
        self._secure = " "
        self._not_secure = " "
        self._no_connection = " "

        self._online = None
        self._mullvad_api_reachable = None
        self._am_i_mullvad_reachable = None

        self._status = None
        self._locations = None
        self._relays = None
        self._default_device_name = subprocess.check_output(
            "networksetup -listnetworkserviceorder | grep $(netstat -rn | grep default | awk '{ print $4 }' | head -n1 | xargs) | cut -d ':' -f 2 | cut -d ',' -f 1 | tr -d '[:space:]'", shell=True, text=True)
        self._check_if_online()
        self._load_mullvad_data()

    def _load_mullvad_data(self):
        if self._online:
            try:
                relay_info = json.loads((requests.get(
                    'https://api.mullvad.net/public/relays/wireguard/v2/', timeout=10).text))
                self._locations = relay_info.get('locations')
                self._relays = relay_info.get('wireguard').get('relays')
                self._mullvad_api_reachable = True
            except (requests.ConnectionError, requests.Timeout, AttributeError, json.JSONDecodeError):
                self._mullvad_api_reachable = False

            if self._mullvad_api_reachable:
                try:
                    self._status = json.loads(
                        (requests.get('https://am.i.mullvad.net/json', timeout=10).text))
                    self._am_i_mullvad_reachable = True
                except (requests.ConnectionError, requests.Timeout, AttributeError, json.JSONDecodeError):
                    self.m_i_mullvad_reachable = False
                    external_ip = subprocess.check_output(
                        "dig +short myip.opendns.com @resolver1.opendns.com | tr -d '[:space:]'", shell=True, text=True)
                    self._status = {'ip': external_ip}
                    if subprocess.call(['ping', '-c', '1', '10.64.0.1']) == 0:
                        self._status['mullvad_exit_ip'] = True
                    else:
                        self._status['mullvad_exit_ip'] = False

    def _check_if_online(self):
        try:
            _ = requests.head(url='https://www.google.com/', timeout=10)
            self._online = True
        except requests.ConnectionError:
            self._online = False

    def _get_countries(self):
        return sorted(list(set([i.get('country') for i in self._locations.values()])))

    def _get_cities(self, country):
        return sorted([i.get('city') for i in self._locations.values() if i.get('country') == country])

    def _get_city_code(self, city):
        return [i for i, j in self._locations.items() if j.get('city') == city][0]

    def _get_hostnames(self, city_code):
        return sorted([i.get('hostname') for i in self._relays if i.get('location') == city_code])

    def _get_ip_v4_address(self, hostname):
        return [i.get('ipv4_addr_in') for i in self._relays if i.get('hostname') == hostname][0]

    def _deactivate_proxy(self):
        return 'shell=networksetup param1=-setsocksfirewallproxystate param2=' + self._default_device_name + ' param3=off'

    def _activate_proxy(self):
        return 'shell=networksetup param1=-setsocksfirewallproxystate param2=' + self._default_device_name + ' param3=on'

    def _get_proxy_url(self, hostname):
        if '-wireguard' in hostname:
            proxy_url = hostname.split(
                '-')[0] + '-wg.socks5.relays.mullvad.net'
        else:
            proxy_url = '-'.join(hostname.split('-')[:-1]) + '-socks5-' + hostname.split(
                '-')[-1] + '.relays.mullvad.net'
        return proxy_url

    def _set_proxy(self, proxy_url):
        return 'shell=networksetup param1=-setsocksfirewallproxy param2=' + self._default_device_name + ' param3=' + proxy_url + ' param4=1080'

    def _get_proxy_status(self):
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
                        'Type: 		' + self._status.get('mullvad_server_type') + '\n')
                    fid.write('Organization:	' +
                              self._status.get('organization') + '\n')
            else:
                fid.write('Connected via mullvad!' + '\n')
                fid.write('Details are not available:' + '\n')
                fid.write('am.i.mullvad.net unreachable' + '\n')
            fid.write('---' + '\n')
            fid.write('Proxy:		' + self._get_proxy_status() + '\n')
            fid.write('Off | terminal=false | refresh=true | ' +
                      self._deactivate_proxy() + '\n')
            if self._status.get('mullvad_exit_ip'):
                fid.write('Mullvad default | terminal=false | refresh=true | ' +
                          self._activate_proxy() + ' | ' + self._set_proxy('10.64.0.1') + '\n')
                fid.write('Countries:' + '\n')
                for country in self._get_countries():
                    # Positive lookhead, do we have proxies in this country?
                    if [x for x in self._get_cities(country) if self._get_hostnames(self._get_city_code(x))]:
                        fid.write('--' + country + '\n')
                        for city in self._get_cities(country):
                            # Positive lookhead, do we have proxies in this city?
                            if self._get_hostnames(self._get_city_code(city)):
                                fid.write('----' + city + '\n')
                                for server in self._get_hostnames(self._get_city_code(city)):
                                    fid.write('------' + server + ' | terminal=false | refresh=true | ' + self._activate_proxy(
                                    ) + ' | ' + self._set_proxy(self._get_proxy_url(server)) + '\n')
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
                fid.write('Proxy:		' + self._get_proxy_status() + '\n')
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


try:
    mullvad_socks_proxy_menu = MullvadSocksProxyMenu()
    mullvad_socks_proxy_menu.print_menu()
except Exception as exception:
    print('' + " | font='FontAwesome5Free-Solid' | size=16 | trim=false | templateImage=" +
          MullvadSocksProxyMenu.mullvad_icon)
    print('---')
    print('Error')
    print('---')
    print(str(exception))
    print('---')
    print('Refresh now | refresh=true')
