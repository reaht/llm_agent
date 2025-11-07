class BaseSensor:
    def __init__(self, name):
        self.name = name

    def read(self):
        raise NotImplementedError