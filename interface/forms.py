"""
forms.py: describes the strucutre and definition of the forms used in the application
"""
from django import forms
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

# from simulator.staticInst.CityGen import City

from .models import userModel, cityData, cityInstantiation, interventions
from .helper import get_or_none, validate_password

import pandas as pd
import geopandas as gpd

## Registration form for new users
class RegisterForm(forms.Form):
    first_name = forms.CharField(label=_('First Name'), widget=forms.TextInput())
    last_name = forms.CharField(label=_('Last Name'), widget=forms.TextInput())
    works_at = forms.CharField(label=_('Organization'), widget=forms.TextInput())
    email = forms.EmailField(widget=forms.EmailInput())
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput(), help_text=mark_safe("Passwords are to be atleast 7 characters long and containing 1 letter and 1 number"))

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        self._validate_password_strength(self.cleaned_data.get('password'))
        return password

    def clean_email(self):
        email = self.cleaned_data.get("email")
        user = get_or_none(userModel, email=email)
        if user is not None:
            raise ValidationError(_("User with the same email is already registered"))
        return email

    def _validate_password_strength(self, value):
        validate_password(value)

    def save(self, commit=True):
        user = userModel.objects.create_user(
                first_name=self.cleaned_data.get('first_name'),
                last_name=self.cleaned_data.get('last_name'),
                email=self.cleaned_data.get('email'),
                works_at=self.cleaned_data.get('works_at'),
                password=self.cleaned_data.get('password'))
        if commit:
            user.save()
        return user


## User login form
class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': '', 'autofocus': ''}))
    password = forms.CharField(
        widget=forms.PasswordInput()
        )

## Form for users to update their account information
class EditUserForm(forms.ModelForm):
    class Meta:
        model = userModel
        fields = ('first_name', 'last_name')
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'works_at': 'Organization',
        }

## Form to instantiate a new synthetic city in citysim, expects file uploads
class addCityDataForm(forms.ModelForm):
    class Meta:
        model = cityData
        fields = ('city_name', 'target_population', 'city_geojson', 'demographics_csv', 'city_profile_json', 'households_csv', 'employment_csv', 'odmatrix_csv')
        labels = {
            "city_name": mark_safe("Name for the instatiation<br>"),
            "target_population": mark_safe("Enter city target population<br>"),
            "city_geojson": mark_safe("This contains ward boundaries of a city.<br> <small>View Sample <a target='_blank' href='/static/sampleData/common_areas.csv'>City geojson file</a></small><br>"),
            "demographics_csv": mark_safe("This contains demographic data for all wards of the city.<br> <small>View Sample <a target='_blank' href='/static/sampleData/staff.csv'>Demographic detail file</a></small><br>"),
            "city_profile_json": mark_safe("This contains age, household size and school size distribution for the city.<br> <small>View Sample <a target='_blank' href='/static/sampleData/mess.csv'>City profile file</a></small><br>"),
            "households_csv": mark_safe("This contains household data for all wards of the city..<br> <small>View Sample <a target='_blank' href='/static/sampleData/timetable.csv'>Household detail file</a></small><br>"),
            "employment_csv": mark_safe("This contains employment data for all wards of the city.<br> <small>View Sample <a target='_blank' href='/static/sampleData/student.csv'>Employment Detail file</a></small><br>"),
            "odmatrix_csv": mark_safe("This contains origin-destination matrix illustrating commute distance between wards.<br> <small>View Sample <a target='_blank' href='/static/sampleData/classes.csv'>ODMatrix file</a></small><br>")
        }

    def clean(self):
        cleaned_data = super(addCityDataForm, self).clean()
        if self.cleaned_data.get('city_name') is None:
            raise ValidationError({"city_name": "The name of the instantiation should not be empty"})
        # Once Instantiation is done add validations
        try:
            # city_geojson = gpd.read_file(self.cleaned_data.get('city_geojson'))
            demographics_csv = pd.read_csv(self.cleaned_data.get('demographics_csv'))
            # city_profile_json = pd.read_json(self.cleaned_data.get('city_profile_json'))
            households_csv = pd.read_csv(self.cleaned_data.get('households_csv'))
            employment_csv = pd.read_csv(self.cleaned_data.get('employment_csv'))
            odmatrix_csv = pd.read_csv(self.cleaned_data.get('odmatrix_csv'))
        except:
            raise ValidationError(_("Ensure files uploaded in proper format"))
        return cleaned_data


## Form to specify the parameters for launching a simulation
class createSimulationForm(forms.Form):
    simulation_name = forms.CharField(
        label="Simulation name",
        initial="city Simulation",
        required=True,
    )
    num_days = forms.IntegerField(
        label="Number of days to simulate",
        initial="120",
        required=True,
    )#Check if you need Fraction Infected or Num Infected
    num_init_infected = forms.IntegerField(
        label="Initial infection value",
        initial="100",
        required=True,
    )
    num_iterations = forms.IntegerField(
        label="Number of simulation iterations that will be run for the intervention",
        initial="10",
        required=True,
    )
    enable_testing = forms.BooleanField(
        label="Enable testing in the simulation?",
        initial=True,
    )
    testing_capacity = forms.IntegerField(
        label = "Testing Capacity",
        initial = "100",
        required=True
    )
    mean_incubation_period = forms.FloatField(
        label="Mean Incubation Period",
        initial="4.58",
        required=True
    )
    mean_asymp_presimp_period = forms.FloatField(
        label="Mean Asymptomatic or Presymptomatic Period",
        initial="0.5",
        required=True
    )
    mean_symp_period = forms.FloatField(
        label="Mean Symptomatic Period",
        initial="5",
        required=True
    )
    symptomatic_frac = forms.FloatField(
        label="Symptomatic Fraction",
        initial="0.67",
        required=True
    )
    mean_hospital_stay = forms.IntegerField(
        label="mean hospital stay",
        initial="8",
        required=True
    )
    mean_icu_stay = forms.IntegerField(
        label="Mean ICU stay",
        initial="8",
        required=True
    )



    def __init__(self, city_queryset, intv_queryset, *args, **kwargs):
        super(createSimulationForm, self).__init__(*args, **kwargs)
        cityChoices = [(city.id, city.inst_name) for city in city_queryset]
        interventionChoices = [(intv.id, intv.intv_name) for intv in intv_queryset]

        self.fields['instantiatedCity'] = forms.ChoiceField(
                label = 'Select the city instantiation to run the simulations',
                choices=cityChoices,
                required=True,
            )
        self.fields['intvName'] = forms.ChoiceField(
                label = 'Select the intervention to simulate',
                choices=interventionChoices,
                required=True,
            )