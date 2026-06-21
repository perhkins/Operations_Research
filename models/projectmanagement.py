class Activity:
    def __init__(self, Activity, duration:int, predecessors:list[Activity] = None):
        self.Activity = Activity
        self.duration = duration
        self.predecessors = predecessors
        self.nextEvent: Event = None

class Event: #Event is a point in time when an Activity starts or ends in a project timeline
    def __init__(self):
        self.id: int = 1
        self.pendingjobs: list[Activity] = []
        self.forwardedjobs: list[Activity] = []
        self.Fpass: int = 0
        self.Bpass: int = 0

class Project:
    def __init__(self):
        self.head: Event = Event()
        self.nEvents: int = 1
        self.activities: list[Activity] = []
        self.paths: list[list[Activity]] = [[]]
        self.critical_path: tuple[list[Activity], int] = ([], 0)

    def add_Activity(self, Activity: Activity):
        self.activities.append(Activity)
        if Activity.predecessors is None:
            self.head.forwardedjobs.append(Activity)
        else:
            # Find the event corresponding to the last predecessor
            last_predecessor = Activity.predecessors[-1]
            if last_predecessor.nextEvent is None:
                # Create a new event if the predecessor doesn't have a next event
                last_predecessor.nextEvent = Event()
                self.nEvents += 1
                last_predecessor.nextEvent.id = self.nEvents
                for predecessor in Activity.predecessors:
                    if predecessor.nextEvent is None:
                        predecessor.nextEvent = last_predecessor.nextEvent
                    last_predecessor.nextEvent.pendingjobs.append(predecessor)
            # Add the Activity to the forwarded jobs of the last predecessor's event
            last_predecessor.nextEvent.forwardedjobs.append(Activity)

    def get_paths(self):
        def dfs(event: Event, path: list[Activity]):
            if not event.forwardedjobs:
                self.paths.append(path.copy())
                duration = sum(Activity.duration for Activity in path)
                if duration > self.critical_path[1]:
                    self.critical_path = (path.copy(), duration)
                return
            for job in event.forwardedjobs:
                path.append(job)
                dfs(job.nextEvent, path)
                path.pop()

        dfs(self.head, [])
    
class TimeAnalysis:
    def __init__(self, project: Project):
        self.project = project
        self.project.get_paths()
        self.tail = Event()
        self.tail.pendingjobs.append(self.project.critical_path[0][-1]) #Tail is the last event in the critical path
        self.project.critical_path[0][-1].nextEvent = self.tail
        self.project.nEvents += 1
        self.tail.id = self.project.nEvents

    def forward_pass(self):
        for path in self.project.paths:
            time = 0
            for Activity in path:
                time += Activity.duration
                if Activity.nextEvent is None: #Last Activity in the path
                    Activity.nextEvent = self.tail
                    self.tail.pendingjobs.append(Activity)
                Activity.nextEvent.Fpass = time if Activity.nextEvent.Fpass == 0 else max(Activity.nextEvent.Fpass, time)
    
    def backward_pass(self):
        for path in self.project.paths:
            time = self.project.critical_path[1]
            for Activity in reversed(path):
                if Activity.nextEvent is None:
                    Activity.nextEvent = self.tail
                    self.tail.pendingjobs.append(Activity)
                Activity.nextEvent.Bpass = time if Activity.nextEvent.Bpass == 0 else min(Activity.nextEvent.Bpass, time)
                time -= Activity.duration

    def floats(self):
        Floats = {}
        for a in self.project.activities:
            total_float = a.nextEvent.Bpass - a.predecessors[-1].nextEvent.Fpass - a.duration
            ind_float = a.nextEvent.Fpass - a.predecessors[-1].nextEvent.Bpass - a.duration
            free_float = a.nextEvent.Fpass - a.predecessors[-1].nextEvent.Fpass - a.duration
            Floats[a.Activity] = (total_float, ind_float, free_float)
        return Floats

class ActivityExtended:
    def __init__(self, Activity: Activity, normal_cost:int, crash_cost:int, crash_time:int):
        self.Activity = Activity
        self.normal_cost = normal_cost
        self.crash_cost = crash_cost
        self.crash_time = crash_time

class CostAnalysis:
    def __init__(self, project: Project, overhead_cost:int = 0):
        self.project = project
        self.project.get_paths()
        self.overhead_cost = overhead_cost * self.project.critical_path[1]
        self.activity_extensions: list[ActivityExtended] = []

    def total_normal_cost(self):
        return sum(a.normal_cost for a in self.activity_extensions) + self.overhead_cost
    
    def minimal_cost_and_duration(self):
        min_cost = self.total_normal_cost()
        min_duration = self.project.critical_path[1]
        for a in self.activity_extensions:
            if a.Activity in self.project.critical_path[0]: #Only consider crashing activities on the critical path
                reduced_duration = a.Activity.duration - a.crash_time
                cost_crash = (a.crash_cost - a.normal_cost)
                if reduced_duration > 0: #Only consider crashing if it reduces cost
                    new_duration = min_duration - reduced_duration
                    new_cost = min_cost + cost_crash - (self.overhead_cost * reduced_duration)
                    if new_cost < min_cost:
                        min_cost = new_cost
                        min_duration = new_duration
        return min_cost, min_duration