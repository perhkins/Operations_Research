class Model:
    """
        Inventory Management Model\n
        q -> order quantity\n
        r -> demand rate\n
        R -> production rate\n
        h -> holding cost\n
        c -> unit cost\n
        k -> setup cost\n
        t -> period
    """
    def __init__(self):
        self.r = None # demand rate
        self.R = None # production rate
        self.q = None # order quantity
        self.h = None # holding cost
        self.c = None # unit cost
        self.k = None # setup cost
        self.t = None # period
        self.f = None # ordering frequency
        self.s = None # shortage cost
    
    def calculate_eoq(self):
        eoq = ((2 * self.r * self.k) / self.h ) ** 0.5
        return eoq
    
    def calculate_ebq(self):
        ebq = ((2 * self.r * self.k) / self.h) ** 0.5 * ((self.R / (self.R - self.r)) ** 0.5)
        return ebq
    
    def calculate_spm(self, selling_price, salvage_price): 
        """Single Point Model for Probabilistic Inventory Model
        It returns the probability of the demand being less than or equal to the optimal order quantity (q) but greater than the optimal quantity - 1."""
        self.s = selling_price - self.c
        self.h = self.c - salvage_price
        probability = self.s / (self.s + self.h)
        return probability
    
    def calculate_total_cost(self, optimal_q, model_type):
        if model_type == "eoq":
            total_cost = (self.r * self.c) + ((self.r * self.k) / optimal_q) + ((optimal_q * self.h) / 2)
        elif model_type == "ebq":
            total_cost = (self.r * self.c) + ((self.r * self.k) / optimal_q) + (((optimal_q * self.h) / 2) * (1 - (self.r / self.R)))
        return total_cost
    
    def total_variable_cost(self, optimal_q, model_type):
        if model_type == "eoq":
            variable_cost = ((self.r * self.k) / optimal_q) + ((optimal_q * self.h) / 2)
        elif model_type == "ebq":
            variable_cost = ((self.r * self.k) / optimal_q) + (((optimal_q * self.h) / 2) * (1 - (self.r / self.R)))
        return variable_cost
    
    def optimal_replenishment_time(self, model_type, optimal_q = None):
        if model_type == "eoq":
            replenishment_time = ((2 * self.k) / (self.h * self.r) ) ** 0.5
        elif model_type == "ebq":
            replenishment_time = optimal_q / self.r if optimal_q else self.calculate_ebq() / self.r
        return replenishment_time
    
    def ordering_frequency(self, optimal_q):
        self.f = self.r / optimal_q
        return self.f