'''
Assessment trends data
'''

MIN_RECORDS = 2

# Returns the graph data for the progress page: one dict per assessment, oldest -> newest,
# or None if the user has fewer than MIN_RECORDS assessments
def trend_points(data, uid):
    user_records = data.get_user_records(uid)
    if len(user_records) < MIN_RECORDS:
        return None

    #As records are stored newest first; reverse so the graph runs oldest -> newest
    return data.get_user_int_records(user_records, uid)[::-1]