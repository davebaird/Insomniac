from insomniac.views import TabBarView, case_insensitive_re
from insomniac.sleeper import sleeper
from insomniac.utils import *
from insomniac.device_facade import DeviceFacade
from insomniac.action_get_my_profile_info import get_my_profile_info
# import re
import os
import time
# import json
# from pprint import pprint
from random import randrange
from datetime import datetime
import pprint
from pathlib import Path

WAIT_EXISTS = 1
WAIT_DEFAULT = 10
WAIT_FOR_LANDING_PAGE = 5

STOPFILE = Path('posting.stopfile').resolve()
FIRST_PAUSE_ENCOUNTERED = False


def _pause(msg=''):
    return

    global FIRST_PAUSE_ENCOUNTERED
    if FIRST_PAUSE_ENCOUNTERED is False:
        FIRST_PAUSE_ENCOUNTERED = True
        STOPFILE.touch()

    if len(msg):
        msg = f'{msg}: '

    _printbold(f'{msg}To continue: rm {str(STOPFILE)}')

    while True:
        if STOPFILE.exists() is False:
            STOPFILE.touch()
            break
        time.sleep(1)


# Use ~/Android/Sdk/tools/bin/uiautomatorviewer to inspect these files
# This (the screencap) throws an exception on AOSP emulators, requires a google_apis emulator - nope, broken there as well

# problems with screenshot, in logcat:
# W SurfaceFlinger : FB is protected: PERMISSION_DENIED
# See: https://support.saucelabs.com/hc/en-us/articles/115003569933-Unable-to-access-UI-elements-record-video-or-take-screenshots-during-Android-Native-Application-tests-on-Real-Devices-and-Emulators


# copied from utils.py
def _get_logs_dir_name():
    return 'logs'
    # if globals.is_ui_process:
    #     return UI_LOGS_DIR_NAME
    # return ENGINE_LOGS_DIR_NAME


# Adapted from utils.py _get_log_file_name()
# Using this so the logfile and ui files sort together in directory listing
def _get_log_file_prefix():
    curr_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_prefix = f"insomniac_log-{curr_time}{'-'+insomniac_globals.execution_id if insomniac_globals.execution_id != '' else ''}"
    return log_prefix


# def _dump_ui(device, name=f"{_get_log_file_prefix()}-ui"):
#     time.sleep(2)
#     dir = _get_logs_dir_name()
#     device.dump_hierarchy(f'{dir}/{name}.uix')
#     _sshot(device, '/sdcard/ui.png')
#     _adb_cmd(device, ['pull', '/sdcard/ui.png', f'{dir}/{name}.png'])
#     _printbold(f"Dumped UI files {dir}/{name}.png and {dir}/{name}.uix")


# def _sshot(device, filepath):
#     # For screencap command and permissions problems: https://blog.actorsfit.com/a?ID=01600-ecf7c9f0-a06f-4289-b10e-1f9ebf8a3c5d
#     # -p: png format

#     # this works from the shell but not from here. Relatedly, probably, uiautomatorviewer can't load from the device.
#     # _adb_cmd(device, f"shell screencap -p {filepath}")
#     _adb_cmd(device, ['shell', 'screencap', '-p', filepath])

#     # device.deviceV2.screenshot().save(filepath)
#     # _printbold(f"Saved screenshot to {filepath}" % filepath)


# def _adb_cmd(device, cmd):
#     if type(cmd) is str:
#         raise RuntimeError("adb commands must be list, not string")
#         # adb_cmd = f"adb {'' if device.device_id is None else ('-s '+ device.device_id)} {cmd}"
#         # _printbold(f"Running adb STR command: {adb_cmd}")

