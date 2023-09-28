#Daftar library yang akan digunakan
import socket
from threading import Thread
import cv2 as cv

#set up URL dan jenis socket
addr = ('192.168.10.1', 8889)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#set up variabel yang menyimpan command untuk drone dan state dari drone
command = ''
state = {}

def send_msg(command):
    #Fungsi ini digunakan untuk mengirimkan action command ke drone.
    #Fungsi akan mengembalikan respon dari drone atas command yang diterima.
    sock.sendto(command.encode(), addr)
    data = sock.recvfrom(1024)
    return data[0].decode()

def receive_state():
    #Fungsi ini akan dijalankan di thread yang berbeda dengan main thread.
    #Fungsi akan berfungsi sebagai server socket yang akan selalu menerima
    #data telemetri/flight parameter dari drone. 
    serv_addr = ('', 8890)
    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    serv_sock.bind(serv_addr)
    while command != 'exit':
        raw_data = serv_sock.recvfrom(1024)
        raw_data = raw_data[0].decode()
        data = raw_data.split(';')
        for i in data:
            item = i.split(':')
            state[item[0]] = float(item[1])
    serv_sock.close()

def video_stream():
    #Fungsi ini akan dijalankan di thread yang berbeda dengan main thread.
    #Fungsi akan digunakan untuk menerima video stream dari drone. Cara
    #fungsi ini menerima video stream berbeda dengan metode socket di fungsi
    #receive_state(). Bila ingin melakukan pengolahan citra, lakukan di
    #fungsi ini.
    cap = cv.VideoCapture('udp://@0.0.0.0:11111')
    if not cap.isOpened():
        cap.open('udp://@0.0.0.0:11111')
    while True:
        ret,img = cap.read()
        if ret:
            img = cv.resize(img, (640, 480))
            cv.imshow('Fligth', img)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break
        if command == 'exit':
            break

if __name__ == "__main__":
    #Ini adalah main function dari kode ini. Kendali drone akan dilakukan
    #secara berulang melalui kode dalam fungsi ini. 
    print("Initiating Connection to Drone")
    data = send_msg("command")                      #mengirim command untuk inisialisasi SDK mode pada drone.
    if data == 'ok':                                #hanya bila SDK mode berhasil diinisiasi.
        print("Entering SDK Mode")
        thread = Thread(target=receive_state)       #memulai thread baru untuk menerima data telemetri.
        thread.start()
        data = send_msg('streamon')                 #mengirim command untuk inisialisasi mode video streaming.
        if data == 'ok':                            #hanya bila mode streaming berhasil diinisiasi.
            thread2 = Thread(target=video_stream)   #memulai thread baru untuk menerima video stream.
            thread2.start()
    else:
        print("Error initiating SDK Mode")

    while command != 'exit':                        #main loop untuk mengendalikan drone.
        command = str(input('Enter command: ')) 
        if command != 'exit':
            data = send_msg(command)
            print('Response: ',data)
            print('Battery: ', state['bat'])        #pada contoh ini, kita hanya melihat data baterai yang tersisa.

    #bila main loop sudah tidak dijalankan, kita akan menghentikan seluruh operasi drone. 
    data = send_msg('land')
    print(data)
    sock.close()
