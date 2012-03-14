import linecache
import re
import sys
from optparse import make_option

from django.core import management
from django.core.management.base import BaseCommand

from django_trace.management.commands.conf import (
    GOOD_PRESETS, BAD_PRESETS)
from django_trace.management.commands.module_names import (
    builtin_modules, stdlib_modules)


# global vars
trace_on = False
indent = 0
prev_name = ''
global_options = {
    'module_only': False,
    'calls_only': False,
}
good_regex = None
bad_regex = None


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--include-builtins', action='store_true', dest='include_builtins', default=False,
                    help='Include builtin functions (default=False)'),
        make_option('--include-stdlib', action='store_true', dest='include_stdlib', default=False,
                    help='Include standard library modules (default=False)'),
        make_option('--module-only', action='store_true', dest='module_only', default=False,
                    help='Display module names only (not lines of code)'),
        make_option('--calls-only', action='store_true', dest='calls_only', default=False,
                    help='Display function calls only (not lines of code)'),
        make_option('--good', action='store', dest='good', default='',
                    help='Comma separated list of exact module names to match'),
        make_option('--bad', action='store', dest='bad', default='',
                    help='Comma separated list of exact module names to exclude (takes precedence over --good and --good-regex)'),
        make_option('--good-regex', action='store', dest='good_regex', default='',
                    help='Regular expression of module to match'),
        make_option('--bad-regex', action='store', dest='bad_regex', default='',
                    help='Regular expression of module to exclude (takes precedence over --good and --good-regex)'),
        make_option('--good-preset', action='store', dest='good_preset', default='',
                    help='A key in the GOOD_PRESETS setting'),
        make_option('--bad-preset', action='store', dest='bad_preset', default='',
                    help='A key in the BAD_PRESETS setting'),
    )
    help = 'Use sys.settrace to trace code'
    args = '[command]'

    def handle(self, *args, **options):
        global good_regex
        global bad_regex
        args = list(args)
        command = args.pop(0)
        global_options['include_builtins'] = options['include_builtins']
        global_options['include_stdlib'] = options['include_stdlib']
        global_options['module_only'] = options['module_only']
        global_options['calls_only'] = options['calls_only']
        global_options['good'] = options['good']
        global_options['bad'] = options['bad']
        global_options['good_regex'] = options['good_regex']
        global_options['bad_regex'] = options['bad_regex']
        global_options['good_preset'] = options['good_preset']
        global_options['bad_preset'] = options['bad_preset']

        good_regex = re.compile(global_options['good_regex'])
        bad_regex = re.compile(global_options['bad_regex'])

        sys.settrace(traceit)

        options = dict(
            use_reloader=False,
        )
        management.call_command(command, *args, **options)


def traceit(frame, event, arg):
    global trace_on
    global indent
    global prev_name
    trace_on = True

    if '__name__' in frame.f_globals:
        name = frame.f_globals["__name__"]
    else:
        name = 'whatisthename'

    # check module name against a number of conditions to decide whether to trace or not
    if not global_options['include_builtins'] and name in builtin_modules:
        return traceit
    if not global_options['include_stdlib'] and name in stdlib_modules:
        return traceit
    if (global_options['bad'] and
        any(name.startswith(bad_substr)
            for bad_substr in global_options['bad'].split(','))):
        return traceit
    if (global_options['good'] and
        all(not name.startswith(good_substr)
            for good_substr in global_options['good'].split(','))):
        return traceit
    if (global_options['bad_preset'] and
        any(name.startswith(bad_substr)
            for bad_substr in BAD_PRESETS.get(global_options['bad_preset'], []))):
        return traceit
    if (global_options['good_preset'] and
        all(not name.startswith(good_substr)
            for good_substr in GOOD_PRESETS.get(global_options['good_preset'], []))):
        return traceit
    # check regexes last because they are slow
    if global_options['bad_regex']:
        bad_match = bad_regex.search(name)
        if bad_match:
            return traceit
    if global_options['good_regex']:
        good_match = good_regex.search(name)
        if not good_match:
            return traceit

    # get line number
    lineno = frame.f_lineno

    # get filename
    if '__file__' in frame.f_globals:
        filename = frame.f_globals["__file__"]
    else:
        filename = 'asdf'
    if filename == "<stdin>":
        filename = "traceit.py"
    if (filename.endswith(".pyc") or
        filename.endswith(".pyo")):
        filename = filename[:-1]

    # get line
    line = linecache.getline(filename, lineno)
    line = line.rstrip()
    output = "%s:%s: %s" % (name, lineno, line)
    # if 'django_apps.user.views:70' in output:
    #     trace_on = True
    # if 'django_apps.user.views:168' in output:
    #     trace_on = False

    if event == 'call':
        indent += 1
    elif event == 'return':
        indent -= 1

    if trace_on and line.strip():
        prefix = '-' * indent + '>'
        if global_options['module_only']:
            if name != prev_name and event == 'line':
                sys.stderr.write(('%02d' % indent) + prefix + name + '\n')
        elif global_options['calls_only']:
            if event == 'call':
                sys.stderr.write(('%02d' % indent) + prefix + output + '\n')
        else:
            if event == 'line':
                sys.stderr.write(('%02d' % indent) + prefix + output + '\n')

        prev_name = name

    return traceit
