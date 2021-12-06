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
        if self.individuals_json:
            return 'os.path.splitext(self.individuals_json.path)[0]'
        else:
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


## defintion for storing user-defined custom interventions
class interventions(models.Model):
    intv_name = models.CharField(max_length=30, null=True)
    intv_json = models.JSONField(null=True)
    created_by = models.ForeignKey(userModel, null=True, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    @classmethod
    def get_count_by(self, user):
        if not user.is_staff:
            return self.objects.filter(created_by=user).count()
        else:
            return self.objects.count()

    @classmethod
    def get_topk_latest(self, user, k=5):
        if not user.is_staff:
            return self.objects.filter(created_by=user).reverse()[:k]
        else:
            return self.objects.reverse()[:k]

    @classmethod
    def get_all(self, user):
        if not user.is_staff:
            return self.objects.filter(created_by=user).all()
        else:
            return self.objects.all()

    def __str__(self):
        return self.intv_name


## definition for storing different testing protocols
class testingParams(models.Model):
    testing_protocol_name = models.CharField(max_length=30, null=True)
    testing_protocol_file = models.JSONField(null=True)
    created_by = models.ForeignKey(userModel, null=True, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True)

    @classmethod
    def get_count_by(self, user):
        if not user.is_staff:
            return self.objects.filter(created_by=user).count()
        else:
            return self.objects.count()

    def __str__(self):
        return self.testing_protocol_name


## defintion for storing the simulation parameters
class simulationParams(models.Model):
    STATUS_CHOICE = (
            ('Created', 'Created'),
            ('Running', 'Running'),
            ('Complete', 'Complete'),
            ('Error', 'Error'),
        )
    simulation_name = models.CharField(max_length=30, null=True)
    days_to_simulate = models.PositiveSmallIntegerField(default=100, null=True)
    init_infected_seed = models.PositiveSmallIntegerField(default=200, null=True)
    simulation_iterations = models.PositiveSmallIntegerField(default=10, null=True)
    city_instantiation = models.ForeignKey(cityInstantiation, null=True, on_delete=models.SET_NULL)
    intervention = models.ForeignKey(interventions, null=True, on_delete=models.SET_NULL)
    # enable_testing = models.BooleanField(default=True)
    output_directory = models.CharField(max_length=500, null=True)
    testing_capacity = models.PositiveSmallIntegerField(default=100, null=True)
    # testing_protocol = models.ForeignKey(testingParams, blank=True, null=True, on_delete=models.SET_NULL)
    mean_incubation_period = models.DecimalField(default=4.58, max_digits=9, decimal_places=5, null=True)
    mean_asymp_presimp_period = models.DecimalField(default=0.5, max_digits=9, decimal_places=5, null=True)
    mean_symp_period = models.DecimalField(default=5, max_digits=9, decimal_places=5, null=True)
    symptomatic_frac = models.DecimalField(default=0.67, max_digits=9, decimal_places=5, null=True)
    mean_hospital_stay = models.PositiveSmallIntegerField(default=8, null=True)
    mean_icu_stay = models.PositiveSmallIntegerField(default=8, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICE, default='Created', null=True)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    updated_on = models.DateTimeField(auto_now_add=True, null=True)
    completed_at = models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(userModel, null=True, on_delete=models.CASCADE)

    @property
    def get_status(self):
        try:
            status = simulationParams.STATUS_CHOICE[self.status][1]
        except:
            status = simulationParams.STATUS_CHOICE['Error'][1]
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
            return self.objects.count()

    @classmethod
    def get_all(self, user):
        if not user.is_staff:
            return self.objects.filter(created_by=user).all()
        else:
            return self.objects.all()

    @classmethod
    def get_latest(self, user):
        if not user.is_staff:
            return self.objects.filter(created_by=user).order_by('-id')[0]
        else:
            return self.objects.order_by('-id')[0]

    def __str__(self):
        return self.simulation_name

## definiton for storing the aggregated results for a simulation
class simulationResults(models.Model):
    simulation_id = models.OneToOneField(simulationParams, primary_key=True, on_delete=models.CASCADE)
    agg_results = models.JSONField(null=True)
    status = models.CharField(max_length=3, default='NA')
    completed_at = models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(userModel, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.simulation_id.simulation_name