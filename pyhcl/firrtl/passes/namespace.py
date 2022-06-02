from typing import List

class Namespace:
    def __init__(self):
        self.start_with: str = "GEN_"
        self.index: int = 0
        self.names: List[str] = []

    def auto_incr(self):
        self.index += 1
    
    def last_name(self):
        return self.names[-1]

    def get_names(self):
        return self.names

    def auto_get_name(self):
        name = f"{self.start_with}{self.index}"
        self.names.append(name)
        self.auto_incr()
        return name
