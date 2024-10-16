import datetime


def has_available_dates_after(availability_json, date_string):
    date_objects = [
        datetime.datetime.strptime(date, "%Y-%m-%d")
        for date in availability_json.keys()
    ]
    if len(date_objects) == 0:
        return False
    latest_date = max(date_objects)
    check_date = datetime.datetime.strptime(date_string, "%Y-%m-%d")
    return latest_date > check_date


def filter_availability(availability_json, begin_date_str, end_date_str):
    # Convert string dates to datetime objects for comparison
    date_objects = {
        datetime.datetime.strptime(date, "%Y-%m-%d"): value
        for date, value in availability_json.items()
    }

    # Convert begin_date_str and end_date_str to datetime objects
    begin_date = datetime.datetime.strptime(begin_date_str, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")

    # Filter the dates that fall between the begin and end date
    filtered_data = {
        date: value
        for date, value in date_objects.items()
        if begin_date <= date <= end_date
    }

    # Update the JSON string with filtered data
    response = {
        date.strftime("%Y-%m-%d"): value for date, value in filtered_data.items()
    }
    return response
