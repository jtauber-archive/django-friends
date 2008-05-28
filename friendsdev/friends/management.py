from django.dispatch import dispatcher
from django.db.models import signals

try:
    from notification import models as notification
    
    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type("friends_invite", "Invitation Received", "you have received an invitation")
        notification.create_notice_type("friends_invite_sent", "Invitation Sent", "you have sent an invitation")
        notification.create_notice_type("friends_accept", "Acceptance Received", "an invitation you sent has been accepted")
        notification.create_notice_type("friends_accept_sent", "Acceptance Sent", "you have accepted an invitation you received")
        notification.create_notice_type("friends_otherconnect", "Other Connection", "one of your friends has a new connection")
        notification.create_notice_type("join_accept", "Join Invitation Accepted", "an invitation you sent to join this site has been accepted")
    
    dispatcher.connect(create_notice_types, signal=signals.post_syncdb, sender=notification)
except ImportError:
    print "Skipping creation of NoticeTypes as notification app not found"
