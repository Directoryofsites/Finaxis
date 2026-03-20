
import psutil
import sys

pid = 23168
try:
    process = psutil.Process(pid)
    print(f"PID: {pid}")
    print(f"Name: {process.name()}")
    print(f"CWD: {process.cwd()}")
    print(f"CommandLine: {process.cmdline()}")
except Exception as e:
    print(f"Error: {e}")
