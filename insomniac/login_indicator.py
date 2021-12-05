from insomniac.utils import *
from insomniac.action_runners.login.action_login import got_login_landing_page


class LoginRequiredError(Exception):
    pass


class LoginIndicator:

    def detect_login_page(self, device, quick=False):

        if got_login_landing_page(device, quick=quick) is True:
            raise LoginRequiredError("Login required!")
        return False


login_indicator = LoginIndicator()
