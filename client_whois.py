# client_whois.py
from bacpypes.core import run, deferred
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import WhoIsRequest, IAmRequest
from bacpypes.pdu import Address

device = LocalDeviceObject(
    objectName="LocalBACnetClient",
    objectIdentifier=600,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15,
)

class SimpleClient(BIPSimpleApplication):
    def confirmation(self, apdu):
        if isinstance(apdu, IAmRequest):
            print(f"👋 Got I-Am from {apdu.pduSource}")
            print(f"   → Device ID: {apdu.iAmDeviceIdentifier}")
            print(f"   → Vendor ID: {apdu.vendorID}")
        else:
            super().confirmation(apdu)

app = SimpleClient(device, Address("127.0.0.1:47809"))

def send_whois():
    req = WhoIsRequest()
    req.pduDestination = Address("127.0.0.1:47808")
    print("📡 Sending Who-Is request to 127.0.0.1:47808...")
    app.request(req)

send_whois()
run()


send_whois()
run()
