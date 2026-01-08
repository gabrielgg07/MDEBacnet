

# --- patch CharacterString early ---
from bacpypes.primitivedata import CharacterString
from bacpypes.core import run
import time, random, threading
from bacpypes.pdu import Address
from bacpypes.app import BIPSimpleApplication
from bacpypes.constructeddata import ArrayOf
from bacpypes.local.device import LocalDeviceObject
from bacpypes.object import AnalogInputObject
from bacpypes.apdu import (
    WhoIsRequest, IAmRequest,
    ReadPropertyRequest, ReadPropertyACK,
    WritePropertyRequest, SimpleAckPDU,
    UnconfirmedTextMessageRequest, ConfirmedTextMessageRequest,
    SubscribeCOVRequest, SimpleAckPDU
)
from bacpypes.apdu import ReadPropertyMultipleRequest, ReadPropertyMultipleACK
from bacpypes.primitivedata import Real
from bacpypes.constructeddata import Any
from bacpypes.apdu import Error
from bacpypes.primitivedata import  Unsigned, Enumerated, Tag, Boolean
from bacpypes.primitivedata import Null
from bacpypes.apdu import Error #, ErrorRejectAbortNack
from bacpypes.primitivedata import Unsigned
    # ✅ newer bacpypes (≥0.20)

#
from bacpypes.basetypes import PropertyIdentifier
from bacpypes.primitivedata import ObjectIdentifier
from bacpypes.basetypes import ServicesSupported
from bacpypes.apdu import ReadAccessResult, ReadAccessResultElement


# --------------------------------------------------------------------
# CCTK Reader here
#from cctkReader import CCTReader

#reader = CCTReader("/var/local/home/ops1/Desktop/projects/UGFCS/UGFCS")




# --------------------------------------------------------------------
# 1️⃣ Configure fake device
from bacpypes.object import DeviceObject
from bacpypes.local.device import LocalDeviceObject




def make_ansi_string(text: str):
    """Force ANSI (encoding=0) CharacterString compatible with BACnet 4J."""
    encoded = text.encode("ascii", errors="ignore")
    tag = Tag(Tag.applicationTagClass, Tag.characterStringAppTag, len(encoded) + 1, bytes([0]) + encoded)
    any_val = Any()
    any_val.tagList = [tag]
    return any_val


this_device = LocalDeviceObject(
    objectIdentifier=('device', 2001),
    objectName='PPFTransmitter',
    systemStatus=Enumerated(0),  # operational
    vendorName=CharacterString('VSA'),
    vendorIdentifier=999,
    modelName=CharacterString('PPF Environmental Transmitter'),
    firmwareRevision=CharacterString('2.0'),
    applicationSoftwareVersion=CharacterString('2.0'),
    protocolVersion=Unsigned(1),
    protocolRevision=Unsigned(22),
    maxApduLengthAccepted=Unsigned(1024),
    segmentationSupported=Enumerated(3),  # noSegmentation = 3
    databaseRevision=Unsigned(1),
)

def _send_ack(self, ack):
    self.response(ack)
    return





