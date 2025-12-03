

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

                

        # --- Realistic sensor categories ---
        self.sensors = {
            # temperature (°C)
            1:  random.uniform(18.0, 24.0),
            2:  random.uniform(18.0, 24.0),
            3:  random.uniform(18.0, 24.0),

            # pressure (kPa)
            4:  random.uniform(85.0, 110.0),
            5:  random.uniform(85.0, 110.0),
            6:  random.uniform(85.0, 110.0),

            # humidity (% RH)
            7:  random.uniform(35.0, 55.0),
            8:  random.uniform(35.0, 55.0),
            9:  random.uniform(35.0, 55.0),
        }

        # --- matching sensor metadata ---
        self.sensor_types = {
            1: "temperature", 2: "temperature", 3: "temperature",
            4: "pressure",    5: "pressure",    6: "pressure",
            7: "humidity",    8: "humidity",    9: "humidity",
        }

        # BACnet engineering units mapping
        self.unit_map = {
            "temperature": 62,   # degreesCelsius
            "pressure":    115,  # kilopascals
            "humidity":    29,   # percentRelativeHumidity
        }

        # start drift loop
        
        self.ai_objects = {}  # store references
        # --- Build REAL analog input objects ---
        for inst, value in self.sensors.items():
            from bacpypes.basetypes import StatusFlags, EventTransitionBits, TimeStamp, EngineeringUnits, NotifyType, EventState
            sensor_type = self.sensor_types[inst]
            unit_enum = self.unit_map[sensor_type]
            ai = AnalogInputObject(
                objectIdentifier=('analogInput', inst),
                objectName=f"{sensor_type.title()} Sensor {inst}",
                presentValue=Real(value),

                # ---- REQUIRED VALID BACNET TYPES ----
                statusFlags=StatusFlags([0, 0, 0, 0]),

                eventState=EventState(0),              # instead of 0
                eventEnable=EventTransitionBits([0,0,0]),
                ackedTransitions=EventTransitionBits([0,0,0]),
                outOfService=Boolean(False),

                notificationClass=Unsigned(0),

                notifyType=1,               # instead of Unsigned(1)

                # ---- FIXED! MUST BE EngineeringUnits ----
                units=EngineeringUnits(unit_enum),              # degreesCelsius
            )

            self.add_object(ai)
            self.ai_objects[inst] = ai

        threading.Thread(target=self._drift_loop, daemon=True).start()



    def _drift_loop(self):
        while True:
            for i, v in self.sensors.items():

                t = self.sensor_types[i]

                if t == "temperature":
                    drift = random.uniform(-0.05, 0.05)
                    new = max(10.0, min(35.0, v + drift))

                elif t == "pressure":
                    drift = random.uniform(-0.3, 0.3)
                    new = max(60.0, min(130.0, v + drift))

                elif t == "humidity":
                    drift = random.uniform(-0.4, 0.4)
                    new = max(10.0, min(90.0, v + drift))

                # SAVE internally
                self.sensors[i] = new

                # UPDATE BACnet object’s presentValue
                ai = self.ai_objects[i]
                ai.presentValue = Real(new)  # <-- THIS is what Ignition reads

            time.sleep(2)



    # ✅ All incoming client requests (confirmed & unconfirmed)
    def indication(self, apdu):
        # --- Unconfirmed services ---
        if isinstance(apdu, ReadPropertyRequest):
            obj_id = apdu.objectIdentifier
            prop_id = apdu.propertyIdentifier
            print(f"🔍 ReadProperty from {apdu.pduSource}: {obj_id} {prop_id}")

        if True:
            super().indication(apdu)
            return 
        print(f"received {apdu}")
        if isinstance(apdu, WhoIsRequest):
            print(f"📡 Who-Is from {apdu.pduSource}")

            i_am = IAmRequest(
                iAmDeviceIdentifier=self.localDevice.objectIdentifier,
                maxAPDULengthAccepted=self.localDevice.maxApduLengthAccepted,
                segmentationSupported=self.localDevice.segmentationSupported,
                vendorID=self.localDevice.vendorIdentifier,
            )

            # ✅ Use the real (ip, port) tuple — not the string
            dest_ip, dest_port = apdu.pduSource.addrTuple
            i_am.pduDestination = Address(f"{dest_ip}:{dest_port}")

            print(f"   ↩️  Replying to {dest_ip}:{dest_port}")
            self.request(i_am)
            print("✅ I-Am sent")


        elif isinstance(apdu, ReadPropertyMultipleRequest):
            print("📦 RPM received (device does NOT support RPM)")

            from bacpypes.apdu import Error
            from bacpypes.basetypes import ServicesSupported

            # Proper defined enum values
            error = Error(
                errorClass='services',
                errorCode='serviceRequestDenied',  # VALID enum
            )

            error.apduSource = apdu.pduSource

            self.response(error)
            print("❌ Sent proper RPM serviceRequestDenied error")
            return


        

        elif isinstance(apdu, SubscribeCOVRequest):
            print(f"🟦 SubscribeCOVRequest from {apdu.pduSource}")

            # Save the subscription (only one subscriber supported for simplicity)
            self.cov_subscriber = apdu.pduSource
            self.cov_object = apdu.monitoredObjectIdentifier
            self.cov_lifetime = apdu.lifetime

            # Must send ACK or Ignition will retry forever
            ack = SimpleAckPDU(context=apdu)
            self.response(ack)
            print("🟩 Sent COV ACK")
            return


        elif isinstance(apdu, UnconfirmedTextMessageRequest):
            print(f"💬 UnconfirmedText from {apdu.pduSource}: {apdu.message}")
        # --- Confirmed services ---
        elif isinstance(apdu, ReadPropertyRequest):
            obj_id = apdu.objectIdentifier
            prop_id = apdu.propertyIdentifier
            print(f"🔍 ReadProperty from {apdu.pduSource}: {obj_id} {prop_id}")

        if True:
            super().indication(apdu)
            return 
       

        elif isinstance(apdu, WritePropertyRequest):
            obj_id = apdu.objectIdentifier
            prop_id = apdu.propertyIdentifier
            value = apdu.propertyValue.cast_out(Real)
            print(f"✏️ WriteProperty from {apdu.pduSource}: {obj_id} {prop_id} = {value}")
            if obj_id[0] == "analogInput" and prop_id == "presentValue":
                self.sensors[obj_id[1]] = float(value)
            ack = SimpleAckPDU(context=apdu)
            self.response(ack)

        elif isinstance(apdu, ConfirmedTextMessageRequest):
            print(f"📨 ConfirmedText from {apdu.pduSource}: {apdu.message}")
            ack = SimpleAckPDU(context=apdu)
            self.response(ack)

        else:
            print(f"❓ Unknown APDU type: {apdu.__class__.__name__}")


# --------------------------------------------------------------------
server = FakeBACnetServer(this_device, Address("127.0.0.1:47809"))
print("🚀 BACnet server running on UDP/47809 ...")
run()



