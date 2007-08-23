from models import Contact

import vobject

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
            Contact(user=user, name=name, email=email).save()
            imported += 1
        except AttributeError:
            pass # missing value so don't add anything
    return imported, total
