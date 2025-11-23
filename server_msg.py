# server_msg.py
from bacpypes.core import run
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import WhoIsRequest, IAmRequest, ConfirmedTextMessageRequest, UnconfirmedTextMessageRequest
from bacpypes.pdu import Address

device = LocalDeviceObject(
    objectName="MessageServer",
    objectIdentifier=599,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15,
)

# a simple sensor store (fake sensors)
fake_sensors = {
    "temp": 22.5,
    "pressure": 101.3,
}

class MessageServer(BIPSimpleApplication):
    def indication(self, apdu):
        # discovery
        if isinstance(apdu, WhoIsRequest):
            iam = IAmRequest()
            iam.iAmDeviceIdentifier = device.objectIdentifier
            iam.maxAPDULengthAccepted = device.maxApduLengthAccepted
            iam.segmentationSupported = device.segmentationSupported
            iam.vendorID = device.vendorIdentifier
            iam.pduDestination = apdu.pduSource
            self.response(iam)
            return

        # incoming confirmed text message
        if isinstance(apdu, ConfirmedTextMessageRequest):
            # messageText is the field with the text
            text = getattr(apdu, "message", None)
            print(f"💬 Received text from {apdu.pduSource}: {text}")

            # optional: if client asked to READ <sensor>, print the value and (optionally) send back a text reply
            if text and text.upper().startswith("READ "):
                key = text.split(maxsplit=1)[1].strip()
                val = fake_sensors.get(key)
                if val is not None:
                    print(f"   → SENSOR {key} = {val}")
                    # send a reply text back to the client as a ConfirmedTextMessageRequest
                    reply = ConfirmedTextMessageRequest()
                    reply.pduDestination = apdu.pduSource
                    reply.messageText = f"{key} {val}"
                    # reply is a new confirmed request from server -> client; use request(...) wrapper here,
                    # but Confirmed requests normally need IOCB; BIPSimpleApplication.request will accept it if used properly.
                    # Simpler option: use response() to ACK the original request (but response only sends response APDU)
                    # For now, just print that we would reply:
                    print(f"   → would reply to {apdu.pduSource} with: {reply.messageText}")
                else:
                    print(f"   → unknown sensor: {key}")
            return


        # ---- unconfirmed text message handler ----
        if isinstance(apdu, UnconfirmedTextMessageRequest):
            text = getattr(apdu, "message", None)
            print(f"💬 [UNCONFIRMED] from {apdu.pduSource}: {text}")

            # interpret simple READ commands
            if text and text.upper().startswith("READ "):
                key = text.split(maxsplit=1)[1].strip()
                val = fake_sensors.get(key)
                if val is not None:
                    print(f"   → SENSOR {key} = {val}")
                else:
                    print(f"   → Unknown sensor: {key}")
            return
        

        super().indication(apdu)

app = MessageServer(device, Address("127.0.0.1:47808"))
print("✅ Message server ready on 127.0.0.1:47808")
run()
