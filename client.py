import os
import fcntl
import re
import psutil
import sys
import time

from socket import *

# File path for storing sequence numbers
tempfile = ""

# Send to Server
def rdt_send(file_name,mss,seq_no):
	segment_data = ''
	with open(file_name, "rb") as fptr:		
		position = seq_no * mss
        	fptr.seek(position,0)
        	for i in range(1,mss+1):
			byte_data = fptr.read(1)
            		if byte_data:
				segment_data = segment_data + str(byte_data)
	fptr.close()        
	segment = make_packet(seq_no,segment_data)
	checked_data = compute_checksum(segment)       
	return checked_data

# Checksum
def compute_checksum(message):
        if message:
		total = 0	
                data = [message[i:i+16] for i in range(0,len(message),16)]
                for y in data:
			total += int(y,2)
			if total >= 65535:
				total -= 65535
		checksum = 65535 - total
		check_sum_bits = '{0:016b}'.format(checksum)
		final = message[0:32] + check_sum_bits + message[48:]
		return final
	else:
		return '0'

# Make a packet
def make_packet(seq_no,segment_data):
	seq_no_bits = '{0:032b}'.format(seq_no)
    	checksum = '0' * 16
    	indicator_bits = '01' * 8
    	data = ''
    	for i in range(1,len(segment_data)+1):
        	data_character = segment_data[i-1]
        	data_byte = '{0:08b}'.format(ord(data_character))
        	data = data + data_byte
    	segment = seq_no_bits + checksum + indicator_bits + data
    	return segment

# Get recent sequence number
def recent_sequence(window_size,tempfile):
	seq_no = -1
	fptr = open(tempfile, "r")
	fcntl.flock(fptr.fileno(),fcntl.LOCK_EX)
	active_count = 0
	for line in reversed(fptr.readlines()):
		if re.findall('(\d+),W\n',line):
			active_count += 1
		elif re.findall('(\d+),\n',line):
			seq_no = str(re.findall('(\d+),\n',line)[0])	
	fptr.close()
	if active_count == window_size:
		return 	-1
	elif active_count < window_size:
		return seq_no
	else:	
		return -1


# Set Sent sequence number
def seq_sent(seq_no,tempfile):
	fptr = open(tempfile, "r+w")
	fcntl.flock(fptr.fileno(),fcntl.LOCK_EX)
	data = fptr.readlines()
	if data[int(seq_no)] == seq_no + ",\n":
		data[int(seq_no)] = seq_no + ",W\n"
	new_data = ''.join(data)
	fptr.seek(0)
	fptr.truncate()
	fptr.write(new_data)
	fptr.close()


# Process to receive 
def rcv_thread(soc,tempfile):
	new_proc = os.fork()
	if new_proc == 0:
		print "Receive Thread " + str(os.getpid()) + " created.."
	       	while 1:
                	message, server_addr = soc.recvfrom(max_buff)
	                seq_no = recv_check(message)
			if seq_no != -1:
				ack_check(seq_no,tempfile)


# Check received sequence number
def recv_check(message):
	seq_no = str(int(message[0:32],2))
	pad = message[32:48]
	ack_ind = message[48:]
	if pad == ('0' * 16) and ack_ind == ('10' * 8):
		return seq_no
	return -1

# Set seq number to completed
def ack_check(seq_no,tempfile):
	make_change = -1
	line_counter = 0
	fptr = open(tempfile, "r+w")
	fcntl.flock(fptr.fileno(),fcntl.LOCK_EX)
	data = fptr.readlines()
	# print "Received ACK for Seq No : " + str(seq_no)
        for line in data:
		line_counter += 1
		match = re.findall('(\d+),(\w)\n',line)
		if match:
			read_seq = match[0][0]
			status = match[0][1]
			if int(read_seq) == int(seq_no) and status == 'W' and line_counter == 1:
				make_change = 1
				break
			elif int(read_seq) < int(seq_no) and status != 'C':
				break
			elif int(read_seq) == int(seq_no) and status == 'W' and line_counter > 1:
				make_change = 1
				break
	if make_change == 1:
		if data[int(seq_no)] == seq_no + ",W\n":
	        	data[int(seq_no)] = seq_no + ",C\n"
		new_data = ''.join(data)
	        fptr.seek(0)
		fptr.truncate()	
		fptr.write(new_data)
        fptr.close()

