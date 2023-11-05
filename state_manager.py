class StateManager:
    def __init__(self):
        self.states = {}

    def add_state(self, canvas, position, label):
        x, y = position
        r = 25
        canvas.create_oval(x-r, y-r, x+r, y+r, fill="white", outline="black")
        canvas.create_text(x, y, text=label, tags=("state_label",), font=("Arial", 14))
        state_id = len(self.states) + 1
        self.states[state_id] = {'label': label, 'position': position}

    def find_nearest_state(self, x, y):
        closest_state = None
        min_dist = float('inf')
        for state_id, state_info in self.states.items():
            state_x, state_y = state_info['position']
            dist = (state_x - x)**2 + (state_y - y)**2
            if dist < min_dist:
                min_dist = dist
                closest_state = state_id
        return closest_state if min_dist <= 2500 else None  # 2500 = (50px)^2 which is a threshold
