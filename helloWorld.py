# helloWorld.py
from bacpypes.core import run
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import UnconfirmedTextMessageRequest
from bacpypes.primitivedata import ObjectIdentifier, CharacterString, Enumerated
from bacpypes.pdu import Address

# Define local BACnet device
device = LocalDeviceObject(
    objectName="MessageClient",
    objectIdentifier=600,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15,
)

class RawClient(BIPSimpleApplication):
    pass

app = RawClient(device, Address("127.0.0.1/24:47809"))

# ---- Build a fully valid UnconfirmedTextMessageRequest ----
apdu = UnconfirmedTextMessageRequest()
apdu.pduDestination = Address("127.0.0.1:47808")

# Required fields
apdu.textMessageSourceDevice = ObjectIdentifier(('device', device.objectIdentifier[1]))
apdu.messagePriority = Enumerated(1)             # ✅ must be Enumerated, not int
apdu.message = CharacterString("HELLO_WORLD")

print("📤 Sending UnconfirmedTextMessageRequest...")
app.request(apdu)

run()
