import datetime
from random import random
import sha

from django.db import models

from django.contrib.auth.models import User

# favour django-mailer but fall back to django.core.mail
try:
    from mailer import send_mail
except ImportError:
    from django.core.mail import send_mail

try:
    from notification import models as notification
except ImportError:
    notification = None

from django.conf import settings


class Contact(models.Model):
    """
    A contact is a person known by a user who may or may not themselves
    be a user.
    """
    
    user = models.ForeignKey(User)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField()
    added = models.DateField(default=datetime.date.today)
    
    class Admin:
        list_display = ('id', 'name', 'email', 'user', 'added')


class FriendshipManager(models.Manager):

    def friends_for_user(self, user):
        friends = []
        for friendship in self.filter(from_user=user):
            friends.append({"friend": friendship.to_user, "friendship": friendship})
        for friendship in self.filter(to_user=user):
            friends.append({"friend": friendship.from_user, "friendship": friendship})
        return friends
    
    def are_friends(self, user1, user2):
        if self.filter(from_user=user1, to_user=user2).count() > 0:
            return True
        if self.filter(from_user=user2, to_user=user1).count() > 0:
            return True
        return False


class Friendship(models.Model):
    """
    A friendship is a bi-directional association between two users who
    have both agreed to the association.
    """
    
    to_user = models.ForeignKey(User, related_name="friends")
    from_user = models.ForeignKey(User, related_name="_unused_")
    # @@@ relationship types
    added = models.DateField(default=datetime.date.today)
    
    objects = FriendshipManager()
    
    class Meta:
        unique_together = (('to_user', 'from_user'),)
    
    class Admin:
        list_display = ('id', 'from_user', 'to_user', 'added', )


def friend_set_for(user):
    return set([obj["friend"] for obj in Friendship.objects.friends_for_user(user)])


INVITE_STATUS = (
    ("1", "Created"),
    ("2", "Sent"),
    ("3", "Failed"),
    ("4", "Expired"),
    ("5", "Accepted"),
    ("6", "Declined"),
)

class JoinInvitationManager(models.Manager):
    
    def send_invitation(self, from_user, to_email, message):
        contact, created = Contact.objects.get_or_create(email=to_email, user=from_user)
        salt = sha.new(str(random())).hexdigest()[:5]
        confirmation_key = sha.new(salt + to_email).hexdigest()
        
        subject = "You have been invited to join Pinax" # @@@ template
        email_message = """
You have been invited by %(user)s to join Pinax.

Pinax is both a platform for building social websites in Django as well
as a demonstration of a site built on that platform.

To accept this invitation, go to

http://pinax.hotcluboffrance.com/invitations/accept/%(confirmation_key)s/

If you have any questions about Pinax, don't hesitate to contact jtauber@jtauber.com
""" % { # @@@ template
            "user": from_user,
            "confirmation_key": confirmation_key,
        }
        send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, [to_email])
        
        return self.create(contact=contact, message=message, status="2", confirmation_key=confirmation_key)


class JoinInvitation(models.Model):
    """
    A join invite is an invitation to join the site from a user to a
    contact who is not known to be a user.
    """
    
    contact = models.ForeignKey(Contact)
    message = models.TextField()
    sent = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=1, choices=INVITE_STATUS)
    confirmation_key = models.CharField(max_length=40)
    
    objects = JoinInvitationManager()


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
    
    def accept(self):
        friendship = Friendship(to_user=self.to_user, from_user=self.from_user)
        friendship.save()
        self.status = 5
        self.save()
        if notification:
            notification.create(self.from_user, "friends_accept", "%s has accepted your friend request.", [self.to_user])
            notification.create(self.to_user, "friends_accept_sent", "You accepted %s's friend request.", [self.from_user])
            for user in friend_set_for(self.to_user) | friend_set_for(self.from_user):
                if user != self.to_user and user != self.from_user:
                    notification.create(user, "friends_otherconnect", "%s and %s are now friends", [self.from_user, self.to_user])
