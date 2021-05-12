from insomniac.views import TabBarView
from insomniac.sleeper import sleeper
from insomniac.utils import *
from insomniac.device_facade import DeviceFacade
import os
import time
# import json
# from pprint import pprint
from random import randrange
from datetime import datetime

# COLOR_OKBLUE
# COLOR_HEADER

WAIT_EXISTS = 5


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


def _dump_ui(device, name='ui', dir='.'):
    time.sleep(2)
    device.dump_hierarchy(f'{dir}/{name}.uix')
    _adb_cmd(device, f"shell screencap -p /sdcard/ui.png")
    _adb_cmd(device, f"pull /sdcard/ui.png {dir}/{name}.png")
    _printbold(f"Dumped UI files {dir}/{name}.png and {dir}/{name}.uix")


def _wait_for(label, device, package, className, resource_id):
    print(f"Waiting for {label}...")
    device.find(resourceId=f'{package}:id/{resource_id}',
                className=className).wait()
    print("   ...OK")


def _wait_exists(thing, label='it'):
    for rep in range(0, WAIT_EXISTS):
        if thing.exists:
            print(f"_wait_exists FOUND {label}")
            return
        print(f"_wait_exists didn't find {label}... sleeping 1")
        time.sleep(1)

    print(f"_wait_exists didn't find {label}... GIVING UP")


def _find_wait_exists(device, dump_ui, label, **kwargs):
    thing = _maybe_find_wait_exists(device, label=label, **kwargs)
    if thing is not None:
        return thing
    _fail(device, dump_ui, label)


def _maybe_find_wait_exists(device, label='it', **kwargs):
    sleeper.random_sleep()
    for _ in range(0, WAIT_EXISTS):
        thing = device.find(**kwargs)
        if thing.exists():
            print(f"_maybe_find_wait_exists FOUND {label}")
            return thing
        print(f"_maybe_find_wait_exists didn't find {label}... sleeping 1")
        time.sleep(1)

    print(f"_maybe_find_wait_exists didn't find {label}... GIVING UP")


def _fail(device, dump_ui, label, msg=None):
    if msg is None:
        msg = f'Cannot find {label}. Quitting.'
    _printfail(msg)
    if dump_ui is True:
        logdir = _get_logs_dir_name()
        prefix_with_ts = _get_log_file_prefix()
        _dump_ui(device, f'{prefix_with_ts}-error-{label}', logdir)
    return


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


