import can, logging

from config import Config

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

bus = can.interface.Bus(Config.canbus_interface, bustype=Config.canbus_type)

msg = can.Message(arbitration_id=0x01F01031, data=bytearray(b'\x00\x0C\x01\x02\x02\x02\x02\x02', extended_id=True))
bus.send(msg)
# 01 F 01 031     00 0C 01 02 02 02 02 02
