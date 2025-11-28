from DB import db_session
from Models import Hub, Sub
from ErrorPrinter import print_error
from HubData import HubData
from sqlalchemy import or_
import BotUtils

ongoing_hubs = {}

# Removes old Hub entries from DB
def clear_old_hubs(cutoff):
    with db_session() as s:
        old = s.query(Hub).filter(Hub.date < cutoff).delete(synchronize_session=False)
    
    if not s.success:
        print_error(s.error)
    
    to_pop = []
    for id,hub in ongoing_hubs.items():
        if hub.date < cutoff:
            to_pop.append(id)
    
    for p in to_pop:
        if p in ongoing_hubs:
            ongoing_hubs.pop(p)

# Check which HUB threads need to be created/updated
def run_hub_threads():
    today = BotUtils.today()
    
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
                process_hubs(s, sub, today)
            except Exception as e:
                print_error(e)
    
    if not s.success:
        print_error(s.error)

# Create or update HUB thread
def process_hubs(s, sub, today):
    # Create Hub DB entry if needed
    create_hub(s, sub, today)

    # Get active Hubs
    hubs = s.query(Hub)\
        .filter(Hub.sub == sub.id)\
        .filter(or_(
            Hub.date == today,
            Hub.finished == False
        ))
    
    # Update each active hub
    for hub in hubs:
        update_hub(s, hub, sub, hub.date)

def create_hub(s, sub, today):
    hub = s.query(Hub)\
        .filter(Hub.sub == sub.id)\
        .filter(Hub.date == today)\
        .first()
    
    if not hub:
        hub = Hub(sub=sub.id, date=today)
        s.add(hub)
    
def update_hub(s, hub, sub, date):
# Get Hub Data object (or create if needed)
    if not hub.id in ongoing_hubs:
        hub_data = HubData(sub.id, date, hub.url)
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
    
    if hub_data.is_hub_finished():
        hub.finished = True