def post(device, on_action, storage, session_state, action_status, is_limit_reached, caption, tagnames, location, dump_ui, image_path_on_device):
    _printok("Starting a new post")

    # -----
    print("Get home_view, prepare to post")
    home_view = TabBarView(device).navigate_to_home()
    if home_view is None:
        return _fail(device, dump_ui, 'home_view', "Cannot find home_view")

    # -----
    print("Press \"New Post (+)\" button")
    start_new_post_button = _maybe_find_wait_exists(device,
                                                    resourceId='com.instagram.android:id/action_bar_left_button',
                                                    className='android.widget.ImageView')
    if start_new_post_button is None:
        start_new_post_button_parent = _find_wait_exists(device, dump_ui, 'start_new_post_button_parent',
                                                         resourceId='com.instagram.android:id/tab_bar',
                                                         className='android.widget.LinearLayout')
        if start_new_post_button_parent is None:
            return

        start_new_post_button = start_new_post_button_parent.child(index=2)
        if not start_new_post_button.exists():
            return _fail(device, dump_ui, "start_new_post_button")

    start_new_post_button.click()

    # -----
    print("Press \"Gallery\" dropdown button")
    gallery_popup_button = _find_wait_exists(device, dump_ui, 'gallery_popup_button',
                                             className='android.widget.Spinner',
                                             resourceId='com.instagram.android:id/gallery_folder_menu_alt')
    if gallery_popup_button is None:
        return
    gallery_popup_button.click()

    # -----
    print("Select \"Other...\" option")
    button_other = _find_wait_exists(device, dump_ui, 'button_other',
                                     resourceId='com.instagram.android:id/action_sheet_row_text_view',
                                     className='android.widget.Button',
                                     text='Other…')
    if button_other is None:
        return
    button_other.click()

    # -----
    # on some phones this takes us directly to the Downloads folder, on others it
    # goes to the Recent folder and we need to navigate to Downloads:
    print("Click the hamb. menu")
    recent_label = _maybe_find_wait_exists(device,
                                           className='android.widget.TextView',
                                           text='Recent')

    if recent_label is not None:
        hamburger_menu_parent = _maybe_find_wait_exists(device,
                                                        className='android.view.ViewGroup',
                                                        resourceId='com.android.documentsui:id/toolbar')
        if hamburger_menu_parent is not None:
            hamburger_menu = hamburger_menu_parent.child(index=0)
            _wait_exists(hamburger_menu)
            if not hamburger_menu.exists():
                return _fail(device, dump_ui, "hamburger_menu")
            hamburger_menu.click()

            print("Click the Downloads menu item")
            downloads_menuitem = _find_wait_exists(device, dump_ui, "downloads_menuitem",
                                                   className='android.widget.TextView',
                                                   text='Downloads')
            if downloads_menuitem is None:
                return
            downloads_menuitem.click()

    # -----
    # One way or another, we're in the Downloads folder.
    # We assume there's only one image, or if more, we select the first
    print("Click the image")
    image_parent = _find_wait_exists(device, dump_ui, 'image',
                                     className='android.widget.FrameLayout',
                                     resourceId='com.android.documentsui:id/thumbnail')
    if image_parent is None:
        return
    image = image_parent.child(index=0)
    _wait_exists(image)
    if not image.exists():
        return _fail(device, dump_ui, "image")
    image.click()

    _wait_for('image display', device, 'com.instagram.android',
              'android.widget.ImageView', 'crop_image_view')

    # -----
    print("Click blue arrow to skip cropping")
    blue_arrow = _find_wait_exists(device, dump_ui, 'blue_arrow',
                                   className='android.widget.ImageView',
                                   resourceId='com.instagram.android:id/save')
    if blue_arrow is None:
        return
    blue_arrow.click()

    _wait_for('image display', device, 'com.instagram.android',
              'android.view.View', 'filter_view')

    # -----
    print("Click blue arrow to skip filters")
    blue_arrow2 = _find_wait_exists(device, dump_ui, 'blue_arrow2',
                                    className='android.widget.ImageView',
                                    resourceId='com.instagram.android:id/next_button_imageview')
    if blue_arrow2 is None:
        return
    blue_arrow2.click()

    #
    # We have now reached the details page, where caption, tagnames, and location can be entered
    #

    _wait_for('default locations to populate', device, 'com.instagram.android',
              'android.widget.LinearLayout', 'suggested_locations_container')

    # -----
    if len(caption) > 0:
        print("Typing in the caption")
        caption_editbox = _find_wait_exists(device, dump_ui, "caption_editbox",
                                            className='android.widget.EditText',
                                            resourceId='com.instagram.android:id/caption_text_view')
        if caption_editbox is None:
            return
        caption_editbox.click()
        sleeper.random_sleep()
        caption_editbox.set_text(caption)

        device.close_keyboard()

    else:
        print('No caption provided')

    # if the caption is long we will need to scroll back to the top to see the tagnames button
    # ! this doesn't seem to be working (but not fully tested), but after adding device.close_keyboard() it's not so important,
    # ! we can see the whole screen so it would have to be a huge caption to lose the tagnames button.
    print("Scroll up...")
    # Remember: to scroll up we need to swipe down :)
    for _ in range(3):
        print("  ... swipe down...")
        device.swipe(DeviceFacade.Direction.BOTTOM, scale=0.25)

    # -----
    if len(tagnames) > 1:
        raise ValueError(
            f"Too many tagnames to tag in photo - can only handle 0 or 1")

    if len(tagnames) == 0:
        print("No tagnames to tag in post")

    if len(tagnames) == 1:
        print(f"Tagging {tagnames[0]} in post: click \"Tag People\" button")
        tag_tagnames_button = _find_wait_exists(device, dump_ui, "tag_tagnames_button",
                                                className='android.widget.TextView',
                                                text='Tag People')
        if tag_tagnames_button is None:
            return
        # clicking this button opens the image
        tag_tagnames_button.click()

        _wait_for('image to display', device, 'com.instagram.android',
                  'android.widget.ImageView', 'tag_image_view')

        # we have to click somewhere within the image
        print("Click in image to set user tag")
        taggable_image = _find_wait_exists(device, dump_ui, 'taggable_image',
                                           className='android.widget.ImageView',
                                           resourceId='com.instagram.android:id/tag_image_view')
        if taggable_image is None:
            return

        bounds = taggable_image.get_bounds()
        x, y = _middlish(bounds)
        device.screen_click_by_coordinates(x, y)

        # -----
        print(f"Type username '{tagnames[0]}' into user_searchbox")
        user_searchbox = _find_wait_exists(device, dump_ui, 'user_searchbox',
                                           className='android.widget.EditText',
                                           resourceId='com.instagram.android:id/row_search_edit_text')
        if user_searchbox is None:
            return
        user_searchbox.set_text(tagnames[0])

        device.close_keyboard()

        _wait_for('users search list', device, 'com.instagram.android',
                  'android.widget.ListView', 'list')

        # -----
        print("Selecting the user")
        selected_user_button = _find_wait_exists(device, dump_ui, 'selected_user_button',
                                                 resourceId='com.instagram.android:id/row_search_user_username',
                                                 className='android.widget.TextView',
                                                 text=tagnames[0])
        if selected_user_button is None:
            return
        selected_user_button.click()

        # the user has now been inserted into the image tag
        # click the blue arrow to confirm and return to main post editing page
        blue_arrow3 = _find_wait_exists(device, dump_ui, 'blue_arrow3',
                                        className='android.widget.ViewSwitcher',
                                        resourceId='com.instagram.android:id/action_bar_button_done')
        if blue_arrow3 is None:
            return
        blue_arrow3.click()

    #
    # location
    #

    if len(location) == 0:
        print("No location to add to post")

    if len(location) > 0:
        # -----
        print(f"Adding location to post: {location}")
        add_location_button = _find_wait_exists(device, dump_ui, 'add_location_button',
                                                className='android.widget.TextView',
                                                resourceId='com.instagram.android:id/location_label')
        if add_location_button is None:
            return
        add_location_button.click()

        # -----
        print("Fill in location search box")
        location_sbox = _find_wait_exists(device, dump_ui, 'location_sbox',
                                          className='android.widget.EditText',
                                          resourceId='com.instagram.android:id/row_search_edit_text')
        if location_sbox is None:
            return
        location_sbox.set_text(location)

        device.close_keyboard()

        _wait_for('locations search list', device,
                  'com.instagram.android', 'android.widget.ListView', 'list')

        # -----
        print("Click the selected location button")
        selected_loc = _find_wait_exists(device, dump_ui, 'selected_loc',
                                         resourceId='com.instagram.android:id/row_venue_title',
                                         className='android.widget.TextView',
                                         text=location)
        if selected_loc is None:
            return
        selected_loc.click()

    # -----
    # everything has been completed, click the blue tick to send the post
    _printok("Send post and wait for result")
    blue_tick = _find_wait_exists(device, dump_ui, 'blue_tick',
                                  className='android.widget.ImageView',
                                  resourceId='com.instagram.android:id/next_button_imageview')
    if blue_tick is None:
        return
    blue_tick.click()

    # wait for Instagram to do its thing
    time.sleep(14)

    # -----
    # check the outcome - if we get a post with these characteristics, Instagram has accepted the post
    caption_regex = f'^{session_state.my_username}'
    posted_caption = _maybe_find_wait_exists(device,
                                             resourceId='com.instagram.android:id/row_feed_comment_textview_layout',
                                             className='com.instagram.ui.widget.textview.IgTextLayoutView',
                                             textMatches=caption_regex)

    logdir = _get_logs_dir_name()
    prefix_with_ts = _get_log_file_prefix()

    # ! POSSIBLE ISSUE
    # There are at least 2 ways IG rejects a post, they're both detected correctly here, so far.
    # Rejection mode 1: Ig may show the post, but the caption isn't visible, so not detected, and therefore the rejection IS detected. This might
    # however be a quirk of the device I'm using - maybe if it had a bigger screen,
    # the caption would be visible. In that case the question is whether the caption
    # still appears in the row_feed_comment_textview_layout element.
    # Rejection mode 2: IG pops up a big full-screen warning.
    # _wait_exists(posted_caption)
    # if posted_caption.exists():
    if posted_caption is not None:
        _printok("SUCCESS!")
        if dump_ui is True:
            _dump_ui(device, f'{prefix_with_ts}-final-success', logdir)
        return True
    else:
        _printokblue(
            "UNKNOWN: can't identify successful post yet")
        if dump_ui is True:
            _dump_ui(device, f'{prefix_with_ts}-final-unknown', logdir)
        return True


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
    dl = "/storage/emulated/0/Download"
    dest = f"{dl}/{filename}"
    _printreport(f"Sending {image_path_on_host} to {dest}")

    # push would create the directory if it doesn't exist, and we don't want that
    _adb_cmd(device, f"shell test -d {dl}")

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
            f"Error running '{cmd}: STDOUT: {result.stdout} STDERR: {result.stderr} [{result.returncode}]")
    return result.stdout.strip()
