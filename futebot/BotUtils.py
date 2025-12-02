import unicodedata
import re
from datetime import date, datetime, timedelta, timezone

month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

### Date/Time Utils ##
# Get current datetime
def now():
    return datetime.now()
    # return datetime.now(timezone(-timedelta(hours=3)))

# Get midnight time of current date
def today():
    return to_day_start(now())

# Get midnight time of next date
def tomorrow():
    return today() + timedelta(days=1)

# Get midnight time of previous date
def yesterday():
    return today() - timedelta(days=1)

def days_from_today(num):
    return today() + timedelta(days=num)

def to_day_start(date):
    return date.replace(hour=0, minute=0, second=0, microsecond=0)

# Removes seconds from time format because who needs them?
def format_time(raw):
    parts = raw.split(":")
    return parts[0] + ":" + parts[1]

# Converts datetime object to "13 de Maio de 2022, 23:59" format
def translate_date(time, with_hours=True):
    templ = "{Day} de {Month}, {Hour}:{Minute}" if with_hours else "{Day} de {Month}"
    
    month = month_names[time.month - 1]
    
    return templ.format(
        Day=time.day,
        Month=month,
        Hour=zero_pad(time.hour, 2),
        Minute=zero_pad(time.minute, 2)
    )

# Formats date string from '2021-02-28' format to '28 de Fevereiro de 2021' format
def format_date(raw):
    parts = raw.split("-")
    day = str(int(parts[2]))
    month = month_names[int(parts[1])-1]

    return "{Dia} de {Mes} de {Ano}".format(Dia=day, Mes=month, Ano=parts[0])

# Formats datetime object to '28/02/2021' format
def format_date_short(dt):
    return "{Dia}/{Mes}/{Ano}".format(Dia=dt.day, Mes=dt.month, Ano=dt.year)

# Converts date string from '23/07/2022' to date object
def convert_date(str):
    parts = str.split("/")

    today = date.today()
    day = int(parts[0])
    month = int(parts[1])
    year = today.year
    if len(parts) > 2:
        try:
            year = int("20" + parts[2]) if len(parts[2]) == 2 else int(parts[2])
        except:
            year = today.year

    if month <= 0 or month > 12:
        month = today.month
    if day <= 0 or day > 31:
        day = today.day

    return datetime(year, month, day)

# Converts datetime string from '2022-07-19 14:42:11' format to datetime object
def to_datetime(val):
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")

# Converts input from '19/07/2022 14:42' format to datetime object
def to_datetime_from_input(val):
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.strptime(val, "%d/%m/%Y %H:%M")
        except:
            try:
                return datetime.strptime(val, "%d/%m/%Y")
            except:
                return None

### String Utils
class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'

# Same as str.format(), but allows for unused {} parameters
def format_str(str, **args):
    return str.format_map(SafeDict(args))

# Converts é to e, ç to c, etc
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').strip()

# Strips accents and returns lower case
def normalize_name(name):
    return strip_accents(name).lower()

# Converts "1" string to "001"
def zero_pad(val, digits):
    while len(str(val)) < digits:
        val = "0"+str(val)
    return val

# Formats a list of strings as "ItemA, ItemB and ItemC"
def readable(list, last_delim="e"):
    if len(list) > 1:
        return ", ".join(list[0:-1]) + " " + last_delim + " " + list[-1]
    elif len(list) == 1:
        return list[0]
    else:
        return ""

### Reddit Utils
# Returns subreddit's name without the /r/ part
def format_sub_name(str):
    if str.startswith("r/"):
        return str[2:]
    elif str.startswith("/r/"):
        return str[3:]
    return str

# Returns user's name without the /u/ part
def format_user_name(str):
    if str.startswith("u/"):
        return str[2:]
    elif str.startswith("/u/"):
        return str[3:]
    return str

# Returns command string as lower case without accents, whitespace or -
def strip_command_name(name):
    n = strip_accents(name.lower().strip())
    n = re.sub(r"[\s\-]", "", n)
    return n
