
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP, DES 

import socket
import random
import string
import time

from utils import *


def main():
    client_socket = tcp_init()

    # step 1
    client_name = client_socket.recv(1024)
    print("client name",client_name.decode('utf-8'))
    # decode to get client pub key
    nonce = client_socket.recv(10240)
    tag = client_socket.recv(10240)
    ciphertext = client_socket.recv(10240)
    key = password[0:16]

    client_pub_key = AES_decrypt(nonce, tag, key, ciphertext)
    client_pub_key_ = RSA.import_key(client_pub_key)
    print("client pub key" , client_pub_key)

    # step 2
    Ks = random_ks()
    print("Ks is" ,Ks)
    cipher_rsa = PKCS1_OAEP.new(client_pub_key_)
    data = cipher_rsa.encrypt(Ks)
    key = password[0:16]

    ciphertext, tag, nonce = AES_encrypt(key, data)
    client_socket.send(nonce)
    time.sleep(0.05)
    client_socket.send(tag)
    time.sleep(0.05)
    client_socket.send(ciphertext)
    
    #step3 revieve NA
    key = Ks[0:8]
    iv = client_socket.recv(10240)
    ciphertext = client_socket.recv(10240)
    NA = DES_decrypt(key, iv, ciphertext)
    print("NA is" ,NA)

    NB = random_ks()
    print("NB is" ,NB)
    key = Ks[0:8]
    data = NA + NB
    iv, ciphertext = DES_encrypt(key, data)
    client_socket.send(iv)
    # 防止粘包
    time.sleep(0.05)
    client_socket.send(ciphertext)
    
    # last step
    key = Ks[0:8]
    iv = client_socket.recv(10240)
    ciphertext = client_socket.recv(10240)

    client_nb = DES_decrypt(key, iv, ciphertext)
    if(client_nb == NB):
        print("pass test, session key is", Ks)
    else:
        print("fail test")
        print("client_nb is", client_nb)
        print("NB is", NB)

    
    # actual message test
    key = Ks[0:8]

    iv = client_socket.recv(10240)
    ciphertext = client_socket.recv(10240)  
    recieve_msg = DES_decrypt(key ,iv, ciphertext)
    print('msg recieved from client', recieve_msg.decode("utf-8"))

    # send data back
    iv, send_data = DES_encrypt(key,recieve_msg)
    client_socket.send(iv)
    time.sleep(0.05)
    client_socket.send(send_data)

    client_socket.close()


if __name__ == '__main__':
    main()
