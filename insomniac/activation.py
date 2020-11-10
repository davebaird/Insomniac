import urllib.request
from urllib.error import HTTPError

from insomniac.utils import *

HOST = "https://insomniac-bot.com"
PATH_VALIDATE = "/validate"
PATH_ACTIVATE = "/activate/"


class ActivationController:
    is_activated = False

    def validate(self, activation_code):
        if not activation_code == "" and _validate(activation_code):
            self.is_activated = True

        if not self.is_activated:
            dot = '\n    - '
            print_timeless(f"Hi! Since of v3.1.0 all core features in this project are free to use.\n"
                           f"You may want to get more fine grained control over the bot via these features:"
                           f"{dot}{COLOR_BOLD}Filtering{COLOR_ENDC} - skip unwanted accounts by various parameters"
                           f"{dot}{COLOR_BOLD}Removing mass followers{COLOR_ENDC} - automate \"cleaning\" you account"
                           f"{dot}{COLOR_BOLD}Analytics tool{COLOR_ENDC} - build presentation that shows your growth"
                           f"{dot}{COLOR_BOLD}Scrapping (next release){COLOR_ENDC} - will make interactions "
                           f"significantly safer and faster\n"
                           f"Activate by supporting our small team: {COLOR_BOLD}{HOST}{PATH_ACTIVATE}{COLOR_ENDC}\n")


def print_activation_required_to(action):
    print_timeless(COLOR_FAIL + f"\nActivate the bot to {action}:\n" + COLOR_BOLD + f"{HOST}{PATH_ACTIVATE}" +
                   COLOR_ENDC)


def _validate(activation_code):
    reason = None
    try:
        with urllib.request.urlopen(f"{HOST}{PATH_VALIDATE}?activation_code={activation_code}",
                                    context=ssl.SSLContext()) as response:
            code = response.code
    except HTTPError as e:
        code = e.code
        reason = e.reason
    except URLError as e:
        code = -1
        reason = e.reason

    if code == 200:
        print(COLOR_OKGREEN + "Your activation code is confirmed, welcome!" + COLOR_ENDC)
        return True

    if reason is None:
        reason = "Unknown response code"

    print(COLOR_FAIL + f"Activation code is not confirmed: {code} ({reason})" + COLOR_ENDC)
    return False


class ActivationRequiredException(Exception):
    pass