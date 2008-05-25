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
    
    def __unicode__(self):
        return "%s (%s's contact)" % (self.email, self.user)
    
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
        
        subject = render_to_string("friends/join_invite_subject.txt")
        email_message = render_to_string("friends/join_invite_message.txt", {
            "user": from_user,
            "message": message,
            "confirmation_key": confirmation_key,
        })
        
        send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, [to_email])        
        return self.create(from_user=from_user, contact=contact, message=message, status="2", confirmation_key=confirmation_key)


class JoinInvitation(models.Model):
    """
    A join invite is an invitation to join the site from a user to a
    contact who is not known to be a user.
    """
    
    from_user = models.ForeignKey(User, related_name="join_from")
    contact = models.ForeignKey(Contact)
    message = models.TextField()
    sent = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=1, choices=INVITE_STATUS)
    confirmation_key = models.CharField(max_length=40)
    
    objects = JoinInvitationManager()
    
    def accept(self, new_user):
        # mark invitation accepted
        self.status = 5
        self.save()
        # auto-create friendship
        friendship = Friendship(to_user=new_user, from_user=self.from_user)
        friendship.save()
        # notify
        if notification:
            notification.send([self.from_user], "join_accept", "%s has joined and is now a friend.", [new_user])
            for user in friend_set_for(new_user) | friend_set_for(self.from_user):
                if user != new_user and user != self.from_user:
                    notification.send([user], "friends_otherconnect", "%s and %s are now friends", [self.from_user, new_user])
    
    class Admin:
        list_display = ('id', 'from_user', 'contact', 'status')


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
            notification.send([self.from_user], "friends_accept", "%s has accepted your friend request.", [self.to_user])
            notification.send([self.to_user], "friends_accept_sent", "You accepted %s's friend request.", [self.from_user])
            for user in friend_set_for(self.to_user) | friend_set_for(self.from_user):
                if user != self.to_user and user != self.from_user:
                    notification.send([user], "friends_otherconnect", "%s and %s are now friends", [self.from_user, self.to_user])
