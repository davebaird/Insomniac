from insomniac.views import TabBarView, case_insensitive_re
from insomniac.sleeper import sleeper
from insomniac.utils import *
from insomniac.device_facade import DeviceFacade
from insomniac.action_get_my_profile_info import get_my_profile_info
import os
import time
# import json
# from pprint import pprint
from random import randrange
from datetime import datetime
from pathlib import Path

# COLOR_OKBLUE
# COLOR_HEADER

# For selecting page elements, see docs here under heading "Selector":
#   https://github.com/openatx/uiautomator2

WAIT_EXISTS = 1


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


def _wait_for(label, device, package, className, resource_id):
    print(f"Waiting for {label}...")
    device.find(resourceId=f'{package}:id/{resource_id}',
                className=className).wait()
    print("   ...OK")


def _find_wait_exists(device, label, **kwargs):
    thing = _maybe_find_wait_exists(device, label=label, **kwargs)
    if thing is not None:
        return thing
    _fail(device, label)


def _maybe_find_wait_exists(device, *, label='it', skip_perms_check=False, reps=WAIT_EXISTS, **kwargs):
    for rep in range(1, reps + 1):
        _accept_perms_if_asked(device, skip_perms_check)
        thing = device.find(**kwargs)
        if thing.exists():
            print(f"FOUND {label}")
            return thing
        print(f"Didn't find {label}... retry")

    print(f"Didn't find {label}... GIVING UP")
    return


def _accept_perms_if_asked(device, skip_perms_check=False):
    if skip_perms_check is False:
        sleeper.random_sleep()
        perms_btn = _maybe_find_wait_exists(
            device, label='perms_btn', skip_perms_check=True, resourceId="com.android.permissioncontroller:id/permission_allow_button")
        if perms_btn is not None:
            _printreport('Accepting permissions request')
            perms_btn.click()
            sleeper.random_sleep()


def _detect_login_screen(device):
    # lifted verbatim from action_login._got_login_landing_page()

    # no username remembered
    landing_page_logo_1 = _maybe_find_wait_exists(
        device, label='landing_page_logo_1', resourceId='com.instagram.android:id/logo')
    if landing_page_logo_1 is not None:
        return True

    # username remembered
    landing_page_logo_2 = _maybe_find_wait_exists(
        device, label='landing_page_logo_2', resourceId='com.instagram.android:id/login_landing_logo')
    if landing_page_logo_2 is not None:
        return True

    return False


def _fail(device, label, msg=None):
    if msg is None:
        msg = f'Cannot find {label}. Quitting.'
    _printfail(msg)
    return


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


# def start_post_orig(device):
#     _printok("Starting a new post")

#     _pause("Navigate to home")

#     print("Get home_view, prepare to post")
#     TabBarView(device).navigate_to_home()

#     _pause("Looking for initial post button")

#     # button version 1
#     post_button = _maybe_find_wait_exists(device, label='post_button_alt.1',
#                                           resourceId='com.instagram.android:id/action_bar_left_button',
#                                           className='android.widget.ImageView',
#                                           description='Camera')

#     if post_button is not None:
#         post_button.click()
#         return True

#     # OK, that was the easy one, but we didn't find it

#     # button version 2
#     # sometimes the button starts out as a camera button, we need to click it then come
#     # back, it will then have changed to the post button
#     post_button = _maybe_find_wait_exists(device, label='post_button_alt.2.1',
#                                           resourceId='com.instagram.android:id/action_bar_left_button',
#                                           className='android.widget.Button',
#                                           description='Camera')

#     if post_button is not None:
#         # go to the camera, then come back
#         post_button.click()
#         sleeper.random_sleep()
#         device.back()

#         # find the same button, but now it doesn't go to camera, it goes to start post (FFS)
#         post_button2 = _find_wait_exists(device, 'post_button_alt.2.2',
#                                          resourceId='com.instagram.android:id/action_bar_left_button',
#                                          className='android.widget.Button',
#                                          description='Camera')
#         post_button2.click()
#         return True

#     # button version 3
#     # this thing appeared on boutique.hotels.bcn, same thing, the button starts out as a camera button,
#     # we need to click it then come back, it will then have changed to the post button
#     post_button = _find_wait_exists(device, 'post_button_alt.3.1',
#                                     resourceId='com.instagram.android:id/creation_tab',
#                                     className='android.widget.FrameLayout',
#                                     description='Camera')

#     if post_button is not None:
#         # go to the camera, then come back
#         post_button.click()
#         sleeper.random_sleep()
#         device.back()

