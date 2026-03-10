## grepbydate
Show events from log files converting input date formats to a unique format: '%Y-%m-%d %H:%M:%S'.

- Format dates in specified input files.
- Transparently works on *.gz and *.xz files.
- Transparently transforms audit.log timestamps.
- Shows full stack trace if starting line matches the filtering options.
- Optional filtering by a time range.
- Optional filtering by Regexp. (Optionally ignore case)

### Usage
~~~
usage: grepbydate [-h] [-f DATE_FROM] [-i] [-t DATE_TO] [-s SEARCH] inputfiles [inputfiles ...]

Show events from log files converting input date formats to a unique format: '%Y-%m-%d %H:%M:%S'.

positional arguments:
  inputfiles            (Required). file/s to read.

options:
  -h, --help            show this help message and exit
  -f, --from DATE_FROM  (Optional). Filter from this datetime.
  -i, --ignorecase      (Optional). Ignore case on the search Regular Expression.
  -t, --to DATE_TO      (Optional). Filter until this datetime.
  -s, --search SEARCH   (Optional). Filter lines using this Regex.

Supported date format for `--from` and `--to` filters: ['%Y-%m-%d', '%Y-%m-%d %H', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H',
'%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S']
~~~

### Examples

- Get events from `/var/log` recursively from a specific date to last available date:
~~~
grepbydate -f 2025-06-02 /var/log/
~~~

- Get events from `/var/log` and `/var/lib/pgsl/data/log` into a time range:
~~~
grepbydate -f "2025-06-02 12:34:07" -t "2025-06-02 12:34:09" /var/log/ /var/lib/pgsql/data/log/
~~~

- Get events from input files matching `Katello.*error` regular expresion.
~~~
grepbydate $(find /var/log/foreman/ -type f) -s "Katello.*error"
~~~

- Get `opened` and `closed` sessions from `/var/log/secure-2025*` ignoring case.
~~~
grepbydate /var/log/secure-2025* -s "OPEned|CLosed" -i
~~~