# --------------------------------------------------------------------
# 2️⃣ Application subclass that handles BACnet traffic
class FakeBACnetServer(BIPSimpleApplication):
    def _send_ack(self, ack):
        self.response(ack)
        print("sent ack")
        return
 

    def __init__(self, device, address):
        super().__init__(device, address)
                # --- 10 fake analog inputs ---
            
            
        # --- Sensor descriptors ---
        self.FD_MAP = {
            1: "LO2 PT-2902 Press Sensor  Mon",
            2: "LO2 PT-2903 Press Sensor  Mon",
            3: "LO2 PT-2904 Press Sensor  Mon",

            4: "GHe PT-1102 Press Sensor  Mon",
            5: "GHe PT-1103 Press Sensor  Mon",
            6: "GHe PT-1104 Press Sensor  Mon",

            7: "ECS HUM-2201 Humidity Sensor  Mon",
            8: "ECS HUM-2202 Humidity Sensor  Mon",
            9: "ECS HUM-2203 Humidity Sensor  Mon",
        }

        self.ai_objects = {}

        # --- Build BACnet AnalogInput objects ---
        for inst, fd_string in self.FD_MAP.items():
            from bacpypes.basetypes import StatusFlags, EventTransitionBits, TimeStamp, EngineeringUnits, NotifyType, EventState
            sensor_type = self.sensor_types[inst]
            unit_enum = self.unit_map[sensor_type]

            ai = AnalogInputObject(
                objectIdentifier=('analogInput', inst),
                objectName=f"{sensor_type.title()} Sensor {inst}",
                
                # temporary dummy until CCTK updates replace it
                presentValue=Real(0.0),

                statusFlags=StatusFlags([0, 0, 0, 0]),
                eventState=EventState(0),
                eventEnable=EventTransitionBits([0,0,0]),
                ackedTransitions=EventTransitionBits([0,0,0]),
                outOfService=Boolean(False),
                notificationClass=Unsigned(0),
                notifyType=1,
                units=EngineeringUnits(unit_enum),
            )

            self.add_object(ai)
            self.ai_objects[inst] = ai

            
        from bacpypes.object import AnalogValueObject
        from bacpypes.basetypes import StatusFlags, EventTransitionBits, TimeStamp, EngineeringUnits, NotifyType, EventState
        av = AnalogValueObject(
            objectIdentifier=('analogValue', 1),
            objectName=f"Test AV {1}",
            presentValue=Real(0.0),
            statusFlags=StatusFlags([0,0,0,0]),
            eventState=EventState(0),
            eventEnable=EventTransitionBits([0,0,0]),
            ackedTransitions=EventTransitionBits([0,0,0]),
            outOfService=Boolean(False),
            notificationClass=Unsigned(0),
            notifyType=1,
            units=EngineeringUnits(0),
        )

        self.add_object(av)
        threading.Thread(target=self._cctk_update_loop, daemon=True).start()

    def _cctk_update_loop(self):
        while True:
            for inst, ai_obj in self.ai_objects.items():
                fd_string = self.FD_MAP[inst]
                new_val = reader.read_fd(fd_string)
                if new_val is not None:
                    ai_obj.presentValue = float(new_val)
            time.sleep(0.5)



    # ✅ All incoming client requests (confirmed & unconfirmed)
    def indication(self, apdu):
        # --- Unconfirmed services ---
        if isinstance(apdu, ReadPropertyRequest):
            obj_id = apdu.objectIdentifier
            prop_id = apdu.propertyIdentifier
            print(f"🔍 ReadProperty from {apdu.pduSource}: {obj_id} {prop_id}")
        if isinstance(apdu, WhoIsRequest):
            print(f"📡 Who-Is from {apdu.pduSource}")


        elif isinstance(apdu, ReadPropertyMultipleRequest):
            print("📦 RPM received (device does NOT support RPM)")


        

        elif isinstance(apdu, SubscribeCOVRequest):
            print(f"🟦 SubscribeCOVRequest from {apdu.pduSource}")



        elif isinstance(apdu, UnconfirmedTextMessageRequest):
            print(f"💬 UnconfirmedText from {apdu.pduSource}: {apdu.message}")
        # --- Confirmed services ---
        elif isinstance(apdu, ReadPropertyRequest):
            obj_id = apdu.objectIdentifier
            prop_id = apdu.propertyIdentifier
            print(f"🔍 ReadProperty from {apdu.pduSource}: {obj_id} {prop_id}")

        elif isinstance(apdu, WritePropertyRequest):
            obj_id = apdu.objectIdentifier
            prop_id = apdu.propertyIdentifier
            value = apdu.propertyValue.cast_out(Real)
            print(f"✏️ WriteProperty from {apdu.pduSource}: {obj_id} {prop_id} = {value}")


        elif isinstance(apdu, ConfirmedTextMessageRequest):
            print(f"📨 ConfirmedText from {apdu.pduSource}: {apdu.message}")


        else:
            print(f"❓ Unknown APDU type: {apdu.__class__.__name__}")


        super().indication(apdu)
        return 
       




# --------------------------------------------------------------------
server = FakeBACnetServer(this_device, Address("127.0.0.1:47809"))
print("🚀 BACnet server running on UDP/47809 ...")
run()