#         # find the same button, but now it doesn't go to camera, it goes to start post (FFS)
#         post_button2 = _find_wait_exists(device, 'post_button_alt.3.2',
#                                          resourceId='com.instagram.android:id/creation_tab',
#                                          className='android.widget.FrameLayout',
#                                          description='Camera')
#         post_button2.click()
#         return True

#     else:
#         # give up
#         return False


def start_post(device):
    _printok("Starting a new post")

    # Any navigate_to_* call will choke if the login screen has been presented,
    # so this check must come before navigate_to_home()
    # This call will also clear any perms modals presented at the start of a session.
    if _detect_login_screen(device) is True:
        _printfail("Login screen detected - aborting")
        return False

    _pause("Navigate to home")

    print("Get home_view, prepare to post")
    TabBarView(device).navigate_to_home()

    _pause("Looking for initial post button")

    # button version 1
    post_button = _find_wait_exists(
        device, 'post_button_1', description='Camera')

    if post_button is None:
        _printfail("Couldn't find post button - giving up")
        return False

    _pause("Click post button for 1st time...")

    # Most post buttons when first clicked, activate the camera. For those, we
    # need to click, go back, and click again. This sequence should also work
    # on post buttons that go directly to post initialisation. They all seem
    # to be identified by the same description ('Camera').
    post_button.click()
    sleeper.random_sleep()
    device.back()

    _pause("Click post button for 2nd time...")

    # find the same button, but now it doesn't go to camera, it goes to start post (FFS)
    post_button2 = _find_wait_exists(
        device, 'post_button_2', description='Camera')
    post_button2.click()
    sleeper.random_sleep()
    return True


def select_image(device):
    print("Press \"Gallery\" dropdown button")
    gallery_popup_button = _find_wait_exists(device, 'gallery_popup_button_alt',
                                             className='android.widget.Spinner',
                                             resourceIdMatches=case_insensitive_re(f"{device.app_id}:id/gallery_folder_menu(?:_alt)?$"))

    if gallery_popup_button is None:
        return False

    gallery_popup_button.click()

    # -----
    print("Select \"Other...\" option")
    button_other = _find_wait_exists(device, 'button_other',
                                     resourceId='com.instagram.android:id/action_sheet_row_text_view',
                                     className='android.widget.Button',
                                     text='Other…')
    if button_other is None:
        return False

    button_other.click()

    # -----
    # on some phones this takes us directly to the Downloads folder, on others it
    # goes to the Recent folder and we need to navigate to Downloads:
    print("Click the hamb. menu")
    recent_label = _maybe_find_wait_exists(device, label='recent_label', reps=2,
                                           className='android.widget.TextView',
                                           text='Recent')

    if recent_label is not None:
        hamburger_menu_parent = _maybe_find_wait_exists(device, label='hamburger_menu_parent',
                                                        className='android.view.ViewGroup',
                                                        resourceIdMatches=case_insensitive_re('com.(?:google\.)?android.documentsui:id/toolbar'))

        if hamburger_menu_parent is not None:
            hamburger_menu = hamburger_menu_parent.child(index=0)
            hamburger_menu.click()

            print("Click the Downloads menu item")
            downloads_menuitem = _find_wait_exists(device, "downloads_menuitem",
                                                   className='android.widget.TextView',
                                                   text='Downloads')
            if downloads_menuitem is None:
                return False
            downloads_menuitem.click()

    # -----
    # One way or another, we're in the Downloads folder.
    # We assume there's only one image, or if more, we select the first
    print("Click the image")
    image_parent = _find_wait_exists(device, 'image',
                                     className='android.widget.FrameLayout',
                                     resourceId='com.android.documentsui:id/thumbnail')

    if image_parent is None:
        image_parent = _find_wait_exists(device, 'image',
                                         className='android.widget.FrameLayout',
                                         resourceId='com.google.android.documentsui:id/thumbnail')

    if image_parent is None:
        return False
    image = image_parent.child(index=0)
    image.click()

    _wait_for('image display', device, 'com.instagram.android',
              'android.widget.ImageView', 'crop_image_view')

    return True


def accept_image(device):
    print("Click blue arrow to skip cropping")
    blue_arrow = _find_wait_exists(device, 'blue_arrow',
                                   className='android.widget.ImageView',
                                   resourceId='com.instagram.android:id/save')
    if blue_arrow is None:
        return False
    blue_arrow.click()

    _wait_for('image display', device, 'com.instagram.android',
              'android.view.View', 'filter_view')

    print("Click blue arrow to skip filters")
    blue_arrow2 = _find_wait_exists(device, 'blue_arrow2',
                                    className='android.widget.ImageView',
                                    resourceId='com.instagram.android:id/next_button_imageview')
    if blue_arrow2 is None:
        return False
    blue_arrow2.click()

    return True


