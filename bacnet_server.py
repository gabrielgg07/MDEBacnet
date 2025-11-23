

# --- patch CharacterString early ---
from bacpypes.primitivedata import CharacterString
from bacpypes.core import run
import time, random, threading
from bacpypes.pdu import Address
from bacpypes.app import BIPSimpleApplication
from bacpypes.constructeddata import ArrayOf
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import (
    WhoIsRequest, IAmRequest,
    ReadPropertyRequest, ReadPropertyACK,
    WritePropertyRequest, SimpleAckPDU,
    UnconfirmedTextMessageRequest, ConfirmedTextMessageRequest
)
from bacpypes.primitivedata import Real
from bacpypes.constructeddata import Any
from bacpypes.apdu import Error
from bacpypes.primitivedata import  Unsigned, Enumerated, Tag
try:
    # ✅ newer bacpypes (≥0.20)
    from bacpypes.basetypes import PropertyIdentifier
except ImportError:
    # ✅ fallback for older bacpypes
    from bacpypes.primitivedata import PropertyIdentifier

# --------------------------------------------------------------------
# 1️⃣ Configure fake device
from bacpypes.object import DeviceObject

def make_ansi_string(text: str):
    """Force ANSI (encoding=0) CharacterString compatible with BACnet 4J."""
    encoded = text.encode("ascii", errors="ignore")
    tag = Tag(Tag.applicationTagClass, Tag.characterStringAppTag, len(encoded) + 1, bytes([0]) + encoded)
    any_val = Any()
    any_val.tagList = [tag]
    return any_val


this_device = DeviceObject(
    objectIdentifier=('device', 1234),        # must match Ignition’s Remote Device ID
    objectName='FakeSensorDevice',
    systemStatus='operational',
    vendorName='PythonSim',
    vendorIdentifier=999,
    modelName='BACpypes Fake Device',
    firmwareRevision='1.0',
    applicationSoftwareVersion='1.0',
    protocolVersion=1,
    protocolRevision=22,
    maxApduLengthAccepted=1024,
    segmentationSupported='noSegmentation',
    databaseRevision=1,
)






# --------------------------------------------------------------------
# 2️⃣ Application subclass that handles BACnet traffic
class FakeBACnetServer(BIPSimpleApplication):

    def __init__(self, device, address):
        super().__init__(device, address)
                # --- 10 fake analog inputs ---
        self.sensors = {i: random.uniform(20.0, 25.0) for i in range(1, 11)}

        # start background thread to drift values
        threading.Thread(target=self._drift_loop, daemon=True).start()

    def _drift_loop(self):
        while True:
            for k in self.sensors:
                self.sensors[k] += random.uniform(-0.1, 0.1)
                self.sensors[k] = max(15.0, min(30.0, self.sensors[k]))
            time.sleep(2)

    # ✅ All incoming client requests (confirmed & unconfirmed)
    def indication(self, apdu):
        # --- Unconfirmed services ---
        print("received something?")
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


        elif isinstance(apdu, UnconfirmedTextMessageRequest):
            print(f"💬 UnconfirmedText from {apdu.pduSource}: {apdu.message}")
        # --- Confirmed services ---
        elif isinstance(apdu, ReadPropertyRequest):
            obj_id = apdu.objectIdentifier
            prop_id = apdu.propertyIdentifier
            print(f"🔍 ReadProperty from {apdu.pduSource}: {obj_id} {prop_id}")

            ack = ReadPropertyACK(context=apdu)
            ack.objectIdentifier = obj_id
            ack.propertyIdentifier = prop_id



            # --- analogInput.presentValue (scalar Real) ---
            if obj_id[0] == "analogInput":
                if prop_id == "objectName":
                    ack.propertyValue = make_ansi_string(f"Sensor {obj_id[1]}")
                    # Respond
                    self.response(ack)
                    print(f"✅ Sent proper ANSI objectName for analogInput {obj_id[1]}")
                    return
                elif prop_id == "description":
                    ack.propertyValue = make_ansi_string(f"Temperature sensor #{obj_id[1]}")
                    self.response(ack)
                    print(f"✅ Sent description for analogInput {obj_id[1]}")
                    return
                elif prop_id == "units":
                    ack.propertyValue = Any(Enumerated(62))  # degrees Celsius
                elif prop_id == "presentValue":
                    ack.propertyValue = Any(Real(self.sensors.get(obj_id[1], 0.0)))
                elif prop_id == "propertyList":
                    print("ran property list")
                    # list the properties this object supports
                    props = [
                        "objectIdentifier",
                        "objectName",
                        "presentValue",
                        "units",
                    ]
                    value = ArrayOf(PropertyIdentifier)(props)
                    ack.propertyValue = Any(value)
                else:
                    ack.propertyValue = Any(Real(0.0))



                value = Real(self.sensors[obj_id[1]])
                ack.propertyValue = Any(value)
            elif obj_id[0] == "device":
                if prop_id == "objectName":
                    ack.propertyValue = make_ansi_string("FakeSensorDevice")
                elif prop_id == "databaseRevision":
                    ack.propertyValue = Any(Unsigned(1))
                    self.response(ack)
                    print("✅ Sent databaseRevision = 1")
                    return
                elif prop_id == "modelName":
                    ack.propertyValue = Any(CharacterString(0, "PythonSim v1.0"))
                elif prop_id == "vendorIdentifier":
                    ack.propertyValue = Any(Unsigned(this_device.vendorIdentifier))
                elif prop_id == "firmwareRevision":
                    ack.propertyValue = Any(CharacterString(0, "1.0.0"))
                elif prop_id == "systemStatus":
                    ack.propertyValue = Any(Enumerated(0))  # 0 = operational
                elif prop_id == "objectList":
                    from bacpypes.constructeddata import ArrayOf
                    from bacpypes.primitivedata import ObjectIdentifier
                    objs = [("device", self.localDevice.objectIdentifier[1])]
                    objs += [("analogInput", i) for i in self.sensors.keys()]
                    value = ArrayOf(ObjectIdentifier)(objs)
                    ack.propertyValue = Any(value)
                else:
                    ack.propertyValue = Any(Real(0.0))
            else:
                ack.propertyValue = Any(Real(0.0))

            self.response(ack)


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
server = FakeBACnetServer(this_device, Address("127.0.0.1:47808"))
print("🚀 BACnet server running on UDP/47808 ...")
run()
