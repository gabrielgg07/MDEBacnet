#!/usr/bin/env python

"""CCTK Module is a library that provides an interface to the CCT Tcl API 

The interface object is CCTK(), which is a subclass of Tkinter.Tk. This allows
us to instantiate it once, set the paths and include the CCT provided library
and then use the interface repeatedly without setup/teardown costs for each 
transaction.

## References

### Reference for subclassing:
 * https://stackoverflow.com/questions/13282862/subclassing-tkinter-tcl


### Example from CCT's own documentation for using their API
 
 ```tcl
cctksh% ::cctk::GetFdInfo "CB2 Analog In 02  Mon"
des_header/ mdt_header/ eu sig_change_info/ max_change_info/ range_info/ except_sid current_value raw_value
```

```bash
echo '[GetFdInfo "CB2 Analog In 02  Mon" raw_value]' | CCTKsh
```
"""


import array
import binascii
import Tkinter

VERSION_NUMBER="1.7.1"
DEFAULT_KPATH="/var/local/home/ops1/Desktop/projects/UGFCS/UGFCS"


class CCTK(Tkinter.Tk, object):
    def __init__(self, KPATH=""):
        """If no KPATH is specified, CCTK requires the system's environment has
        KPATH set and pointing to an active project directory."""

        # Valid arguments for Tk.__init__()
        # screenName=None, baseName=None, className='Tk', useTk=1, sync=0, use=None):
        super(CCTK, self).__init__(useTk=0)
        # print("KPATH={0}".format(KPATH))
        if not KPATH:
            from os import environ
            environ['KPATH'] = KPATH
    
        kpath_set_cmd = "set ::env(KPATH) {0}".format(KPATH)
        self._query(kpath_set_cmd, debug_print=True)

        if KPATH.lower() == 'simulator':
            return
        
        # use cctk tcl package
        package_set_cmd = 'set resp [package require cctk]'
        self._query(package_set_cmd, debug_print=True)
        # '2.18.5'

    def _query(self, command, debug_print=False):
        ans = self._eval(command)
        if debug_print:
            print("{0} returned: {1}".format(command, ans))
        return ans
    
    def _eval(self, *args):
        """Internal method that serves as an injection point for unit testing.
        Never invoke this directly, instead please use the internal _query()
        method when extending this class."""
        return self.eval(*args)

    def getRaw(self, fd_string, return_hex=False, prepend_0x=False):
        '''Return a raw value as an int or as a hex string. The hex string 
        is returned with the msb on the left and lsb on the right. No readability
        swapping is required'''

        command = 'set ans [::cctk::GetFdInfo "{0}" raw_value]'.format(fd_string)
        #expect a string response
        ans = self._query(command=command)
        # print("Result of getRaw tcl query: {0}\nFor: {1}".format(ans, command))
        while len(ans) < 4:
            ans = '0' + ans

        # prepend '0' if odd-number of hex chars (make bytes!)
        if bool(len(ans) & 1): 
            ans = '0' + ans

        # received as endian-swapped (3412)
        hex_array = array.array('h', binascii.unhexlify(ans))
        hex_array.byteswap()
        hex_array.reverse()
        # endian swapped (1234)

        try:
            hex_str = hex_array.tostring().encode('hex').upper()
            if return_hex or prepend_0x:
                if prepend_0x:
                    hex_str = '0x' + hex_str
                
                return hex_str
            
            return int(hex_str, 16)
        except:
            # If that breaks, assume raw doesn't work and return none?
            print("Requested a raw value for FD: '{0}' and received a malformed response".format(fd_string) )
            return None
        
    def getProc(self, fd_string, fd_type=int):
        # type: (str, type) -> str
        command = 'set ans [::cctk::GetFdInfo "{0}" current_value]'.format(fd_string)
        return self._query(command=command)
    
    def getUnits(self, fd_string, default=""):
        # type: (str, str) -> int
        command = 'set ans [::cctk::GetFdInfo "{0}" eu]'.format(fd_string)
        ans = self._query(command=command)
        if not ans:
            ans = default
        return ans
    
    def GetMeasValue(self, meas_fd):
        return self.getProc(fd_string=meas_fd)
    
    def IssueCctkSysCmd(self, cmd_fd, *cmd_params):
        cmdstr = 'IssueCmd "{0}"'.format(cmd_fd)
        for param in cmd_params:
            cmdstr += " {0}".format(param)

        return self.eval(cmdstr)

    def dump_model(self):
        pass
    

if __name__ == "__main__":
    from time import sleep
    TESTFD = "LO2 PT-2902 Press Sensor  Mon"

    cct = CCTK(KPATH="/var/local/home/ops1/Desktop/projects/UGFCS/UGFCS")
    # cct = CCTK(KPATH="simulator")

    # Test State FDs
    tests = {
        "State 1":    ["ECS DCVNC-5245 State"],
        "Ind 1":      ["ECS DCVNC-5245 Ball Valve Open Ind"],
        "Ctl 1":      ["ECS DCVNC-5245 Ball Valve  Ctl", 1],
        "Ctl 2":      ["ECS DCVNC-5245 Ball Valve Close Ctl"],
        "Cmd 2":      ["LO2 Flow Control Cmd", 500, 600],
        "State 2":    ["Ghe DCVNO-4062 State"],
        "Ctl 4":      ["Ghe DCVNO-4062 Ball Valve Close Ctl"], # interlocked
        "State 3":    ["Ghe DCVNO-4062 State"],
        "Ctl 3":      ["Ghe DCVNO-4062 Ball Valve Open Ctl"], # interlocked
    }

    test_count = 0
    for k, v in tests.items():
        fd = v[0]
        params = v[1:]
        test_count+=1
        print("Test {0} - {1} : {2}".format(test_count, fd, params) )
        if any(substring in k for substring in ["Ctl", "Cmd"]): 
            print(cct.IssueCctkSysCmd(fd, *params))
            sleep(0.5)
        else:
            raw = cct.getRaw(fd)
            proc = cct.GetMeasValue(fd)
            print("    PROC : {0:13} type : {1:20}".format(proc, type(proc) ))
            print("    RAW  : {0:13} type : {1:20}".format(raw,  type(raw)  ))


    # fd = CCTFD(TESTFD, float)
    # print(fd.get_proc_value(cct))

    # 3qBdbccz
            
