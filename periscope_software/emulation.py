import tkinter as tk
import math
import ast
import operator as op

# Allowed math operations for safe evaluation
allowed_operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg
}

# Allowed math names
allowed_names = {
    k: getattr(math, k) for k in dir(math) if not k.startswith("_")
}
allowed_names.update({
    "pi": math.pi,
    "tau": math.tau,
    "e": math.e
})

def safe_eval(expr):
    """Safely evaluate a math expression."""
    def _eval(node):
        if isinstance(node, ast.Num):         # <number>
            return node.n
        elif isinstance(node, ast.BinOp):     # <left> <operator> <right>
            return allowed_operators[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):   # - <operand>
            return allowed_operators[type(node.op)](_eval(node.operand))
        elif isinstance(node, ast.Name):
            if node.id in allowed_names:
                return allowed_names[node.id]
        elif isinstance(node, ast.Call):      # function calls: sin(x), cos(x), etc.
            if node.func.id in allowed_names:
                args = [_eval(a) for a in node.args]
                return allowed_names[node.func.id](*args)
        raise ValueError(f"Invalid expression: {expr}")

    tree = ast.parse(expr, mode='eval')
    return _eval(tree.body)


class GimbalGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cross-Coupled Gimbal Demo (Math Inputs)")

        self.canvas = tk.Canvas(self.root, width=500, height=500, bg="white")
        self.canvas.pack()

        # Gimbal state
        self.azimuth = 0
        self.elevation = 0
        self.target_azimuth = 0
        self.target_elevation = 0

        # cross-coupling strength
        self.coupling_factor = 0.3

        # Input UI
        control_frame = tk.Frame(self.root)
        control_frame.pack()

        tk.Label(control_frame, text="Azimuth Target:").grid(row=0, column=0)
        tk.Label(control_frame, text="Elevation Target:").grid(row=1, column=0)

        self.az_input = tk.Entry(control_frame)
        self.el_input = tk.Entry(control_frame)
        self.az_input.grid(row=0, column=1)
        self.el_input.grid(row=1, column=1)

        tk.Button(control_frame, text="Move", command=self.set_targets).grid(row=2, column=0, columnspan=2)

        self.animate()
        self.root.mainloop()

    def set_targets(self):
        """Parse math expressions from user input."""
        try:
            self.target_azimuth = safe_eval(self.az_input.get())
            self.target_elevation = safe_eval(self.el_input.get())
            print("Parsed:",
                  self.target_azimuth,
                  self.target_elevation)
        except Exception as e:
            print("Expression error:", e)

    def animate(self):
        # compute changes
        delta_az = self.target_azimuth - self.azimuth
        delta_el = self.target_elevation - self.elevation

        # cross-coupling
        if abs(delta_az) > 0.01:
            self.elevation += delta_az * self.coupling_factor

        # smooth converge
        self.azimuth += delta_az * 0.05
        self.elevation += delta_el * 0.05

        self.draw_gimbal()
        self.root.after(16, self.animate)  # ~60 FPS

    def draw_gimbal(self):
        self.canvas.delete("all")
        cx, cy = 250, 250
        radius_outer = 150
        radius_inner = 100

        # Draw outer ring
        self.canvas.create_oval(cx - radius_outer, cy - radius_outer,
                                cx + radius_outer, cy + radius_outer,
                                outline="black", width=3)

        # Azimuth line
        ax = cx + radius_outer * math.cos(math.radians(self.azimuth))
        ay = cy + radius_outer * math.sin(math.radians(self.azimuth))
        self.canvas.create_line(cx, cy, ax, ay, fill="blue", width=3)

        # Elevation relative to azimuth
        ex = cx + radius_inner * math.cos(math.radians(self.elevation + self.azimuth))
        ey = cy + radius_inner * math.sin(math.radians(self.elevation + self.azimuth))
        self.canvas.create_oval(cx - radius_inner, cy - radius_inner,
                                cx + radius_inner, cy + radius_inner,
                                outline="gray", width=2)
        self.canvas.create_line(cx, cy, ex, ey, fill="red", width=3)

        self.canvas.create_text(250, 470,
                                text=f"Azimuth: {self.azimuth:.1f}°    Elevation: {self.elevation:.1f}°",
                                font=("Arial", 14))


GimbalGUI()
