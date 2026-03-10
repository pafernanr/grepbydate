import argparse
from datetime import datetime
import gzip
import lzma
import os
from pathlib import Path
import re
import warnings
warnings.filterwarnings("error")


class GrepByDate():

    def __init__(self):
        self.show = False
        self.current_date = False
        self.dateformat_from = False
        self.dateformat_to = False
        self.current_file = ""
        self.file_list = []
        self.exceptions = {}
        self.file_mdate = False
        # patterns order is important. First pattern match will be used
        self.date_formats = {
            '%a %b %d %H:%M:%S UTC %Y': re.compile(r'((Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2} \d{2}:\d{2}:\d{2} UTC \d{4})'),
            '%a %b %d %H:%M:%S GMT %Y': re.compile(r'((Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2} \d{2}:\d{2}:\d{2} GMT \d{4})'),
            '%a %b %d %H:%M:%S EST %Y': re.compile(r'((Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2} \d{2}:\d{2}:\d{2} EST \d{4})'),
            '%a %b %d %H:%M:%S CST %Y': re.compile(r'((Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2} \d{2}:\d{2}:\d{2} CST \d{4})'),
            '%a %b %d %H:%M:%S MST %Y': re.compile(r'((Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2} \d{2}:\d{2}:\d{2} MST \d{4})'),
            '%a %b %d %H:%M:%S PST %Y': re.compile(r'((Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2} \d{2}:\d{2}:\d{2} PST \d{4})'),
            '%b %d %H:%M:%S': re.compile(r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) {1,2}\d{1,2} \d{2}:\d{2}:\d{2})'),  # noqa: E501
            '%d/%b/%Y:%H:%M:%S %z': re.compile(r'(\d{2}/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)/\d{4}:\d{2}:\d{2}:\d{2} \+\d{4})'),  # noqa: E501
            '%d %b %Y %H:%M:%S': re.compile(r'(\d{2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4} \d{2}:\d{2}:\d{2})'),  # noqa: E501
            '%d-%b-%Y %H:%M:%S': re.compile(r'(\d{2}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4} \d{2}:\d{2}:\d{2})'),  # noqa: E501
            '%Y-%m-%dT%H:%M:%S%z': re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{4})'),  # noqa: E501
            '%Y-%m-%dT%H:%M:%S': re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})'),  # noqa: E501
            '%Y-%m-%d %H:%M:%S': re.compile(r'(\d{4}-\d{2}-\d{2} {1,2}\d{1,2}:\d{2}:\d{2})'),  # noqa: E501
            'timestamp.audit': re.compile(r'(audit\((\d{10})\.\d{3}:\d{7}\))'),  # noqa: E501
        }

        self.valid_date_formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%d/%b/%Y:%H:%M:%S"
            ]

        self.parser = argparse.ArgumentParser(
            prog="grepbydate",
            description="Show events from log files converting input date"
                        + " formats to a unique format: '%Y-%m-%d %H:%M:%S'.",
            epilog=f"""Supported date format for `--from` and `--to` filters:
            {str(self.valid_date_formats)}"""
            )
        self.parser.add_argument(
            '-f',
            '--from',
            dest='date_from',
            help="(Optional). Filter from this datetime.",
            default='1974-04-10',
            type=self.valid_date
            )
        self.parser.add_argument(
            '-i',
            '--ignorecase',
            help='(Optional). Ignore case on the search Regular Expression.',
            default=False,
            action='store_true',
            )
        self.parser.add_argument(
            '-t',
            '--to',
            dest='date_to',
            help="(Optional). Filter until this datetime.",
            default='2999-01-01',
            type=self.valid_date
            )
        self.parser.add_argument(
            '-s',
            '--search',
            help='(Optional). Filter lines using this Regex.',
            )
        self.parser.add_argument(
            'inputfiles',
            help='(Required). file/s to read.',
            type=self.valid_path,
            nargs='+'
            )
        self.args = self.parser.parse_args()
        if self.args.date_to < self.args.date_from:
            print("ERROR: `--to` must be greater than `--from`.")
            exit(1)
        if self.args.search:
            if self.args.ignorecase:
                self.args.search = re.compile(self.args.search,
                                              flags=re.IGNORECASE)
            else:
                self.args.search = re.compile(self.args.search)
        for f_list in self.args.inputfiles:
            for f in f_list:
                self.file_list.append(f)

        textchars = bytearray(
            {7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
        self.is_binary_string = lambda bytes: bool(
            bytes.translate(None, textchars))

    def valid_date(self, d):
        valid = self.valid_date_formats
        for v in valid:
            newd = self.date_from_string(d)
            if newd:
                return newd
        raise argparse.ArgumentTypeError(
            f"not a valid date: {d!r}. Valid formats: {str(valid)}")

    def valid_path(self, path):
        if os.path.exists(path):
            if os.path.isdir(path):
                paths = []
                for fname in Path(path).rglob('*'):
                    if os.path.isfile(fname):
                        paths.append(str(fname))
                return paths
            else:
                return [path]
        else:
            raise argparse.ArgumentTypeError(f"{path!r} Is not a valid path.")

    def add_exception(self, f, e):
        try:
            self.exceptions[f].append(e)
        except KeyError:
            self.exceptions[f] = [e]

    def show_exceptions(self):
        if len(self.exceptions) > 0:
            print("\n##### There are some `grepbydate` parsing exceptions:")
            for f in self.exceptions.keys():
                print(f"## {f}")
                for e in self.exceptions[f]:
                    print(f"    - {e}")

    def date_from_string(self, d):
        valid = self.valid_date_formats
        for v in valid:
            try:
                return datetime.strptime(d, v)
            except ValueError:
                continue
        self.add_exception(
            self.current_file,
            f"ERROR: not a valid date: {d!r}.")

    def read(self, fname):
        lines = []
        try:
            with open(fname, 'rb') as f:
                isbin = self.is_binary_string(f.read())
                if isbin:
                    if fname.endswith(".gz"):
                        f = gzip.open(fname, 'r')
                    elif fname.endswith(".xz"):
                        f = lzma.open(fname, 'r')
                    else:
                        return []
                else:
                    f = open(fname, 'rb')
                for item in f.readlines():
                    # Some lines can contain strings in multiple encodings
                    # that could break the parser.
                    # I don't care about encoding (UnicodeEncodeError)
                    # so just convert to str and cut unneeded chars
                    # E.g: b'\t2025-05-07 03:10:01 log line content.\n'
                    #
                    #   lines.append(str(item)[2:-3])
                    #
                    # Next seems a better solution because it honors "\t"
                    #
                    lines.append(item.decode('utf-8', 'ignore').rstrip())
            f.close()
        except Exception as e:
            print(f"ERROR parsing: {fname}\n{e}")
        return lines

    def line_contains_date(self, line):
        # search for dates only if line starts with a word char
        # and only in the first 69 chars
        for f, pattern in self.date_formats.items():
            if re.match(r'\w', line):
                r = re.search(pattern, line[0:68])
                if r:
                    self.dateformat_from = r.group(1)
                    self.dateformat_to = f
                    return True
        return False

    def date_is_in_range(self):
        if self.args.date_from <= self.current_date <= self.args.date_to:
            return True
        return False

    def line_contains_regex(self, line):
        if self.args.search and not re.search(self.args.search, line):
            return False
        return True

    def format_date(self, line, datestr, format):
        if format == "timestamp.audit":
            # audit\((\d{10})\.\d{3}:\d{7}\)
            date = datetime.fromtimestamp(int(datestr[6:16]))
            newdatestr = datestr.replace(datestr[6:16], str(date))
        else:
            try:
                date = datetime.strptime(datestr, format)
            # workaround dates without year (E.g /var/log/messages)
            # '%b %d %H:%M:%S'
            except DeprecationWarning as dw:
                if "https://github.com/python/cpython/issues/70647" in str(dw):
                    format = '%Y %b %d %H:%M:%S'
                    try:
                        date = datetime.strptime(
                            f"{self.file_mdate.year} {datestr}", format)
                    except ValueError as ve:
                        self.add_exception(
                            self.current_file,
                            f"({self.file_mdate.year} {datestr} to {format})"
                            + f" {ve}\n      {line}")
                        return line
            self.current_date = date.replace(tzinfo=None)
            newdatestr = str(self.current_date)

        return line.replace(datestr, newdatestr)

    def main(self):
        for file in self.file_list:
            self.file_mdate = datetime.fromtimestamp(os.path.getmtime(file))
            self.current_file = file
            newfile = True
            for line in self.read(file):
                if self.line_contains_date(line):
                    # format date
                    line = self.format_date(
                        line,
                        self.dateformat_from,
                        self.dateformat_to)
                    if (self.date_is_in_range()
                            and self.line_contains_regex(line)):
                        self.show = True
                    else:
                        self.show = False
                # line contains a date and line line matches regex (if exists)
                if self.show:
                    if newfile:  # Show header
                        print(f"\n{'#' * 80}\n# {file}\n{'#' * 80}")
                        newfile = False
                    print(line)
        self.show_exceptions()


GrepByDate().main()
