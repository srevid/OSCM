import timeit

class InfosScript:

    def __init__(self):
        pass

    def infosScriptExec_init(self):
        self.m_iTimeStartScript = timeit.default_timer()

    def infosScriptExec(self):
        self.m_iTimeEndScript = timeit.default_timer()
        self.m_iTimeStartEndDelayScript = self.m_iTimeEndScript - self.m_iTimeStartScript
        print(" %s %s" % ("script time (s)|",str(self.m_iTimeStartEndDelayScript)))