# server_whois.py
from bacpypes.core import run
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import WhoIsRequest, IAmRequest
from bacpypes.pdu import Address

device = LocalDeviceObject(
    objectName="LocalBACnetServer",
    objectIdentifier=599,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15,
)

class SimpleServer(BIPSimpleApplication):
    def indication(self, apdu):
        # Handle Who-Is -> reply with I-Am
        if isinstance(apdu, WhoIsRequest):
            print(f"📥 Received Who-Is from {apdu.pduSource}")
            iam = IAmRequest()
            iam.iAmDeviceIdentifier = device.objectIdentifier
            iam.maxAPDULengthAccepted = device.maxApduLengthAccepted
            iam.segmentationSupported = device.segmentationSupported
            iam.vendorID = device.vendorIdentifier
            iam.pduDestination = apdu.pduSource
            print(f"📤 Sending I-Am to {apdu.pduSource}")
            self.response(iam)
        else:
            super().indication(apdu)

app = SimpleServer(device, Address("127.0.0.1:47808"))
print("✅ Server ready on 127.0.0.1:47808")
run()
