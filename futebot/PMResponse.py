import FormattingData.PMResponseText as PMResponseText
import Redditor
from BotUtils import format_user_name, readable, translate_date, format_date_short
from datetime import datetime
from DB import db_session
from Models import UnsentPM
from ErrorPrinter import print_error

pending_responses = {}

# Clear responses at the start of the new loop so old messages aren't sent again
def clear_responses():
    global pending_responses
    pending_responses = {}

# Register a response that needs to be sent to an user
def add_response(username, type, data, pm = None):
    # Removes /u/ from username
    user = format_user_name(username)
    
    # Creates UserResponse data if it doesn't exists
    if not user in pending_responses:
        pending_responses[user] = UserResponse(user)
    
    # Register data about response according to type
    resp = pending_responses[user]
    resp.register_data(type, data, pm)

# Check all responses registered and formats them as a PM to their respective users
def process_responses():
    with db_session() as s:
        unsent = s.query(UnsentPM).all()
        for m in unsent:
            res = Redditor.send_pm(m.name, m.message, None, True)
            if res:
                s.delete(m)
    if not s.success:
        print_error(s.error)
    
    for user,data in pending_responses.items():
        res = format_response_data(user, data)
        if res != None:
            Redditor.send_pm(user, res, data.pm_ref)
        
