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

WAIT_EXISTS = 1
WAIT_DEFAULT = 10
WAIT_FOR_LANDING_PAGE = 10

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


def _dump_ui(device, name=f"{_get_log_file_prefix()}-ui"):
    time.sleep(2)
    dir = _get_logs_dir_name()
    device.dump_hierarchy(f'{dir}/{name}.uix')
    _sshot(device, '/sdcard/ui.png')
    _adb_cmd(device, ['pull', '/sdcard/ui.png', f'{dir}/{name}.png'])
    _printbold(f"Dumped UI files {dir}/{name}.png and {dir}/{name}.uix")


def _sshot(device, filepath):
    # For screencap command and permissions problems: https://blog.actorsfit.com/a?ID=01600-ecf7c9f0-a06f-4289-b10e-1f9ebf8a3c5d
    # -p: png format

    # this works from the shell but not from here. Relatedly, probably, uiautomatorviewer can't load from the device.
    # _adb_cmd(device, f"shell screencap -p {filepath}")
    _adb_cmd(device, ['shell', 'screencap', '-p', filepath])

    # device.deviceV2.screenshot().save(filepath)
    # _printbold(f"Saved screenshot to {filepath}" % filepath)


def _adb_cmd(device, cmd):
    if type(cmd) is str:
        raise RuntimeError("adb commands must be list, not string")
        # adb_cmd = f"adb {'' if device.device_id is None else ('-s '+ device.device_id)} {cmd}"
        # _printbold(f"Running adb STR command: {adb_cmd}")

    adb_cmd = ['adb']
    if device.device_id is not None:
        adb_cmd.extend(['-s', device.device_id])
    adb_cmd.extend(cmd)
    _printbold(f"Running adb command: {adb_cmd}")
    result = subprocess.run(adb_cmd, stdout=PIPE,
                            stderr=PIPE, shell=False, encoding="utf8")
    pprint.pprint(result)
    if result.returncode != 0:
        raise IOError(
            f"Error running '{adb_cmd}': STDOUT: {result.stdout} STDERR: {result.stderr} [{result.returncode}]")
    return result.stdout.strip()


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


def _find_wait_exists(device, dump_ui, label, **kwargs):
    thing = _maybe_find_wait_exists(device, label=label, **kwargs)
    if thing is not None:
        return thing
    _fail(device, dump_ui, label)


def _fail(device, dump_ui, label, msg=None):
    if msg is None:
        msg = f'Cannot find {label}. Quitting.'
    _printfail(msg)
    if dump_ui is True:
        prefix_with_ts = _get_log_file_prefix()
        _dump_ui(device, f'{prefix_with_ts}-error-{label}')
    return


def _maybe_find_wait_exists(device, *, label='it', reps=WAIT_EXISTS, **kwargs):
    sleeper.random_sleep()
    for _ in range(0, reps):
        thing = device.find(**kwargs)
        if thing.exists():
            print(f"_maybe_find_wait_exists FOUND {label}")
            return thing
        print(f"_maybe_find_wait_exists didn't find {label}... sleeping 1")
        time.sleep(1)

    print(f"_maybe_find_wait_exists didn't find {label}... GIVING UP")
    return


def _got_landing_page(device):
    _printreport("Waiting for IG landing page")
    landing_page_logo = _maybe_find_wait_exists(device, label='landing_page_logo', reps=WAIT_FOR_LANDING_PAGE,
                                                resourceId='com.instagram.android:id/logo')  # com.instagram.android:id/login_landing_logo
    if landing_page_logo is None:
        return False
    return True


def _no_username_found(device):
    create_new_account_btn = _maybe_find_wait_exists(device, label='create_new_account_btn',
                                                     text='Create New Account')
    if create_new_account_btn is not None:
        return True
    return False


def _correct_username_found(device, login, reps=WAIT_EXISTS):
    correct_username = _maybe_find_wait_exists(
        device, label='correct_username', reps=reps, text=login)
    if correct_username is not None:
        return True
    return False


