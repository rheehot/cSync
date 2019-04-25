import queue
import select
import socket
import threading
import sys
from time import sleep


class fileServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)    
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(0)
        self.server.bind(('0.0.0.0', 0))
        self.server.listen(128)
        self.inputs = [self.server]
        self.errors = []
        self.message_queues = {}
        self.runningFlag = True
        self.clientID = 0
        print(self.server.getsockname())

    def getPort(self):
        return self.server.getsockname()[1]

    def stop(self):
        self.runningFlag = False
    def run(self):
        while self.inputs:
            if not self.runningFlag :
                for item in self.inputs:
                    if item != self.server:
                        item.close()
                        del self.message_queues[item]
                self.server.close()
                break
                
            readable, _, exceptional = select.select(
                self.inputs, [], [], 1)
            for s in readable:
                if s is self.server:
                    connection, _ = s.accept()
                    connection.setblocking(0)
                    self.inputs.append(connection)
                    self.message_queues[connection] = queue.Queue()
                else:
                    data = s.recv(1024)
                    if data:
                        print("[RECV " + str(self.inputs.index(s)) + "] " + str(data))
                        self.message_queues[s].put(data)
                    else:
                        self.inputs.remove(s)
                        s.close()
                        del self.message_queues[s]
            