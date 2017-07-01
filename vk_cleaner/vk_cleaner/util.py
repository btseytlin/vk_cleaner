import json
import time
from datetime import datetime
from django.utils.formats import localize


def localize_list_dates(friend_dates_list):
    for val in friend_dates_list:
        if val['date']:
            val['date'] = localize(val['date'])
        else:
            val['date'] = "Никогда"

    return friend_dates_list

def mark_deactivated(friend_dates_list):
    for val in friend_dates_list:
        if 'deactivated' in val:
            val['date'] = val['date'] + ' (страница удалена)'

    return friend_dates_list

def sort_friends_by_last_interaction_date(friends, dialogs):
    friend_dates = {}
    for friend in friends:
        friend_dates[friend['user_id']]= friend#{'date':None,'user_id':friend['user_id'], 'screen_name':friend['screen_name'],'first_name':friend['first_name'], 'last_name':friend['last_name']}
        friend_dates[friend['user_id']]['date'] = None
        
    for dialog in dialogs:
        if dialog['uid'] in friend_dates.keys():
            if not friend_dates[dialog['uid']]['date'] or datetime.fromtimestamp(int(dialog['date'])) > friend_dates[dialog['uid']]['date']:
                friend_dates[dialog['uid']]['date'] = datetime.fromtimestamp(int(dialog['date']))    
    

    friend_dates_list = sorted(list(friend_dates.values()), key = lambda friend:   (not (friend['date'] is None), friend['date']), reverse=False)
    friend_dates_list = localize_list_dates(friend_dates_list)
    friend_dates_list = mark_deactivated(friend_dates_list)

    return friend_dates_list     
