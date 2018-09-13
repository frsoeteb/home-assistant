"""
EnOcean Component.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/EnOcean/
"""
import logging

import voluptuous as vol

from homeassistant.const import CONF_DEVICE
import homeassistant.helpers.config_validation as cv

REQUIREMENTS = ['enocean==0.40']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'enocean'

ENOCEAN_DONGLE = None

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_DEVICE): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    """Set up the EnOcean component."""
    global ENOCEAN_DONGLE

    serial_dev = config[DOMAIN].get(CONF_DEVICE)

    ENOCEAN_DONGLE = EnOceanDongle(hass, serial_dev)

    return True


class EnOceanDongle:
    """Representation of an EnOcean dongle."""

    def __init__(self, hass, ser):
        """Initialize the EnOcean dongle."""
        from enocean.communicators.serialcommunicator import SerialCommunicator
        self.__communicator = SerialCommunicator(
            port=ser, callback=self.callback)
        self.__communicator.start()
        self.__devices = []

    def register_device(self, dev):
        """Register another device."""
        self.__devices.append(dev)

    
    def base_id(self):
        """Return base id of the EnOcean dongle."""
        return self.__communicator.base_id()

    def send_command(self, command):
        """Send a command from the EnOcean dongle."""
        self.__communicator.send(command)

    # pylint: disable=no-self-use
    def _combine_hex(self, data):
        """Combine list of integer values to one big integer."""
        output = 0x00
        for i, j in enumerate(reversed(data)):
            output |= (j << i * 8)
        return output
    
    def _updateDevice(self, device, data):
        rxtype = None
        value = None
        if data[0] == 0xa5:
            if data[1] == 0x02:
                rxtype = "dimmerstatus"
                value = data[2]
                _LOGGER.debug("dimmer value = %s", value)
            elif data[4] == 0x8f:
                rxtype = "power status serial number"
            elif data[4] in [0x0C, 0x1C]:
                rxtype = "powersensor"
                value = data[3] + (data[2] << 8)
            elif data[4] in [0x09, 0x19]:
                rxtype = "energysensor"
                divisor = data[4] & 0x3
                value = (data[1] << 16) + (data[2] << 8) + data[3]
                value = value / float(10 ** divisor)
        elif data[0] == 0xF6:
            if device.stype == "listener":
                if data[6] == 0x30:
                    rxtype = "wallswitch"
                    value = 1
                elif data[6] == 0x20:
                    rxtype = "wallswitch"
                    value = 0
                elif data[2] == 0x60:    
                    rxtype = "switch_status"
                    if data[3] == 0xe4:
                        value = 1
                    elif data[3] == 0x80:
                        value = 0
            else:
                rxtype = "FSR14"
                value = True if data[1] == 0x70 else False

        _LOGGER.debug("rxtype = %s", rxtype)
        
        try:
            if value != None:
                if rxtype == "wallswitch" and device.stype == "listener":
                    device.value_changed(value, data[1])
                elif rxtype == "energysensor":
                    updateval = {"energy" : value}
                    if value > 0:
                        _LOGGER.debug("energy in update = %s", value)           
                        _LOGGER.debug("energy valuedict = %s", updateval)
                        device.value_changed(updateval)  
                    else:
                        return             
                else:
                    device.value_changed(value)    
        except:
            _LOGGER.error("exception updating device, rxtype = %s, value = %s, device = %s, data = %s", rxtype, value, str(device._dev_id),  str(data))


    def callback(self, temp):
        """Handle EnOcean device's callback.

        This is the callback function called by python-enocan whenever there
        is an incoming packet.
        """
        from enocean.protocol.packet import RadioPacket
        if isinstance(temp, RadioPacket):
            for device in self.__devices:
                if temp.sender_int == self._combine_hex(device._dev_id):
                    self._updateDevice(device, temp.data)
 

class EnOceanDevice():
    """Parent class for all devices associated with the EnOcean component."""

    def __init__(self):
        """Initialize the device."""
        ENOCEAN_DONGLE.register_device(self)
        self.stype = ""
        self.sensorid = [0x00, 0x00, 0x00, 0x00]
        self._dev_id = None

    # pylint: disable=no-self-use
    def send_command(self, data, optional, packet_type):
        """Send a command via the EnOcean dongle."""
        from enocean.protocol.packet import Packet
        packet = Packet(packet_type, data=data, optional=optional)
        ENOCEAN_DONGLE.send_command(packet)
