"""
Custom pipeline functions used in Seattle Clearinghouse.

"""
from django.http import HttpResponseRedirect
from social_auth.backends.exceptions import AuthException
from social_auth.backends.pipeline.social import social_auth_user
from seattlegeni.website.control import interface
from uuid import uuid4
                                
def redirect_to_auto_register(*args, **kwargs):
    if not kwargs['request'].session.get('saved_username') and \
       kwargs.get('user') is None:
        return HttpResponseRedirect('/html/auto_register')

def username(request, *args, **kwargs):
    if kwargs.get('user'):
        username = kwargs['user'].username
    else:
        username = request.session.get('saved_username')
    return {'username': username}
   
def custom_social_auth_user(*args, **kwargs):
    try:
        return social_auth_user(*args, **kwargs)
    except AuthException:
    	 return HttpResponseRedirect('associate_error')      
    
def custom_create_user(backend, details, response, uid, username, user=None, *args,
                **kwargs):
    """Create user. Depends on get_username pipeline."""
    if user:
        return {'user': user}
    if not username:
        return None
    
    #set a random password
    password=str(uuid4())
    # NOTE: not return None because Django raises exception of strip email
    email = details.get('email') or ''
    if email == '':
      email= 'auto-register@'+ backend.name +'.com'
    user = interface.register_user(username, password, email, affiliation='auto-register@'+ backend.name)
    return {
        'user': user,
        'is_new': True
    }             
