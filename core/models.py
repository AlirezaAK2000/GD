from django.db import models
from django.conf.settings import AUTH_MODEL_USER

PAYMENT_STATES = [
    ('CM' , 'COMPLETED'),
    ('PN' , 'PENDING'),
    ('RJ' , 'REJECTED')
]

SERVICE_TYPE = [
    ('WS' , 'WORKSHOP'),
    ('TK'  , 'TALK'),
    ('CP' , 'COMPETITION')
]

LEVEL = [
    ('BG' , 'BEGINNER'),
    ('IM' , 'INTERMEDIATE'),
    ('EX' , 'EXPERT')
]


class Presenter(models.Model):
    first_name = models.CharField(max_length=30,blank=False)
    last_name = models.CharField(max_length=30 , blank=False)
    email = models.EmailField(blank=True , null=True)
    descriptions = models.TextField()
    linked_in = models.URLField(blank=True)


    class Meta:
        unique_together = ('first_name' , 'last_name')

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

class Talk(models.Model):
    title = models.CharField(max_length=100 , blank=False)
    date = models.DateTimeField(blank=False)
    content = models.TextField(blank=False)
    capacity = models.IntegerField(blank=False)
    participant_count = models.IntegerField()
    presenter = models.ForeignKey(Presenter, on_delete=models.PROTECT , null=True)
    presentation_link = models.URLField(blank=True)
    level = models.CharField(choices=LEVEL , default='BG')

    def get_total_services(self):
        return self.services.count()

    def get_services(self):
        return self.services.all()

    def get_remain_capacity(self):
        registered_user=self.services.filter(payment__state='CM').count()
        return self.capacity -int(registered_user)

    def __str__(self):
        return self.title


class Workshop(models.Model):
    title = models.CharField(max_length=100 , blank=False) 
    date = models.DateTimeField(blank=False)
    content = models.TextField(blank=False)
    capacity = models.IntegerField(blank=False)
    participant_count = models.IntegerField()
    presenter = models.ForeignKey(Presenter , on_delete=models.PROTECT , null=True)
    presentation_link = models.URLField(blank=True)
    level = models.CharField(choices=LEVEL , default='BG')

    def get_total_services(self):
        return self.services.count()

    def get_services(self):
        return self.services.all()

    def get_remain_capacity(self):
        registered_user=self.services.filter(payment__state='CM').count()
        return self.capacity -int(registered_user)

    def __str__(self):
        return self.title

class Competition(models.Model):
    title = models.CharField(max_length=30 , blank=False , unique=True)
    start_date = models.DateTimeField(auto_now=True,blank=False)
    end_date = models.DateTimeField(auto_now=True,blank=False)
    description = models.TextField()

    # overrided for constraints
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError('Start date is after end date')


class EventService(models.Model):
    payment_state = models.CharField(
        max_length=2,
        choices=PAYMENT_STATES,
        default='PN'
    )
    service = models.CharField(
        max_length=2,
        choices=SERVICE_TYPE,
        blank=False
    )
    talk = models.ForeignKey(Talk , blank=True , on_delete=models.CASCADE,related_name='services')
    workshop = models.ForeignKey(Workshop , blank=True , on_delete=models.CASCADE,related_name='services')
    competion = models.ForeignKey(Competition , blank=True , on_delete=models.CASCADE,related_name='services')
    user = models.ForeignKey(AUTH_MODEL_USER, on_delete=models.CASCADE, blank=True,related_name='services')

    def __str__(self):
        return self.user.user_name +'__'+self.service+'__'+self.payment_state
