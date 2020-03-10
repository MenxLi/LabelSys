

class LabelHolder:
    """
    HOlding the label result
    """
    def __init__(self):
        self.data = None
        self.SAVED = True
    def initialize(self, entries, SOPInstanceUIDs):
        self.data = []
        for ids in SOPInstanceUIDs:
            self.data.append({})
            for entry in entries:
                self.data[-1][entry] = []
            self.data[-1]["SOPInstanceUID"] = ids
