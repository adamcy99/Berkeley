class Debugdict:
    def __init__(self):
        self.debugdict = {}
        
    def addval(self, varname, value):
        self.debugdict[varname] = value