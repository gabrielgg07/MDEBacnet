import threading
from bacpypes.core import run, stop, deferred
from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject
from bacpypes.apdu import (
    WhoIsRequest, IAmRequest,
    ReadPropertyRequest, WritePropertyRequest,
    ReadPropertyACK, SimpleAckPDU,
    UnconfirmedTextMessageRequest, ConfirmedTextMessageRequest,
)
from bacpypes.primitivedata import ObjectIdentifier, CharacterString, Enumerated, Real

from bacpypes.constructeddata import ArrayOf
from bacpypes.apdu import Error
from bacpypes.pdu import Address
from bacpypes.iocb import IOCB
from bacpypes.primitivedata import Real
from bacpypes.constructeddata import Any


# ---- BACnet device setup ----
device = LocalDeviceObject(
    objectName="CommandClient",
    objectIdentifier=600,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15,
)

# ---- Application ----
class CommandClient(BIPSimpleApplication):
    def confirmation(self, apdu):
        # Let BACpypes complete the IOCB first
        super().confirmation(apdu)
        # Handle replies to confirmed requests
        if isinstance(apdu, ReadPropertyACK):
            try:
                decoded_value = apdu.propertyValue.cast_out(ArrayOf(ObjectIdentifier))
            except:
                try:
                    # Try Real first
                    decoded_value = apdu.propertyValue.cast_out(Real)
                except Exception:
                    try:
                        # Then try CharacterString
                        from bacpypes.primitivedata import CharacterString, Enumerated, Unsigned
                        decoded_value = apdu.propertyValue.cast_out(CharacterString)
                    except Exception:
                        try:
                            decoded_value = apdu.propertyValue.cast_out(Enumerated)
                        except Exception:
                            try:
                                decoded_value = apdu.propertyValue.cast_out(Unsigned)
                            except Exception:
                                # fallback if unknown type
                                decoded_value = str(apdu.propertyValue)
            print(f"📥 ReadPropertyACK: {apdu.objectIdentifier} → {decoded_value}")




        elif isinstance(apdu, SimpleAckPDU):
            print("✅ SimpleAckPDU (WriteProperty or ConfirmedText ACK)")

        elif hasattr(apdu, "messageText"):
            print(f"💬 ConfirmedText Reply: {apdu.messageText}")
        else:
            print(f"ℹ️ Got confirmation from {apdu.pduSource}")

    def indication(self, apdu):
        # --- handle incoming unconfirmed messages like I-Am ---
        if isinstance(apdu, IAmRequest):
            device_id = apdu.iAmDeviceIdentifier
            vendor_id = apdu.vendorID
            src = apdu.pduSource
            print(f"📥 I-Am from {src} → device {device_id}, vendor {vendor_id}")

        elif isinstance(apdu, UnconfirmedTextMessageRequest):
            print(f"💬 UnconfirmedText from {apdu.pduSource}: {apdu.message}")

        else:
            # let BACpypes handle everything else
            super().indication(apdu)

app = CommandClient(device, Address("127.0.0.1/24:47809"))

# -------------------------------------------------------------------
# Command Functions
# -------------------------------------------------------------------

def send_whois():
    apdu = WhoIsRequest()
    apdu.pduDestination = Address("127.0.0.1")  # broadcast
    print("📡 Sending Who-Is...")
    app.request(apdu)

def send_iam():
    apdu = IAmRequest(
        iAmDeviceIdentifier=device.objectIdentifier,
        maxAPDULengthAccepted=device.maxApduLengthAccepted,
        segmentationSupported=device.segmentationSupported,
        vendorID=device.vendorIdentifier,
    )
    apdu.pduDestination = Address("255.255.255.255")
    print("📡 Sending I-Am...")
    app.request(apdu)

def send_unconfirmed_text(text):
    apdu = UnconfirmedTextMessageRequest()
    apdu.pduDestination = Address("127.0.0.1:47808")
    apdu.textMessageSourceDevice = ObjectIdentifier(("device", device.objectIdentifier[1]))
    apdu.messagePriority = Enumerated(1)
    apdu.message = CharacterString(text)
    print(f"📤 [UNCONFIRMED TEXT] {text}")
    app.request(apdu)

