from datetime import datetime
import copy


def format_date(date_input):
    def convert(d):
        if isinstance(d, str):
            try:
                d = datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                return d
        elif not isinstance(d, datetime):
            return d
        return d.strftime("%d-%b-%y")

    if isinstance(date_input, list):
        return ", ".join(convert(d) for d in date_input)
    else:
        return convert(date_input)


def format_scheduler_output(data):
    formatted_data = copy.deepcopy(data)
    date_fields = ["dev_start", "dev_end",
                   "test_start", "test_end", "leave_schedule"]

    for item in formatted_data:
        for field in date_fields:
            if field in item and item[field]:
                item[field] = format_date(item[field])
    return formatted_data
