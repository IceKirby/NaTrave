import sys
import pdb
import os
import datetime
import time
from datetime import date, datetime
from ErrorPrinter import print_error

import DB
import CommandHandler
import Redditor
import SubManager
import MatchManager
import HubManager
import Scheduler
import PMResponse
import SubLockManager
import BotUtils

update_interval = 30
cache_clear_interval = 120
last_date = None

def start_up():
    print("Bot Name: {Name}".format(Name=Redditor.get_bot_name()))
    print("Bot started at {}".format(BotUtils.now().strftime("%d/%m/%Y, %H:%M:%S")))
    cache_clear_count = 0
    
    # Creates Database tables if needed
    DB.create_database()

    while True:
        # Clear PM Responses from previous loop
        PMResponse.clear_responses()
        
        # Clear unnecessary MatchData objects
        MatchManager.clear_match_objects()
        
        # Clear outdated Schedule objects
        Scheduler.clear_cached()
        
        # Check if a sub needs to be locked
        SubLockManager.clear_old_tokens()
        SubLockManager.check_for_locks()
        
        # Clear edited threads' cache
        cache_clear_count += 1
        if cache_clear_count > cache_clear_interval:
            Redditor.clear_cached_threads()
            cache_clear_count = 0
        
        # Functions that only need to be executed once per day
        today = BotUtils.today()
        global last_date
        if today != last_date or SubManager.has_new_follows:
            # Removes old Match, Threads and Requests from DB
            Scheduler.clear_old_matches()
            
            # Schedule matches according to sub's follows
            # And update date if follows have been scheduled successfully
            try:
                if Scheduler.schedule_follows():
                    last_date = today
                    SubManager.has_new_follows = False
            except Exception as e:
                print_error(e)
                
        
        # Checks PMs for user requests
        Redditor.read_pm()
        
        # Searchs for URL for matches about to start
        Scheduler.find_match_links()
        
        # Creates the thread for match threads
        Scheduler.create_match_threads()
        
        # Sets state to pre_match for matches starting in 60 minutes
        MatchManager.start_pre_match()
        
        # Updates threads' contents, and create post-match thread if needed
        MatchManager.run_matches()
        MatchManager.finish_untracked_matches()
        
        # Tries to find matches that have been cancelled/postponed
        Scheduler.find_aborted_matches()
        
        # Sets state as finished and update one last time a few minutes after match is finished
        MatchManager.finish_matches()
        
        # TODO: Manage HUB Threads
        HubManager.clear_old_hubs()
        HubManager.run_hub_threads()
        
        # Unpins pinned threads after time has passed
        Scheduler.unpin_threads()
        
        # Send PMs to users when necessary
        PMResponse.process_responses()
        
        # Checks if bot needs to be shutdown
        if needs_shutdown():
            break
        
        # now = BotUtils.now().strftime("%H:%M:%S")
        # print(f'Última atualização às {now}.')
        
        # Wait some time until next update
        time.sleep(update_interval)

def needs_shutdown():
    return False

if __name__ == "__main__":
    import sys
    try:
        start_up()
        print("Program has finished operation.")
    except KeyboardInterrupt:
        print("Terminating program forcefully.")
