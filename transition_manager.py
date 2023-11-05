import tkinter as tk

class TransitionManager:
    def __init__(self):
        self.transitions = []

    def add_transition(self, canvas, start, end, label, curve=False, control_point=None):
        if curve and control_point:
            canvas.create_line(start[0], start[1], control_point[0], control_point[1], end[0], end[1], smooth=True, arrow=tk.LAST)
        else:
            canvas.create_line(start[0], start[1], end[0], end[1], arrow=tk.LAST)
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        canvas.create_text(mid_x, mid_y, text=label, tags=("transition_label",), font=("Arial", 14))
        self.transitions.append({
            'start': start,
            'end': end,
            'label': label,
            'type': 'curved_transition' if curve else 'straight_transition',
            'control': control_point
        })
