"""
Support for EnOcean light sources.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.enocean/
"""
import logging
import math

import voluptuous as vol

from homeassistant.components.light import (
    Light, ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, CONF_ID)
from homeassistant.components import enocean
import homeassistant.helpers.config_validation as cv
from enocean.protocol.packet import RadioPacket
from enocean.protocol.constants import RORG

_LOGGER = logging.getLogger(__name__)

CONF_SENDER_ID = 'sender_id'

DEFAULT_NAME = 'EnOcean Light'
DEPENDENCIES = ['enocean']

SUPPORT_ENOCEAN = SUPPORT_BRIGHTNESS

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_ID, default=[]):
        vol.All(cv.ensure_list, [vol.Coerce(int)]),
    vol.Required(CONF_SENDER_ID): vol.All(cv.ensure_list, [vol.Coerce(int)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the EnOcean light platform."""
    sender_id = config.get(CONF_SENDER_ID)
    devname = config.get(CONF_NAME)
    dev_id = config.get(CONF_ID)

    add_entities([EnOceanLight(sender_id, devname, dev_id)])


class EnOceanLight(enocean.EnOceanDevice, Light):
    """Representation of an EnOcean light source."""

    def __init__(self, sender_id, devname, dev_id):
        """Initialize the EnOcean light source."""
        enocean.EnOceanDevice.__init__(self)
        self._on_state = False
        self._brightness = 0
        self._sender_id = sender_id
        self._dev_id = dev_id
        self._devname = devname
        self._stype = 'dimmer'
        self.last_saved_brightness = 50

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._devname

    @property
    def brightness(self):
        """Brightness of the light.

        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self):
        """If light is on."""
        return self._on_state

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_ENOCEAN

    def turn_on(self, **kwargs):
        """Turn the light source on or sets a specific dimmer value."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is  None:
            brightness = self.last_saved_brightness if self.last_saved_brightness > 0 else 50
        
        _LOGGER.debug("brigthness = '%d'", brightness)
        
        if brightness > 0:
            bval = math.floor(float(brightness) *100 / 255)
            p = RadioPacket.create(rorg=RORG.BS4, rorg_func=0x38, rorg_type=0x08, destination=self._dev_id, sender=self._sender_id, command=2, RMP=1,SW=1,EDIM=bval)
            enocean.ENOCEAN_DONGLE.send_command(p)
            self._on_state = True
        else:
            self.turn_off()
        self.schedule_update_ha_state()        

    def turn_off(self, **kwargs):
        """Turn the light source off."""
        p = RadioPacket.create(rorg=RORG.BS4, rorg_func=0x38, rorg_type=0x08, destination=self._dev_id, sender=self._sender_id, command=2, RMP=1,SW=0,EDIM=0x0)
        enocean.ENOCEAN_DONGLE.send_command(p)
        self._on_state = False
        self._brightness = 0

    def value_changed(self, val):
        """Update the internal state of this device."""
        self._brightness = val*255/100
        _LOGGER.debug("dimmer value changed '%d'", val)
        self._on_state = bool(val > 0)
        if self._brightness > 0:
            self.last_saved_brightness = self._brightness 
        self.schedule_update_ha_state()