#     adb_cmd = ['adb']
#     if device.device_id is not None:
#         adb_cmd.extend(['-s', device.device_id])
#     adb_cmd.extend(cmd)
#     _printbold(f"Running adb command: {adb_cmd}")
#     result = subprocess.run(adb_cmd, stdout=PIPE,
#                             stderr=PIPE, shell=False, encoding="utf8")
#     pprint.pprint(result)
#     if result.returncode != 0:
#         raise IOError(
#             f"Error running '{adb_cmd}': STDOUT: {result.stdout} STDERR: {result.stderr} [{result.returncode}]")
#     return result.stdout.strip()


def _printfail(msg):
    print(COLOR_FAIL + msg + COLOR_ENDC)


def _printok(msg):
    print(COLOR_OKGREEN + msg + COLOR_ENDC)


def _printokblue(msg):
    print(COLOR_OKBLUE + msg + COLOR_ENDC)


def _printreport(msg):
    print(COLOR_REPORT + msg + COLOR_ENDC)


def _printbold(msg):
    print(COLOR_BOLD + msg + COLOR_ENDC)


def _find_wait_exists(device, label, **kwargs):
    thing = _maybe_find_wait_exists(device, label=label, **kwargs)
    if thing is not None:
        return thing
    _fail(device, label)


def _fail(device, label, msg=None):
    if msg is None:
        msg = f'Cannot find {label}. Quitting.'
    _printfail(msg)
    # if dump_ui is True:
    #     prefix_with_ts = _get_log_file_prefix()
    #     _dump_ui(device, f'{prefix_with_ts}-error-{label}')
    return


def _maybe_find_wait_exists(device, *, label='it', reps=WAIT_EXISTS, **kwargs):
    sleeper.random_sleep()
    for rep in range(1, reps + 1):
        thing = device.find(**kwargs)
        if thing.exists():
            print(f"FOUND {label}")
            return thing
        print(f"Didn't find {label}... sleeping {rep} of {reps}")
        time.sleep(1)

    print(f"Didn't find {label}... GIVING UP")
    return


def _got_login_landing_page(device):
    _printreport("Waiting for IG landing page")

    # no username remembered
    landing_page_logo_1 = _maybe_find_wait_exists(device, label='landing_page_logo_1', reps=WAIT_FOR_LANDING_PAGE,
                                                  resourceId='com.instagram.android:id/logo')
    if landing_page_logo_1 is not None:
        return True

    # username remembered
    landing_page_logo_2 = _maybe_find_wait_exists(device, label='landing_page_logo_2', reps=WAIT_FOR_LANDING_PAGE,
                                                  resourceId='com.instagram.android:id/login_landing_logo')
    if landing_page_logo_2 is not None:
        return True

    return False


def _a_username_found(device):
    create_new_account_btn = _maybe_find_wait_exists(device, label='create_new_account_btn',
                                                     text='Create New Account')
    if create_new_account_btn is not None:
        return False
    return True


def _correct_username_found(device, login):
    correct_username_1 = _maybe_find_wait_exists(
        device, label='correct_username_1', text=login, resourceId='com.instagram.android:id/login_username')
    if correct_username_1 is not None:
        return True

    correct_username_2 = _maybe_find_wait_exists(
        device, label='correct_username_2', text=login, resourceId='com.instagram.android:id/title')
    if correct_username_2 is not None:
        return True

    return False


def fill_in_password(device, password):
    _printreport("Filling in password ...")
    password_field = _find_wait_exists(device, label='password_field',
                                       resourceId='com.instagram.android:id/password_input_layout')
    _printreport("Filling in password ...")
    password_field.set_text(password)
    sleeper.random_sleep()


def fill_in_username(device, login):
    _printreport("Filling in username ...")
    username_field = _find_wait_exists(device, label='username_field',
                                       text='Phone number, email or username')
    username_field.set_text(login)
    sleeper.random_sleep()


def click_login_if_exists(device):
    log_in_button = _maybe_find_wait_exists(device, label='log_in_button',
                                            textMatches=case_insensitive_re('log in'))
    if log_in_button.exists():
        click_login(device)


def click_login(device):
    _printreport("Click login...")
    log_in_button = _find_wait_exists(device, label='log_in_button',
                                      textMatches=case_insensitive_re('log in'))
    _printreport("Clicking log in button")
    log_in_button.click()
    sleeper.random_sleep()


