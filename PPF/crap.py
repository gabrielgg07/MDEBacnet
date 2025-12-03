   def get_property_value(self, obj_id, prop_id):
        """Return correct BACnet typed value for RPM requests."""

        # -----------------------------
        # ANALOG INPUT OBJECTS
        # -----------------------------
        if obj_id[0] == "analogInput":
            idx = obj_id[1]
            t = self.sensor_types[idx]

            if prop_id == "objectName":
                return CharacterString(f"{t.capitalize()} Sensor {idx}")

            elif prop_id == "description":
                desc = {
                    "temperature": "Air Temperature Sensor (°C)",
                    "pressure":    "Line Pressure Sensor (kPa)",
                    "humidity":    "Relative Humidity Sensor (%)",
                }[t]
                return CharacterString(desc)

            elif prop_id == "presentValue":
                return Real(self.sensors[idx])

            elif prop_id == "units":
                unit_map = {
                    "temperature": 62,
                    "pressure":    53,
                    "humidity":    29,
                }
                return Enumerated(unit_map[t])

            elif prop_id == "outOfService":
                from bacpypes.primitivedata import Boolean
                return Boolean(False)

            elif prop_id == "propertyList":
                from bacpypes.constructeddata import ArrayOf
                from bacpypes.basetypes import PropertyIdentifier
                props = [
                    "objectIdentifier",
                    "objectName",
                    "description",
                    "presentValue",
                    "units",
                    "outOfService",
                ]
                return ArrayOf(PropertyIdentifier)(props)

            # fallback
            return CharacterString("N/A")

        # -----------------------------
        # DEVICE OBJECT
        # -----------------------------
        dev = self.localDevice

        # things Ignition ALWAYS asks for
        if prop_id == "objectIdentifier":
            return dev.objectIdentifier

        if prop_id == "objectName":
            return CharacterString(dev.objectName)

        if prop_id == "systemStatus":
            return Enumerated(0)

        if prop_id == "vendorName":
            return CharacterString(dev.vendorName)

        if prop_id == "vendorIdentifier":
            return Unsigned(dev.vendorIdentifier)

        if prop_id == "modelName":
            return CharacterString(str(dev.modelName))

        if prop_id == "firmwareRevision":
            return CharacterString(str(dev.firmwareRevision))

        if prop_id == "applicationSoftwareVersion":
            return CharacterString(str(dev.applicationSoftwareVersion))

        if prop_id == "protocolVersion":
            return Unsigned(dev.protocolVersion)

        if prop_id == "protocolRevision":
            return Unsigned(dev.protocolRevision)

        if prop_id == "maxApduLengthAccepted":
            return Unsigned(dev.maxApduLengthAccepted)

        if prop_id == "databaseRevision":
            return Unsigned(dev.databaseRevision)

        if prop_id == "segmentationSupported":
            return dev.segmentationSupported  # already BACnet type

        if prop_id == "serialNumber":
            return CharacterString("SN-PPF-001")

        if prop_id == "apduTimeout":
            return Unsigned(3000)

        if prop_id == "numberOfApduRetries":
            return Unsigned(3)

        if prop_id == "propertyList":
            from bacpypes.constructeddata import ArrayOf
            from bacpypes.basetypes import PropertyIdentifier
            props = [
                "objectIdentifier",
                "objectName",
                "systemStatus",
                "vendorName",
                "vendorIdentifier",
                "modelName",
                "firmwareRevision",
                "applicationSoftwareVersion",
                "protocolVersion",
                "protocolRevision",
                "maxApduLengthAccepted",
                "segmentationSupported",
                "databaseRevision",
                "serialNumber",
                "apduTimeout",
                "numberOfApduRetries",
                "objectList",
            ]
            return ArrayOf(PropertyIdentifier)(props)

        # default
        return CharacterString("N/A")





 elif isinstance(apdu, ReadPropertyRequest):
            obj_id = apdu.objectIdentifier
            prop_id = apdu.propertyIdentifier
            print(f"🔍 ReadProperty from {apdu.pduSource}: {obj_id} {prop_id}")

            ack = ReadPropertyACK(context=apdu)
            ack.objectIdentifier = obj_id
            ack.propertyIdentifier = prop_id


            # -------------------------------
            # ANALOG INPUTS
            # -------------------------------
            if obj_id[0] == "analogInput":
                ai_index = obj_id[1]
                sensor_type = self.sensor_types[ai_index]

                # -- objectName --
                if prop_id == "objectName":
                    names = {
                        "temperature": f"Temp Sensor {ai_index}",
                        "pressure":    f"Pressure Sensor {ai_index-3}",
                        "humidity":    f"Humidity Sensor {ai_index-6}",
                    }
                    ack.propertyValue = Any(CharacterString(names[sensor_type]))
                    return self._send_ack(ack)

                # -- description --
                if prop_id == "description":
                    desc = {
                        "temperature": "Air Temperature Sensor (°C)",
                        "pressure":    "Line Pressure Sensor (kPa)",
                        "humidity":    "Relative Humidity Sensor (%)",
                    }
                    ack.propertyValue = Any(CharacterString(desc[sensor_type]))
                    return self._send_ack(ack)

                # -- presentValue --
                if prop_id == "presentValue":
                    ack.propertyValue = Any(Real(self.sensors.get(ai_index, 0.0)))
                    return self._send_ack(ack)

                # -- units --
                if prop_id == "units":
                    unit_map = {
                        "temperature": 62,  # degreesCelsius
                        "pressure":    53,  # kilopascals
                        "humidity":    29,  # percent
                    }
                    ack.propertyValue = Any(Enumerated(unit_map[sensor_type]))
                    return self._send_ack(ack)

                    # required by Ignition
                if prop_id == "statusFlags":
                    print("STATUS FLAGS HIT!")
                    from bacpypes.basetypes import StatusFlags
                    # (inOrder, fault, overridden, outOfService)
                    flags = StatusFlags([0, 0, 0, 0])   # all false
                    ack.propertyValue = Any(flags)
                    return self._send_ack(ack)
                


                if prop_id == "eventState":
                    from bacpypes.basetypes import EventState
                    ack.propertyValue = Any(EventState(0))  # normal = 0
                    return self._send_ack(ack)


                if prop_id == "outOfService":
                    print("calling out of service")
                    ack.propertyValue = Any(Boolean(False))
                    return self._send_ack(ack)
                if prop_id == "notifyType":
                    # 0 = alarm, 1 = event, 2 = ackNotification
                    ack.propertyValue = Any(Enumerated(1))   # "event"
                    return self._send_ack(ack)
                if prop_id == "eventEnable":
                    from bacpypes.basetypes import EventTransitionBits
                    bits = EventTransitionBits([0, 0, 0])   # toOffnormal, toFault, toNormal
                    
                    ack.propertyValue = Any(bits)

                    return self._send_ack(ack)
                if prop_id == "ackedTransitions":
                    from bacpypes.basetypes import EventTransitionBits
                    print("trans")
                    ack.propertyValue = Any(EventTransitionBits([0, 0, 0]))  # all transitions acked
             

                    return self._send_ack(ack)
                if prop_id == "eventTimeStamps":
                    from bacpypes.basetypes import TimeStamp

                    ts = TimeStamp(sequenceNumber=Unsigned(0))

                    # a proper BACnet SEQUENCE OF TimeStamp
                    EventTSArray = ArrayOf(TimeStamp)

                    arr = EventTSArray([ts, ts, ts])

                    ack.propertyValue = Any(arr)
                    return self._send_ack(ack)

                if prop_id == "notificationClass":
                    ack.propertyValue = Any(Unsigned(0))
                    return self._send_ack(ack)



                if prop_id == "priorityArray":
                #    from bacpypes.constructeddata import ArrayOf
                 #   from bacpypes.primitivedata import Null
                    PA = ArrayOf(Null)
                    arr = PA([Null()] * 16)   # 16 BACnet priorities
                    ack.propertyValue = Any(arr)
                    return self._send_ack(ack)


                # -- propertyList --
                if prop_id == "propertyList":
                    props = [
                        "objectIdentifier",
                        "objectName",
                        "presentValue",
                        "units",
                        "statusFlags",
                        "eventState",
                        "eventEnable",
                        "ackedTransitions",
                        "outOfService",
                        "notificationClass",
                        "notifyType",
                        "eventTimeStamps",
                    ]
                    arr = ArrayOf(PropertyIdentifier)(props)
                    ack.propertyValue = Any(arr)
                    return self._send_ack(ack)

                # fallback
                ack.propertyValue = Any(Real(0.0))
                return self._send_ack(ack)

            # ---------------------------------------------------
            # DEVICE OBJECT
            # ---------------------------------------------------
            elif obj_id[0] == "device":
                dev = self.localDevice

                # required scalar properties
                if prop_id == "objectIdentifier":
                    ack.propertyValue = Any(dev.objectIdentifier)
                    return self._send_ack(ack)

                if prop_id == "objectName":
                    ack.propertyValue = Any(CharacterString(dev.objectName))
                    return self._send_ack(ack)

                if prop_id == "systemStatus":
                    ack.propertyValue = Any(dev.systemStatus)
                    return self._send_ack(ack)


                if prop_id == "vendorName":
                    ack.propertyValue = Any(CharacterString(dev.vendorName))
                    return self._send_ack(ack)

                if prop_id == "vendorIdentifier":
                    ack.propertyValue = Any(Unsigned(dev.vendorIdentifier))
                    return self._send_ack(ack)

                if prop_id == "model-name":
                    ack.propertyValue = Any(CharacterString(str(dev.modelName)))
                    return self._send_ack(ack)

                if prop_id == "firmwareRevision":
                    ack.propertyValue = Any(CharacterString(dev.firmwareRevision))
                    return self._send_ack(ack)

                if prop_id == "applicationSoftwareVersion":
                    ack.propertyValue = Any(CharacterString(dev.applicationSoftwareVersion))
                    return self._send_ack(ack)

                if prop_id == "protocolVersion":
                    ack.propertyValue = Any(Unsigned(dev.protocolVersion))
                    return self._send_ack(ack)

                if prop_id == "protocolRevision":
                    ack.propertyValue = Any(Unsigned(dev.protocolRevision))
                    return self._send_ack(ack)

                if prop_id == "maxApduLengthAccepted":
                    ack.propertyValue = Any(Unsigned(dev.maxApduLengthAccepted))
                    return self._send_ack(ack)

                if prop_id == "segmentationSupported":
                    ack.propertyValue = Any(dev.segmentationSupported)
                    return self._send_ack(ack)

                if prop_id == "databaseRevision":
                    ack.propertyValue = Any(Unsigned(dev.databaseRevision))
                    return self._send_ack(ack)

                if prop_id == "serialNumber":
                    ack.propertyValue = Any(CharacterString("SN-001"))
                    return self._send_ack(ack)

                if prop_id == "apduTimeout":
                    ack.propertyValue = Any(Unsigned(3000))
                    return self._send_ack(ack)

                if prop_id == "numberOfApduRetries":
                    ack.propertyValue = Any(Unsigned(3))
                    return self._send_ack(ack)

                if prop_id == "objectList":
                    objs = [("device", dev.objectIdentifier[1])]
                    objs += [("analogInput", i) for i in self.sensors.keys()]
                    print("OBJECT LIST SENT:", objs)
                    arr = ArrayOf(ObjectIdentifier)(objs)
                    ack.propertyValue = Any(arr)
                    return self._send_ack(ack)

                if prop_id == "propertyList":
                    props = [
                        "objectIdentifier",
                        "objectName",
                        "systemStatus",
                        "vendorName",
                        "vendorIdentifier",
                        "modelName",
                        "firmwareRevision",
                        "applicationSoftwareVersion",
                        "protocolVersion",
                        "protocolRevision",
                        "maxApduLengthAccepted",
                        "segmentationSupported",
                        "databaseRevision",
                        "serialNumber",
                        "apduTimeout",
                        "numberOfApduRetries",
                        "objectList",
                    ]
                    arr = ArrayOf(PropertyIdentifier)(props)
                    ack.propertyValue = Any(arr)
                    return self._send_ack(ack)

                if prop_id == "protocolServicesSupported":
                    print("⚙️ protocolServicesSupported requested")

                    from bacpypes.basetypes import ServicesSupported
                    s = ServicesSupported()

                    s.whoIs = 1
                    s.iAm = 1
                    s.readProperty = 1
                    s.writeProperty = 1

                    # disable everything else
                    s.readPropertyMultiple = 0
                    s.writePropertyMultiple = 0
                    s.readRange = 0
                    s.reinitializeDevice = 0
                    s.atomicReadFile = 0
                    s.atomicWriteFile = 0
                    s.createObject = 0
                    s.deleteObject = 0
                    s.subscribeCOV = 0
                    s.confirmedCOVNotification = 0
                    s.unconfirmedCOVNotification = 0
                    s.iHave = 0

                    ack.propertyValue = Any(s)
                    print("⚙️ Sent protocolServicesSupported = RPM DISABLED")
                    return self._send_ack(ack)

                # fallback
                ack.propertyValue = Any(CharacterString("N/A"))
                return self._send_ack(ack)
