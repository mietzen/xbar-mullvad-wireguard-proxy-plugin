# xbar Mullvad Wireguard SOCKS5 proxy switcher

This [xbar](https://github.com/matryer/xbar) plugin let's you switch between Mullvad WireGuard proxies.

![alt text](assets/demo.gif "Demo Gif")

It can also be used to set Proxy Auto-Config via a URL, you can either create a file in `<xbar-plugins-folder>/mullvad-wireguard-proxy/.pac_url` with your URL or set the URL manually via system settings.

![alt text](assets/pac-example.png "PAC Example")

The plugin will also automatically set the proxy bypass domains, including you current local network and search domain:

```Shell
$ networksetup -getproxybypassdomains Wi-Fi
127.0.0.1/8
169.254.0.0/16
192.168.178.0/24
localhost
*.local
*.box
```