#! /usr/bin/python
# -*- coding: utf-8 -*-

import re
import string
import base64
import hashlib
import struct
import random

import kvheaders

"""
                     -------------------
    dataRecv() ---->|                   |<----- status()
    state() ------->|                   |<----- result()
                    |                   |<----- dataSend()
                     -------------------
"""

# dataRecv() : data received from network (handshake or data frame)
# status() : what to do with processing result (i.e send to network, send to application ...)
# result() : processing result
# dataSend() : data to be encoded before sent to network
# state() : state of connection (readyState see websocket API)
# sendPing()
# sendClose()

rx_get = re.compile("^GET")
rx_kv = re.compile("^([^:]*): (.*)")
guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
hsResponse = [ "HTTP/1.1 101 Switching Protocols","Upgrade: websocket", "Connection: Upgrade"]
hsWrongResponse = ["HTTP/1.1 400 Bad Request"]

# readyState
#CONNECTING = 0
#OPEN = 1
#CLOSING = 2
#CLOSED = 3

# status
#   0   Nothing to do
#   1   HandShake OK to network
#   2   HandShake NOK to network
#   3   Data (frame encoded) to network
#   4   Pong (After receiving a Ping) to network
#   5   Close (After receiving close) to network
#   8   Data (frame decoded) to application

