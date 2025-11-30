import re
import enum
import PMResponse
import Redditor
from ErrorPrinter import print_error
from psycopg2.errors import UniqueViolation
from sqlalchemy import and_, func
from Models import Sub, Follow
from DB import db_session
from SubredditConfigOpt import config_options
from BotUtils import strip_command_name, convert_date
from praw.exceptions import InvalidURL

has_new_follows = False

def register_sub(author, sub_name, lines, pm):
    with db_session() as s:
        sub = Sub(sub_name=sub_name)
        s.add(sub)
            
    if s.success:
        PMResponse.add_response(author, "sub_registered", sub_name, pm)
        return True
    else:
        if s.db_error:
            if isinstance(s.db_error, UniqueViolation):
                PMResponse.add_response(author, "sub_already_registered", sub_name, pm)
            else:
                PMResponse.add_response(author, "sub_register_error", sub_name, pm)
            return True
        else:
            raise s.error
    
def unregister_sub(author, sub_name, lines, pm):
    with db_session() as s:
        sub = s.query(Sub).filter(Sub.sub_name.ilike(sub_name)).first()
        s.delete(sub)
            
    if s.success:
        PMResponse.add_response(author, "sub_unregistered", sub_name, pm)
        return True
    else:
        PMResponse.add_response(author, "sub_unregister_error", sub_name, pm)
        return True

def unlock_sub(author, sub_name, lines, pm):
    with db_session() as s:
        sub = s.query(Sub).filter(Sub.sub_name.ilike(sub_name)).first()
        sub.locked = False
            
    if s.success:
        PMResponse.add_response(author, "sub_unlocked", sub_name, pm)
        return True
    else:
        PMResponse.add_response(author, "sub_unlocked_error", sub_name, pm)
        return True

def subscribe_sub(author, sub_name, lines, pm):
    groups = group_follows_params(split_params(lines))
    
    if groups["team"][0] == None and groups["tour"][0] == None:
        PMResponse.add_response(author, "subscribe_invalid_format", sub_name, pm)
        return True
    
    if groups["team"][0] == "" and groups["tour"][0] == "":
        PMResponse.add_response(author, "subscribe_invalid_format", sub_name, pm)
        return True
    
    subs_data = { "sub": sub_name, "team": groups["team"], "tour": groups["tour"] }
    with db_session() as s:
        new_follows = []
        sub = s.query(Sub).filter(Sub.sub_name.ilike(sub_name)).first()
        
        existing = s.query(Follow).filter_by(sub=sub.id).all()
        
        for to in groups["tour"]:
            for te in groups["team"]:
                if not has_existing_follow(existing, to, te):
                    new_follows.append(Follow(sub=sub.id, team=te, tour=to))
        
        if len(new_follows) > 0:
            s.add_all(new_follows)
            global has_new_follows
            has_new_follows = True
    
    if s.success:
        PMResponse.add_response(author, "subscribe_success", subs_data, pm)
        return True
    else:
        print_error(s.error)
        PMResponse.add_response(author, "subscribe_fail", subs_data, pm)
        return True

def unsubscribe_sub(author, sub_name, lines, pm):
    groups = group_follows_params(split_params(lines))
    
    if groups["team"][0] == '' and groups["tour"][0] == '':
        PMResponse.add_response(author, "unsubscribe_invalid_format", [], pm)
        return True
    
    subs_data = { "sub": sub_name, "team": groups["team"], "tour": groups["tour"] }
    with db_session() as s:
        new_follows = []
        sub = s.query(Sub).filter(Sub.sub_name.ilike(sub_name)).first()
        
        removed = s.query(Follow).filter(Follow.sub == sub.id).filter(and_(
            func.lower(Follow.team).in_(map(str.lower, groups["team"])),
            func.lower(Follow.tour).in_(map(str.lower, groups["tour"]))
        )).delete(synchronize_session=False)
    
    if s.success:
        PMResponse.add_response(author, "unsubscribe_success", subs_data, pm)
        return True
    else:
        PMResponse.add_response(author, "unsubscribe_fail", subs_data, pm)
        return True

def get_sub_follows(author, sub_name, lines, pm):
    subs_data = { "sub": sub_name }
    with db_session() as s:
        # Get Sub info from DB
        sub = s.query(Sub).filter(Sub.sub_name.ilike(sub_name)).first()
        
        # Get all Follows under that Sub
        follows = s.query(Follow).filter(Follow.sub == sub.id).all()
        
        # follows_id arrays store a no-accents lowercase version of the team/tour names
        team_follows, team_follows_id = [], []
        tour_follows, tour_follows_id = [], []
        mixed_follows, team_id_dict = {}, {}
        both_follows = {}
        
        # First check which teams have total coverage and which tours have total coverage
        for f in follows:
            if f.team == '':
                id = strip_command_name(f.tour)
                if not id in tour_follows_id:
                    tour_follows.append(f.tour)
                    tour_follows_id.append(id)
            elif f.tour == '':
                id = strip_command_name(f.team)
                if not id in team_follows_id:
                    team_follows.append(f.team)
                    team_follows_id.append(id)
        
        # Find Follows for a Team on a specific Tour not covered by above function
        for f in follows:
            if f.team != '' and f.tour != '':
                team, team_id = f.team, strip_command_name(f.team)
                tour, tour_id = f.tour, strip_command_name(f.tour)
                if not team_id in team_follows_id and not tour_id in tour_follows_id:
                    if not team_id in mixed_follows:
                        team_id_dict[team_id] = team
                        mixed_follows[team_id] = []
                    mixed_follows[team_id].append(tour)
        
        
        # Convert id key to full name
        for key,value in mixed_follows.items():
            both_follows[team_id_dict[key]] = value
        
        # Save data for response
        subs_data["team"] = team_follows
        subs_data["tour"] = tour_follows
        subs_data["both"] = both_follows
        
    
    if s.success:
        PMResponse.add_response(author, "get_follows_success", subs_data, pm)
        return True
    else:
        print_error(s.error)
        PMResponse.add_response(author, "get_follows_fail", sub_name, pm)
        return True

