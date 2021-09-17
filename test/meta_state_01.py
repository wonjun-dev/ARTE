import time

from transitions import Machine


class SignalState:

    states = ["idle", "stg_1", "stg_order"]

    def __init__(self):
        transitions = [
            {"trigger": "proceed", "source": "idle", "dest": "stg_1", "conditions": "check_sig_1"},
            {
                "trigger": "proceed",
                "source": "stg_1",
                "dest": "stg_order",
                "conditions": "check_sig_2",
                "after": "notify_pass_all",
            },
            {"trigger": "initialize", "source": "*", "dest": "idle", "before": "print_end"},
        ]
        m = Machine(
            model=self,
            states=SignalState.states,
            transitions=transitions,
            initial="idle",
            after_state_change="auto_proceed",
        )

    def print_end(self, **kwargs):
        print(f"From {self.state} go back to Idle state.")

    def auto_proceed(self, **kwargs):
        if not self.state == "idle":
            if not self.proceed(**kwargs):
                self.initialize()

    def check_sig_1(self, **kwargs):
        return kwargs["a"]

    def check_sig_2(self, **kwargs):
        return kwargs["b"]

    def notify_pass_all(self, **kwargs):
        print("Passed all signals.")
        self.initialize()


# ss = SignalState()
# ss.proceed(a=True, b=True)


class PositionState:
    states = ["empty", "part_long", "part_short", "full_long", "full_short"]

    def __init__(self):
        transitions = [
            {
                "trigger": "buy_long",
                "source": ["empty", "part_long", "full_long"],
                "dest": "=",
                "conditions": "check_over_full_position",
                "before": "error_buy",
            },
            {
                "trigger": "buy_long",
                "source": ["empty", "part_long"],
                "dest": "full_long",
                "conditions": "check_full_position",
                "before": "before_buy",
                "after": "after_buy",
            },
            {
                "trigger": "buy_long",
                "source": ["empty", "part_long"],
                "dest": "part_long",
                "before": "before_buy",
                "after": "after_buy",
            },
            {"trigger": "buy_long", "source": "full_long", "dest": "=", "after": "error_buy"},
        ]
        m = Machine(model=self, states=PositionState.states, transitions=transitions, initial="empty")

        self.max_position_size = 5
        self.position_size = 0

    def check_full_position(self, **kwargs):
        return self.position_size + kwargs["size"] == self.max_position_size

    def check_over_full_position(self, **kwargs):
        return self.position_size + kwargs["size"] > self.max_position_size

    def error_buy(self, **kwargs):
        print("Oversize, cannot buy!")

    def after_buy(self, **kwargs):
        # real order in here
        self.position_size += kwargs["size"]

    def before_buy(self, **kwargs):
        print(f"{self.state}: {kwargs['size']}")

    def sell_long(self, **kwargs):
        print(f"sell long {kwargs['size']}")
        self.position_size -= kwargs["size"]

    def sell_short(self, **kwargs):
        print(f"sell short {kwargs['size']}")
        self.position_size -= kwargs["size"]

    def notify_full_hold(self, **kwargs):
        print(f"Reached to full hold: {self.state}")


ps = PositionState()
ps.buy_long(size=3)
print(ps.state)
ps.buy_long(size=1)
print(ps.state)
ps.buy_long(size=1)
print(ps.state)
ps.buy_long(size=3)
print(ps.state)
