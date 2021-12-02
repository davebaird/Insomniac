from insomniac.action_runners import *

from insomniac.safely_runner import run_safely
from insomniac.utils import *
from pathlib import Path


class LoginActionRunner(CoreActionsRunner):
    ACTION_ID = "login"
    ACTION_ARGS = {
        "login": {
            "help": 'Instagram username'
        },
        "password": {
            'help': 'Password',
            'default': None
        },
        "dump_ui": {
            "help": 'dump ui files to working dir on fail or on completion',
            "action": 'store_true',
            'default': None
        }
    }

    login = ''
    password = ''
    dump_ui = False

    def is_action_selected(self, args):
        if args.login is not None and len(args.login) > 0:
            if args.password is not None and len(args.password) > 0:
                return True
            else:
                raise FileNotFoundError("LOGIN: password required '")
        else:
            print("LOGIN: login (username) is required")
            return False

    def reset_params(self):
        self.login = ''
        self.password = ''
        self.dump_ui = False

    def set_params(self, args):
        self.reset_params()

        self.login = args.login

        self.password = args.password

        if args.dump_ui is not None:
            self.dump_ui = True

    def run(self, device_wrapper, storage, session_state, on_action, is_limit_reached, is_passed_filters=None):
        from insomniac.action_runners.login.action_login import login

        self.action_status = ActionStatus(ActionState.PRE_RUN)

        @run_safely(device_wrapper=device_wrapper)
        def job():
            self.action_status.set(ActionState.RUNNING)
            # indicate that success was never returned, due to exception handling -
            session_state.exit_code = 7
            success = login(device=device_wrapper.get(),
                            on_action=on_action,
                            storage=storage,
                            session_state=session_state,
                            action_status=self.action_status,
                            is_limit_reached=is_limit_reached,
                            login=self.login,
                            password=self.password,
                            dump_ui=self.dump_ui)

            if success is True:
                session_state.exit_code = 0
                print(COLOR_REPORT + f"Logged in to {self.login}" + COLOR_ENDC)
                # storage.increment_logins_count()
            else:
                session_state.exit_code = 1
                print(COLOR_REPORT +
                      f"Could not log in to {self.login}" + COLOR_ENDC)

            self.action_status.set(ActionState.DONE)

        while not self.action_status.get() == ActionState.DONE:
            job()
