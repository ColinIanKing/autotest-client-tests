import re


def get_stats(stdout_results):
    # search for the benchmark output line
    # for example, search for "300 300.0  6776.8  0.000  0.960 0.00000" which has
    #     1. 6 numbers, either integers (300) or floats in x.x format (6776.8)
    #     2. the third number (6776.8) is what we want
    #
    # regular expression:
    #     1. (\d+(\.\d+)?) for x.x or x
    #         1.1. \d for numbers, equivalent to [0-9]
    #         1.2. \d+ one or more numbers. + is short for {1, }
    #         1.3. (\.\d+)? zero or one ".x". ? is short for {0, 1}
    #     2. \s for space, short for [\f\n\r\t\v\u00A0\u2028\u2029]
    #         2.1. \s+ for one or more spaces
    #     3. (){n} for n repetitions of group
    pattern = r"""(\d+(\.\d+)?)         # for x.x or x
                  (\s+(\d+(\.\d+)?)){2} # 2 repetitions of _x.x or _x
                  (\s+(\d+(\.\d+)?)){3} # 3 repetitions of _x.x or _x"""
    rc = re.compile(pattern, re.VERBOSE)
    matches = rc.findall(stdout_results, re.MULTILINE)

    # get the key number
    target_number = matches[1][3]

    return target_number
