
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP, DES 

import socket
import random
import string
import time

from utils import *

def main():
	private_key, public_key = rsa_init()
	private_key_ = RSA.import_key(private_key)
	public_key_ = RSA.import_key(public_key)

	tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_addr = ("127.0.0.1", 2333)
	tcp_socket.connect(server_addr)
	print("connect to server")

	#step1
	name = "A"
	tcp_socket.send(name.encode("utf-8"))

	key = password[0:16]

	ciphertext, tag, nonce = AES_encrypt(key, public_key)

	tcp_socket.send(nonce)
	time.sleep(0.05)
	tcp_socket.send(tag)
	time.sleep(0.05)
	tcp_socket.send(ciphertext)


	#step3
	nonce = tcp_socket.recv(10240)
	tag = tcp_socket.recv(10240)
	ciphertext = tcp_socket.recv(10240)
	key = password[0:16]

	data = AES_decrypt(nonce, tag, key, ciphertext)

	cipher_rsa = PKCS1_OAEP.new(private_key_)
	Ks = cipher_rsa.decrypt(data)
	print("Ks is" ,Ks)

	N_A = random_ks()
	print("NA is" ,N_A)
	key = Ks[0:8]
	iv, ciphertext = DES_encrypt(key, N_A)
	tcp_socket.send(iv)
	time.sleep(0.05)
	tcp_socket.send(ciphertext)
	
	#step5
	key = Ks[0:8]
	iv = tcp_socket.recv(10240)
	ciphertext = tcp_socket.recv(10240)
	# data = NA + NB
	data = DES_decrypt(key, iv, ciphertext)
	server_na = data[:len(N_A)]
	if N_A == server_na:
		print("pass test, session key is", Ks)
	else:
		print("fail test")
		print("server na is", server_na)
		print("client na is", N_A)
	N_B = data[len(N_A):]
	print("NB is" ,N_B)

	key = Ks[0:8]

	iv, ciphertext = DES_encrypt(key, N_B)
	tcp_socket.send(iv)
	time.sleep(0.05)
	tcp_socket.send(ciphertext)

	# actual msg test
	key = Ks[0:8]
	send_data = input("input msg send to server: ").encode("utf-8")
	iv, send_data = DES_encrypt(key,send_data)
	tcp_socket.send(iv)
	time.sleep(0.05)
	tcp_socket.send(send_data)
	iv = tcp_socket.recv(10240)
	ciphertext = tcp_socket.recv(10240)  
	recv_data = DES_decrypt(key ,iv, ciphertext).decode("utf-8")
	print('data revieved from server:', recv_data)

	tcp_socket.close()


if __name__ == "__main__":
	main()
