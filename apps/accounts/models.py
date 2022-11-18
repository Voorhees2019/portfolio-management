from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import datetime


class UserManager(BaseUserManager):
    """
    Creates and saves a User with the given email, name, password and optional extra info.
    """
    def _create_user(self, email,
                     name,
                     password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()

        if not email:
            raise ValueError(_('The given email must be set'))

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name or '',
            is_staff=is_staff, is_active=True,
            is_superuser=is_superuser,
            date_joined=now,
            last_login=now,
            **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, password=None, **extra_fields):
        return self._create_user(email, name, password, False, False, **extra_fields)

    def create_superuser(
            self, email, name, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email,
        name and password.
        """
        return self._create_user(email, name, password, True, True, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)


class User(AbstractBaseUser, PermissionsMixin):
    """
    A model which implements the authentication model.

    Email and password are required. Other fields are optional.

    Email field are used for logging in.
    """
    email = models.EmailField(_('Email'), max_length=255, unique=True)
    name = models.CharField(_('Full name'), max_length=255)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    email_confirmed = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether the user has verified the email address.'),
    )

    date_joined = models.DateTimeField(_('Date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['name', '-date_joined']

    def get_first_name(self):
        chunks = self.name.split()
        if len(chunks) >= 1:
            return chunks[0]
        else:
            return ''

    @property
    def first_name(self):
        return self.get_first_name()

    def get_last_name(self):
        chunks = self.name.split()
        if len(chunks) >= 2:
            return chunks[1]
        else:
            return ''

    @property
    def last_name(self):
        return self.get_last_name()

    def __str__(self):
        return self.name

    def get_email_md5_hash(self):
        import hashlib
        m = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return m

    def has_usable_password(self) -> bool:
        return super().has_usable_password()
    has_usable_password.boolean = True

    @property
    def days_on_site(self):
        from django.utils.timezone import now
        delta = now() - self.date_joined
        return delta.days


class Company(models.Model):
    name = models.CharField(_('Company name'), max_length=150)
    logo = models.ImageField(_('Company logo'), upload_to='company_logos/')
    founder = models.OneToOneField(User, on_delete=models.CASCADE, related_name='founder_company')
    year_founded = models.IntegerField(validators=[MinValueValidator(1950), MaxValueValidator(datetime.now().year)])
    website = models.URLField(_('Company website'))
    email = models.EmailField(_('Contact email'), max_length=255, unique=True)
    slogan = models.CharField(_('Company slogan'), max_length=255)
    description = models.TextField(_('Description'))

    class Meta:
        verbose_name_plural = 'Companies'

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        """Delete the previous logo from the storage if a new one has been uploaded."""

        try:
            company = Company.objects.get(pk=self.pk)
            if company.logo != self.logo:
                company.logo.delete(save=False)  # `save=False` to prevent a recursive save
        except:
            pass
        super().save(*args, **kwargs)
