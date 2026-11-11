'''
Functionality for user to view history
'''

from datetime import datetime


DATE_FORMAT = "%d-%m-%Y"

#Return all of the user's records dated today (newest first)
def todays_records(data, user_id):
    today = datetime.now().strftime(DATE_FORMAT)
    return [record for record in data.get_user_records(user_id) if record.get_date() == today]

# User's assessment records for the history page, newest first
def history_records(data, user_id):
    return data.get_user_records(user_id)


# User's most recent assessment record
def latest_record(data, user_id):
    records = data.get_user_records(user_id)
    return records[0] if records else None


# Find user's assessment record from id.
# None if there is no such record or record belongs to another user
def find_record(data, user_id, record_id):
    for record in data.get_user_records(user_id):
        if record.get_record_id() == record_id:
            return record
    return None