# Checks each data registered for user and formats as string
def format_response_data(user, resp):
    result = []
    
    # General Command Errors
    if "no_sub_specified" in resp.data:
        result.append(PMResponseText.no_sub_specified)
    if "no_such_sub" in resp.data:
        result.append(PMResponseText.no_such_sub.format(Name=to_sub(resp.data["no_such_sub"])))
    if "mod_only_command" in resp.data:
        result.append(PMResponseText.mod_only_command.format(Name=to_sub(resp.data["mod_only_command"])))
    if "admin_only_command" in resp.data:
        result.append(PMResponseText.admin_only_command)
    if "registered_only_command" in resp.data:
        result.append(PMResponseText.registered_only_command.format(Name=to_sub(resp.data["registered_only_command"])))
        
    # [COMMAND] Match Thread
    requested, created, created_silent = [], [], []
    if "request_match_success" in resp.data:
        requested = resp.data["request_match_success"]
    if "requested_match_created" in resp.data:
        created = resp.data["requested_match_created"]
    if len(requested) > 0 and "requested_match_created_silent" in resp.data:
        created_silent = resp.data["requested_match_created_silent"]
    all_requested = merge_requests_data(requested, created)
    all_requested = merge_requests_data(all_requested, created_silent)
    
    if len(all_requested) > 0:
        result.append(PMResponseText.request_match_success.format(
            Matches=format_match_list(all_requested)
        ))
    if "request_match_error" in resp.data:
        result.append(PMResponseText.request_match_error.format(Name=to_sub(resp.data["request_match_error"])))
    if "request_match_no_match" in resp.data:
        result.append(PMResponseText.request_match_no_match.format(Name=to_sub(resp.data["request_match_no_match"])))
    if "request_match_invalid_format" in resp.data:
        result.append(PMResponseText.request_match_invalid_format.format(Name=to_sub(resp.data["request_match_invalid_format"])))
    if "request_match_blocked_user" in resp.data:
        result.append(PMResponseText.request_match_blocked_user.format(
            Name=to_sub(resp.data["request_match_blocked_user"][0]["sub"]),
            Date=translate_date(resp.data["request_match_blocked_user"][0]["date"]),
        ))
    
    # [COMMAND] Abort Match Thread
    if "abort_match_success" in resp.data:
        result.append(PMResponseText.abort_match_success.format(
            Matches=format_match_list(resp.data["abort_match_success"], True)
        ))
    if "abort_match_error" in resp.data:
        result.append(PMResponseText.abort_match_error.format(Name=to_sub(resp.data["abort_match_error"])))
    if "abort_match_invalid_format" in resp.data:
        result.append(PMResponseText.abort_match_invalid_format.format(Name=to_sub(resp.data["abort_match_invalid_format"])))

    # [COMMAND] Restart Match Thread
    if "restart_match_success" in resp.data:
        result.append(PMResponseText.restart_match_success.format(
            Matches=format_restart_list(resp.data["restart_match_success"][0])
        ))
    if "restart_match_error" in resp.data:
        result.append(PMResponseText.restart_match_error.format(Name=to_sub(resp.data["restart_match_error"])))
    if "restart_match_invalid_format" in resp.data:
        result.append(PMResponseText.restart_match_invalid_format.format(Name=to_sub(resp.data["restart_match_invalid_format"])))

    # [COMMAND] Set HUB Only
    if "set_hubonly_success" in resp.data:
        result.append(PMResponseText.set_hubonly_success.format(
            Matches=format_match_list(resp.data["set_hubonly_success"], True)
        ))
    if "set_hubonly_error" in resp.data:
        result.append(PMResponseText.set_hubonly_error.format(Name=to_sub(resp.data["set_hubonly_error"])))
    if "hubonly_match_invalid_format" in resp.data:
        result.append(PMResponseText.hubonly_match_invalid_format.format(Name=to_sub(resp.data["hubonly_match_invalid_format"])))
    
    # [COMMAND] Register
    if "sub_registered" in resp.data:
        result.append(PMResponseText.sub_registered.format(Name=to_sub(resp.data["sub_registered"])))
    if "sub_already_registered" in resp.data:
        result.append(PMResponseText.sub_already_registered.format(Name=to_sub(resp.data["sub_already_registered"])))
    if "sub_register_error" in resp.data:
        result.append(PMResponseText.sub_register_error.format(Name=to_sub(resp.data["sub_register_error"])))
    
    # [COMMAND] Unregister
    if "sub_unregistered" in resp.data:
        result.append(PMResponseText.sub_unregistered.format(Name=to_sub(resp.data["sub_unregistered"])))
    if "sub_unregister_error" in resp.data:
        result.append(PMResponseText.sub_unregister_error.format(Name=to_sub(resp.data["sub_unregister_error"])))
        
    # [COMMAND] Mod
    if "mod_accepted" in resp.data:
        result.append(PMResponseText.mod_accepted.format(Name=to_sub(resp.data["mod_accepted"])))
    if "mod_invite_fail" in resp.data:
        result.append(PMResponseText.mod_invite_fail.format(Name=to_sub(resp.data["mod_invite_fail"])))
    
    # [COMMAND] Subscribe
    if "subscribe_success" in resp.data:
        for x in resp.data["subscribe_success"]:
            result.append(PMResponseText.subscribe_success.format(
                Name=to_sub(x["sub"]),
                Follows=format_subscribe_list(x)
            ))
    if "subscribe_fail" in resp.data:
        result.append(PMResponseText.subscribe_fail.format(Name=to_sub(resp.data["subscribe_fail"][0]["sub"])))
    if "subscribe_invalid_format" in resp.data:
        result.append(PMResponseText.subscribe_invalid_format.format(Name=to_sub(resp.data["subscribe_invalid_format"])))
        
    # [COMMAND] Unsubscribe
    if "unsubscribe_success" in resp.data:
        for x in resp.data["unsubscribe_success"]:
            result.append(PMResponseText.unsubscribe_success.format(
                Name=to_sub(x["sub"]),
                Follows=format_subscribe_list(x)
            ))
    if "unsubscribe_fail" in resp.data:
        result.append(PMResponseText.unsubscribe_fail.format(Name=to_sub(resp.data["unsubscribe_fail"])))
    if "unsubscribe_invalid_format" in resp.data:
        result.append(PMResponseText.unsubscribe_invalid_format.format(Name=to_sub(resp.data["unsubscribe_invalid_format"])))
    
    # [COMMAND] Get Follows
    if "get_follows_success" in resp.data:
        for x in resp.data["get_follows_success"]:
            result.append(PMResponseText.subscribe_success.format(
                Name=to_sub(x["sub"]),
                Follows=format_subscribe_list_all(x)
            ))
    if "get_follows_fail" in resp.data:
        result.append(PMResponseText.get_follows_fail.format(Name=to_sub(resp.data["get_follows_fail"])))
    
    # [COMMAND] VIEW REQUESTS
    if "view_requests_success" in resp.data:
        sub_name = to_sub(resp.data["view_requests_success"][0]["sub"])
        result.append(PMResponseText.view_requests_success.format(
            Name=sub_name,
            Matches=format_requests_list(resp.data["view_requests_success"])
        ))
    if "view_requests_empty" in resp.data:
        result.append(PMResponseText.view_requests_empty.format(Name=to_sub(resp.data["view_requests_empty"])))
    if "view_requests_error" in resp.data:
        result.append(PMResponseText.view_requests_error.format(Name=to_sub(resp.data["view_requests_error"])))

    # [COMMAND] Block User
    if "block_user_success" in resp.data:
        sub_name = to_sub(resp.data["block_user_success"][0]["sub"])
        result.append(PMResponseText.block_user_success.format(
            Name=sub_name,
            Blocked=format_block_list(resp.data["block_user_success"])
        ))
    if "block_user_error" in resp.data:
        result.append(PMResponseText.block_user_error.format(
            Blocked=format_simple_list(resp.data["block_user_error"])
        ))
    if "block_user_empty" in resp.data:
        result.append(PMResponseText.block_user_empty.format(Name=to_sub(resp.data["block_user_empty"])))
    if "block_user_fail" in resp.data:
        result.append(PMResponseText.block_user_fail.format(Name=to_sub(resp.data["block_user_fail"])))

    # [COMMAND] Config
    if "config_sub_list" in resp.data:
        for x in resp.data["config_sub_list"]:
            result.append(PMResponseText.config_sub_list.format(
                Name=to_sub(x["sub"]),
                Config="  \n".join(x["config_sub_list"])
            ))
    if "config_sub_success" in resp.data:
        for x in resp.data["config_sub_success"]:
            result.append(PMResponseText.config_sub_success.format(
                Name=to_sub(x["sub"]),
                Config="  \n".join(x["values_changed"])
            ))
    if "config_sub_invalid_value" in resp.data:
        for x in resp.data["config_sub_invalid_value"]:
            result.append(PMResponseText.config_sub_invalid_value.format(
                Name=to_sub(x["sub"]),
                Config="  \n".join(x["invalid_values"])
            ))
    if "config_sub_invalid_option" in resp.data:
        for x in resp.data["config_sub_invalid_option"]:
            result.append(PMResponseText.config_sub_invalid_option.format(
                Name=to_sub(x["sub"]),
                Config="  \n".join(x["invalid_params"])
            ))
    
    if "config_sub_fail" in resp.data:
        result.append(PMResponseText.config_sub_fail.format(Name=to_sub(resp.data["config_sub_fail"])))
    
    # Other
    if "sub_locked" in resp.data:
        result.append(PMResponseText.sub_locked_message.format(
            Name=to_sub(resp.data["sub_locked"]),
            Bot="u/" + Redditor.get_bot_name()
        ))
    if "sub_unlocked" in resp.data:
        result.append(PMResponseText.sub_unlocked.format(
            Name=to_sub(resp.data["sub_unlocked"]),
        ))
    if "sub_unlocked_error" in resp.data:
        result.append(PMResponseText.sub_unlocked_error.format(
            Name=to_sub(resp.data["sub_unlocked_error"]),
        ))
    
    # Admin
    if "admin_command_result" in resp.data:
        result.append(PMResponseText.admin_command_result.format(
            Result="  \n".join(resp.data["admin_command_result"]),
        ))
    
    if len(result) == 0:
        return None
    
    return "  \n  \n---  \n  \n".join(result)

