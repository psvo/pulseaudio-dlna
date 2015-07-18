#!/usr/bin/python

# This file is part of pulseaudio-dlna.

# pulseaudio-dlna is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pulseaudio-dlna is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pulseaudio-dlna.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import socket as s
import renderer
import logging
import time


class BaseUpnpMediaRendererDiscover(object):

    SSDP_ADDRESS = '239.255.255.250'
    SSDP_PORT = 1900

    MSEARCH = 'M-SEARCH * HTTP/1.1\r\n' + \
              'HOST: {}:{}\r\n'.format(SSDP_ADDRESS, SSDP_PORT) + \
              'MAN: "ssdp:discover"\r\n' + \
              'MX: 2\r\n' + \
              'ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n\r\n'

    def search(self, ttl=10, timeout=2, times=7):
        s.setdefaulttimeout(timeout)
        sock = s.socket(s.AF_INET, s.SOCK_DGRAM, s.IPPROTO_UDP)
        sock.setsockopt(s.IPPROTO_IP, s.IP_MULTICAST_TTL, ttl)
        buffer_size = 1024

        for i in range(0, times):
            logging.info('Searching for renderers, try #{i}'.format(
                i=i))
            sock.sendto(self.MSEARCH, (self.SSDP_ADDRESS, self.SSDP_PORT))
            try:
                end_time = time.time() + timeout + 0.1
                while True:
                    _timeout = end_time - time.time()
                    if _timeout <= 0:
                        break
                    sock.settimeout(_timeout)
                    header, address = sock.recvfrom(buffer_size)
                    self._header_received(header, address)
            except s.timeout:
                continue

        sock.close()

    def _header_received(self, header, address):
        pass


class UpnpMediaRendererDiscover(BaseUpnpMediaRendererDiscover):

    def __init__(self, device_filter=None):
        self.renderers = None
        self.device_filter = device_filter

    def search(self, ttl=10, timeout=2, times=7):
        self.renderers = []
        BaseUpnpMediaRendererDiscover.search(self, ttl, timeout, times)

    def _add_renderer(self, upnp_device):
        if upnp_device not in self.renderers:
            self.renderers.append(upnp_device)

    def _header_received(self, header, address):
        logging.debug("Recieved the following SSDP header: \n{header}".format(
            header=header))
        upnp_device = renderer.UpnpMediaRendererFactory.from_header(
            header,
            renderer.CoinedUpnpMediaRenderer)
        if upnp_device is not None:
            if self.device_filter is None:
                self._add_renderer(upnp_device)
            else:
                if upnp_device.name in self.device_filter:
                    self._add_renderer(upnp_device)
                else:
                    logging.info('Skipped the device "{name}."'.format(
                        name=upnp_device.name))
