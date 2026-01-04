from CommandData import command_data
import Redditor
import PMResponse
import re
import os
from ErrorPrinter import print_error
from DB import db_session
from Models import Sub
from BotUtils import strip_command_name, format_sub_name, format_user_name, extract_command
from prawcore import PrawcoreException

BOT_ADMIN = (os.environ.get('BOT_ADMIN') or "BOT_ADMIN not found at os.env").lower()

def try_command(pm):
    if handle_mod_invite(pm):
        return True
    # Cancel PM and marks as read without executing anything if no author data
    if pm.author == None:
        return True
    
    # Cancel PM and marks as read without executing anything if unknown command
    comm = extract_command(pm.body.replace(';','\n').split('\n')[0])
    command = find_command_name(comm)
    if not command:
        comm = strip_command_name(pm.subject)
        command = find_command_name(comm)
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
            if not Redditor.is_mod_from_sub(author, sub) and not is_bot_admin(author):
                PMResponse.add_response(author, "mod_only_command", format_sub_name(sub), pm)
                return True
        except Exception as e:
            return False
    
    # Check if a command is Admin-only
    if admin_only_command(command) and not is_bot_admin(author):
        PMResponse.add_response(author, "admin_only_command", format_sub_name(sub), pm)
        return True
    
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

def admin_only_command(comm):
    if not "admin" in command_data[comm]["options"]:
        return False
    return command_data[comm]["options"]["admin_only"]

def registered_only_command(comm):
    return command_data[comm]["options"]["registered_sub"]

def allow_even_locked(comm):
    return command_data[comm]["options"]["allow_locked"]

def is_bot_admin(author):
    return format_user_name(author).lower() == BOT_ADMIN

def handle_mod_invite(pm):
    #handles mod invites. returns true if it was a valid invite, false otherwise
    if pm.author == None and pm.subject.startswith('Invitation to moderate'):
        return Redditor.auto_accept_mod(pm)
    else:
        return False