def login(device, on_action, storage, session_state, action_status, is_limit_reached, login, password, dump_ui):
    # This function will have influence on click, long_click, drag_to, get_text, set_text, clear_text, etc.
    device.deviceV2.implicitly_wait(WAIT_DEFAULT)

    _printok(f"Logging in user {login} password {password}")

    # There are 4 cases - 1. IG remembers a username and password and logs the user in (theoretically could be correct or wrong user)
    #                   - 2. IG remembers the correct username, and populates the username field, but not the password field
    #                   - 3. IG remembers the wrong   username, and populates the username field,
    #                   - 4. IG does not remember any username, and username field is empty

    if _got_landing_page(device) is False:
        _printfail("Never saw landing page - checking if already logged in")
        return _check_logged_in(device, login)

    remembers_correct_username = _correct_username_found(device, login)
    remembers_no_username = _no_username_found(device)

    if remembers_no_username is False and remembers_correct_username is False:
        _printfail(f"IG remembers unexpected username instead of '{login}'")
        return False

    # there's a log in button in all remaining scenarios
    log_in_button = _find_wait_exists(device, dump_ui, label='log_in_button',
                                      textMatches=case_insensitive_re('log in'))
    _printreport("Clicking log in button")
    log_in_button.click()

    sleeper.random_sleep()

    # IG does not remember any username
    if remembers_no_username is True:
        _printreport("Filling in username ...")
        username_field = _find_wait_exists(device, dump_ui, label='username_field',
                                           text='Phone number, email or username')
        username_field.set_text(login)

    password_field = _maybe_find_wait_exists(device, label='password_field',
                                             resourceId='com.instagram.android:id/password_input_layout')
    if password_field is not None:
        _printreport("Filling in password ...")
        password_field.set_text(password)

        sleeper.random_sleep()

        _printreport("Clicking log in button again")
        log_in_button2 = _find_wait_exists(device, dump_ui, label='log_in_button2',
                                           textMatches=case_insensitive_re('log in'))
        log_in_button2.click()
    else:
        pass  # IG has already logged us in with saved credentials

    _accept_cookies_if_offered(device, 5)

    # _stop_here()

    sleeper.random_sleep()

    return _check_logged_in(device, login)

# _check_logged_in() can take a long time to proceed through Insomniac's various tries but seems quite reliable


def _stop_here():
    _printreport("Stopping - ctrl-C to quit")
    time.sleep(99999)


def _accept_cookies_if_offered(device, reps=WAIT_EXISTS):
    # either we get offered to accept cookies, if this is a new account, or not, if
    # we've accepted cookies previously
    cookies_btn = _maybe_find_wait_exists(
        device, label='cookies_btn', reps=reps, textMatches=case_insensitive_re('Allow All Cookies'))
    if cookies_btn is not None:
        _printreport('Accepting cookies')
        cookies_btn.click()
    else:
        _printreport("No cookies button offered")


def _check_logged_in(device, login):
    _printok("Checking if logged in OK")

    # there can be a big delay after login and we miss the cookies modal, then get
    # into a cycle of exception handling, finally reaching the _check_logged_in()
    # call, by which time the cookies modal has been presented, so we need to
    # check for it first
    _printok("But first, checking for cookies modal")
    _accept_cookies_if_offered(device)

    sleeper.random_sleep()

    try:
        # doing it like this is an ugly hack but it works
        my_username = get_my_profile_info(device, login)[0]
    except RuntimeError:  # can't access profile page bc not logged in - nb. this catch does not prevent a stacktrace being printed
        _printfail(f"No logged in user")
        return False

    if my_username is not None:
        if my_username == login:
            return True
        else:
            _printfail(f"Wrong logged-in user '{my_username}' != '{login}'")
            return False
    else:
        _printfail(f"Empty logged-in user - expected {login}")  # impossible
        return False
