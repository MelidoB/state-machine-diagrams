class CanvasManager:
    def __init__(self, canvas):
        self.canvas = canvas

    def draw_grid(self, grid_size=100):
        for i in range(0, 801, grid_size):
            self.canvas.create_line([(i, 0), (i, 600)], tag='grid_line', fill="gray80")
            self.canvas.create_line([(0, i), (800, i)], tag='grid_line', fill="gray80")
