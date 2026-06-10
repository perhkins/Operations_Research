from collections import deque


class TransportationProblem:
    def __init__(self, supply_length, demand_length):
        self.supply = [0] * supply_length
        self.demand = [0] * demand_length
        self.costs = [[0] * demand_length for _ in range(supply_length)]
    
    def set_supply(self, index, value):
        self.supply[index] = value

    def set_demand(self, index, value):
        self.demand[index] = value

    def set_cost(self, supply_index, demand_index, value):
        self.costs[supply_index][demand_index] = value

    def is_balanced(self):
        print("is_balanced:", sum(self.supply) == sum(self.demand))
        return sum(self.supply) == sum(self.demand)
    
    def balance(self):
        total_supply = sum(self.supply)
        total_demand = sum(self.demand)
        if total_supply > total_demand:
            self.demand.append(total_supply - total_demand)
            for row in self.costs:
                row.append(0)  # No cost for artificial demand
        elif total_demand > total_supply:
            self.supply.append(total_demand - total_supply)
            self.costs.append([0] * len(self.demand))  # No cost for artificial supply
    
    def solve(self, method='northwest', optimization_method='modi', show_iterations=False):
        # Build an initial feasible solution and then improve it with the requested optimizer.
        method = method.lower()
        optimization_method = optimization_method.lower()

        if not self.is_balanced():
            self.balance()

        if method == 'northwest':
            initial_basic_feasible_solution = self.northwest_corner_method()
        elif method == 'leastcost':
            initial_basic_feasible_solution = self.leastcost_method()
        else:
            raise ValueError(f"Unsupported initial solution method: {method}")

        optimal_result = self.optimal_solution(
            initial_basic_feasible_solution,
            method=optimization_method,
            show_iterations=show_iterations,
        )

        if show_iterations:
            optimal_feasible_solution, history = optimal_result
            return initial_basic_feasible_solution, optimal_feasible_solution, history

        return initial_basic_feasible_solution, optimal_result
    
    def leastcost_method(self):
        allocation_table = AllocationTable(len(self.supply), len(self.demand))
        supply_remaining = self.supply[:]
        demand_remaining = self.demand[:]
        costs = self.costs[:]
        
        sorted_costs = self.get_sorted_positions(costs)

        for r, c in sorted_costs:
            if supply_remaining[r] == 0 or demand_remaining[c] == 0:
                    continue
            allocation = min(supply_remaining[r], demand_remaining[c])
            allocation_table.allocations[r][c] = allocation
            supply_remaining[r] -= allocation
            demand_remaining[c] -= allocation
        
        return allocation_table
        
    def northwest_corner_method(self):
        allocation_table = AllocationTable(len(self.supply), len(self.demand))
        supply_remaining = self.supply[:]
        demand_remaining = self.demand[:]
        

        for i in range(len(self.supply)):
            for j in range(len(self.demand)):
                if supply_remaining[i] == 0 or demand_remaining[j] == 0:
                    continue
                allocation = min(supply_remaining[i], demand_remaining[j])
                allocation_table.allocations[i][j] = allocation
                supply_remaining[i] -= allocation
                demand_remaining[j] -= allocation
        
        return allocation_table
    
    def is_degenerate(self, allocation_table):
        allocated_cells = sum(1 for row in allocation_table.allocations for cell in row if cell is not None)
        return allocated_cells != (len(self.supply) + len(self.demand) - 1)
    
    def get_sorted_positions(self, matrix: list[list[int]]) -> list[tuple[int, int]]:
        """
        Returns a list of (row, col) positions sorted by their values in ascending order.
        """
        if not matrix or not matrix[0]:
            return []
    
        # Flatten with positions
        flat_with_pos = [
            (matrix[r][c], r, c)
            for r in range(len(matrix))
            for c in range(len(matrix[0]))
        ]
    
        # Sort by value
        flat_with_pos.sort(key=lambda x: x[0])
    
        # Return only positions
        return [(r, c) for _, r, c in flat_with_pos]
    
    def optimal_solution(self, allocation_table, method='modi', show_iterations=False):
        """Improve an initial feasible transportation solution.

        method:
            - "modi": use row/column potentials and reduced costs.
            - "steppingstone": use the stepping-stone cycle cost change directly.

        If show_iterations is True, return a tuple of (optimal_table, history) where
        history contains a copy of every allocation table encountered, including the initial one.
        """
        method = method.lower()
        if method not in {"modi", "steppingstone"}:
            raise ValueError(f"Unsupported optimization method: {method}")

        current_table = self._copy_allocation_table(allocation_table)
        history = [self._copy_allocation_table(current_table)] if show_iterations else None
        tolerance = 1e-9
        max_iterations = max(1, len(self.supply) * len(self.demand) * 10)

        for _ in range(max_iterations):
            self._ensure_non_degenerate_basis(current_table)

            entering_cell, improvement = self._select_entering_cell(current_table, method)
            if entering_cell is None or improvement >= -tolerance:
                if show_iterations:
                    return current_table, history
                return current_table

            cycle_cells = self._build_cycle(current_table, entering_cell[0], entering_cell[1])
            if not cycle_cells:
                raise ValueError("Unable to build an improvement cycle for the selected entering cell.")

            pivot_changed = self._pivot_cycle(current_table, cycle_cells)
            if show_iterations:
                history.append(self._copy_allocation_table(current_table))

            if not pivot_changed:
                raise RuntimeError("Transportation pivot did not change the solution; check degeneracy handling.")

        raise RuntimeError("Optimal solution search did not converge within the iteration limit.")

    def _copy_allocation_table(self, allocation_table):
        copied = AllocationTable(
            len(allocation_table.allocations),
            len(allocation_table.allocations[0]) if allocation_table.allocations else 0,
        )
        copied.allocations = [row[:] for row in allocation_table.allocations]
        return copied

    def _basic_cells(self, allocation_table):
        return [
            (i, j)
            for i in range(len(allocation_table.allocations))
            for j in range(len(allocation_table.allocations[i]))
            if allocation_table.allocations[i][j] is not None
        ]

    def _ensure_non_degenerate_basis(self, allocation_table):
        required_basic_cells = len(self.supply) + len(self.demand) - 1
        basic_cells = self._basic_cells(allocation_table)
        if len(basic_cells) >= required_basic_cells:
            return

        total_nodes = len(self.supply) + len(self.demand)
        parent = list(range(total_nodes))
        rank = [0] * total_nodes

        def find(node):
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        def union(left, right):
            root_left = find(left)
            root_right = find(right)
            if root_left == root_right:
                return
            if rank[root_left] < rank[root_right]:
                parent[root_left] = root_right
            elif rank[root_left] > rank[root_right]:
                parent[root_right] = root_left
            else:
                parent[root_right] = root_left
                rank[root_left] += 1

        for i, j in basic_cells:
            union(i, len(self.supply) + j)

        while len(basic_cells) < required_basic_cells:
            best_cell = None
            best_cost = None
            for i in range(len(self.supply)):
                for j in range(len(self.demand)):
                    if allocation_table.allocations[i][j] is not None:
                        continue
                    if find(i) != find(len(self.supply) + j):
                        cell_cost = self.costs[i][j]
                        if best_cell is None or cell_cost < best_cost:
                            best_cell = (i, j)
                            best_cost = cell_cost

            if best_cell is None:
                break

            row_index, column_index = best_cell
            allocation_table.allocations[row_index][column_index] = 0
            basic_cells.append(best_cell)
            union(row_index, len(self.supply) + column_index)

    def _build_basis_adjacency(self, allocation_table):
        adjacency = {('r', i): [] for i in range(len(self.supply))}
        adjacency.update({('c', j): [] for j in range(len(self.demand))})

        for i, j in self._basic_cells(allocation_table):
            row_node = ('r', i)
            col_node = ('c', j)
            adjacency[row_node].append(col_node)
            adjacency[col_node].append(row_node)

        return adjacency

    def _find_path_between_nodes(self, allocation_table, start_node, end_node):
        adjacency = self._build_basis_adjacency(allocation_table)
        queue = deque([start_node])
        parent = {start_node: None}

        while queue:
            node = queue.popleft()
            if node == end_node:
                break
            for neighbor in adjacency[node]:
                if neighbor not in parent:
                    parent[neighbor] = node
                    queue.append(neighbor)

        if end_node not in parent:
            return None

        path = []
        node = end_node
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()
        return path

    def _edge_to_cell(self, left_node, right_node):
        if left_node[0] == 'r' and right_node[0] == 'c':
            return left_node[1], right_node[1]
        if left_node[0] == 'c' and right_node[0] == 'r':
            return right_node[1], left_node[1]
        raise ValueError("Cycle path must alternate between supply and demand nodes.")

    def _build_cycle(self, allocation_table, entering_row, entering_col):
        node_path = self._find_path_between_nodes(allocation_table, ('r', entering_row), ('c', entering_col))
        if not node_path:
            return None

        cycle_cells = [(entering_row, entering_col)]
        for left_node, right_node in zip(node_path, node_path[1:]):
            cycle_cells.append(self._edge_to_cell(left_node, right_node))
        return cycle_cells

    def _cycle_cost_change(self, cycle_cells):
        total_change = 0
        for index, (row, col) in enumerate(cycle_cells):
            if index % 2 == 0:
                total_change += self.costs[row][col]
            else:
                total_change -= self.costs[row][col]
        return total_change

    def _compute_modi_potentials(self, allocation_table):
        u = [None] * len(self.supply)
        v = [None] * len(self.demand)
        u[0] = 0

        changed = True
        basic_cells = self._basic_cells(allocation_table)
        while changed:
            changed = False
            for i, j in basic_cells:
                if u[i] is not None and v[j] is None:
                    v[j] = self.costs[i][j] - u[i]
                    changed = True
                elif v[j] is not None and u[i] is None:
                    u[i] = self.costs[i][j] - v[j]
                    changed = True

        if any(value is None for value in u) or any(value is None for value in v):
            raise ValueError("Unable to compute MODI potentials from the current basis.")

        return u, v

    def _select_entering_cell(self, allocation_table, method):
        empty_cells = [
            (i, j)
            for i in range(len(self.supply))
            for j in range(len(self.demand))
            if allocation_table.allocations[i][j] is None
        ]

        if not empty_cells:
            return None, 0

        best_cell = None
        best_change = 0

        if method == 'modi':
            u, v = self._compute_modi_potentials(allocation_table)
            for i, j in empty_cells:
                change = self.costs[i][j] - u[i] - v[j]
                if change < best_change:
                    best_change = change
                    best_cell = (i, j)
        else:
            for i, j in empty_cells:
                cycle_cells = self._build_cycle(allocation_table, i, j)
                if not cycle_cells:
                    continue
                change = self._cycle_cost_change(cycle_cells)
                if change < best_change:
                    best_change = change
                    best_cell = (i, j)

        return best_cell, best_change

    def _pivot_cycle(self, allocation_table, cycle_cells):
        entering_row, entering_col = cycle_cells[0]
        minus_cells = cycle_cells[1::2]
        theta = min(allocation_table.allocations[row][col] for row, col in minus_cells)

        if theta == 0:
            zero_minus_cell = next(
                ((row, col) for row, col in minus_cells if allocation_table.allocations[row][col] == 0),
                None,
            )
            if zero_minus_cell is None:
                return False

            allocation_table.allocations[entering_row][entering_col] = 0
            allocation_table.allocations[zero_minus_cell[0]][zero_minus_cell[1]] = None
            return True

        for index, (row, col) in enumerate(cycle_cells):
            if index % 2 == 0:
                current_value = allocation_table.allocations[row][col]
                allocation_table.allocations[row][col] = theta if current_value is None else current_value + theta
            else:
                updated_value = allocation_table.allocations[row][col] - theta
                allocation_table.allocations[row][col] = None if updated_value == 0 else updated_value

        return True

    
    def calculate_total_cost(self, allocation_table):
        total_cost = 0
        if self.is_degenerate(allocation_table):
            print("Degenerate Solution")
        for i in range(len(self.supply)):
            for j in range(len(self.demand)):
                allocation = allocation_table.allocations[i][j]
                if allocation is not None:
                    total_cost += allocation * self.costs[i][j]
                    
        return total_cost
    
    def show_allocation_schedule(self, allocation_table):
        schedule_lines = []
        for i, row in enumerate(allocation_table.allocations):
            for j, allocated in enumerate(row):
                if allocated is not None and allocated > 0:
                    line = f"S{i} --|{allocated}|--> D{j}"
                    schedule_lines.append(line)
                    print(line)
        return schedule_lines

class AllocationTable:
    def __init__(self, supply_length, demand_length):
        self.allocations = [[None] * demand_length for _ in range(supply_length)]

#test case  
problem = TransportationProblem(4,3)
supply = [20,16,10,12]
demand = [14,24,10]
for i,val in enumerate(supply):
    problem.set_supply(i,val)
print(problem.supply)
for j,val in enumerate(demand):
    problem.set_demand(j,val)
print(problem.demand)

costs = [[8,6,4],[10,12,2],[12,8,6],[6,10,8]]
for k, row in enumerate(costs):
    for l, val in enumerate(row):
        problem.set_cost(k,l,val)
print(problem.costs)

solution = problem.solve("leastcost")
print(solution)
allocation_schedule = problem.show_allocation_schedule(solution[0])
print("Degenerate Solution?", problem.is_degenerate(solution[0]))
print("Initial Basic Feasible Transportation Cost",problem.calculate_total_cost(solution[0]))