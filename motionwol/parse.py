# encoding: utf-8

# Parses config enties like:
#
#  wake 00:24:1d:d9:fa:09:
#      10:00 < now < 12:00
#      18:00 < now < 23:45
#      inactivity 10 min
#      hold off 5 min
#      now not Sun
#
# into dsl.Rule objects


from calendar import day_name
from datetime import time
from pyparsing import *
from motionwol.dsl import *


multipliers = {
    'sec' : 1,    's' : 1,
    'min' : 60,   'm' : 60,
    'hour': 3600, 'h' : 3600,
}

weekdays = list(day_name)
weekdays.extend([i[:3] for i in weekdays])


# indent/unindent helpers
indent_stack = [1]
def check_peer_indent(s, l, t):
    cur_col = col(l,s)
    if cur_col != indent_stack[-1]:
        if (not indent_stack) or cur_col > indent_stack[-1]:
            raise ParseFatalException(s, l, 'illegal nesting')

        raise ParseException(s, l, 'not a peer entry')

def is_indent(s, l, t):
    cur_col = col(l, s)
    if cur_col > indent_stack[-1]:
        indent_stack.append( cur_col )
    else:
        raise ParseException(s, l, 'not an indent')

def is_unindent(s, l, t):
    if l >= len(s): return
    cur_col = col(l,s)
    if not(cur_col < indent_stack[-1] and cur_col <= indent_stack[-2]):
        raise ParseException(s, l, 'not an unindent')

def do_unindent():
    indent_stack.pop()


# parse action helpers
def to_inactivity(s, l, t):
    return InactiveFor(t[1] * multipliers[t[2]])

def to_hold_off(s, l, t):
    return HoldOffFor(t[1] * multipliers[t[2]])

def to_day_number(s, l, t):
    return weekdays.index(t[0]) % 7

def to_dayofweek(s, l, t):
    res = []

    res.append(DayOfWeek(t[-1]))
    return res

def to_rule(s, l, t):
    r = Rule(t[0], When(*t[1]))
    return r


# shortcut for 'suppressed literal'
s = lambda x: Literal(x).suppress()

# handle indentation
INDENT = lineEnd.suppress() + empty + empty.copy().setParseAction(is_indent)
UNDENT = FollowedBy(empty).setParseAction(is_unindent)
UNDENT.setParseAction(do_unindent)

# grammar
stmt = Forward()
suite = Group(OneOrMore(empty + stmt))

dow = OneOrMore(oneOf(weekdays))
hex2 = Word(hexnums, exact=2)
integer = Word(nums)
interval = oneOf(list(multipliers.keys()))
ip_address = Combine(Word(nums) + ('.' + Word(nums)) * 3)
mac_address = Combine(hex2 + (':' + hex2) * 5)
hh = Word(nums, exact=2)
mm = Word(nums, exact=2)
ss = Word(nums, exact=2)
hhmmss = hh + Optional(s(':') + mm) + Optional(s(':') + ss)

inactivity = 'inactivity' + integer + interval
hold_off = 'hold off' + integer + interval
host = 'wake' + mac_address + ':'
day_of_week = 'now' + Optional('not') + dow
time_between = hhmmss + s('<') + s('now') + s('<') + hhmmss

rule = host + INDENT + suite + UNDENT
stmt << ( rule | inactivity | hold_off | day_of_week | time_between )

# parse actions
stmt.setParseAction(check_peer_indent)
integer.setParseAction(lambda t: int(t[0]))
dow.setParseAction(to_day_number)
inactivity.setParseAction(to_inactivity)
hold_off.setParseAction(to_hold_off)
host.setParseAction(lambda s, l, t: Host(t[1]))
day_of_week.setParseAction(to_dayofweek)
time_between.setParseAction(lambda s, l, t: TimeBetween(*t))
hhmmss.setParseAction(lambda s, l, t: time(*t))
rule.setParseAction(to_rule)
[i.setParseAction(lambda t: int(t[0])) for i in (hh,mm,ss)]


def parse_config(fn):
    if hasattr(fn, 'read'):
        c = fn.read()
    else:
        with open(fn) as fh:
            c = fh.read()

    tree = suite.parseString(c)
    return tree[0].asList()