def merge_requests_data(list1, list2):
    # First check for duplicates, then make sure both have an URL
    for m1 in list1:
        for m2 in list2:
            if m1["match_id"] == m2["match_id"]:
                url = m1["url"] if m1["url"] != None else m2["url"]
                m1["url"] = url
                m2["url"] = url
                m2["duplicate"] = True
                break
    
    # Make a final list with entries from both, but excluding those marked as duplicate
    final_list = list(filter(lambda x: "duplicate" not in x, list1 + list2))
    
    return final_list

def format_match_list(matches, aborted=False):
    result = []
    for m in matches:
        result.append(PMResponseText.match_listing.format(
            Sub=to_sub(m["sub"]),
            Home=m["home"],
            Away=m["away"],
            Tour=m["tour"],
            Time=translate_date(m["time"]),
            Thread=get_thread_info(m, aborted)
        ))
    return "  \n".join(result)

def format_block_list(blocks):
    result = []
    for b in blocks:
        result.append(PMResponseText.blocked_user_line.format(
            Name=b["name"],
            Date=translate_date(b["end_date"]),
            User=b["applied_by"],
            Start=format_date_short(b["start_date"])
        ))
    return "  \n".join(result)

def format_requests_list(requests):
    result = []
    for r in requests:
        result.append(PMResponseText.view_request_line.format(
            Date=format_date_short(r["date"]),
            User=r["user"],
            Home=r["home_team"],
            Away=r["away_team"],
            Tour=r["tour"],
            HubOnly="Sim" if r["hub_only"] == False else "Não"
        ))
    return "  \n".join(result)

