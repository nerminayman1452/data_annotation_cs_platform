from django_filters import rest_framework as filters

from apps.qualification_test.models.exam import Exam


class ExamFilter(filters.FilterSet):
    annotation_type = filters.CharFilter(field_name='annotation_type', lookup_expr='exact')

    class Meta:
        model = Exam
        fields = ['annotation_type']
