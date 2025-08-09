# scheduler.py
from datetime import date, datetime, timedelta
import copy


class Scheduler:
    RESOURCE_TYPE_DEVELOPER = 'DEV'
    RESOURCE_TYPE_TESTER = 'TESTER'

    def __init__(self, resource_list=None, work_items_list=None):
        """
        resource_list: list of dicts, each must have keys: id, name, type, leave_schedule (list of 'YYYY-MM-DD' strings)
        work_items_list: list of dicts, each must have keys: id, name, dev_effort (days, can be decimal),
                         tester_effort, priority (lower = higher priority)
        """
        # Keep original (for display) and working copy
        self._initial_resource_list = copy.deepcopy(resource_list or [])
        self.resourceList = copy.deepcopy(resource_list or [])
        self.workItemsList = copy.deepcopy(work_items_list or [])

        # Normalize: ensure leave_schedule exists and items are strings
        for r in self.resourceList:
            ls = r.get("leave_schedule", [])
            if isinstance(ls, str):
                # e.g., "['2025-08-06','2025-08-07']" or "2025-08-06,2025-08-07"
                # try to parse comma separated
                r["leave_schedule"] = [d.strip()
                                       for d in ls.strip("[] ").split(",") if d.strip()]
            else:
                r["leave_schedule"] = [str(d) for d in ls]

        for w in self.workItemsList:
            # Ensure numerical efforts are floats
            w["dev_effort"] = float(w.get("dev_effort", 0) or 0)
            w["tester_effort"] = float(w.get("tester_effort", 0) or 0)

        self.logs = []

    def get_resource_list(self):
        return self.resourceList

    def get_resource_list_initial(self):
        return copy.deepcopy(self._initial_resource_list)

    def get_work_items(self):
        return self.workItemsList

    # --------- Date utilities ----------
    def is_weekend(self, dt):
        # dt is a datetime.date or datetime
        return dt.weekday() >= 5  # Sat=5, Sun=6

    def next_business_day(self, dt):
        # dt is a datetime or date; return datetime
        if isinstance(dt, str):
            dt = datetime.strptime(dt, "%Y-%m-%d")
        if isinstance(dt, date) and not isinstance(dt, datetime):
            dt = datetime(dt.year, dt.month, dt.day)
        while self.is_weekend(dt):
            dt += timedelta(days=1)
        return dt

    def generate_business_days(self, start_date_str, duration_days):
        """
        Returns a list of business-day date strings (YYYY-MM-DD) covering duration_days.
        Duration is in days and may be decimal; we convert to hours (1 day = 8 hours)
        and allocate full business days until hours requirement is met.
        """
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        hours_required = duration_days * 8.0
        allocated_hours = 0.0
        business_days = []

        current = self.next_business_day(start_dt)
        while allocated_hours < hours_required:
            if not self.is_weekend(current):
                business_days.append(current.strftime("%Y-%m-%d"))
                allocated_hours += 8.0
            current += timedelta(days=1)
        return business_days

    # --------- Scheduling helpers ----------
    def find_earliest_block(self, resource, start_date_str, duration_days):
        """
        For a given resource, find the earliest continuous block (list of YYYY-MM-DD strings)
        of length = duration_days (in business days/hours sense) starting at or after start_date_str.
        The block is continuous across business days; weekends are skipped in generation.
        """
        attempt_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        attempt_dt = self.next_business_day(attempt_dt)

        # Keep searching until a block with no overlap found
        while True:
            block = self.generate_business_days(
                attempt_dt.strftime("%Y-%m-%d"), duration_days)
            # if none of the dates in block are in resource's leave_schedule => available
            if all(day not in resource.get("leave_schedule", []) for day in block):
                return block
            # otherwise shift start by 1 day and try again (to next business day)
            attempt_dt += timedelta(days=1)
            attempt_dt = self.next_business_day(attempt_dt)

    def assign_best_resource(self, start_date_str, duration_days, resource_type):
        """
        Among all resources of resource_type, find which can finish earliest
        (i.e., whose earliest available block ends soonest). Assign that resource
        by appending the block dates into its leave_schedule and return:
            (resource_name, block_start_str, block_end_str)
        If none available, returns (None, None, None)
        """
        best_resource = None
        best_block = None
        best_end_dt = None

        for resource in self.resourceList:
            if resource.get("type") != resource_type:
                continue
            # find earliest continuous block for this resource
            block = self.find_earliest_block(
                resource, start_date_str, duration_days)
            if not block:
                continue
            end_dt = datetime.strptime(block[-1], "%Y-%m-%d")
            if best_end_dt is None or end_dt < best_end_dt:
                best_end_dt = end_dt
                best_resource = resource
                best_block = block

        if best_resource and best_block:
            # Block the days in the resource's leave_schedule (avoid duplicates)
            for d in best_block:
                if d not in best_resource["leave_schedule"]:
                    best_resource["leave_schedule"].append(d)
            return best_resource.get("name"), best_block[0], best_block[-1]

        return None, None, None

    # --------- Main scheduling ----------
    def schedule_work_items(self, output_to_console=True, start_date=None):
        start_date = date.today().strftime("%Y-%m-%d")  # starting with today's date
        result = []

        for item in self.workItemsList:
            dev_name, dev_start, dev_end = self.assign_best_resource(
                start_date, item["dev_effort"], self.RESOURCE_TYPE_DEVELOPER)
            tester_start_date = self.next_business_day(datetime.strptime(
                dev_end, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            tester_name, tester_start, tester_end = self.assign_best_resource(
                tester_start_date, item["tester_effort"], self.RESOURCE_TYPE_TESTER)

            msg = f"{item['name']} => Dev: {dev_name} ({dev_start} to {dev_end}), Tester: {tester_name} ({tester_start} to {tester_end})"
            self.logs.append(msg)

            result.append({
                "work_id": item["id"],
                "work_name": item["name"],
                "dev_name": dev_name,
                "dev_effort": item["dev_effort"],
                "dev_start": datetime.strptime(dev_start, "%Y-%m-%d"),
                "dev_end": dev_end,
                "tester_name": tester_name,
                "tester_effort": item["tester_effort"],
                "test_start": tester_start,
                "test_end": tester_end
            })

        if output_to_console:
            for log in self.logs:
                print(log)

        return result


if __name__ == "__main__":
    # Quick local test
    sample_resources = [
        {"id": "r1", "name": "Dev 1", "type": Scheduler.RESOURCE_TYPE_DEVELOPER,
            "leave_schedule": ["2025-08-06"]},
        {"id": "r2", "name": "Dev 2",
            "type": Scheduler.RESOURCE_TYPE_DEVELOPER, "leave_schedule": []},
        {"id": "r3", "name": "Tester 1", "type": Scheduler.RESOURCE_TYPE_TESTER,
            "leave_schedule": ["2025-08-08"]},
        {"id": "r4", "name": "Tester 2",
            "type": Scheduler.RESOURCE_TYPE_TESTER, "leave_schedule": []}
    ]
    sample_work_items = [
        {"id": "w1", "name": "Work 1", "dev_effort": 2.5,
            "tester_effort": 1.0, "priority": 1},
        {"id": "w2", "name": "Work 2", "dev_effort": 1.0,
            "tester_effort": 0.5, "priority": 2}
    ]

    s = Scheduler(sample_resources, sample_work_items)
    out = s.schedule_work_items(
        output_to_console=True, start_date="2025-08-04")
    print("\nRESULTS:")
    for r in out:
        print(r)
