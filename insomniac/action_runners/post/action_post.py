# from insomniac.actions_impl import open_new_post
from insomniac.views import TabBarView
from insomniac.sleeper import sleeper
from insomniac.utils import *
import os, time
# import json
# from pprint import pprint
from random import randrange
from datetime import datetime

# COLOR_OKBLUE
# COLOR_HEADER

def _printfail(msg):
    print(COLOR_FAIL + msg + COLOR_ENDC)

# to debug something triggering this call, replace the _fail() call with _printfail() and add a _dump_ui() after
def _fail(msg):
    _printfail(msg)
    return

def _printok(msg):
    print(COLOR_OKGREEN + msg + COLOR_ENDC)

def _printreport(msg):
    print(COLOR_REPORT + msg + COLOR_ENDC)

def _printbold(msg):
    print(COLOR_BOLD + msg + COLOR_ENDC)

def _dump_ui(device, name=None, dir=None):
    time.sleep(5)
    if name is None:
        name = 'ui'
    if dir is None:
        dir = '.'
    device.dump_hierarchy(f'{dir}/{name}.uix')
    # adb shell screencap -p /sdcard/screencap.png && adb pull /sdcard/screencap.png
    _adb_cmd(device, f"shell screencap -p /sdcard/ui.png")
    _adb_cmd(device, f"pull /sdcard/ui.png {dir}/{name}.png")
    _printbold(f"Dumped UI files {dir}/{name}.png and {dir}/{name}.uix")

def _find(device, package, className, resource_id):
    sleeper.random_sleep()
    return device.find(resourceId=f'{package}:id/{resource_id}', className=className)

def _wait_for(label, device, package, className, resource_id):
    print(f"Waiting for {label}...")
    device.find(resourceId=f'{package}:id/{resource_id}', className=className).wait()
    print("   ...OK")

# copied from utils.py
def _get_logs_dir_name():
    if globals.is_ui_process:
        return UI_LOGS_DIR_NAME
    return ENGINE_LOGS_DIR_NAME

# Adapted from utils.py _get_log_file_name()
# Using this so the logfile and ui files sort together in directory listing
def _get_log_file_prefix():
    curr_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_prefix = f"insomniac_log-{curr_time}{'-'+globals.execution_id if globals.execution_id != '' else ''}"
    return log_prefix

def _middlish(bounds):
    left = bounds["left"]
    top = bounds["top"]
    right = bounds["right"]
    bottom = bounds["bottom"]
    width = right - left
    height = bottom - top
    centre_x = left + width / 2
    centre_y = top + height / 2
    min_x = round(centre_x - width / 4)
    max_x = round(centre_x + width / 4)
    min_y = round(centre_y - height / 4)
    max_y = round(centre_y + height / 4)
    x = randrange(min_x, max_x)
    y = randrange(min_y, max_y)
    return x, y