def config_sub(author, sub_name, lines, pm):
    params = split_params(lines)
    config_values = {}
    
    # If not parameters, just list all current settings
    if len(params) == 0:
        config_data = { "sub": sub_name }
        with db_session() as s:
            sub = s.query(Sub).filter(Sub.sub_name.ilike(sub_name)).first()
            config_data["config_sub_list"] = get_sub_values(sub)
        if s.success:
            PMResponse.add_response(author, "config_sub_list", config_data, pm)
            return True
        else:
            print_error(s.error)
            return False
    
    invalid_params = []
    invalid_values = []
    values_changed = []
    
    # Check for valid parameters and values, and mark invalid ones
    for x in params:
        comm = identify_config_command(x["param"])
        if comm == None:
            invalid_params.append(x["param"])
        else:
            val = validate_config_value(config_options[comm], x["value"])
            if val != None:
                config_values[comm] = val
            else:
                invalid_values.append(get_option_formatted(comm, x["value"]))
    
    # Actually update the values on database
    with db_session() as s:
        sub = s.query(Sub).filter(Sub.sub_name.ilike(sub_name)).first()
        
        if bool(config_values):
            for key,value in config_values.items():
                setattr(sub, key, value)
                values_changed.append(get_option_formatted(key, value))
        
    if s.success:
        if len(values_changed) > 0:
            PMResponse.add_response(author, "config_sub_success", { "sub": sub_name, "values_changed": values_changed }, pm)
        if len(invalid_values) > 0:
            PMResponse.add_response(author, "config_sub_invalid_value", { "sub": sub_name, "invalid_values": invalid_values }, pm)
        if len(invalid_params) > 0:
            PMResponse.add_response(author, "config_sub_invalid_option", { "sub": sub_name, "invalid_params": invalid_params }, pm)
        
        return True
    else:
        print_error(s.error)
        PMResponse.add_response(author, "config_sub_fail", sub_name, pm)
        return True
    

def get_sub_values(sub):
    res = []
    for key,value in config_options.items():
        val = getattr(sub, key)
        if val != None:
            res.append(get_option_formatted(key, val))
    return res

def get_option_formatted(key, value):
    return "- {Title} = {Value}".format(
        Title=config_options[key]["title"], 
        Value=to_readable_value(value)
    )

def to_readable_value(val):
    if isinstance(val, bool):
        if val == True:
            return "Sim"
        elif val == False:
            return "Não"
    elif isinstance(val, enum.Enum):
        return val.name
    else:
        return val

team_aliases = ["time", "equipe", "clube", "times", "equipes", "clubes"]
tour_aliases = ["torneio", "competicao", "campeonato", "torneios", "competicoes", "campeonatos"]

def group_follows_params(params):
    result = {}
    for x in params:
        type = strip_command_name(x["param"])
        val = list(map(lambda s: s.strip(), x["value"].split(",")))
        if type in team_aliases:
            type = "team"
        elif type in tour_aliases:
            type = "tour"
        if not type in result:
            result[type] = []
        result[type] = result[type] + val
    
    if not "team" in result:
        result["team"] = [""]
    if not "tour" in result:
        result["tour"] = [""]
    
    return result

def has_existing_follow(follows, tour, team):
    for f in follows:
        if f.tour.lower() == tour.lower() and f.team.lower() == team.lower():
            return True
    return False

def split_params(lines):
    result = []
    for l in lines:
        parts = l.split("=")
        if len(parts) > 1:
            result.append({
                "param": parts[0].strip(),
                "value": parts[1].strip()
            })
    return result

def describe_config(name):
    if name in config_options:
        return config_options[name]["desc"]
    return None

def identify_config_command(name):
    for key, value in config_options.items():
        n = strip_command_name(name)
        if n == key:
            return key
        if n == strip_command_name(value["title"]):
            return key
        if n in value["alts"]:
            return key
    return None

def validate_config_value(comm, value):
    type = comm["type"]
    if value == None:
        return None
    
    # BOOLEAN
    if type == "Boolean":
        if value.lower().strip() in ["sim", "s", "yes", "y", "true",]:
            return True
        if value.lower().strip() in ["não", "nao", "n", "no", "false",]:
            return False
    # STRING
    elif type == "String":
        if "max_length" in comm and len(value) > comm["max_length"]:
            return None
        if "reddit_url" in comm and comm["reddit_url"] == True:
            url = is_reddit_post_or_wiki(value)
            if not url:
                return None
            value = url
        return value
    # NUMBER
    elif type == "Number":
        try:
            val = int(value)
            if "min" in comm and val < comm["min"]:
                return None
            return val
        except ValueError:
            return None
    # ENUM
    elif type == "Enum":
        enum = comm["enum"]
        val = value.lower().strip()
        if val in enum.__members__:
            return enum[val]
    return None

def is_reddit_post_or_wiki(url):
    try:
        id = Redditor.url_to_thread_id(url)
        return url
    except InvalidURL as e:
        res = re.match(r'https?://www.reddit.com/r/[\w%-]+/wiki/[\w\\\-]+', url)
        if res:
            return res.group(0)
        else:
            return None
    except Exception as e:
        print_error(e)
        return None