def format_restart_list(requests):
    result = []
    for key,value in requests.items():
        result.append(PMResponseText.restart_match_line.format(
            Home=value["home"],
            Away=value["away"],
            Tour=value["tour"]
        ))
    return "  \n".join(result)

def format_subscribe_list(subs):
    teams, tours = None, None
    if not subs["team"][0] == None:
        teams = readable(subs["team"])
    if not subs["tour"][0] == None:
        tours = readable(subs["tour"])
        
    if teams and tours:
        return PMResponseText.subscribe_team_tour.format(Teams=teams, Tours=tours)
    elif teams:
        return PMResponseText.subscribe_team_only.format(Teams=teams)
    elif tours:
        return PMResponseText.subscribe_tour_only.format(Tours=tours)

def format_simple_list(arr):
    return "  \n".join(list(map(lambda x: "- " + x, arr)))

def format_subscribe_list_all(subs):
    result = []
    
    if len(subs["team"]) > 0:
        result.append(PMResponseText.get_subs_teams.format(Teams=readable(subs["team"])))
    if len(subs["tour"]) > 0:
        result.append(PMResponseText.get_subs_tours.format(Tours=readable(subs["tour"])))
    if len(subs["both"]) > 0:
        result.append(PMResponseText.get_subs_both.format(Teams=format_teams_on_tours(subs["both"])))
    
    if len(result) == 0:
        return PMResponseText.subscribe_none
    else:
        return "  \n".join(result)

def format_teams_on_tours(subs):
    res = []
    
    for key,value in subs.items():
        res.append(PMResponseText.get_subs_both_li.format(Team=key, Tours=readable(value)))
    
    return "  \n".join(res)
        

def get_thread_info(match, aborted=False):
    if match["url"]:
        return PMResponseText.match_listing_thread_existing.format(URL=match["url"])
    else:
        if aborted:
            return PMResponseText.match_listing_thread_pending_aborted.format(Date=translate_date(match["thread_time"]))
        elif match["hub_only"]:
            return PMResponseText.match_listing_thread_hub_only
        else:
            return PMResponseText.match_listing_thread_pending.format(Date=translate_date(match["thread_time"]))

def to_sub(sub_list):
    if isinstance(sub_list, str):
        return "r/" + sub_list
    else:
        return readable(list(map(lambda x: "r/"+x, sub_list)))

# Class to organize response data
class UserResponse():
    def __init__(self, username):
        self.username = username
        self.data = {}
        self.pm_ref = None
    
    # Register response data
    def register_data(self, type, value, pm = None):
        # Save Reddit PM reference so it can be replied directly to
        if pm and self.pm_ref == None:
            self.pm_ref = pm
            
        # Create type if it doesn't exists
        if not type in self.data:
            self.data[type] = []
        
        # Concat value if list, append otherwise
        if isinstance(value, list):
            self.data[type] = self.data[type] + value
        else:
            self.data[type].append(value)
    