def post(device, on_action, storage, session_state, action_status, is_limit_reached, caption, people, location, image_path_on_device):
    _printok("Starting a new post")

    # if not open_new_post(device=device, username=None, on_action=on_action):
    #     return
    # sleeper.random_sleep()
    home_view = TabBarView(device).navigate_to_home()
    if home_view is None:
        return _fail("Cannot find home_view")

    print("Got home_view, ready to post")

    start_new_post_button = _find(
        device, 'com.instagram.android', 'android.widget.ImageView', 'action_bar_left_button')
    if not start_new_post_button.exists():
        return _fail("Cannot find start_new_post_button. Quitting.")

    print("Press \"New Post (+)\" button")
    start_new_post_button.click()

    gallery_popup_button = _find(
        device, 'com.instagram.android', 'android.widget.Spinner', 'gallery_folder_menu_alt')
    if not gallery_popup_button.exists():
        return _fail("Cannot find gallery_popup_button. Quitting.")

    print("Press \"Gallery\" dropdown button")
    gallery_popup_button.click()

    # select 'Other' from the gallery popup
    button_other = _find(device, 'com.instagram.android',
                            'androidx.recyclerview.widget.RecyclerView', 'recycler_view').child(index=3)
    if not button_other.exists():
        return _fail("Cannot find button_other. Quitting.")

    print("Select \"Other...\" option")
    button_other.click()

    # we assume there's only one image, or if more, we select the first
    image = _find(device, 'com.android.documentsui',
                    'android.widget.FrameLayout', 'thumbnail').child(index=0)
    if not image.exists():
        return _fail("Cannot find image. Quitting.")

    print("Click the image")
    image.click()

    _wait_for('image display', device, 'com.instagram.android', 'android.widget.ImageView', 'crop_image_view')

    blue_arrow = _find(device, 'com.instagram.android',
                        'android.widget.ImageView', 'save')
    if not blue_arrow.exists():
        return _fail("Cannot find blue_arrow. Quitting.")

    print("Click blue arrow to skip cropping")
    blue_arrow.click()

    _wait_for('image display', device, 'com.instagram.android', 'android.view.View', 'filter_view')

    sleeper.random_sleep()
    blue_arrow2 = _find(device, 'com.instagram.android',
                        'android.widget.ImageView', 'next_button_imageview')
    if not blue_arrow2.exists():
        return _fail("Cannot find blue_arrow2. Quitting.")

    print("Click blue arrow to skip filters")
    blue_arrow2.click()

    #
    # We have now reached the details page, where caption, people, and location can be entered
    #

    _wait_for('default locations to populate', device, 'com.instagram.android', 'android.widget.LinearLayout', 'suggested_locations_container')

    if len(caption) > 0:
        caption_editbox = _find(
            device, 'com.instagram.android', 'android.widget.EditText', 'caption_text_view')
        if not caption_editbox.exists():
            return _fail("Cannot find caption_editbox. Quitting.")

        print("Typing in the caption")
        caption_editbox.click()
        sleeper.random_sleep()
        caption_editbox.set_text(caption)
    else:
        print('No caption provided')

    if len(people) > 1:
        raise ValueError(
            f"Too many people to tag in photo - can only handle 0 or 1")

    if len(people) == 1:
        print("Tagging person in post: " + people[0])
        tag_people_button = device.find(
            className='android.widget.TextView', text='Tag People')
        if not tag_people_button.exists():
            return _fail("Cannot find tag_people_button. Quitting.")

        # clicking this button opens the image
        print("Click \"Tag People\" button")
        tag_people_button.click()

        _wait_for('image to display', device, 'com.instagram.android', 'android.widget.ImageView', 'tag_image_view')

        # we have to click somewhere within the image
        print("Click in image to set user tag")
        taggable_image = _find(
            device, 'com.instagram.android', 'android.widget.ImageView', 'tag_image_view')
        if not taggable_image.exists():
            return _fail("Cannot find taggable_image. Quitting.")

        bounds = taggable_image.get_bounds()
        x, y = _middlish(bounds)
        device.screen_click_by_coordinates(x, y)

        user_searchbox = _find(
            device, 'com.instagram.android', 'android.widget.EditText', 'row_search_edit_text')
        if not user_searchbox.exists():
            return _fail("Cannot find user_searchbox. Quitting.")

        # # let's just go ahead and type
        print("Type username '" + people[0] + "' into user_searchbox")
        user_searchbox.set_text(people[0])

        _wait_for('users search list', device, 'com.instagram.android', 'android.widget.ListView', 'list')

        # select the first user
        selected_user_button = device.find(
            resourceId='com.instagram.android:id/row_search_user_username', className='android.widget.TextView', text=people[0])
        if not selected_user_button.exists():
            return _fail("Cannot find selected_user_button. Quitting.")

        selected_user_button.click()

        # the user has now been inserted into the image tag
        # click the blue arrow to confirm and return to main post editing page
        blue_arrow3 = _find(device, 'com.instagram.android',
                            'android.widget.ViewSwitcher', 'action_bar_button_done')
        if not blue_arrow3.exists():
            return _fail("Cannot find blue_arrow3. Quitting.")

        blue_arrow3.click()

    if len(people) == 0:
        print("No people to tag in post")

    #
    # location
    #

    if len(location) == 0:
        print("No location to add to post")

    if len(location) > 0:
        print("Adding location to post: " + location)
        add_location_button = _find(
            device, 'com.instagram.android', 'android.widget.TextView', 'location_label')
        if not add_location_button.exists():
            return _fail("Cannot find add_location_button. Quitting.")

        add_location_button.click()

        print("Fill in location search box")
        location_sbox = _find(device, 'com.instagram.android',
                                'android.widget.EditText', 'row_search_edit_text')
        if not location_sbox.exists():
            return _fail("Cannot find location_sbox. Quitting.")

        location_sbox.set_text(location)

        _wait_for('locations search list', device, 'com.instagram.android', 'android.widget.ListView', 'list')

        # select the first location in the results
        selected_loc = device.find(resourceId='com.instagram.android:id/row_venue_title',
                                    className='android.widget.TextView', text=location)
        if not selected_loc.exists():
            return _fail("Cannot find selected_loc. Quitting.")

        print("Click the selected location button")
        selected_loc.click()

    #
    # everything has been completed, click the blue tick to send the post
    blue_tick = _find(device, 'com.instagram.android',
                        'android.widget.ImageView', 'next_button_imageview')
    # blue_tick = _find(device, 'com.instagram.android', 'android.widget.ViewSwitcher', 'action_bar').child(index=0).child(index=2)
    if not blue_tick.exists():
        return _fail("Cannot find blue_tick. Quitting.")

    blue_tick.click()
    _printok("Post sent - waiting for result")
    prefix_with_ts = _get_log_file_prefix()

    # wait for Instagram to do its thing
    time.sleep(20)

    # check the outcome - if we get a post with these characteristics, Instagram has accepted the post
    caption_regex = f'^{session_state.my_username}'
    posted_caption = device.find(resourceId='com.instagram.android:id/row_feed_comment_textview_layout',
                                    className='com.instagram.ui.widget.textview.IgTextLayoutView',
                                    textMatches=caption_regex)

    logdir = _get_logs_dir_name()

    # ! POSSIBLE ISSUE
    # There are at least 2 ways IG rejects a post, they're both detected correctly here, so far.
    # Rejection mode 1: Ig may show the post, but the caption isn't visible, so not detected, and therefore the rejection IS detected. This might
    # however be a quirk of the device I'm using - maybe if it had a bigger screen,
    # the caption would be visible. In that case the question is whether the caption
    # still appears in the row_feed_comment_textview_layout element.
    # Rejection mode 2: IG pops up a big full-screen warning.
    if posted_caption.exists():
        _printok("SUCCESS!")
        _dump_ui(device, f'{prefix_with_ts}-final-success', logdir)
        return True
    else:
        _printfail(
            "FAILED: can't find expected post - check for possible SOFTBAN")
        _dump_ui(device, f'{prefix_with_ts}-final-fail', logdir)
        return


