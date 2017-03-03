
class AlarmParameters(object):
    __instance = None

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if(AlarmParameters.__instance is None):
            AlarmParameters.__instance = object.__new__(cls, *args, **kwargs)
        return AlarmParameters.__instance

    def load_parameter(self):
        self.delay_pos = 20000

