# main.py
import tkinter as tk
from ui_manager import UIManager

def main():
    root = tk.Tk()
    root.title('State Machine Designer')
    UIManager(root)  # This will automatically call __init__ and setup UI
    root.mainloop()

if __name__ == '__main__':
    main()
