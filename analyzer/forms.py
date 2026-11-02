from django import forms

class DatasetUploadForm(forms.Form):
    file = forms.FileField(label="Upload your CSV or Excel file")