#!/usr/bin/python

class kvheaders:
    """
    Case un-sensitive kv list
    """
    def __init__(self):
        self.headers = {}
    def add(self,key,value):
        self.headers[key.lower()] = (key,value)
    def check(self,key,value):
        if self.headers.has_key(key.lower()):
            val = self.headers[key.lower()][1]
            if value.lower()==val.lower():
                return True
            else:
                return False
        return False
    def get(self,key):
        if self.headers.has_key(key.lower()):
            return self.headers[key.lower()][1]
        else:
            return None
    def hasKey(self,key):
        if self.headers.has_key(key.lower()):
            return True
        else:
            return False
    def keys(self):
        list = []
        for k in self.headers.keys():
            list.append(self.headers[k][0])
        return list
    def keyslower(self):
        list = []
        for k in self.headers.keys():
            list.append(k)
        return list
        
if __name__ == '__main__':
    h = kvheaders()
    h.add('Upgrade','Websocket')
    h.add('Connection','Upgrade')
    print h.check('Upgrade','Websocket')
    print h.check('Connection','Upgrade')
    print h.check('upgrade','websocket')
    print h.check('connection','upgrade')
    print h.get('Upgrade')
    print h.hasKey('conneCtion')
    print h.keys()
    print h.keyslower()
            
        