import tkinter as tk
from tkinter.simpledialog import askstring
import math

class UIManager:
    def __init__(self, root):
        self.root = root
        self.current_tool = None
        self.states = {}  # This will store the state positions and labels
        self.transitions = []  # This will store the transitions
        self.temp_start_point = None  # Temporary start point for drawing transitions
        self.temp_line = None  # Temporary line object for transitions
        self.ghost_state = None  # Ghost state object
        self.curve_control_point = None  # Control point for the curve
        self.curve_phase = 0  # To track the phase of curve creation: 0 = start, 1 = control point, 2 = end point

        self.setup_ui()


    def setup_ui(self):
        self.toolbox_frame = tk.Frame(self.root)
        self.toolbox_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.state_button = tk.Button(self.toolbox_frame, text="Add State", command=self.set_tool_state)
        self.state_button.pack(fill=tk.X)

        self.transition_button = tk.Button(self.toolbox_frame, text="Add Transition", command=self.set_tool_transition)
        self.transition_button.pack(fill=tk.X)

        self.curve_transition_button = tk.Button(self.toolbox_frame, text="Add Curve Transition", command=self.set_tool_curve_transition)
        self.curve_transition_button.pack(fill=tk.X)

        self.generate_button = tk.Button(self.toolbox_frame, text="Generate TikZ Code", command=self.on_generate_code)
        self.generate_button.pack(fill=tk.X)

        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind("<Motion>", self.update_ghost)
        self.canvas.bind("<ButtonRelease-1>", self.add_transition_end)
        self.draw_grid()


    def draw_grid(self):
        grid_size = 100  # Adjust as needed
        for i in range(0, 801, grid_size):
            self.canvas.create_line([(i, 0), (i, 600)], tag='grid_line', fill="gray80")
            self.canvas.create_line([(0, i), (800, i)], tag='grid_line', fill="gray80")

    def set_tool_state(self):
        self.current_tool = "state"
        self.remove_ghost_transition()

    def set_tool_transition(self):
        self.current_tool = "straight_transition"
        self.remove_ghost_state()
        self.canvas.bind("<Motion>", self.update_temp_line)


    def set_tool_curve_transition(self):
        self.current_tool = "curved_transition"
        self.curve_phase = 0  # Reset the curve phase
        self.remove_ghost_state()
        self.remove_ghost_transition()
        self.canvas.bind("<Motion>", self.update_ghost_curve)
    
    def update_ghost_curve(self, event):
        if self.current_tool == "curved_transition" and self.curve_phase in {1, 2}:
            # If the starting state is selected, draw a ghost line from it to the mouse position
            start_position = self.states[self.temp_start_point]['position'] if self.temp_start_point else (event.x, event.y)
            if self.curve_phase == 1:
                # Draw a line from the start state to the current mouse position
                if self.temp_line:
                    self.canvas.coords(self.temp_line, start_position[0], start_position[1], event.x, event.y)
                else:
                    self.temp_line = self.canvas.create_line(start_position[0], start_position[1], event.x, event.y, dash=(4, 2))
            elif self.curve_phase == 2:
                # Draw a curve from the start state to the end state with the mouse position as the control point
                end_position = self.states[self.temp_end_point]['position']
                if self.temp_line:
                    self.canvas.coords(self.temp_line, start_position[0], start_position[1], event.x, event.y, end_position[0], end_position[1], smooth=True)
                else:
                    self.temp_line = self.canvas.create_line(start_position[0], start_position[1], event.x, event.y, end_position[0], end_position[1], smooth=True)
                
    def update_ghost_line(self, event):
        if self.current_tool == "curved_transition" and self.curve_phase == 1:
            # Update the ghost line here to follow the cursor
            start_position = self.states[self.temp_start_point]['position']
            self.canvas.coords(self.temp_line, start_position[0], start_position[1], event.x, event.y)

    def update_ghost(self, event):
        if self.current_tool == "state":
            self.update_ghost_state(event)
        elif self.current_tool in ["straight_transition", "curved_transition"] and self.temp_start_point:  # Corrected the strings
            self.update_temp_line(event, curve=self.current_tool == "curved_transition")  # Corrected the condition

    def update_ghost_state(self, event):
        grid_size = 100
        x = ((event.x + grid_size // 2) // grid_size) * grid_size
        y = ((event.y + grid_size // 2) // grid_size) * grid_size
        r = 25
        if not self.ghost_state:
            self.ghost_state = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="white", outline="gray", dash=(2,2))
        else:
            self.canvas.coords(self.ghost_state, x-r, y-r, x+r, y+r)

    def remove_ghost_state(self):
        if self.ghost_state:
            self.canvas.delete(self.ghost_state)
            self.ghost_state = None

    def canvas_click(self, event):
        if self.current_tool == "state":
            self.add_state(event)
        elif self.current_tool == "straight_transition":
            if not self.temp_start_point:
                self.add_transition_start(event)
            else:
                self.add_transition_end(event)
        elif self.current_tool == "curved_transition":
            if self.curve_phase == 0:
                # Select the start state
                self.temp_start_point = self.find_nearest_state(event.x, event.y)
                if self.temp_start_point:
                    self.curve_phase = 1
            elif self.curve_phase == 1:
                # Select the end state
                self.temp_end_point = self.find_nearest_state(event.x, event.y)
                if self.temp_end_point and self.temp_end_point != self.temp_start_point:
                    self.curve_phase = 2
            elif self.curve_phase == 2:
                # The final click sets the control point and finalizes the curve
                control_point = (event.x, event.y)
                label = self.prompt_for_label("Enter transition label")
                if label:
                    self.finalize_curve_transition(label, control_point)
                self.curve_phase = 0
                self.canvas.unbind("<Motion>")
                self.remove_ghost_transition()
        
    def finalize_curve_transition(self, label):
        # Make sure temp_end_point is defined
        if hasattr(self, 'temp_end_point') and self.temp_end_point:
            end_state = self.states[self.temp_end_point]
            control_point = self.curve_control_point
            self.draw_curved_transition(self.states[self.temp_start_point]['position'], control_point, end_state['position'], label)

    def add_state(self, event):
        grid_size = 100
        x = ((event.x + grid_size // 2) // grid_size) * grid_size
        y = ((event.y + grid_size // 2) // grid_size) * grid_size
        r = 25
        oval = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="white", outline="black")
        label = self.prompt_for_label("Enter state label")
        if label:
            self.canvas.create_text(x, y, text=label, tags=("state_label",), font=("Arial", 14))
            # Store the state position along with its label
            state_id = len(self.states) + 1
            self.states[state_id] = {'label': label, 'position': (x, y)}
        else:
            # If the label prompt was cancelled, remove the created oval
            self.canvas.delete(oval)
        self.remove_ghost_state()

        
    def add_transition_start(self, event):
        nearest_state_id = self.find_nearest_state(event.x, event.y)
        if nearest_state_id:
            self.temp_start_point = nearest_state_id
            start_position = self.states[self.temp_start_point]['position']
            if self.current_tool == "curve_transition":
                # For curve transition, we initially draw a straight line, which will be updated as the mouse moves
                self.temp_line = self.canvas.create_line(start_position[0], start_position[1], event.x, event.y, arrow=tk.LAST)
            else:
                # For straight transitions, the line will follow the mouse cursor
                self.temp_line = self.canvas.create_line(start_position[0], start_position[1], event.x, event.y, arrow=tk.LAST)


    def update_temp_line(self, event):
        if self.current_tool == "straight_transition" and self.temp_start_point:
            start_position = self.states[self.temp_start_point]['position']
            # Update the temporary line with the current mouse position
            if self.temp_line:
                self.canvas.coords(self.temp_line, start_position[0], start_position[1], event.x, event.y)
            else:
                # Create a dashed temporary line
                self.temp_line = self.canvas.create_line(start_position[0], start_position[1], event.x, event.y, dash=(4, 2))

            if self.temp_start_point:
                start_position = self.states[self.temp_start_point]['position']
                if curve:
                    control_x = (start_position[0] + event.x) / 2
                    control_y = start_position[1] if abs(start_position[1] - event.y) < 50 else (start_position[1] + event.y) / 2 - 50
                    self.canvas.coords(self.temp_line, start_position[0], start_position[1], control_x, control_y, event.x, event.y)
                else:
                    self.canvas.coords(self.temp_line, start_position[0], start_position[1], event.x, event.y)

    def draw_straight_transition(self, start, end, label):
        # Draw the line
        line = self.canvas.create_line(start[0], start[1], end[0], end[1], arrow=tk.LAST)

        # Calculate the midpoint for the label
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2

        # Draw the label
        self.canvas.create_text(mid_x, mid_y, text=label, tags=("transition_label",), font=("Arial", 14))


    def draw_curved_transition(self, start, control, end, label):
        # Create the curve with the control point
        self.canvas.create_line(start[0], start[1], control[0], control[1], end[0], end[1], smooth=True, arrow=tk.LAST)
        
        # Calculate the position for the label
        label_x = (control[0] + end[0]) / 2
        label_y = (control[1] + end[1]) / 2
        
        # Create the label
        self.canvas.create_text(label_x, label_y, text=label, tags=("transition_label",), font=("Arial", 14))

        # Append the transition to the list
        self.transitions.append({
            'start': self.temp_start_point,
            'end': self.temp_end_point,
            'label': label,
            'control': control,
            'type': 'curved_transition'
        })


    def add_transition_end(self, event):
        # First, handle the case where we are adding a curved transition
        if self.current_tool == "curved_transition":
            if self.curve_phase == 1:
                # First click - set the start point
                self.temp_start_point = self.find_nearest_state(event.x, event.y)
                if self.temp_start_point:
                    self.curve_phase = 2
            elif self.curve_phase == 2:
                # Second click - set the end point
                self.temp_end_point = self.find_nearest_state(event.x, event.y)
                if self.temp_end_point and self.temp_end_point != self.temp_start_point:
                    self.curve_phase = 3
            elif self.curve_phase == 3:
                # Third click - determine the control point and draw the curve
                start_pos = self.states[self.temp_start_point]['position']
                end_pos = self.states[self.temp_end_point]['position']
                
                # Determine the depth of the curve based on the third click position
                depth = event.y - min(start_pos[1], end_pos[1]) if event.y < min(start_pos[1], end_pos[1]) else max(start_pos[1], end_pos[1]) - event.y
                
                # Control point calculation can be adjusted based on your requirements
                control_x = (start_pos[0] + end_pos[0]) / 2
                control_y = (start_pos[1] + end_pos[1]) / 2 + depth

                label = self.prompt_for_label("Enter transition label")
                if label:
                    self.draw_curved_transition(start_pos, (control_x, control_y), end_pos, label)
                    self.transitions.append({
                        'start': self.temp_start_point,
                        'end': self.temp_end_point,
                        'label': label,
                        'control': (control_x, control_y),
                        'type': 'curved_transition'
                    })
                # Reset everything for the next transition
                self.curve_phase = 1
                self.temp_start_point = None
                self.temp_end_point = None
                self.canvas.unbind("<Motion>")
                self.remove_ghost_transition()

        # Now handle the case where we are adding a straight transition
        elif self.current_tool == "straight_transition":
            end_state_id = self.find_nearest_state(event.x, event.y)
            if end_state_id and self.temp_start_point and end_state_id != self.temp_start_point:
                start_pos = self.states[self.temp_start_point]['position']
                end_pos = self.states[end_state_id]['position']

                # Prompt for the label after the second click
                label = self.prompt_for_label("Enter transition label")
                if label:
                    self.draw_straight_transition(start_pos, end_pos, label)
                    self.transitions.append({
                        'start': self.temp_start_point,
                        'end': end_state_id,
                        'label': label,
                        'type': 'straight_transition'
                    })
                # Reset the temporary variables for the next transition
                self.temp_start_point = None
                self.remove_ghost_transition()
            elif end_state_id and self.temp_start_point == end_state_id:
                # Handle self-loop transition
                label = self.prompt_for_label("Enter transition label")
                if label:
                    self.draw_loop_transition(self.states[end_state_id]['position'], "above")
                    self.transitions.append({
                        'start': end_state_id,
                        'end': end_state_id,
                        'label': label,
                        'type': 'self_loop'
                    })
                self.temp_start_point = None
                
                self.remove_ghost_transition()

        # Additional conditions for other types of transitions could be added here





    def remove_ghost_transition(self):
        if self.temp_line:
            self.canvas.delete(self.temp_line)
            self.temp_line = None
            
    def add_transition_end(self, event):
        nearest_state_id = self.find_nearest_state(event.x, event.y)
        if nearest_state_id and self.temp_start_point:
            if self.current_tool == "curved_transition":
                if not hasattr(self, 'curve_phase'):
                    self.curve_phase = 1
                    self.curve_control_point = None
                    self.curve_end_point = None
                    self.temp_line = self.canvas.create_line(
                        self.states[self.temp_start_point]['position'][0],
                        self.states[self.temp_start_point]['position'][1],
                        event.x, event.y, arrow=tk.LAST
                    )
                elif self.curve_phase == 1:
                    # First click - set the control point
                    self.curve_control_point = (event.x, event.y)
                    self.curve_phase = 2
                    # Update the line to the control point
                    self.canvas.coords(
                        self.temp_line,
                        self.states[self.temp_start_point]['position'][0],
                        self.states[self.temp_start_point]['position'][1],
                        event.x, event.y
                    )
                elif self.curve_phase == 2:
                    # Second click - set the end point and draw the curve
                    self.curve_end_point = (event.x, event.y)
                    label = self.prompt_for_label("Enter transition label")
                    if label:  # Only proceed if a label was provided
                        self.draw_curved_transition(
                            self.states[self.temp_start_point]['position'],
                            self.curve_control_point,
                            self.curve_end_point,
                            label
                        )
                        # Append the transition with all three points and label
                        self.transitions.append({
                            'start': self.temp_start_point,
                            'control': self.curve_control_point,
                            'end': nearest_state_id,
                            'label': label,
                            'type': self.current_tool
                        })
                    # Reset the control points and phase
                    self.temp_start_point = None
                    self.curve_control_point = None
                    self.curve_end_point = None
                    self.curve_phase = 0
                    self.remove_ghost_transition()
            elif self.temp_start_point == nearest_state_id:
                # Self-transition
                label = self.add_self_transition(nearest_state_id)
                if label:
                    self.transitions.append({
                        'start': nearest_state_id,
                        'end': nearest_state_id,
                        'label': label,
                        'type': 'self_transition'
                    })
                self.temp_start_point = None
            else:
                # Straight transition
                label = self.prompt_for_label("Enter transition label")
                if label:
                    self.draw_straight_transition(
                        self.states[self.temp_start_point]['position'],
                        self.states[nearest_state_id]['position'],
                        label
                    )
                    self.transitions.append({
                        'start': self.temp_start_point,
                        'end': nearest_state_id,
                        'label': label,
                        'type': 'straight_transition'
                    })
                self.temp_start_point = None







    def calculate_midpoint(self, start, end):
        return ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)

    def prompt_for_label(self, prompt):
        return askstring("Label", prompt, parent=self.root)


    def draw_loop_transition(self, position, direction):
        x, y = position
        loop_size = 50  # Adjust size as needed

        if direction == 'above':
            self.canvas.create_arc(x - loop_size, y - loop_size, x + loop_size, y, start=0, extent=180, style=tk.ARC, arrow=tk.LAST)
        elif direction == 'below':
            self.canvas.create_arc(x - loop_size, y, x + loop_size, y + loop_size, start=180, extent=180, style=tk.ARC, arrow=tk.LAST)
        elif direction == 'left':
            self.canvas.create_arc(x - loop_size, y - loop_size, x, y + loop_size, start=90, extent=180, style=tk.ARC, arrow=tk.LAST)
        elif direction == 'right':
            self.canvas.create_arc(x, y - loop_size, x + loop_size, y + loop_size, start=270, extent=180, style=tk.ARC, arrow=tk.LAST)
            

    def find_nearest_state(self, x, y):
        # Find the state closest to the (x, y) position
        closest_state = None
        min_dist = float('inf')
        for state_id, state_info in self.states.items():
            state_x, state_y = state_info['position']
            dist = (state_x - x)**2 + (state_y - y)**2
            if dist < min_dist:
                min_dist = dist
                closest_state = state_id
        return closest_state if min_dist <= 2500 else None  # 2500 = (50px)^2 which is a threshold

    def generate_tikz_code(self):
        tikz_code = ["\\begin{tikzpicture}[->,>=stealth',shorten >=1pt,auto,node distance=2.8cm,semithick]"]
        
        # Generate code for states
        for state_id, state_info in self.states.items():
            position = f"({state_info['position'][0]/100},{-state_info['position'][1]/100})"
            label = state_info['label']
            tikz_code.append(f"\\node[state] (S{state_id}) {position} {{$label$}};")
        
        # Generate code for transitions
        for transition in self.transitions:
            start_state = transition['start']
            end_state = transition['end']
            label = transition['label']
            tikz_code.append(f"\\path (S{start_state}) edge node {{$label$}} (S{end_state});")

        tikz_code.append("\\end{tikzpicture}")
        return "\n".join(tikz_code)

    def on_generate_code(self):
        tikz_code = self.generate_tikz_code()
        # For now, let's just print it to the console
        print(tikz_code)

    def add_self_transition(self, state_id):
        state_info = self.states[state_id]
        x, y = state_info['position']
        r = 25  # Use a smaller radius for the loop
        
        # Create an arc that starts from the top of the state and loops outwards
        self.canvas.create_arc(x-r+5, y-r*2+10, x+r-15, y, start=0, extent=180, style=tk.ARC)
        
        # Create the arrowhead, pointing upwards at the top of the state
        arrow_size = 6  # Size of the arrowhead
        self.canvas.create_polygon(x+10, y - r + arrow_size, x - arrow_size+20, y - r, x + arrow_size, y - r, fill='black')

        # Prompt for label
        label = self.prompt_for_label("Enter transition label")
        if label:
            # Adjust label offset here
            label_offset = 5  # Move the label 20 pixels above the loop
            self.canvas.create_text(x, y-r*2-label_offset, text=label, tags=("transition_label",), font=("Arial", 14))

        return label  # Return the label so it can be added to the transition list





