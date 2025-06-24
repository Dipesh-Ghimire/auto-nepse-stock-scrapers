from ..capital import CAPITALS

class Account:
    def __init__(self, user, dp, username, password, crn, pin):
        self.user = user
        self.dp = dp
        self.username = username
        self.password = password
        self.crn = crn
        self.pin = pin
        self.capital_id = next(item for item in CAPITALS if item['code'] == str(dp))['id']

    @property
    def demat(self):
        return f"130{self.dp}{self.username}"