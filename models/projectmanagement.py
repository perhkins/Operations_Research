class activity:
    def __init__(self, activity, duration:int, predecessors:list[activity] = None):
        self.activity = activity
        self.duration = duration
        self.predecessors = predecessors
        self.nextEvent: Event = None

class Event: #Event is a point in time when an activity starts or ends in a project timeline
    def __init__(self):
        self.id: int = 1
        self.pendingjobs: list[activity] = []
        self.forwardedjobs: list[activity] = []
        self.Fpass: int = 0
        self.Bpass: int = 0

class Project:
    def __init__(self):
        self.head: Event = Event()
        self.nEvents: int = 1
        self.activities: list[activity] = []
        self.paths: list[list[activity]] = [[]]
        self.critical_path: tuple[list[activity], int] = ([], 0)

    def add_activity(self, activity: activity):
        self.activities.append(activity)
        if activity.predecessors is None:
            self.head.forwardedjobs.append(activity)
        else:
            # Find the event corresponding to the last predecessor
            last_predecessor = activity.predecessors[-1]
            if last_predecessor.nextEvent is None:
                # Create a new event if the predecessor doesn't have a next event
                last_predecessor.nextEvent = Event()
                self.nEvents += 1
                last_predecessor.nextEvent.id = self.nEvents
                for predecessor in activity.predecessors:
                    if predecessor.nextEvent is None:
                        predecessor.nextEvent = last_predecessor.nextEvent
                    last_predecessor.nextEvent.pendingjobs.append(predecessor)
            # Add the activity to the forwarded jobs of the last predecessor's event
            last_predecessor.nextEvent.forwardedjobs.append(activity)

    def get_paths(self):
        def dfs(event: Event, path: list[activity]):
            if not event.forwardedjobs:
                self.paths.append(path.copy())
                duration = sum(activity.duration for activity in path)
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
            for activity in path:
                time += activity.duration
                if activity.nextEvent is None: #Last activity in the path
                    activity.nextEvent = self.tail
                    self.tail.pendingjobs.append(activity)
                activity.nextEvent.Fpass = time if activity.nextEvent.Fpass == 0 else max(activity.nextEvent.Fpass, time)
    
    def backward_pass(self):
        for path in self.project.paths:
            time = self.project.critical_path[1]
            for activity in reversed(path):
                if activity.nextEvent is None:
                    activity.nextEvent = self.tail
                    self.tail.pendingjobs.append(activity)
                activity.nextEvent.Bpass = time if activity.nextEvent.Bpass == 0 else min(activity.nextEvent.Bpass, time)
                time -= activity.duration

    def floats(self):
        Floats = {}
        for a in self.project.activities:
            total_float = a.nextEvent.Bpass - a.predecessors[-1].nextEvent.Fpass - a.duration
            ind_float = a.nextEvent.Fpass - a.predecessors[-1].nextEvent.Bpass - a.duration
            free_float = a.nextEvent.Fpass - a.predecessors[-1].nextEvent.Fpass - a.duration
            Floats[a.activity] = (total_float, ind_float, free_float)
        return Floats
