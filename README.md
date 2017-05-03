# Go-back-N-ARQ-Protocol

An implementation of the Go Back N protocol, in Python.

**Project Description**: [Please click here](https://github.com/gms298/Go-back-N-ARQ-Protocol/tree/master/Project%20Description)

## Developers

**Manoj Sharan** & **Anthony Scalabrino**

## GENERATE FILE TEST FILE

1.	Open Terminal on Ubuntu and use this command `dd if=/dev/zero of=testfile.txt bs=1 count=0 seek=1195K`
2.	This will generate a text file with all “0”s written with size 1.1MB (approx..)## RUN PROJECT & MEASURE RESULTS

1.	Before executing the program, there are some changes needed to adapt it to your environment. Open “client.py” and navigate to line 10 that has the following line :` tempfile = "/temp.txt" ` . Replace the empty string with a valid full file path. For example, ` tempfile = "/home/ubuntu/temp.txt" `. This will be used to create a temp.txt file that will be used by the program. 2.	Open Terminal on Ubuntu and use this command `python server.py <port> <filename> <loss>`  Where, `<filename>` should be replaced with the desired name of the file to write the received packets into  `<loss>` should be replaced with the desired probability value for inducing error/ packet loss  `<port>` should be replaced with the desired port number to run the server on.3.	Open another terminal window on Ubuntu (preferably on a separate machine) and use this command `python client.py < IP> <Port > testfile.txt <WS> <MSS>` where, `<WS>` should be replaced with the desired Window Size
 `<MSS>` should be replaced with the desired Maximum Segment Size
  `<IP>` should be replaced with the desired server IP address/hostname to connect to
  `<Port>` should be replaced with the desired server port number to connect to.**Note:** If a different filename is used, change the “testfile.txt” to reflect the new file name.

## RESULTS

![1](https://cloud.githubusercontent.com/assets/21252571/25644671/e51a932a-2f75-11e7-9872-e94e60aa4aeb.png)

![2](https://cloud.githubusercontent.com/assets/21252571/25644670/e517cad2-2f75-11e7-89f9-599840d32c3f.png)

![3](https://cloud.githubusercontent.com/assets/21252571/25644669/e517adfe-2f75-11e7-8865-2caf0d9b0761.png)
