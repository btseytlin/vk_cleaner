from django.shortcuts import render, redirect
from .util import sort_friends_by_last_interaction_date
from django.conf import settings
from .forms import AuthInfoForm
from django.core.urlresolvers import reverse
import vk
import urllib.parse as urlparse
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
import json
import time
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.contrib import messages
from vk.exceptions import VkAPIError, VkAuthError

def _get_access_token(request):
    if 'access_token' in request.session and 'user_id' in request.session:
        access_token = request.session['access_token'] 
        user_id = int(request.session['user_id'])
        return access_token, user_id
    return None, None

def _get_api(request):
    access_token, user_id = _get_access_token(request)
    if access_token:
        session = vk.Session(access_token=access_token)
        api = vk.API(session)
        return api, access_token, user_id
    return None, None, None


def vk_required(fail_redirect_url_name):
    def _vk_required_decorator(func):
        def wrapper(request, *args, **kwargs):
            api, access_token, user_id = _get_api(request)
            if api:
                return func(request, api,access_token, user_id, *args, **kwargs)
            else:
                messages.add_message(request, messages.ERROR, 'Для этого действия требуется авторизоваться VK')
                return redirect(reverse(fail_redirect_url_name)) 
        return wrapper
    return _vk_required_decorator

def vk_api_call(request, func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except VkAPIError as e:
        if 'access_token' in str(e):
            messages.add_message(request, messages.ERROR, 'Неверный access token.\nАвторизуйтесь снова.'.format(e))
            return redirect(reverse('logout'))
        else:
            messages.add_message(request, messages.ERROR, 'Ошибка при взаимодействии с VK API: {}.\nПопробуйте ещё раз.'.format(e))
            return redirect(reverse('index'))
    except Exception as e:
        messages.add_message(request, messages.ERROR, 'Произошла неизветсная ошибка: {} {} {}.'.format(repr(e), e, str(e.args)))
        return redirect(request.META.get('HTTP_REFERER', reverse('logout')))




def _get_user_friends(api, user_id):

    friends = cache.get('{}_friends'.format(user_id))
    if friends:
        friends = json.loads(friends)
    else:
        friends = api.friends.get(user_id=user_id, order='random', fields=['fist_name','deactivated','photo_50', 'last_name'])
        
        cache.set('{}_friends'.format(user_id), json.dumps(friends))

    return friends

def _get_user_dialogs(api, user_id):
    dialogs = cache.get('{}_dialogs'.format(user_id))
    if dialogs:
        dialogs = json.loads(dialogs)
    else:
        dialogs = []
        offset = 0
        _query_dialogs = api.messages.getDialogs(preview_length=1, offset=offset, count=200)[1:]
        dialogs += _query_dialogs
        while len(_query_dialogs) >= 200:
            offset+=200
            _query_dialogs = api.messages.getDialogs(preview_length=1, offset=offset, count = 200)[1:]
            dialogs += _query_dialogs
            time.sleep(2)

        cache.set('{}_dialogs'.format(user_id), json.dumps(dialogs))
    return dialogs

@csrf_protect
def index(request):

    if request.method == 'POST':
        auth_info_form = AuthInfoForm(request.POST)
        if auth_info_form.is_valid():
            vk_link = auth_info_form.cleaned_data['vk_link']
            params = urlparse.parse_qs(urlparse.urlparse(vk_link).fragment)
            access_token = params['access_token'][0]
            user_id = params['user_id'][0]
            request.session['access_token'] = access_token
            request.session['user_id'] = user_id
            messages.add_message(request, messages.INFO, 'Вы авторизовались VK.com')
            return redirect(reverse('index'))
    else:
        auth_info_form = AuthInfoForm()
    auth_uri = settings.VK_AUTH_URI
    context = RequestContext(request)
    respose_data = {"context":context,"auth_uri":auth_uri, "auth_info_form": auth_info_form}

    api, access_token, user_id = _get_api(request)
    if api:
        respose_data['user_data'] = {}

        api_response = vk_api_call(request, api.users.get, user_ids=[user_id], fields=['photo_100'])
        if isinstance(api_response, HttpResponse):
            if isinstance(api_response, HttpResponseRedirect):
                return redirect(reverse('logout'))
        user = api_response[0]

        respose_data['user_data']['user_full_name'] = user['first_name'] + ' ' + user['last_name']
        respose_data['user_data']['user_pic'] = user['photo_100']

    return render(request, "index.html",  context=respose_data)

@vk_required('index')
def logout(request, api, access_token, user_id):
    del request.session['access_token']
    del request.session['user_id']
    request.session.modified = True
    cache.delete('{}_friends'.format(user_id))
    cache.delete('{}_dialogs'.format(user_id))

    messages.add_message(request, messages.INFO, 'Вы вышли из приложения')
    return redirect(reverse('index'))

@vk_required('logout')
def friend_list(request, api, access_token, user_id):
    api_response = vk_api_call(request, _get_user_friends, api, user_id)
    if isinstance(api_response, HttpResponse):
        return api_response
    friends = api_response

    api_response = vk_api_call(request, _get_user_dialogs, api, user_id)
    if isinstance(api_response, HttpResponse):
        return api_response
    dialogs = api_response

    friends_dates = sort_friends_by_last_interaction_date(friends, dialogs)
    return render(request, "friend_list.html", {"friends_dates":friends_dates} )

""" ajax """
@vk_required('logout')
def delete_friend(request, api, access_token, user_id):
    friend_user_id = request.GET.get('friend_user_id')
    if friend_user_id:
        api_response = vk_api_call(request, api.friends.delete, user_id=friend_user_id)
        if isinstance(api_response, HttpResponse):
            return api_response
    else:
        return HttpResponseBadRequest({'error':'invalid friend user id'}, content_type="text/json")

    data = {'success': api_response}
    cache.delete('{}_friends'.format(user_id))
    return JsonResponse(data=data)

def about(request):
    return render(request, 'about.html')
