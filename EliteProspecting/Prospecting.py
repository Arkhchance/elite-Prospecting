#!/usr/bin/python
import Tkinter as tk
import socket , sys , time
import threading
from config import config
from collections import deque

class Prospecting():
    def __init__(self):
        self.connected = False
        self.run = True
        self.parent = None
        self.total_msg  = 0
        self.messages = deque()
        self.buffer = 1024
        self.sock = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.load_config()

    def load_config(self):
        self.ip = config.get("server_ip") or "127.0.0.1"
        self.port = config.get("server_port") or 44988

        self.track_LTD = config.getint("track_LTD") or True
        self.track_Painite = config.getint("track_Painite") or True

        self.ltd_threshold = config.get("LTD_t") or 18
        self.painite_threshold = config.get("Painite_t") or 25

        self.font_size = config.get("font_size") or 14

    def init_gui(self,parent):
        print("call init")
        self.parent = parent
        self.frame = tk.Frame(parent, borderwidth=2)
        self.frame.grid(sticky=tk.NSEW, columnspan=2)

        self.connection = tk.Button(self.frame, text="Connect to server", command=self.connect)
        row = 0
        self.connection.grid(row=row, columnspan=2)

        self.status = tk.Label(self.frame, text="", foreground="yellow")
        self.status.config(font=("Courier", int(self.font_size)))
        row += 1
        self.status.grid(row=row, pady=5, sticky=tk.W)
        return self.frame

    def display_msg(self,msg):
        msg = msg + "\n"
        val = ""
        self.total_msg += 1

        if self.total_msg >= 5 :
            self.messages.remove(self.messages.popleft())
            self.total_msg -= 1
            self.messages.append(msg)
            self.messages.rotate(1)
        else :
            self.messages.append(msg)

        for text in self.messages :
            val += text

        self.status['text'] = val

    def sendMsg(self,message):
        try :
            self.sock.sendall(message.encode())
        except socket.error, exc:
            print("error sending")
            print("Caught exception socket.error : %s" % exc)

    def connect(self):
        try :
            self.connection["text"] = "Connecting..."
            print("connecting to ",self.ip)
            self.sock.connect((self.ip , int(self.port)))

        except socket.error, exc:
            print("Caught exception socket.error : %s" % exc)
            print("Error connecting")
            self.connection["text"] = "Error connecting check configuration"
            return

        self.connected = True
        self.sendMsg("New Player")
        threading.Thread(target=self.recvs).start()
        self.connection["text"] = "Connected"
        time.sleep(2)
        self.connection.grid_remove()

    def stop(self):
        if not self.connected:
            return
        self.run = False
        self.connected = False
        self.sendMsg("quit")
        time.sleep(1)
        try:
            self.sock.close()
        except socket.error, exc:
            print("socket.error : %s" % exc)

    def recvMsg(self):
        data = self.sock.recv(self.buffer)
        return data.decode()

    def recvs(self):
        while self.run:
            try:
                msg = self.recvMsg()
                if msg.decode() == "quit":
                    break
                self.display_msg(msg)
            except socket.error, exc:
                print("error receiving")
                print("Caught exception socket.error : %s" % exc)

    def publish(self,cmdr,name,prop):
        message = cmdr + " " + name + " {:.2f}%"
        message = mmessage.format(prop)
        if self.connected :
            self.sendMsg(message)
        self.display_msg(message)

    def event(self,cmdr,entry):
        #received a ProspectedAsteroid event
        #check for materials
        for mat in entry['Materials']:
            if mat['Name'] == "LowTemperatureDiamond" and self.track_LTD :
                if mat['Proportion'] > float(self.ltd_threshold):
                    self.publish(cmdr,mat['Name_Localised'],mat['Proportion'])
            elif mat['Name'] == "Painite" and self.track_Painite :
                if mat['Proportion'] > float(self.painite_threshold):
                    self.publish(cmdr,mat['Name_Localised'],mat['Proportion'])