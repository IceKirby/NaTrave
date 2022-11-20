from DB import db_session
from Models import Hub, Sub
from ErrorPrinter import print_error
from HubData import HubData
import BotUtils

ongoing_hubs = {}

# Removes old Hub entries from DB
def clear_old_hubs():
    today = BotUtils.today()
    
    with db_session() as s:
        old = s.query(Hub).filter(Hub.date < today).delete(synchronize_session=False)
    
    if not s.success:
        print_error(s.error)
    
    to_pop = []
    for id,hub in ongoing_hubs.items():
        if hub.date < today:
            to_pop.append(id)
    
    for p in to_pop:
        if p in ongoing_hubs:
            ongoing_hubs.pop(p)

# Check which HUB threads need to be created/updated
def run_hub_threads():
    today = BotUtils.today()
    tomorrow = BotUtils.tomorrow()
    
    with db_session() as s:
        # Get subs with the Match Hub option enabled
        pending = s.query(Sub)\
            .filter(Sub.match_hub == True)\
            .filter(Sub.locked == False)\
            .all()
            
        if len(pending) == 0:
            return
        
        for sub in pending:
            try:
                create_or_update_hub(s, sub, today, tomorrow)
            except Exception as e:
                print_error(e)
    
    if not s.success:
        print_error(s.error)

# Create or update HUB thread
def create_or_update_hub(s, sub, today, tomorrow):
    hub = s.query(Hub)\
        .filter(Hub.sub == sub.id)\
        .filter(Hub.date == today)\
        .first()
    
    # Create Hub DB entry if needed
    if not hub:
        hub = Hub(sub=sub.id, date=today)
        s.add(hub)
    
    # Get Hub Data object (or create if needed)
    if not hub.id in ongoing_hubs:
        hub_data = HubData(sub.id, today, hub.url)
        ongoing_hubs[hub.id] = hub_data
    hub_data = ongoing_hubs[hub.id]
    
    # Update Hub Data's list of today's matches being tracked
    hub_data.find_tracked_matches(s)
    
    # Create or update HUB thread if needed
    if hub_data.needs_update or hub_data.pending_creation:
        if not hub.url:
            hub_data.create_thread(s, hub, sub)
        else:
            hub_data.update_thread(s, hub, sub)
