import ctypes
from datetime import datetime

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ('dwLength', ctypes.c_ulong),
        ('dwMemoryLoad', ctypes.c_ulong),
        ('ullTotalPhys', ctypes.c_ulonglong),
        ('ullAvailPhys', ctypes.c_ulonglong),
        ('ullTotalPageFile', ctypes.c_ulonglong),
        ('ullAvailPageFile', ctypes.c_ulonglong),
        ('ullTotalVirtual', ctypes.c_ulonglong),
        ('ullAvailVirtual', ctypes.c_ulonglong),
        ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
    ]

stat = MEMORYSTATUSEX()
stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))

total_ram = stat.ullTotalPhys / (1024**3)
free_ram = stat.ullAvailPhys / (1024**3)
used_ram = total_ram - free_ram
used_pct = stat.dwMemoryLoad
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

avail_pass = free_ram >= 2.50
usage_pass = used_pct <= 65
overall_pass = avail_pass and usage_pass

print("=" * 60)
print("       AICF STEP 1: RAM RECOVERY VERIFICATION")
print("=" * 60)
print(f"Timestamp:              {now_str}")
print(f"Total Physical RAM:     {total_ram:.2f} GB")
print(f"Available Physical RAM: {free_ram:.2f} GB")
print(f"Used Physical RAM:      {used_ram:.2f} GB")
print(f"Memory Usage:           {used_pct}%")
print("-" * 60)
print(f"Threshold 1 (Available RAM >= 2.50 GB): {'PASS' if avail_pass else 'BLOCKED'} ({free_ram:.2f} GB)")
print(f"Threshold 2 (Memory Usage <= 65%):      {'PASS' if usage_pass else 'BLOCKED'} ({used_pct}%)")
print("-" * 60)
print(f"DECISION: {'PASS - SAFE FOR INFERENCE VERIFICATION' if overall_pass else 'BLOCKED - DO NOT RUN INFERENCE'}")
print("=" * 60)
