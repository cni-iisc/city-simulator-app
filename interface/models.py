"""
models.py: provides the defintions for the database tables used in the application
"""
import datetime

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .managers import UserManager

class userModel(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    works_at = models.CharField(null=True, blank=True, max_length=110)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    USERNAME_FIELD = 'email'
    objects = UserManager()

    def get_staff(self):
        return self.is_staff

    def get_full_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    def get_short_name(self):
        return self.email

    def __str__(self):
        return self.email


## contains the generated token when a new user registers
class UserRegisterToken(models.Model):
    user = models.OneToOneField(userModel, on_delete=models.CASCADE)
    token = models.CharField(unique=True, max_length=100)

## contains the most-recent generated token set for a user to reset their password
class UserPasswordResetToken(models.Model):
    user = models.OneToOneField(userModel, on_delete=models.CASCADE)
    token = models.CharField(unique=True, max_length=100)

## used for activating a new user.
## Users are being redirect to 'redirect_url' after getting 'name' from a GET parameter.
class RegisterOrigin(models.Model):
    name = models.SlugField()
    redirect_url = models.URLField()

## definition for storing the city data files locations
def set_upload_path(instance, filename):
    return '/'.join(['cityData', f"{ datetime.datetime.today().strftime('%Y%m%d') }", instance.city_name.replace(' ', '_'), filename])

class cityData(models.Model):
    odmatrix_csv = models.FileField(upload_to=set_upload_path, null=True)
    city_geojson = models.FileField(upload_to=set_upload_path, null=True)
    city_profile_json = models.FileField(upload_to=set_upload_path, null=True)
    demographics_csv = models.FileField(upload_to=set_upload_path, null=True)
    employment_csv = models.FileField(upload_to=set_upload_path, null=True)
    households_csv = models.FileField(upload_to=set_upload_path, null=True)
    target_population = models.IntegerField(default=100000, null=True)
    city_name = models.CharField(max_length=20, null=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(userModel, null=True, on_delete=models.CASCADE)

    @classmethod
    def get_all(self, user):
        if not user.is_staff:
            return self.objects.filter(created_by=user).all()
        else:
            return self.objects.all()

    @classmethod
    def get_topk_latest(self, user, k=5):
        if not user.is_staff:
            return self.objects.filter(created_by=user).reverse()[:k]
        else:
            return self.objects.reverse()[:k]

    def __str__(self):
        return self.city_name


## definition for storing the instantiation city's file paths
def set_instantiation_filePath(instance, filename):
    if filename != '':
        return '/'.join(['instantiation', f"{ datetime.datetime.today().strftime('%Y%m%d') }", instance.inst_name.city_name.replace(' ', '_'), filename])
    else:
        return '/'.join(['instantiation', f"{ datetime.datetime.today().strftime('%Y%m%d') }", instance.inst_name.city_name.replace(' ', '_')])

class cityInstantiation(models.Model):
    STATUS_CHOICE = (
            ('Created', 'Created'),
            ('Running', 'Running'),
            ('Complete', 'Complete'),
            ('Error', 'Error'),
        )
    inst_name = models.ForeignKey(cityData, null=True, on_delete=models.CASCADE)
    individuals_json = models.FileField(upload_to=set_instantiation_filePath, null=True)
    houses_json = models.FileField(upload_to=set_instantiation_filePath, null=True)
    workplaces_json = models.FileField(upload_to=set_instantiation_filePath, null=True)
    schools_json = models.FileField(upload_to=set_instantiation_filePath, null=True)
    ward_centre_distance_json = models.FileField(upload_to=set_instantiation_filePath, null=True)
    common_area_json = models.FileField(upload_to=set_instantiation_filePath, null=True)
    fraction_population_json = models.FileField(upload_to=set_instantiation_filePath, null=True)
    # prg_np_random_state_bin = models.FileField(upload_to=set_instantiation_filePath, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICE, default='Created', null=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(userModel, null=True, on_delete=models.CASCADE)

    @property
    def get_inst_path(self):
        # if self.individuals_json:
        #     return 'os.path.splitext(self.individuals_json.path)[0]'
        # else:
        return set_instantiation_filePath(self)

    @property
    def get_status(self):
        try:
            status = cityInstantiation.STATUS_CHOICE[self.status][1]
        except:
            status = cityInstantiation.STATUS_CHOICE['Error'][1]
        return status

    @classmethod
    def get_topk_latest(self, user, k=5):
        if not user.is_staff:
            return self.objects.filter(created_by=user).reverse()[:k]
        else:
            return self.objects.reverse()[:k]

    @classmethod
    def get_count_by(self, user):
        if not user.is_staff:
            return self.objects.filter(created_by=user).count()
        else:
            return self.objects.count()

    @classmethod
    def get_count_by_status(self, user, status):
        if not user.is_staff:
            return self.objects.filter(created_by=user, status=status).count()
        else:
            return self.objects.filter(status=status).count()

    @classmethod
    def get_all(self, user):
        if not user.is_staff:
            return self.objects.filter(created_by=user).all()
        else:
            return self.objects.all()

    @classmethod
    def get_latest(self, user):
        if not user.is_staff:
            return self.objects.filter(created_by=user).order_by('-pk')[0]
        else:
            return self.objects.order_by('-pk')[0]

    def __str__(self):
        return self.inst_name.city_name
