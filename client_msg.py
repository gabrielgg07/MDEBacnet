import threading
from bacpypes.core import run, stop, deferred
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import (
    UnconfirmedTextMessageRequest,
    ConfirmedTextMessageRequest,
)
from bacpypes.primitivedata import ObjectIdentifier, CharacterString, Enumerated
from bacpypes.pdu import Address
from bacpypes.iocb import IOCB

# ---- BACnet device setup ----
device = LocalDeviceObject(
    objectName="MessageClient",
    objectIdentifier=600,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15,
)

class MessageClient(BIPSimpleApplication):
    def confirmation(self, apdu):
        # this will trigger when a ConfirmedTextMessageRequest gets a response
        if hasattr(apdu, "messageText"):
            print(f"✅ Got reply from {apdu.pduSource}: {apdu.messageText}")
        else:
            print(f"ℹ️ Got confirmation from {apdu.pduSource}")

app = MessageClient(device, Address("127.0.0.1/24:47809"))

# ---- sending functions ----
def do_send_unconfirmed(text):
    apdu = UnconfirmedTextMessageRequest()
    apdu.pduDestination = Address("127.0.0.1:47808")
    apdu.textMessageSourceDevice = ObjectIdentifier(("device", device.objectIdentifier[1]))
    apdu.messagePriority = Enumerated(1)
    apdu.message = CharacterString(text)
    print(f"📤 [UNCONFIRMED] Sending: {text}")
    app.request(apdu)

def do_send_confirmed(text):
    apdu = ConfirmedTextMessageRequest()
    apdu.pduDestination = Address("127.0.0.1:47808")
    apdu.textMessageSourceDevice = ObjectIdentifier(("device", device.objectIdentifier[1]))
    apdu.messagePriority = Enumerated(1)
    apdu.message = CharacterString(text)
    iocb = IOCB(apdu)
    print(f"📤 [CONFIRMED] Sending: {text}")
    app.request_io(iocb)

# ---- scheduler wrapper ----
def send_text(text):
    if text.lower().startswith("conf:"):
        # send as confirmed
        deferred(do_send_confirmed, text[5:].strip())
    else:
        # send as unconfirmed by default
        deferred(do_send_unconfirmed, text)

# ---- user input thread ----
def input_loop():
    try:
        while True:
            s = input("> ").strip()
            if s:
                send_text(s)
    except KeyboardInterrupt:
        print("\n👋 Exiting.")
        deferred(stop)

# ---- start everything ----
threading.Thread(target=input_loop, daemon=True).start()
print("🚀 Type messages below.")
print("   • Normal input = UnconfirmedTextMessageRequest")
print("   • Prefix with 'conf:' = ConfirmedTextMessageRequest (e.g., conf: READ temp)")
run()
