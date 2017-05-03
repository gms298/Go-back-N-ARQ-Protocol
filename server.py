from socket import *
from decimal import *
import os 
import random
import time
import sys

# Collect CLI arguments
f_name = sys.argv[2]
probability = float(sys.argv[3])
port = int(sys.argv[1])
hostname = ""

# Method to send to client
def rdt_send(msg,s_counter):
	if msg:	
		seq_no = str(int(msg[0:32],2))
		expected_seq = s_counter
		# print "Waiting on Sequence #" + str(expected_seq)	
		send_seq_no = '{0:032b}'.format(int(seq_no))
		pad = '0' * 16
		ack_ind = '10' * 8
		return send_seq_no + pad + ack_ind
	else:
		return ''

# Calculate the checksum
def checksum_gen(temp_msg):
	if temp_msg[48:64] == '01' * 8:
		total = 0
		data = [temp_msg[i:i+16] for i in range(0,len(temp_msg),16)]
		for d in data:
			total += int(d,2)
			if total >= 65535:
				total -= 65535
			if total == 0:
				return 1
			else:
				return -1
	else:
		return -1

# Write to File
def f_write(msg,f_name):
	f_ptr = open(f_name,'a')
	temp_msg = str(msg[64:])
	temp = len(temp_msg)/8
	to_write = ''
	for i in range(0,temp):
		bit_data = str(temp_msg[i*8:(i+1)*8])
		char_data = chr(int(bit_data, 2))
		to_write = to_write + char_data
	f_ptr.write(to_write)
	f_ptr.close()

# Return Random number
def random_num():
	while 1:
		generated_number = random.random()
		if Decimal(generated_number) != Decimal(0.0):
			break
	return generated_number

# Communication
s = socket(AF_INET,SOCK_DGRAM)
s.bind((hostname,port))
print ("Listening for client requests ... ")
s_counter = 0
while 1:
	msg, client_address = s.recvfrom(65535)
	rnum = random_num()
	if rnum > probability:
		checksum = checksum_gen(msg)
		if checksum == 1 and msg[48:64] == '01' * 8:
			got_seq_no = int(msg[0:32],2)
			if got_seq_no == s_counter:
				to_send = rdt_send(msg,s_counter)
				if to_send:
					s.sendto(to_send, client_address)
					f_write(msg,f_name)
					s_counter = s_counter + 1
			elif got_seq_no > s_counter:
				print ("Packet loss, sequence number = " + str(got_seq_no))
			elif got_seq_no < s_counter:
				to_send = rdt_send(msg,s_counter)
				if to_send:
					# print ("Retransmitted ACK - " + str(got_seq_no))
					s.sendto(to_send, client_address)
		else:
			print ("Checksum invalid. Packet dropped.")
	else:
		got_seq_no = int(msg[0:32],2)
		print ("Packet loss, sequence number = " + str(got_seq_no))

s.close()