import copy


class RawDataCloner:
    """
    Responsible solely for cloning existing Raw Data records (linking to same files).
    """
    @staticmethod
    def clone(source_plan, new_plan, data_model):
        if not data_model:
            return

        source_data_qs = data_model.objects.filter(plan=source_plan)
        new_data_objects = []

        for raw_obj in source_data_qs:
            raw_copy = copy.copy(raw_obj)
            raw_copy.id = None
            raw_copy.pk = None
            raw_copy.plan = new_plan
            # Points to the same file path (Efficient reuse)
            new_data_objects.append(raw_copy)

        if new_data_objects:
            data_model.objects.bulk_create(new_data_objects)