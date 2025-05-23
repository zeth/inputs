import platform
import ctypes

WIN = True if platform.system() == 'Windows' else False
MAC = True if platform.system() == 'Darwin' else False
NIX = True if platform.system() == 'Linux' else False

if WIN:
    # pylint: disable=wrong-import-position
    import ctypes.wintypes
    DWORD = ctypes.wintypes.DWORD
    HANDLE = ctypes.wintypes.HANDLE
    WPARAM = ctypes.wintypes.WPARAM
    LPARAM = ctypes.wintypes.WPARAM
    MSG = ctypes.wintypes.MSG
else:
    DWORD = ctypes.c_ulong
    HANDLE = ctypes.c_void_p
    WPARAM = ctypes.c_ulonglong
    LPARAM = ctypes.c_ulonglong
    MSG = ctypes.Structure
