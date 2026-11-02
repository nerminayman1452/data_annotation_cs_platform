from rest_framework import serializers

from apps.planning.models.measure_unit import MeasureUnits

class MeasureUnitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasureUnits
        fields = '__all__'

# class MeasureUnitsListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MeasureUnits
#         fields = ['id', 'title']
