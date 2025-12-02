import praw
import os
import re
import SubManager
import CommandHandler
import PMResponse
from DB import db_session
from ErrorPrinter import print_error
from praw.models import Comment, Message, Submission
from praw.exceptions import RedditAPIException
from prawcore.exceptions import Forbidden
from prawcore import NotFound
from BotUtils import format_sub_name
from Models import UnsentPM

reddit = praw.Reddit(
    username=os.environ.get('reddit_username'),
    password=os.environ.get('reddit_password'),
    client_id=os.environ.get('reddit_client_id'),
    client_secret=os.environ.get('reddit_client_secret'),
    user_agent=os.environ.get('reddit_user_agent'),
    ratelimit_seconds=300
)
cached_threads = {}

def clear_cached_threads():
    global cached_threads
    cached_threads = {}

def get_bot_name():
    return str(reddit.user.me())

def read_pm():
    unread_messages = []
    comments = get_unread_pm()
    
    for pm in comments:
        if isinstance(pm, Message):
            if CommandHandler.try_command(pm):
                unread_messages.append(pm)

    if len(unread_messages) > 0:
        mark_pm_as_read(unread_messages)

def get_unread_pm():
    try:
        return reversed(list(reddit.inbox.unread(limit=None)))
    except Exception as e:
        print_error(e)
        return []

def mark_pm_as_read(messages):
    try:
        pass
        reddit.inbox.mark_read(messages)
    except Exception as e:
        print_error(e)
    

def send_pm(user, message, pm, is_retry=False):
    print("------------------------------------------------")
    print("-- Response to", user, "-----------------------")
    print(message)
    print("------------------------------------------------")
    # return True
    title = "Resposta de u/{}".format(get_bot_name())
    
    try:
        if pm:
            pm.reply(body=message)
        else:
            if is_sub_name(user):
                reddit.subreddit(format_sub_name(user)).message(subject=title, message=message)
            else:
                reddit.redditor(user).message(subject=title, message=message)
    except RedditAPIException as exception:
        for subexc in exception.items:
             if subexc.error_type == "USER_DOESNT_EXIST":
                print("User u/{} not found, cancelling PM".format(user))
                return True
    except Exception as e:
        print_error(e)
        if not is_retry:
            with db_session() as s:
                pm = UnsentPM(name=user, message=message)
                s.add(pm)
            
            if not s.success:
                print_error(s.error)
        return False
    return True
        
    # print(response)

def create_thread(data):
    subreddit = reddit.subreddit(data["sub"])
    
    if data["flair"]:
        flair = find_flair(subreddit, data["flair"])
    else:
        flair = None
    
    if not flair:
        requeriments = subreddit.post_requirements()
        if requeriments["is_flair_required"] == True:
            flair = get_default_flair(subreddit)
    
    if flair:
        submission = subreddit.submit(data["title"], selftext=data["text"], flair_id=flair["id"], send_replies=False)
    else:
        submission = subreddit.submit(data["title"], selftext=data["text"], send_replies=False)
        
    id = url_to_thread_id(submission.url)
    cached_threads[id] = data["text"]
    return submission.url

def post_comment(data):
    thread = reddit.submission(data["thread"])
    comment = thread.reply(data["text"])
    
    if comment:
        comment.disable_inbox_replies()
        return comment.permalink
    return None
    

def update_thread(data):
    id = data["id"]
    text = data["text"]
    
    # Checks if the thread's current content is identical to the update
    if id in cached_threads and cached_threads[id] == text:
        return
    
    # Updates cached text
    cached_threads[id] = text
    
    # Updates thread contents
    submission = reddit.submission(id=id)
    submission.edit(text)

def delete_thread(thread_url):
    try:
        submission = reddit.submission(url_to_thread_id(thread_url))
        submission.delete()
        return True
    except Exception as e:
        print_error(e)
        return False

def set_thread_sticky(thread_id, state=True):
    try:
        submission = reddit.submission(id=thread_id)
        sub = submission.subreddit.display_name
        
        if is_mod_from_sub(None, sub):
            submission.mod.sticky(state=state, bottom=True)
    except Exception as e:
        print_error(e)

def set_thread_sort(thread_id, sort="new"):
    try:
        submission = reddit.submission(id=thread_id)
        sub = submission.subreddit.display_name
        
        if is_mod_from_sub(None, sub):
            submission.mod.suggested_sort(sort=sort)
    except Exception as e:
        print_error(e)

def accept_mod(author, sub, lines, pm):
    subreddit = find_sub(sub)
    if subreddit == None:
        PMResponse.add_response(author, "no_such_sub", sub, pm)
        return True
    else:
        try:
            subreddit.mod.accept_invite()
            PMResponse.add_response(author, "mod_accepted", sub, pm)
            return True
        except Exception as e:
            PMResponse.add_response(author, "mod_invite_fail", sub, pm)
            return True

def find_sub(subname):
    try:
        res = reddit.subreddits.search_by_name(format_sub_name(subname), exact=True)
        if len(res) == 0:
            return None
        res = res[0]
        # Try to access an attribute to check if the sub is private
        desc = res.description
        return res
    except NotFound:
        return None
    except Forbidden as e:
        return None
    except Exception as e:
        print_error(e)
        raise e

def is_mod_from_sub(user, sub):
    subreddit = find_sub(sub)
    
    if not subreddit:
        return False
    
    if user == None:
        user = reddit.user.me().name
    try:
        for moderator in subreddit.moderator():
            if moderator.name.lower() == user.lower():
                return True
        return False
    except Forbidden as e:
        return False
    except Exception as e:
        raise e

# Find Post Flair in specific sub
def find_flair(sub, str):
    for f in sub.flair.link_templates:
        if f["text"] == str:
            return f

def get_default_flair(sub):
    for f in sub.flair.link_templates:
        return f

def url_to_thread_id(url):
    return Submission.id_from_url(url)

def is_sub_name(str):
    return re.match(r'/?r/', str)
