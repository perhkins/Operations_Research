class Constraint:
    def __init__(self, coefficients: list, operator: str, value: float):
        if operator not in ['<=', '>=', '=']:
            raise ValueError("Operator must be one of '<=', '>=', or '='")
        self.coefficients = coefficients
        self.operator = operator # can be '<=', '>=', or '='
        self.value = value

class LinearProgramming:
    def __init__(self, objective: str = "max", coefficients: list = None, constraints: list[Constraint] = None):
        if objective != "max" and objective != "min":
            raise ValueError("Objective must be either 'max' or 'min'")
        
        self.objective = objective # 'max' or 'min'
        self.obj_F = Constraint(coefficients, "=", value=0) if coefficients is not None else None # Objective function
        self.constraints = constraints if constraints is not None else []

        self._check_and_balance_constraints()

    def _check_and_balance_constraints(self, constraint: Constraint = None) -> Constraint|None:
        if not constraint and self.constraints:
            for constraint in self.constraints:
                if (constraint.operator == '>=' and self.objective == "max") or (constraint.operator == '<=' and self.objective == "min"):
                    constraint.coefficients = [-c for c in constraint.coefficients]
                    constraint.value = -constraint.value
                    constraint.operator = '<=' if self.objective == "max" else '>='
            return
        else:
            if (constraint.operator == '>=' and self.objective == "max") or (constraint.operator == '<=' and self.objective == "min"):
                constraint.coefficients = [-c for c in constraint.coefficients]
                constraint.value = -constraint.value
                constraint.operator = '<=' if self.objective == "max" else '>='
            return constraint

    def set_objective(self, objective: str, coefficients: list):
        if objective != "max" and objective != "min":
            raise ValueError("Objective must be either 'max' or 'min'")
        
        self.objective = objective
        self.obj_F = Constraint(coefficients, "=", value=0)

    def add_constraint(self, coefficients: list, operator: str, value: float):
        new_constraint = Constraint(coefficients, operator, value)
        new_constraint = self._check_and_balance_constraints(new_constraint)
        self.constraints.append(new_constraint)

    #Solution using either graphical method (for 2 variables) or Simplex Tableau (for more than 2 variables)
    def solution(self, method: str = "graphical"):
        if method == "graphical" and len(self.obj_F.coefficients) != 2:
            raise ValueError("Graphical method can only be used for problems with 2 variables. Try again with 'simplex' method.")
        
        if method == "graphical":
            return self._graphical_solution()
        elif method == "simplex":
            return self._simplex_solution()
        else:
            raise ValueError("Method must be either 'graphical' or 'simplex'")
    
    def _graphical_solution(self):
        feasible_solns = []

        for constraint in self.constraints: #At optimality, the inequality constraints will be satisfied as equalities.
            # For each constraint, find the intercepts with the axes
            x_intercept = constraint.value / constraint.coefficients[0] if constraint.coefficients[0] != 0 else None
            y_intercept = constraint.value / constraint.coefficients[1] if constraint.coefficients[1] != 0 else None
            feasible_solns.append((x_intercept if x_intercept > 0 else None, y_intercept if y_intercept > 0 else None))
        new_CFS = self._CFS_(feasible_solns)
        self.obj_F.value = new_CFS["optimal_value"]
        fig = self._plot(new_CFS["cfs"])
        return (new_CFS, fig)
    
    def _plot(self, cfs: list[tuple]):
        import matplotlib.pyplot as plt
        import numpy as np
        x_vals = np.linspace(0, 10, 400)
        fig, ax = plt.subplots(figsize=(8, 6))
        for a, b, c in zip(self.constraints.coefficients[0], self.constraints.coefficients[1], self.constraints.value):
            if b != 0:
                y_vals = (c - a*x_vals) / b
                ax.plot(x_vals, y_vals, label=f"{a}x + {b}y ≤ {c}")
            else:
                ax.axvline(x=c/a, label=f"x = {c/a}")
        if cfs:
            polygon = np.array(cfs)
            ax.fill(polygon[:, 0], polygon[:, 1], color='lavender', alpha=0.5, label="Feasible Region")
        for x, y in cfs:
            ax.scatter(x, y, color='black')
            ax.text(x + 0.1, y + 0.1, f"({x:.1f}, {y:.1f})")
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.set_title("Linear Programming Feasible Region")
        ax.legend()
        ax.grid(True)
        return fig

    def _line_equation(self, x_int, y_int):
        """
        Returns slope (m) and intercept (b) of a line given its x- and y-intercepts.
        Equation: y = m*x + b
        """
        if x_int is None or y_int is None:
            raise ValueError("Both x and y intercepts are required for a line.")

        # Line passes through (x_int, 0) and (0, y_int)
        m = (0 - y_int) / (x_int - 0)
        b = y_int
        return m, b


    def _intersect_lines(self, line1, line2):
        """
        Finds intersection point between two lines.
        Each line is given as (x_intercept, y_intercept).
        """
        m1, b1 = self._line_equation(*line1)
        m2, b2 = self._line_equation(*line2)

        if m1 == m2:
            return None  # Parallel lines, no intersection

        # Solve for x: m1*x + b1 = m2*x + b2
        x = (b2 - b1) / (m1 - m2)
        y = m1 * x + b1

        if x < 0 or y < 0:
            return None  # Intersection is not in the first quadrant
        
        return (x, y)


    def _intersect_line_point(self, line, point):
        """
        Find intersection between a line and an axis point.
        - (x, None) means point on x-axis at (x,0).
        Intersection is (x, y_line(x)).
        - (None, y) means point on y-axis at (0,y).
        Intersection is (x_line(y), y).
        """
        m, b = self._line_equation(*line)
        px, py = point

        if px is not None and py is None:
            # Point on x-axis
            x = px
            y = m * x + b

            if y < 0:
                return None  # Intersection is not in the first quadrant
            return (x, y)

        elif py is not None and px is None:
            # Point on y-axis
            y = py
            # Solve for x: y = m*x + b
            if m == 0:
                return None  # Horizontal line never meets this y (unless y==b)
            x = (y - b) / m

            if x < 0:
                return None  # Intersection is not in the first quadrant
            return (x, y)

        else:
            raise ValueError("Point must be on one axis (x,None) or (None,y).")
        
    def _is_feasible(self, point: tuple) -> bool:
        x, y = point
        for constraint in self.constraints:
            lhs = constraint.coefficients[0] * x + constraint.coefficients[1] * y
            if constraint.operator == '<=' and lhs > constraint.value:
                return False
            elif constraint.operator == '>=' and lhs < constraint.value:
                return False
            elif constraint.operator == '=' and lhs != constraint.value:
                return False
        return True
    
    def _feasible_corners(self, feasible_solns: list[tuple]) -> list[tuple]:
        points = []
        for i in range(len(feasible_solns)):
            for j in range(i+1, len(feasible_solns)):
                if None not in feasible_solns[i] and None not in feasible_solns[j]:
                    intersection = self._intersect_lines(feasible_solns[i], feasible_solns[j])
                    points.append(intersection) if intersection else None
                else:
                    if None not in feasible_solns[i]:
                        intersection = self._intersect_line_point(feasible_solns[i], feasible_solns[j])
                        points.append(intersection) if intersection else None
                    else:
                        continue #To reduce redundant checks since the line-point intersection will be checked when the other point is treated as a line in the next iteration.
                        # intersection = self._intersect_line_point(feasible_solns[j], feasible_solns[i])
                        # points.append(intersection) if intersection else None
        return [point for point in points if self._is_feasible(point)]

    
    def _CFS_(self, feasible_solns: list[tuple]) -> dict:
        cfs = [(0, 0)] if self._is_feasible((0, 0)) else [] # Check if origin is feasible
        if self.objective == "max":
            # min x_intercept and min y_intercept
            min_x_idx = min((i for i, soln in enumerate(feasible_solns) if soln[0] is not None), key=lambda i: feasible_solns[i][0], default=None)
            cfs.append((feasible_solns[min_x_idx][0], 0)) if min_x_idx is not None else None

            min_y_idx = min((i for i, soln in enumerate(feasible_solns) if soln[1] is not None), key=lambda i: feasible_solns[i][1], default=None)
            cfs.append((0, feasible_solns[min_y_idx][1])) if min_y_idx is not None else None

            cfs.extend(self._feasible_corners(feasible_solns))
        elif self.objective == "min":
            # max x_intercept and max y_intercept
            max_x_idx = max((i for i, soln in enumerate(feasible_solns) if soln[0] is not None), key=lambda i: feasible_solns[i][0], default=None)
            cfs.append((feasible_solns[max_x_idx][0], 0)) if max_x_idx is not None else None

            max_y_idx = max((i for i, soln in enumerate(feasible_solns) if soln[1] is not None), key=lambda i: feasible_solns[i][1], default=None)
            cfs.append((0, feasible_solns[max_y_idx][1])) if max_y_idx is not None else None

            cfs.extend(self._feasible_corners(feasible_solns))

        return {"cfs": cfs, "optimal_point": max(cfs, key=lambda p: self.obj_F.coefficients[0] * p[0] + self.obj_F.coefficients[1] * p[1]) if self.objective == "max" else min(cfs, key=lambda p: self.obj_F.coefficients[0] * p[0] + self.obj_F.coefficients[1] * p[1]), "optimal_value": max(self.obj_F.coefficients[0] * x + self.obj_F.coefficients[1] * y for x, y in cfs) if self.objective == "max" else min(self.obj_F.coefficients[0] * x + self.obj_F.coefficients[1] * y for x, y in cfs)}
    
    def _construct_tableau(self):
        T = [self.obj_F.coefficients.copy()]
        T[0].extend([0] * (len(self.constraints) + 1)) # Add value column for objective function
        for i in self.constraints:
            row = self.constraints[i].coefficients.copy()
            row.append(self.constraints[i].value)
            row.extend([1 if i == j else 0 for j in range(len(self.constraints))]) # Add slack variable coefficients
            T.append(row)
        return T

    def _row_op(self, A, target, source, coeff_t=1, coeff_s=1, operation="add"):
        """
        Perform row operation on matrix A:
        target row = coeff_target*target_row (+/-) coeff_source*source_row
        """
        if operation == "add":
            A[target] = coeff_t*A[target] + coeff_s*A[source]
        elif operation == "sub":
            A[target] = coeff_t*A[target] - coeff_s*A[source]
        else:
            raise ValueError("operation must be 'add' or 'sub'")
        return A
    
    def _find_pivot(self, tableau):
        import numpy as np
        # Find pivot column (most negative in objective function row)
        pivot_col = np.argmin(tableau[0][:-1])
        if tableau[0][pivot_col] >= 0:
            return None, None  # Optimal solution found

        # Find pivot row (minimum ratio test)
        ratios = []
        for i in range(1, len(tableau)):
            if tableau[i][pivot_col] > 0:
                ratios.append(tableau[i][-1] / tableau[i][pivot_col])
            else:
                ratios.append(float('inf'))  # Ignore non-positive entries
        pivot_row = np.argmin(ratios) + 1  # +1 to account for objective function row
        if ratios[pivot_row - 1] == float('inf'):
            raise ValueError("Linear program is unbounded.")
        
        return pivot_row, pivot_col

    def _simplex_solution(self):
        import numpy as np
        tableau = np.array(self._construct_tableau())
        basic_vars_idx = [len(self.obj_F.coefficients) + i for i in range(len(self.constraints))] # Initial basic variables are the slack variables

        pivot_row, pivot_col = self._find_pivot(tableau)
        while pivot_row is not None and pivot_col is not None:
            tableau[pivot_row] = (1/tableau[pivot_row][pivot_col]) * tableau[pivot_row] # Normalize pivot row

            for i in range(len(tableau)):
                if i != pivot_row:
                    tableau = self._row_op(tableau, i, pivot_row, operation="sub", coeff_s=tableau[i][pivot_col])
            basic_vars_idx[pivot_row - 1] = pivot_col # Update basic variable index for the pivot row
            pivot_row, pivot_col = self._find_pivot(tableau)
        
        optimal_value = tableau[0][-1]
        optimal_point = [0] * len(self.obj_F.coefficients)
        for i, var_idx in enumerate(basic_vars_idx):
            if 0 <= var_idx < len(optimal_point):
                optimal_point[var_idx] = tableau[i + 1][-1]
        return {"optimal_value": optimal_value, "optimal_point": optimal_point}