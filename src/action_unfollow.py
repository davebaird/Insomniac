from src.storage import FollowingStatus
from src.utils import *

#
## added min_following and following_count to unfollow function
def unfollow(device, count, on_unfollow, storage, only_non_followers, my_username, following_count, min_following, unfollow_any):
    _open_my_followings(device)
    _sort_followings_by_date(device)
    ## added min_following and following_count to _iterate_over_followings function
    _iterate_over_followings(device, count, on_unfollow, storage, only_non_followers, my_username, following_count, min_following, unfollow_any)


def _open_my_followings(device):
    print("Open my followings")
    followings_button = device(resourceId='com.instagram.android:id/row_profile_header_following_container',
                               className='android.widget.LinearLayout')
    followings_button.click.wait()


def _sort_followings_by_date(device):
    print("Sort followings by date: from oldest to newest.")
    sort_button = device(resourceId='com.instagram.android:id/sorting_entry_row_icon',
                         className='android.widget.ImageView')

    if not sort_button.exists:
        print(COLOR_FAIL + "Cannot find button to sort followings. Continue without sorting.")
        return

    sort_button.click.wait()
    sort_options_recycler_view = device(resourceId='com.instagram.android:id/follow_list_sorting_options_recycler_view')
    sort_options_recycler_view.child(index=2).click.wait()

## added min_following and following_count to _iterate_over_followings function
def _iterate_over_followings(device, count, on_unfollow, storage, only_non_followers, my_username, following_count, min_following, unfollow_any):
    
    following_deduction = 0
    # If following is = 0 then validate limit
    if min_following > 0:
        if following_count <= min_following:
            print("\033[91mYou currently have a total of ["+ str(following_count) +"] users follorwing, the minimum assigned is ["+ str(min_following) +"], ending session....\033[37m")
            return
        # Calculate how many following we can remove form user
        following_deduction = (following_count - min_following)
        following_total = (following_count - following_deduction)
        print("\033[96mUser Currently has ["+ str(following_count) +"] and would stop unfollowing at ["+ str(following_deduction) +"] unfollows, total user followings after job ["+ str(following_total) +"]\033[37m")
    else:
        print("\033[96mUser Currently has ["+ str(following_count) +"] and it would not stop unfollowing!\033[37m")

    if unfollow_any > 0:
        print("\033[96mUser unfollow_any activated, script will not validate interation with the users followed by the script!\033[37m")



    unfollowed_count = 0
    while True:
        print("Iterate over visible followings")
        screen_iterated_followings = 0

        for item in device(resourceId='com.instagram.android:id/follow_list_container',
                           className='android.widget.LinearLayout'):

            # if we've reach the minimum amount of users following and min_following is more than 0, print message and exit
            if unfollowed_count >= following_deduction and min_following > 0:
                print("\033[96mUnfollow stopped, you have reach the minimum amount of following you could have\033[37m")
                return

            user_info_view = item.child(index=1)
            user_name_view = user_info_view.child(index=0).child()
            if not user_name_view.exists:
                print(COLOR_OKGREEN + "Next item not found: probably reached end of the screen." + COLOR_ENDC)
                break

            username = user_name_view.text
            screen_iterated_followings += 1

            following_status = storage.get_following_status(username)
            if not following_status == FollowingStatus.FOLLOWED and unfollow_any == 0:
                print("Skip @" + username + ". Following status: " + following_status.name + ".")
            elif only_non_followers and _check_is_follower(device, username, my_username):
                print("Skip @" + username + ". This user is following you.")
            else:
                print("Unfollow @" + username)

                unfollow_button = item.child(resourceId='com.instagram.android:id/button',
                                             className='android.widget.TextView')
                if not unfollow_button.exists:
                    print(COLOR_FAIL + "Cannot find unfollow button" + COLOR_ENDC)
                    break
                unfollow_button.click.wait()
                _close_dialog_if_shown(device)
                storage.add_interacted_user(username, unfollowed=True)
                on_unfollow()

                random_sleep()

                unfollowed_count += 1
                if unfollowed_count >= count:
                    return

        if screen_iterated_followings > 0:
            print(COLOR_OKGREEN + "Need to scroll now" + COLOR_ENDC)
            list_view = device(resourceId='android:id/list',
                               className='android.widget.ListView')
            list_view.scroll.toEnd(max_swipes=1)
        else:
            print(COLOR_OKGREEN + "No followings were iterated, finish." + COLOR_ENDC)
            return


def _close_dialog_if_shown(device):
    dialog_root_view = device(resourceId='com.instagram.android:id/dialog_root_view',
                              className='android.widget.FrameLayout')
    if not dialog_root_view.exists:
        return

    print(COLOR_OKGREEN + "Dialog shown, confirm unfollowing." + COLOR_ENDC)
    random_sleep()
    unfollow_button = dialog_root_view.child(index=0).child(resourceId='com.instagram.android:id/primary_button',
                                                            className='android.widget.TextView')
    unfollow_button.click.wait()


def _check_is_follower(device, username, my_username):
    print(COLOR_OKGREEN + "Check if @" + username + " is following you." + COLOR_ENDC)
    username_view = device(resourceId='com.instagram.android:id/follow_list_username',
                           className='android.widget.TextView',
                           text=username)
    if not username_view.exists:
        print(COLOR_FAIL + "Cannot find @" + username + ", skip." + COLOR_ENDC)
        return True
    username_view.click.wait()

    following_container = device(resourceId='com.instagram.android:id/row_profile_header_following_container',
                                 className='android.widget.LinearLayout')
    following_container.click.wait()

    my_username_view = device(resourceId='com.instagram.android:id/follow_list_username',
                              className='android.widget.TextView',
                              text=my_username)
    result = my_username_view.exists
    device.press.back()
    device.press.back()
    return result
