from django import forms

class PlaceSearchForm(forms.Form):
    query = forms.CharField(label='Search for places')
