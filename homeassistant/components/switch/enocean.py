"""
Support for EnOcean switches.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/switch.enocean/
"""
import logging

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_ID)
from homeassistant.components import enocean
from homeassistant.helpers.entity import ToggleEntity
import homeassistant.helpers.config_validation as cv
from enocean.protocol.packet import RadioPacket
from enocean.protocol.constants import RORG

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'EnOcean Switch'
DEPENDENCIES = ['enocean']
CONF_CHANNEL = 'channel'
DEFAULT_TYPE = 'Eltako'

CONF_TYPE = 'type'
CONF_SENDERID = "sender_id"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
    vol.Optional(CONF_SENDERID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TYPE, default=DEFAULT_TYPE): cv.string,
    vol.Optional(CONF_CHANNEL, default=0): cv.positive_int,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the EnOcean switch platform."""
    dev_id = config.get(CONF_ID)
    devname = config.get(CONF_NAME)
    channel = config.get(CONF_CHANNEL)
    devtype = config.get(CONF_TYPE)
    sender_id = config.get(CONF_SENDERID)

    if devtype == DEFAULT_TYPE:
        add_entities([EnOceanFSR14Switch(dev_id, devname, sender_id, channel)])
    elif devtype == "RPS":
        add_entities([EnOceanRPSSwitch(dev_id, devname, sender_id, channel)])
    else:
        add_entities([EnOceanSwitch(dev_id, devname, channel)])

class EnOceanSwitch(enocean.EnOceanDevice, ToggleEntity):
    """Representation of an EnOcean switch device."""

    def __init__(self, dev_id, devname, channel):
        """Initialize the EnOcean switch device."""
        enocean.EnOceanDevice.__init__(self)
        self._dev_id = dev_id
        self._devname = devname
        self._channel = channel
        self._light = None
        self._on_state = False
        self._on_state2 = False
        self.stype = "switch"

    @property
    def is_on(self):
        """Return whether the switch is on or off."""
        return self._on_state

    @property
    def name(self):
        """Return the device name."""
        return self._devname

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        optional = [0x03, ]
        optional.extend(self._dev_id)
        optional.extend([0xff, 0x00])
        self.send_command(data=[0xD2, 0x01, self._channel & 0xFF, 0x64, 0x00,
                                0x00, 0x00, 0x00, 0x00], optional=optional,
                          packet_type=0x01)
        self._on_state = True

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        optional = [0x03, ]
        optional.extend(self._dev_id)
        optional.extend([0xff, 0x00])
        self.send_command(data=[0xD2, 0x01, self._channel & 0xFF, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00], optional=optional,
                          packet_type=0x01)
        self._on_state = False

    def value_changed(self, val):
        """Update the internal state of the switch."""
        self._on_state = val
        self.schedule_update_ha_state()

class EnOceanFSR14Switch(EnOceanSwitch):
    """Representation of an EnOcean switch device."""

    def __init__(self, dev_id, devname, senderid, channel):
        """Initialize the EnOcean switch device."""
        EnOceanSwitch.__init__(self, dev_id, devname, channel)
        self._sender_id = senderid

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        p = RadioPacket.create(rorg=RORG.BS4, rorg_func=0x38, rorg_type=0x08, destination=self._dev_id, sender=self._sender_id, CMD=1,SW=1)
        enocean.ENOCEAN_DONGLE.send_command(p)
        self._on_state = True

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        p = RadioPacket.create(rorg=RORG.BS4, rorg_func=0x38, rorg_type=0x08, destination=self._dev_id, sender=self._sender_id, CMD=1,SW=0)
        enocean.ENOCEAN_DONGLE.send_command(p)
        self._on_state = False

    def value_changed(self, val):
        """Update the internal state of the switch."""
        self._on_state = val
        self.schedule_update_ha_state()

class EnOceanRPSSwitch(EnOceanSwitch):
    """Representation of an EnOcean switch device."""

    def __init__(self, dev_id, devname, senderid, channel):
        """Initialize the EnOcean switch device."""
        EnOceanSwitch.__init__(self, dev_id, devname, channel)
        self._sender_id = senderid

    def turn_on(self, **kwargs):
        """Turn on the switch."""
        p = RadioPacket.create(rorg=RORG.RPS, rorg_func=0x02, rorg_type=0x02, destination=self._dev_id, sender=self._sender_id, R1=3, EB=1)
        enocean.ENOCEAN_DONGLE.send_command(p)
        self._on_state = True

    def turn_off(self, **kwargs):
        """Turn off the switch."""
        p = RadioPacket.create(rorg=RORG.RPS, rorg_func=0x02, rorg_type=0x02, destination=self._dev_id, sender=self._sender_id, R1=2,  EB=1)
        enocean.ENOCEAN_DONGLE.send_command(p)
        self._on_state = False

    def value_changed(self, val):
        """Update the internal state of the switch."""
        self._on_state = val
        self.schedule_update_ha_state()
