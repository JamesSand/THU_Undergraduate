from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP, DES 

import socket
import random
import string
import time

password = "123456789101112131415".encode("utf-8")


def DES_encrypt(key, data):
    # padding to 8 bytes
    while len(data)%8 != 0:
        data += str("\0").encode("utf-8")

    des_cipher = DES.new(key, DES.MODE_CBC)
    ciphertext = des_cipher.encrypt(data)
    return des_cipher.iv, ciphertext

def DES_decrypt(key, iv, ciphertext):
	cipher = DES.new(key, DES.MODE_CBC, iv)
	return cipher.decrypt(ciphertext)

def AES_decrypt(nonce, tag, key, ciphertext):
    aes_cipher = AES.new(key, AES.MODE_EAX, nonce)
    plaintext = aes_cipher.decrypt_and_verify(ciphertext, tag)
    return plaintext

def AES_encrypt(key, data):
    aes_cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = aes_cipher.encrypt_and_digest(data)
    return ciphertext, tag, aes_cipher.nonce

def random_ks(length=16):
    pool = string.ascii_letters+string.digits
    key = random.sample(pool,length)
    keys = "".join(key)
    return keys.encode('utf-8')

def rsa_init():
    random_generator = Random.new().read
    rsa = RSA.generate(2048, random_generator)
    # 生成私钥
    private_key = rsa.exportKey()
    print(private_key.decode('utf-8'))
    # 生成公钥
    public_key = rsa.publickey().exportKey()
    print(public_key.decode('utf-8'))

    return private_key, public_key

def tcp_init():
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    address = ('127.0.0.1', 2333)
    tcp_server_socket.bind(address)
    print("wait for client")
    # 最大允许的等待数量为 1
    tcp_server_socket.listen(1)
    client_socket, clientAddr = tcp_server_socket.accept()
    print("client connected")
    return client_socket