def add_caption(device, caption):
    if len(caption) > 0:
        print("Typing in the caption")
        caption_editbox = _find_wait_exists(device, "caption_editbox",
                                            className='android.widget.EditText',
                                            resourceId='com.instagram.android:id/caption_text_view')
        if caption_editbox is None:
            return False

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

    return True


def add_tags(device, tagnames):
    print("Adding tagnames:")
    print(tagnames)

    if len(tagnames) > 1:
        raise ValueError(
            f"Too many tagnames to tag in photo - can only handle 0 or 1")

    if len(tagnames) == 0:
        print("No tagnames to tag in post")
        return True

    if len(tagnames) == 1:
        device.close_keyboard()
        time.sleep(2)

        print(f"Tagging {tagnames[0]} in post: click \"Tag People\" button")
        tag_tagnames_button = _find_wait_exists(device, "tag_tagnames_button",
                                                className='android.widget.TextView',
                                                text='Tag People')
        if tag_tagnames_button is None:
            return False
        # clicking this button opens the image
        tag_tagnames_button.click()

        _wait_for('image to display', device, 'com.instagram.android',
                  'android.widget.ImageView', 'tag_image_view')

        # we have to click somewhere within the image
        print("Click in image to set user tag")
        taggable_image = _find_wait_exists(device, 'taggable_image',
                                           className='android.widget.ImageView',
                                           resourceId='com.instagram.android:id/tag_image_view')
        if taggable_image is None:
            return False

        bounds = taggable_image.get_bounds()
        x, y = _middlish(bounds)
        device.screen_click_by_coordinates(x, y)

        # -----
        print(f"Type username '{tagnames[0]}' into user_searchbox")
        user_searchbox = _find_wait_exists(device, 'user_searchbox',
                                           className='android.widget.EditText',
                                           resourceId='com.instagram.android:id/row_search_edit_text')
        if user_searchbox is None:
            return False
        user_searchbox.set_text(tagnames[0])

        device.close_keyboard()

        _wait_for('users search list', device, 'com.instagram.android',
                  'android.widget.ListView', 'list')

        # -----
        print("Selecting the user")
        selected_user_button = _find_wait_exists(device, 'selected_user_button',
                                                 resourceId='com.instagram.android:id/row_search_user_username',
                                                 className='android.widget.TextView',
                                                 text=tagnames[0])

        if selected_user_button is None:
            print(
                f"No selected_user_button for '{tagnames[0]}' yet - will wait one more time for it")
            selected_user_button = _find_wait_exists(device, 'selected_user_button',
                                                     resourceId='com.instagram.android:id/row_search_user_username',
                                                     className='android.widget.TextView',
                                                     text=tagnames[0])

        if selected_user_button is None:
            return False
        selected_user_button.click()

        # the user has now been inserted into the image tag
        # click the blue arrow to confirm and return to main post editing page
        blue_arrow3 = _maybe_find_wait_exists(device, label='blue_arrow3.1',
                                              className='android.widget.Button',
                                              resourceId='com.instagram.android:id/action_bar_button_done',
                                              description='Done')

        if blue_arrow3 is None:
            blue_arrow3 = _maybe_find_wait_exists(device, label='blue_arrow3.2',
                                                  className='android.widget.ViewSwitcher',
                                                  resourceId='com.instagram.android:id/action_bar_button_done')

        if blue_arrow3 is None:
            blue_arrow3 = _find_wait_exists(device, 'blue_arrow3.3',
                                            className='android.widget.ImageView',
                                            resourceId='com.instagram.android:id/next_button_imageview',
                                            description='Next'
                                            )

        if blue_arrow3 is None:
            return False

        blue_arrow3.click()

        return True


def add_location(device, location):
    if len(location) == 0:
        print("No location to add to post")

    if len(location) > 0:
        # -----
        print(f"Adding location to post: {location}")
        add_location_button = _find_wait_exists(device, 'add_location_button',
                                                className='android.widget.TextView',
                                                resourceId='com.instagram.android:id/location_label')
        if add_location_button is None:
            return False
        add_location_button.click()

        # -----
        print("Fill in location search box")
        location_sbox = _find_wait_exists(device, 'location_sbox',
                                          className='android.widget.EditText',
                                          resourceId='com.instagram.android:id/row_search_edit_text')
        if location_sbox is None:
            return False
        location_sbox.set_text(location)

        device.close_keyboard()

        _wait_for('locations search list', device,
                  'com.instagram.android', 'android.widget.ListView', 'list')

        # -----
        print("Click the selected location button")
        selected_loc = _find_wait_exists(device, 'selected_loc',
                                         resourceId='com.instagram.android:id/row_venue_title',
                                         className='android.widget.TextView',
                                         text=location)
        if selected_loc is None:
            return False
        selected_loc.click()

    return True


