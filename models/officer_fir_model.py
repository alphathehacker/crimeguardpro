from mongoengine import Document, StringField, DateTimeField, ReferenceField
from datetime import datetime
from models.officer_model import Officer  # assuming you already have Officer model

class OfficerFIR(Document):
    title = StringField(required=True)
    category = StringField(default="General")
    suspect_name = StringField()
    contact = StringField()
    location = StringField()
    description = StringField()
    priority = StringField(default="High")  # default higher priority
    officer = ReferenceField(Officer, required=True)
    status = StringField(default="Open")
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'officer_firs',
        'ordering': ['-created_at']
    }
