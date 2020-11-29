class Event:
    
    def __init__(self):
        self.room = None
        self._will_execute = True

    @property
    def will_execute(self):
        return self._will_execute

    def execute(self):
        return NotImplemented