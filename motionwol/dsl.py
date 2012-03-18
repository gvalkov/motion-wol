# encoding: utf-8

'''
A little 'dsl' for defining the conditions under which a host
should be woken up. Example:

Rule(
    Host('192.168.1.101', '00:24:1d:d9:fa:09'),
    HoldOff(300),
    When(
        And (
            TimeBetween(time(10, 00, 00), time(12, 00, 00)),
            InactiveFor(300),
            Not (DayOfWeek(6, 5)),
        )
    )
)
'''


from time import time as utime, mktime
from datetime import time, date, datetime
from motionwol.state import wakelog, last_motion, prev_motion, config


class Condition:
    def __init__(self, *args):
        self.args = args

    def check(self):
        return self._check(datetime.now(), self.host)

class DayOfWeek(Condition):
    def _check(self, now, host):
        now = now.date().weekday()
        return any(map(lambda x: x == now, self.args))

class TimeBetween(Condition):
    def _check(self, now, host):
        nt = now.time()
        return self.args[0] < nt < self.args[1]

class InactiveFor(Condition):
    ''' Time in seconds since the last motion event '''
    def _check(self, now, host):
        return (int(utime()) - prev_motion[0]) > self.args[0]

class HoldOff(Condition):
    ''' Ignore motion events for this many seconds after host becomes inactive'''
    def _check(self, now, host):
        if host in wakelog:
            return (int(utime()) - wakelog[host]) >= self.args[0]


class LogicOp:
    def __init__(self, *conditions):
        self.conditions = conditions

    def eval(self, root=None):
        if not root:
            root = self

    def flatten(self):
        # :bug: should be made recursive
        for cond in self.conditions:
            if isinstance(cond, LogicOp):
                yield cond.eval
            else:
                yield cond.check

class And(LogicOp):
    def eval(self):
        for cond in self.flatten():
            if not cond(): return False
        return True

class Or(LogicOp):
    def eval(self):
        for cond in self.flatten():
            if cond(): return True
        return False

class Not(LogicOp):
    def eval(self):
        return not self.conditions[0].check()


class Rule:
    def __init__(self, *args):
        isins = lambda t: lambda x: isinstance(x, t)

        self.host = filter(isins(Host), args)
        self.when = filter(isins(When), args)
        self.hold = filter(isins(HoldOff), args)


        try:
            self.host = list(self.host)[0]
            self.when = list(self.when)[0]
            self.hold = list(self.hold)[0]
        except IndexError:
            raise Exception('Rule requires at least one host and condition')

        self.enabled = True
        self.inject_host()

        # simply instantiating a rule adds it to the global config list
        config.append(self)

    def inject_host(self):
        for i in self.when.get_conditions():
            i.host = self.host

    def eval(self):
        return self.when.eval()


class When:
    def __init__(self, *args):
        self.conditions = args

    def eval(self):
        res = (i.eval() for i in self.conditions)
        return all(res)

    def get_conditions(self):
        conditions = []

        def _helper(root):
            for i in root.conditions:
                if isinstance(i, Condition):
                    conditions.append(i)
                else:
                    _helper(i)

        _helper(self)
        return conditions


class Host:
    def __init__(self, addr, mac):
        self.addr = addr
        self.mac = mac

    def __repr__(self):
        return '{} {}'.format(self.addr, self.mac)


if __name__ == '__main__':
    last_motion = utime()

    r = Rule(
        Host('192.168.1.101', '00:24:1d:d9:fa:09'),
        HoldOff(300),
        When(
            And (
                TimeBetween(time(00, 00, 00), time(12, 00, 00)),
                InactiveFor(300),
                Not (DayOfWeek(5)),
            )
        )
    )

    print(r.eval())