# Note: uiautomator2 (accessible via device_wrapper.device.deviceV2) works by installing
# a server on the device (atx-agent) and sending commands via http requests. This screws
# with file ownership and perms, so using adb directly here.
    # ret = device_wrapper.device.deviceV2.push(image_path_on_host, dest)
    # pprint(ret)
    # sr = device_wrapper.device.deviceV2.shell(["chmod", "0666", dest])
    # pprint(sr)
    # shell_response = device_wrapper.device.deviceV2.shell(["ls", "-l", dest])
    # pprint(shell_response)
def send_image_to_device(device, image_path_on_host):
    filename = os.path.basename(image_path_on_host)
    dest = "/storage/emulated/0/Download/" + filename
    _printreport("Sending " + image_path_on_host + " to " + dest)
    _adb_cmd(device, f"push {image_path_on_host} {dest}")
    _adb_cmd(device, f"shell test -f {dest}")
    return dest


def clear_image_from_device(device, dest):
    _adb_cmd(device, f"shell rm {dest}")
    _adb_cmd(device, f"shell ! test -f {dest}")
    _printreport("Deleted " + dest)


def _adb_cmd(device, cmd):
    adb_cmd = f"adb {'' if device.device_id is None else ('-s '+ device.device_id)} {cmd}"
    result = subprocess.run(adb_cmd, stdout=PIPE,
                            stderr=PIPE, shell=True, encoding="utf8")
    # pprint(result)
    if result.returncode != 0:
        raise IOError(
            f"Error running '{cmd}: {result.stderr} [{result.returncode}]")
    return result.stdout.strip()
