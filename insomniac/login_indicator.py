from insomniac.utils import *
from insomniac.action_runners.login.action_login import got_login_landing_page


class LoginError(Exception):
    pass


class LoginIndicator:

    def detect_login_page(self, device, quick=False):

        if got_login_landing_page(device, quick=quick) is True:
            raise LoginError("Login required!")
        return False


login_indicator = LoginIndicator()
