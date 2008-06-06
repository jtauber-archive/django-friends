from django.conf import settings

from models import Contact

import vobject
import ybrowserauth
import simplejson
import gdata.contacts.service

def import_vcards(stream, user):
    """
    Imports the given vcard stream into the contacts of the given user.
    
    Returns a tuple of (number imported, total number of cards).
    """
    
    total = 0
    imported = 0
    for card in vobject.readComponents(stream):
        total += 1
        try:
            name = card.fn.value
            email = card.email.value
            try:
                Contact.objects.get(user=user, email=email)
            except Contact.DoesNotExist:
                Contact(user=user, name=name, email=email).save()
                imported += 1
        except AttributeError:
            pass # missing value so don't add anything
    return imported, total

def import_yahoo(bbauth_token, user):
    """
    Uses the given BBAuth token to retrieve a Yahoo Address Book and
    import the entries with an email address into the contacts of the
    given user.
    
    Returns a tuple of (number imported, total number of entries).
    """
    
    ybbauth = ybrowserauth.YBrowserAuth(settings.BBAUTH_APP_ID, settings.BBAUTH_SHARED_SECRET)
    ybbauth.token = bbauth_token
    address_book_json = ybbauth.makeAuthWSgetCall("http://address.yahooapis.com/v1/searchContacts?format=json&email.present=1&fields=name,email")
    address_book = simplejson.loads(address_book_json)
    
    total = 0
    imported = 0
    
    for contact in address_book["contacts"]:
        total += 1
        email = contact['fields'][0]['data']
        name = contact['fields'][1]['first'] + contact['fields'][1]['last']
        try:
            Contact.objects.get(user=user, email=email)
        except Contact.DoesNotExist:
            Contact(user=user, name=name, email=email).save()
            imported += 1
    return imported, total


def import_google(authsub_token, user):
    """
    Uses the given AuthSub token to retrieve Google Contacts and
    import the entries with an email address into the contacts of the
    given user.
    
    Returns a tuple of (number imported, total number of entries).
    """

    contacts_service = gdata.contacts.service.ContactsService()
    contacts_service.auth_token = authsub_token
    contacts_service.UpgradeToSessionToken()
    emails = []
    feed = contacts_service.GetContactsFeed()
    emails.extend(sum([[email.address for email in entry.email] for entry in feed.entry], []))
    next_link = feed.GetNextLink()
    while next_link:
        feed = contacts_service.GetContactsFeed(uri=next_link.href)
        emails.extend(sum([[email.address for email in entry.email] for entry in feed.entry], []))
        next_link = feed.GetNextLink()
    total = 0
    imported = 0
    for email in emails: # @@@ how do we get name?
        total += 1
        try:
            Contact.objects.get(user=user, email=email)
        except Contact.DoesNotExist:
            Contact(user=user, email=email).save()
            imported += 1
    return imported, total
