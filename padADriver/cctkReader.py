# cct_wrapper.py
from cctk import CCTK

class CCTReader:
    def __init__(self, kpath):
        self.cct = CCTK(KPATH=kpath)

    def read_fd(self, fd):
        """Return processed value (string/number)."""
        try:
            return self.cct.getProc(fd)
        except:
            return None

    def read_raw(self, fd):
        """Return raw int value."""
        try:
            return self.cct.getRaw(fd)
        except:
            return None

    def read_units(self, fd):
        try:
            return self.cct.getUnits(fd)
        except:
            return ""