# There are 4 cases - 1. IG remembers a username and password and logs the user in (theoretically could be correct or wrong user)
#                   - 2. IG remembers the correct username, and populates the username field, but not the password field
#                   - 3. IG remembers the wrong   username, and populates the username field,
#                   - 4. IG does not remember any username, and username field is empty
def login(device, on_action, storage, session_state, action_status, is_limit_reached, login, password, dump_ui):
    # This function will have influence on click, long_click, drag_to, get_text, set_text, clear_text, etc.
    device.deviceV2.implicitly_wait(WAIT_DEFAULT)

    _printok(f"Logging in user {login} password {password}")

    _pause("Check for login screen details")

    if _got_login_landing_page(device) is False:
        _printfail("Never saw landing page - checking if already logged in")
        return _check_logged_in(device, storage, login)

    _pause("Check if username remembered")

    a_username_found = _a_username_found(device)

    if a_username_found is True:
        expect_cookies_confirmation = False
        if _correct_username_found(device, login) is False:
            _printfail(f"Unexpected username instead of '{login}'")
            return False
    else:
        expect_cookies_confirmation = True
        _pause("No username remembered. Need to click 'log in' to access form.")
        click_login(device)
        _pause("Going to fill in username")
        fill_in_username(device, login)

    _pause("Username is filled in. Sometimes there's still a login button.")
    click_login_if_exists(device)

    _pause("Username is filled in. Going to fill in password.")

    fill_in_password(device, password)

    _pause("Password is filled in. Going to click login.")

    click_login(device)

    _pause("Pause for cookies...")

    accept_cookies_if_offered(device, expect_cookies_confirmation)

    _pause("Check if logged in")

    return _check_logged_in(device, storage, login)


def accept_cookies_if_offered(device, expect_cookies_confirmation=False):
    if expect_cookies_confirmation is True:
        reps = max(5, WAIT_EXISTS)
    else:
        reps = WAIT_EXISTS
    # either we get offered to accept cookies, if this is a new account, or not, if
    # we've accepted cookies previously
    cookies_btn = _maybe_find_wait_exists(
        device, label='cookies_btn', reps=reps, textMatches=case_insensitive_re('Allow All Cookies'))
    if cookies_btn is not None:
        _printreport('Accepting cookies')
        cookies_btn.click()
    else:
        _printreport("No cookies button offered")
    sleeper.random_sleep()


# InsomniacSession.run() prepares the session, but we skip populating user stats
# bc we are not logged in. .end_session() stores the current session data (i.e.
# user stats) back into the database. So we need to add the user stats into the session
# if we have successfully logged in, or else they get set back to 0
def _check_logged_in(device, storage, login):
    _printok("Checking if logged in OK")

    # there can be a big delay after login and we miss the cookies modal, then get
    # into a cycle of exception handling, finally reaching the _check_logged_in()
    # call, by which time the cookies modal has been presented, so we need to
    # check for it again
    _printok("But first, checking for cookies modal")
    accept_cookies_if_offered(device, False)

    sleeper.random_sleep()

    try:
        my_username, followers, following, posts = get_my_profile_info(
            device, login)
    except RuntimeError:  # can't access profile page bc not logged in - nb. this catch does not prevent a stacktrace being printed
        _printfail(f"No logged in user")
        return False

    if my_username is not None:
        if my_username == login:
            # Setting these data was skipped in InsomniacSession.prepare_session_state()
            # bc we were not logged in
            # session_state.my_username = my_username
            # session_state.my_followers_count = followers
            # session_state.my_following_count = following
            # session_state.my_posts_count = posts
            storage.log_login(followers, following, posts)
            return True
        else:
            _printfail(f"Wrong logged-in user '{my_username}' != '{login}'")
            return False
    else:
        _printfail(f"Empty logged-in user - expected {login}")  # impossible
        return False
