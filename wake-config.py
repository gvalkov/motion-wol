Rule(
    Host('192.168.1.101', '00:11:12:13:14:15'),
    HoldOff(300),
    When(
        And (
            TimeBetween(time(00, 00, 00), time(12, 00, 00)),
            InactiveFor(300),
            Not (DayOfWeek(6, 5)), )
        ))
