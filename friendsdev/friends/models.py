import datetime

from django.db import models

from django.contrib.auth.models import User

class Contact(models.Model):
    """
    A contact is a person known by a user who may or may not themselves
    be a user.
    """
    
    user = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    added = models.DateField(default=datetime.date.today)
    
    class Admin:
        list_display = ('id', 'name', 'email', 'user', 'added')



class Friendship(models.Model):
    """
    A friendship is a bi-directional association between two users who
    have both agreed to the association.
    """
    
    to_user = models.ForeignKey(User, related_name="friends")
    from_user = models.ForeignKey(User, related_name="_unused_")
    # @@@ relationship types
    added = models.DateField(default=datetime.date.today)
    
    class Meta:
        unique_together = (('to_user', 'from_user'),)
    
    class Admin:
        list_display = ('id', 'from_user', 'to_user', 'added', )


INVITE_STATUS = (
    ("1", "Created"),
    ("2", "Sent"),
    ("3", "Failed"),
    ("4", "Expired"),
    ("5", "Accepted"),
    ("6", "Declined"),
)



class JoinInvitation(models.Model):
    """
    A join invite is an invitation to join the site from a user to a
    contact who is not known to be a user.
    """
    
    contact = models.ForeignKey(Contact)
    message = models.TextField()
    sent = models.DateField()
    status = models.CharField(max_length=1, choices=INVITE_STATUS)



class FriendshipInvitation(models.Model):
    """
    A frienship invite is an invitation from one user to another to be
    associated as friends.
    """
    
    from_user = models.ForeignKey(User, related_name="invitations_from")
    to_user = models.ForeignKey(User, related_name="invitations_to")
    message = models.TextField()
    sent = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=1, choices=INVITE_STATUS)
    
    class Admin:
        list_display = ('id', 'from_user', 'to_user', 'sent', 'status', )
