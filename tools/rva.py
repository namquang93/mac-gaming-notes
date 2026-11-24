#!/usr/bin/env python3
"""Print the 32-bit value (and any C string) stored at one or more RVAs in a PE file.

Use it to read exported data such as D3D12SDKVersion from a game exe:

    objdump -p Game.exe | grep -A4 "Export Table"   # note the RVA of D3D12SDKVersion
    python3 rva.py Game.exe 2717050                 # -> 2717050 611 ...
"""
import struct
import sys


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(f"usage: {sys.argv[0]} <file.exe|file.dll> <rva-hex> [rva-hex ...]")
    with open(sys.argv[1], "rb") as f:
        data = f.read()

    pe = struct.unpack_from("<I", data, 0x3C)[0]
    nsections = struct.unpack_from("<H", data, pe + 6)[0]
    opt_size = struct.unpack_from("<H", data, pe + 20)[0]
    sections = pe + 24 + opt_size

    def to_offset(rva: int):
        for i in range(nsections):
            vsize, vaddr, rsize, rptr = struct.unpack_from("<IIII", data, sections + 40 * i + 8)
            if vaddr <= rva < vaddr + max(vsize, rsize):
                return rva - vaddr + rptr
        return None

    for arg in sys.argv[2:]:
        rva = int(arg.removeprefix("0x"), 16)
        off = to_offset(rva)
        if off is None:
            print(arg, "not in any section")
            continue
        value = struct.unpack_from("<I", data, off)[0]
        text = data[off:off + 64].split(b"\0")[0]
        print(arg, value, text)


if __name__ == "__main__":
    main()
