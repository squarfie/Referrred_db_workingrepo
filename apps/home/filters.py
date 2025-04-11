import django_filters
from .models import Egasp_Data

class dataFilter(django_filters.FilterSet):
    class Meta:
        model = Egasp_Data
        fields = {  'Egasp_Id': ['exact'], 
                    'Laboratory': ['icontains'],
                    'Clinic':['icontains'],
                    'Consult_Date':['icontains'],
                    'Consult_Type':['icontains'],
                    'Uic_Ptid':['exact'], 
                    'Clinic_Code':['icontains'], 
                    'First_Name':['icontains'], 
                    'Last_Name':['icontains'], 
                    'Birthdate':['icontains'], 
                    'Sex':['icontains'],
                    'Date_of_Entry':['exact']
                    }
        order_by =['Date_of_Entry']
