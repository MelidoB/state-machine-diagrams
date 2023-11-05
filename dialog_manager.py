import tkinter.simpledialog as sd

class DialogManager:
    def __init__(self, root):
        self.root = root

    def prompt_for_label(self, prompt):
        return sd.askstring("Label", prompt, parent=self.root)