# Push sequence numbers to file
def create_tempfile(send_file,mss,tempfile_name):
	if os.path.exists(send_file):
		if os.path.getsize(send_file) > 0:
                        if os.path.exists(tempfile_name):
				os.remove(tempfile_name)
            		tempfptr = open(tempfile_name,'a')
            		sequence = 0
			tempfptr.write(str(sequence) + ',\n')
            		with open(send_file, "rb") as fptr:
				while 1:
					position = (sequence + 1) * mss
			                fptr.seek(position,0)
                    			byte_data = fptr.read(1)
                    			if not byte_data:
						break
                    			sequence = sequence + 1
                    			tempfptr.write(str(sequence) + ',\n')                    
            		fptr.close()
            		tempfptr.close()
            		return '1'
		else:
			return '-1'
	else:
		return '-2'

# Timers
def set_timeout(send_seq_no,tempfile):
	child_process = os.fork()
	if child_process == 0:
		p = psutil.Process(os.getpid())
		time.sleep(0.5)
		fptr = open(tempfile,'r+w')
		fcntl.flock(fptr.fileno(),fcntl.LOCK_EX)
		update_seq_status = -1
		data = fptr.readlines()
		for line in data:
			match = re.findall('(\d+),(\w)\n',line)
			if match:
				if send_seq_no == str(match[0][0]):
					if str(match[0][1]) == 'C':
						break
					elif str(match[0][1]) == 'W':
						print "Timeout, sequence number =:" + send_seq_no
						update_seq_status = 1
						break
					else:
						break
		if update_seq_status == 1:
			if data[int(send_seq_no)] == send_seq_no + ",W\n":
				data[int(send_seq_no)] = send_seq_no + ",\n"
			new_data = ''.join(data)
			fptr.seek(0)
			fptr.truncate()
			fptr.write(new_data)
		fptr.close()
		os._exit(0)		

# Keep up with status
def status_check(tempfile):
        file_transfer = 0
        fptr = open(tempfile,'r')
	fcntl.flock(fptr.fileno(),fcntl.LOCK_EX)
        for line in fptr:
		if line != '\n':
	        	status = re.findall('\d+,([C])\n',line)
        	        if not status:
				file_transfer = -1
				break
	fptr.close()
        return file_transfer

# Set the start time
start_time = time.time()

# Get command line arguments
server_host = sys.argv[1]
port = int(sys.argv[2])
send_file = sys.argv[3]
window_size = int(sys.argv[4])
mss = int(sys.argv[5])

# Set the maximum buffer size
max_buff = 65535

# Create temporary file to keep track of sequence numbers
tempfile_status = create_tempfile(send_file,mss,tempfile)

if tempfile_status == '-1':
	print "File empty. Closing program.."
	os._exit(0)
elif tempfile_status == '-2':
	print "File not found. Closing program.."
	os._exit(0)

# COMMS
client_socket = socket(AF_INET,SOCK_DGRAM)

# Thread to handle ACKS
rcv_thread(client_socket,tempfile)

# Send file
while 1:
	p = psutil.Process(os.getpid())
        transfer_status = status_check(tempfile)
	if transfer_status == 0:
                print "File transfer Complete .."
		print "Total time in seconds : " + str(time.time() - start_time)
                break

	send_seq_no = recent_sequence(window_size,tempfile)
	if send_seq_no > -1:
		seq_sent(send_seq_no,tempfile)
		message_to_send = rdt_send(send_file,mss,int(send_seq_no))
		client_socket.sendto(message_to_send,(server_host,port))
		set_timeout(send_seq_no,tempfile)

# Close socket
client_socket.close()