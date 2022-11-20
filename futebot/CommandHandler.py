from CommandData import command_data
import Redditor
import PMResponse
import re
from ErrorPrinter import print_error
from DB import db_session
from Models import Sub
from BotUtils import strip_command_name, format_sub_name
from prawcore import PrawcoreException

def try_command(pm):
    # Cancel PM and marks as read without executing anything if no author data
    if pm.author == None:
        return True
    
    # Cancel PM and marks as read without executing anything if unknown command
    command = find_command_name(pm.subject)
    if not command:
        return True
    
    # Cancel PM and marks as read without executing anything if no sub detected
    lines = split_into_lines(pm.body)
    sub = detect_sub_name(lines)
    author = pm.author.name
    if not sub:
        PMResponse.add_response(author, "no_sub_specified", {}, pm)
        return True
    
    sub = format_sub_name(sub)
    
    # DEBUG
    print("Comando '{Subject}' (por {User} para r/{Sub}): {CommandData}".format(User=author, Subject=command, Sub=sub, CommandData=lines))
    
    # Check if target subreddit exists
    try:
        if not Redditor.find_sub(sub):
            PMResponse.add_response(author, "no_such_sub", format_sub_name(sub), pm)
            return True
    except Exception as e:
        return False
    
    # Checks if PM sender is a mod of target subreddit (for some commands)
    if mod_only_command(command) or mod_only_request(command, sub):
        try:
            if not Redditor.is_mod_from_sub(author, sub):
                PMResponse.add_response(author, "mod_only_command", format_sub_name(sub), pm)
                return True
        except Exception as e:
            return False
    
    # Checks if subreddit is registered with bot (for some commands)
    if registered_only_command(command): 
        try:
            if not sub_is_registered(sub):
                PMResponse.add_response(author, "registered_only_command", format_sub_name(sub), pm)
                return True
        except Exception as e:
            return False
    
    # Checks if subreddit is currently locked
    if not allow_even_locked(command): 
        try:
            if sub_is_locked(sub):
                PMResponse.add_response(author, "registered_only_command", format_sub_name(sub), pm)
                return True
        except Exception as e:
            return False
        
    # Get function for specified command
    action = command_data[command]["action"]
    
    # Run command
    try:
        result = action(author, sub, lines, pm)
        return result
    except Exception as e:
        print_error(e)
        return False

def find_command_name(comm):
    comm = strip_command_name(comm)
    if comm in command_data:
        return comm
    
    for key, value in command_data.items():
        if comm in value["alts"]:
            return key
    
    return None

def split_into_lines(str):
    lines = re.split(r'[\n;]', str)
    return list(map(lambda x: x.strip(), lines))

def detect_sub_name(lines):
    sub_re = r"\/?r\/[A-z0-9\-_]{3,21}$"
    for index, item in enumerate(lines):
        if re.match(sub_re, item, re.IGNORECASE):
            lines.pop(index)
            return item
    
    return None

def sub_is_registered(name):
    with db_session() as s:
        sub = s.query(Sub).filter(Sub.sub_name.ilike(name)).first()
        if sub:
            return True
        else:
            return False
    
    if s.db_error or s.error:
        raise s.error

def sub_is_locked(name):
    with db_session() as s:
        sub = s.query(Sub).filter(Sub.sub_name.ilike(name)).first()
        if sub:
            return sub.locked
        else:
            return False
    
    if s.db_error or s.error:
        raise s.error

def mod_only_request(comm, name):
    mod_only = command_data[comm]["options"]["mod_only_by_options"]
    if not mod_only:
        return False
    
    with db_session() as s:
        sub = s.query(Sub).filter(Sub.sub_name.ilike(name)).first()
        if sub:
            return sub.mod_only_request
        else:
            return False
    
    if s.db_error or s.error:
        raise s.error
    
    return False

def mod_only_command(comm):
    return command_data[comm]["options"]["mod_only"]

def registered_only_command(comm):
    return command_data[comm]["options"]["registered_sub"]

def allow_even_locked(comm):
    return command_data[comm]["options"]["allow_locked"]
