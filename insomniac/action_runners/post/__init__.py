from insomniac.action_runners import *

from insomniac.safely_runner import run_safely
from insomniac.utils import *
from pathlib import Path


class PostActionRunner(CoreActionsRunner):
    ACTION_ID = "post"
    ACTION_ARGS = {
        "post": {
            "help": 'path to image to use for the post'
        },
        "caption": {
            'help': 'Caption for the post',
            'default': None
        },
        "location": {
            "help": 'location to tag the post',
            "default": None
        },
        "tagnames": {
            "nargs": '+',
            "help": 'accounts to tag in the post (with or without @)',
            "default": None
        },
        "dump_ui": {
            "help": 'dump ui files to working dir on fail or on completion',
            "action": 'store_true',
            'default': None
        }
    }

    caption = ''
    location = ''
    tagnames = []
    image_path_on_host = ''
    dump_ui = False

    def is_action_selected(self, args):
        if args.post is not None and len(args.post) > 0:
            if Path(args.post).is_file():
                return True
            else:
                raise FileNotFoundError(
                    "POSTING: file '" + args.post + "' not found on host")
        else:
            print("POSTING: no host file specified")
            return False

    def reset_params(self):
        self.caption = ''
        self.location = ''
        self.tagnames = []
        self.image_path = ''
        self.dump_ui = False

    def set_params(self, args):
        self.reset_params()

        self.image_path_on_host = args.post

        if args.caption is not None:
            self.caption = args.caption

        if args.location is not None:
            self.location = args.location

        if args.tagnames is not None:
            self.tagnames = args.tagnames

        if args.dump_ui is not None:
            self.dump_ui = True

    def run(self, device_wrapper, storage, session_state, on_action, is_limit_reached, is_passed_filters=None):
        from insomniac.action_runners.post.action_post import post, send_image_to_device, clear_image_from_device

        image_path_on_device = send_image_to_device(
            device_wrapper.device, self.image_path_on_host)

        self.action_status = ActionStatus(ActionState.PRE_RUN)

        @run_safely(device_wrapper=device_wrapper)
        def job():
            self.action_status.set(ActionState.RUNNING)
            success = post(device=device_wrapper.get(),
                           on_action=on_action,
                           storage=storage,
                           session_state=session_state,
                           action_status=self.action_status,
                           is_limit_reached=is_limit_reached,
                           caption=self.caption,
                           tagnames=self.tagnames,
                           location=self.location,
                           dump_ui=self.dump_ui,
                           image_path_on_device=image_path_on_device)

            if success is not None:
                print(COLOR_REPORT + "Posted image to " + session_state.my_username + COLOR_ENDC)
                storage.log_post()
            else:
                print(COLOR_REPORT + "Did not post image" + COLOR_ENDC)

            self.action_status.set(ActionState.DONE)
            clear_image_from_device(
                device_wrapper.device, image_path_on_device)

        while not self.action_status.get() == ActionState.DONE:
            job()