def do_post(device):
    _printok("Send post and wait for result")
    blue_tick = _find_wait_exists(device, 'blue_tick',
                                  className='android.widget.ImageView',
                                  resourceId='com.instagram.android:id/next_button_imageview')
    if blue_tick is None:
        return False

    blue_tick.click()

    # wait for Instagram to do its thing

    # if we started from the profile view
    time.sleep(5)
    # TabBarView(device).navigate_to_home()
    time.sleep(9)

    return True


def check_posted(device, session_state):
    posts_count_before = session_state.my_posts_count

    # This updates the data in the session. When post() returns, the database is
    # also updated with the new posts count.
    session_state.my_username, \
        session_state.my_followers_count, \
        session_state.my_following_count, \
        session_state.my_posts_count = get_my_profile_info(
            device, session_state.my_username)

    posts_count_after = session_state.my_posts_count

    if posts_count_after > posts_count_before:
        _printok("SUCCESS!")
        return True
    else:
        _printfail("FAIL: posts count did not increase")
        return False


# def check_posted(device, session_state):
#     # print("Scroll up...")
#     # # Remember: to scroll up we need to swipe down :)
#     # for _ in range(3):
#     #     print("  ... swipe down...")
#     #     device.swipe(DeviceFacade.Direction.BOTTOM, scale=0.25)

#     # -----
#     # check the outcome - if we get a post with these characteristics, Instagram has accepted the post
#     caption_regex = f'^{session_state.my_username}'
#     # posted_caption = _find_wait_exists(device, 'posted_caption',
#     #                                    resourceId='com.instagram.android:id/row_feed_comment_textview_layout',
#     #                                    className='com.instagram.ui.widget.textview.IgTextLayoutView',
#     #                                    textMatches=caption_regex)
#     posted_caption = _maybe_find_wait_exists(device, label='posted_caption',
#                                              resourceId='com.instagram.android:id/row_feed_comment_textview_layout',
#                                              className='com.instagram.ui.widget.textview.IgTextLayoutView',
#                                              textMatches=caption_regex)

#     logdir = _get_logs_dir_name()
#     prefix_with_ts = _get_log_file_prefix()

#     # ! POSSIBLE ISSUE
#     # There are at least 2 ways IG rejects a post, they're both detected correctly here, so far.
#     # Rejection mode 1: Ig may show the post, but the caption isn't visible, so not detected, and therefore the rejection IS detected. This might
#     # however be a quirk of the device I'm using - maybe if it had a bigger screen,
#     # the caption would be visible. In that case the question is whether the caption
#     # still appears in the row_feed_comment_textview_layout element.
#     # Rejection mode 2: IG pops up a big full-screen warning.
#     # _wait_exists(posted_caption)
#     # if posted_caption.exists():
#     if posted_caption is not None:
#         _printok("SUCCESS!")
#         if dump_ui is True:
#             _dump_ui(device, f'{prefix_with_ts}-final-success', logdir)
#         return True
#     else:
#         _printokblue(
#             "UNKNOWN: can't identify successful post yet")
#         if dump_ui is True:
#             _dump_ui(device, f'{prefix_with_ts}-final-unknown', logdir)
#         return True


# def _debug_end():
#     _printokblue("DEBUG HALT")
#     time.sleep(10)


def post(device, on_action, storage, session_state, action_status, is_limit_reached, caption, tagnames, location, image_path_on_device):

    # This function will have influence on click, long_click, drag_to, get_text, set_text, clear_text, etc.
    device.deviceV2.implicitly_wait(10)

    _pause("Going to start post")

    if start_post(device) is False:
        return False

    if select_image(device) is False:
        return False

    if accept_image(device) is False:
        return False

    #
    # We have now reached the details page, where caption, tagnames, and location can be entered
    #

    _wait_for('default locations to populate', device, 'com.instagram.android',
              'android.widget.LinearLayout', 'suggested_locations_container')

    if add_caption(device, caption) is False:
        return False

    if add_tags(device, tagnames) is False:
        return False

    if add_location(device, location) is False:
        return False

    if do_post(device) is False:
        return False

    return check_posted(device, session_state)


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
