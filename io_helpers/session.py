'''
Session State
'''

# Session Class
class Session:
    def __init__(self):
        self.running = True
        self.uid = None
        self.username = None

    #Check if a user is logged in
    def is_logged_in(self):
        return self.uid is not None

    #Change state to logged in
    def log_in(self, uid, username):
        self.uid = uid
        self.username = username

    #Change state to logged out
    def log_out(self):
        self.uid = None
        self.username = None