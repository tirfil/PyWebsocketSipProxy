#!/usr/bin/python

#    Copyright 2014 Philippe THIRION
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
            
        