def send_confirmed_text(text):
    # always make a brand-new APDU and IOCB
    apdu = ConfirmedTextMessageRequest()
    apdu.pduDestination = Address("127.0.0.1:47808")
    apdu.textMessageSourceDevice = ObjectIdentifier(("device", device.objectIdentifier[1]))
    apdu.messagePriority = Enumerated(1)
    apdu.message = CharacterString(text)

    iocb = IOCB(apdu)           # 👈 brand-new IOCB each time

    # callback fires when the transaction completes
    def on_complete(iocb_result):
        if iocb_result.ioResponse:
            print("✅ ConfirmedText acknowledged")
        elif iocb_result.ioError:
            print(f"❌ ConfirmedText failed: {iocb_result.ioError}")
        else:
            print("⚠️ ConfirmedText no response / timeout")

    iocb.add_callback(on_complete)

    print(f"📤 [CONFIRMED] Sending: {text}")
    app.request_io(iocb)


def send_read(device_id, obj_type, obj_inst, prop_id):
    apdu = ReadPropertyRequest(
        objectIdentifier=(obj_type, int(obj_inst)),
        propertyIdentifier=prop_id
    )
    apdu.pduDestination = Address(f"127.0.0.1:47808")
    iocb = IOCB(apdu)
    print(f"🔍 Reading {obj_type}:{obj_inst} → {prop_id}")
    app.request_io(iocb)

def send_write(device_id, obj_type, obj_inst, prop_id, value):
    apdu = WritePropertyRequest()
    apdu.pduDestination = Address("127.0.0.1:47808")
    apdu.objectIdentifier = (obj_type, int(obj_inst))
    apdu.propertyIdentifier = prop_id

    # ✅ Wrap the value properly
    apdu.propertyValue = Any(Real(float(value)))

    iocb = IOCB(apdu)
    print(f"✏️ Writing {obj_type}:{obj_inst}.{prop_id} = {value}")
    app.request_io(iocb)

# -------------------------------------------------------------------
# Command Parser
# -------------------------------------------------------------------
def handle_command(cmd: str):
    parts = cmd.strip().split()
    if not parts:
        return

    c = parts[0].lower()

    if c == "whois":
        deferred(send_whois)
    elif c == "iam":
        deferred(send_iam)
    elif c == "text":
        deferred(send_unconfirmed_text, " ".join(parts[1:]))
    elif c == "conf:text":
        deferred(send_confirmed_text, " ".join(parts[1:]))

    # read <device_id> <obj_type> <obj_inst> <prop_id>
    elif c == "read" and len(parts) >= 6 and parts[1].lower() == "device":
        # e.g., read device 1234 analogInput 1 presentValue
        device_id = parts[2]
        obj_type = parts[3]
        obj_inst = parts[4]
        prop_id = parts[5]
        deferred(send_read, device_id, obj_type, obj_inst, prop_id)

    elif c == "write" and len(parts) >= 7 and parts[1].lower() == "device":
        # e.g., write device 1234 analogInput 1 presentValue 42.5
        device_id = parts[2]
        obj_type = parts[3]
        obj_inst = parts[4]
        prop_id = parts[5]
        value = " ".join(parts[6:])
        deferred(send_write, device_id, obj_type, obj_inst, prop_id, value)


    elif c in ("exit", "quit"):
        deferred(stop)
    else:
        print("❓ Unknown command. Try:")
        print("   whois")
        print("   read 1234 analogInput 1 presentValue")
        print("   write 1234 analogInput 1 presentValue 42.5")
        print("   text hello world")
        print("   conf:text urgent message")


# -------------------------------------------------------------------
# Input Thread
# -------------------------------------------------------------------
def input_loop():
    try:
        while True:
            s = input("> ").strip()
            if s:
                handle_command(s)
    except KeyboardInterrupt:
        print("\n👋 Exiting.")
        deferred(stop)

# -------------------------------------------------------------------
# Start
# -------------------------------------------------------------------
threading.Thread(target=input_loop, daemon=True).start()
print("🚀 Command Client Ready")
print("   Examples:")
print("     whois")
print("     read device 1234 analogInput 1 presentValue")
print("     write device 1234 analogInput 1 presentValue 42.5")
print("     text hello world")
print("     conf:text urgent message")
run()