class wsserver:
    def __init__(self):
        self.readyState = 0
        self.hsHeaders = kvheaders.kvheaders()
        self._result = ""
        self.error = False
        self._status=0
        self.extra=""
        
    def state(self):
        return self.readyState
        
    def status(self):
        return self._status
        
    def dataRecv(self,buffer):
        if self.readyState == 0:
            self.processHandshake(buffer)
        elif self.readyState > 0:
            self.processData(buffer)
            
    def result(self):
        result = self._result
        self._result = ""
        self._status=0
        return result
        
    def isIncomplete(self):
        if len(self.extra) > 0:
            return True
        else:
            return False
            
    def processData(self,buffer):
        print "processData"

        if len(self.extra)>0:
            buffer = self.extra+buffer
            self.extra=""
        blen = len(buffer)
            
        frame = struct.unpack("BB",buffer[:2])
        if frame[0] > 0x7f:
            final = True
        else:
            final = False
        opcode = frame[0] & 0x0f
        print "Opcode 0x%02x" % opcode
        if opcode > 0x7:
            control = True
        else:
            control = False
        if frame[1] > 0x7f:
            maskb = True
        else:
            maskb = False
        length = frame[1] & 0x7f
        offset = 2
        if length == 126:
            (length,) = struct.unpack(">H",buffer[2:4])
            offset = 4
        if length == 127:
            (length,) = struct.unpack(">Q",buffer[2:10])
            offset = 10
        print "len= %d" % length
        if maskb:
            masks = struct.unpack("BBBB",buffer[offset:offset+4])
            print "Mask0 0x%02x" % masks[0]
            print "Mask1 0x%02x" % masks[1]
            print "Mask2 0x%02x" % masks[2]
            print "Mask3 0x%02x" % masks[3]
            offset = offset+4
            imask = 0
        last = offset+length
        
        print "frame size: %s, packet size: %s" % (last,blen) 
        if last > blen:
            # packet too small
            self.extra=buffer
            self._status=0
            return

        result = ""
        for index in range(offset,last):
            (byte,) = struct.unpack("B",buffer[index])
            if maskb:
                result += str(unichr(int(byte ^ masks[imask])).encode('utf-8'))
                imask = (imask + 1) % 4
            else:
                result += str(byte)
        if control:
            # close
            if opcode == 0x8:
                print "Receive Close"
                if self.readyState == 1:
                    self.readyState = 2
                    print "Send Close"
                    self.sendData(result,0x8)
                    self._status = 5
                elif self.readyState == 2:
                    self.readyState = 3
                    self._status = 0
            # ping
            elif opcode == 0x9:
                print "Ping"
                self.sendData(result,0xa)
                self._status = 4
        else:
            # text
            #if opcode == 0x1:
            self._result = result
            self._status=8

        if last < blen:
            # packet too big
            self.extra=buffer[last+1:]
                
    def sendData(self,buffer,opcode=0x01,final=True,mask=False):
        size = len(buffer)
        if final:
            b0=0x80
        else:
            b0=0x00
        b0 += opcode
        if size < 126:
            b1 = size
            result = struct.pack(">BB",b0,b1)
        elif size < 65536:
            b1 = 126
            result = struct.pack(">BBH",b0,b1,size)
        else:
            b1 = 127
            result = struct.pack(">BBQ",b0,b1,size)
        if mask:
            b1 += 0x80
            masks=[]
            for i in range(4):
                masks.append(random.uniform(0,255))
            result += struct.pack("BBBB",masks[0],masks[1],masks[2],masks[3])
        result += buffer
        self._result=result
        self._status=3
        
    def sendPing(self,buffer):
        size = len(buffer)
        if size < 126:
            self.sendData(buffer,0x9)
        else:
            print "Ping data too big"
            self._status=0
            
    def sendClose(self,buffer):
        size = len(buffer)
        if size < 126:
            if self.readyState == 1:
                self.sendData(buffer,0x8)
                self.readyState = 2
            else:
                print "Close wrong state"
        else:
            print "Close data too big"
            self._status=0
            
    def checkHsHeader(self,key,value,code):
        if not self.error:
            if value == "":
                if not self.hsHeaders.hasKey(key):
                    self.processHandshakeError(code)
            elif not self.hsHeaders.check(key,value):
                self.processHandshakeError(code)
            
    def processHandshake(self,buffer):
        self.error = False
        lines=string.split(buffer,"\r\n")
        start = True
        for line in lines:
            if start:
                if not rx_get.search(lines[0]):
                    self.processHandshakeError("400")
                    break
                else:
                    start = False
            else:
                if len(line):
                    md = rx_kv.search(line)
                    if md:
                        key = string.strip(md.group(1))
                        value = string.strip(md.group(2))
                        self.hsHeaders.add(key,value)
        if not self.error:                
            self.checkHsHeader("upgrade","websocket","400")
            #self.checkHsHeader("connection","upgrade","400")
            self.checkHsHeader("sec-websocket-version","13","400")
            self.checkHsHeader("host","","400")
            self.checkHsHeader("origin","","400")
            if self.hsHeaders.hasKey("connection"):
                header = self.hsHeaders.get("connection")
                if string.find(header.lower(),"upgrade") < 0:
                    self.processHandshakeError("400")
            else:
                self.processHandshakeError("400")
        if not self.error:
            if self.hsHeaders.hasKey("sec-websocket-key"):
                key = self.hsHeaders.get("sec-websocket-key")
                str = "%s%s" % (key,guid)
                accept = base64.b64encode(hashlib.sha1(str).digest())
                result = hsResponse[:]
                result.append("Sec-WebSocket-Accept: %s" % accept)
                if self.hsHeaders.hasKey("sec-websocket-protocol"):
                    protocol = self.hsHeaders.get("sec-websocket-protocol")
                    result.append("Sec-WebSocket-Protocol: %s" % protocol)
                #if self.hsHeaders.hasKey("sec-websocket-extensions"):
                #    extensions = self.hsHeaders.get("sec-websocket-extensions")
                #    result.append("Sec-WebSocket-Extensions: ")
                result.append("")
                result.append("")
                self._result = "\r\n".join(result)
                self.readyState = 1
                print "Handshaking succeeded"
                self._status=1
            else:
                self.processHandshakeError("400")
                self._status=2
            
    def processHandshakeError(self,code):
        self._result = "\r\n".join(hsWrongResponse)
        #raise Exception()
        self.error = True
        
if __name__ == "__main__":
    list = [
    "GET / HTTP/1.1",
    "Host: sip//ws.example.com",
    "Upgrade: websocket", 
    "Connection: Upgrade", 
    "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==", 
    "Origin: http://www.example.com", 
    "Sec-WebSocket-Protocol: sip", 
    "Sec-WebSocket-Version: 13",
    ""    ]
    buffer = "\r\n".join(list)
    print buffer
    r = wsserver()
    r.dataRecv(buffer)
    print r.result()
    
    buffer = struct.pack("BB",0x12,0x34)
    r.recv(buffer)
