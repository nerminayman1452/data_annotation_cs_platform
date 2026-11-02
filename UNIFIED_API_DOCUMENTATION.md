# Unified Plan Task Generation API

## Overview
A single unified API endpoint replaces the previous separate `GenerateImagePlanTasksAPIView` and `GenerateTextPlanTasksAPIView` views. The API now accepts a `plan_type` parameter to determine which plan model and source data builder to use.

## Endpoints
- **Image annotation**: `POST /image-annotation/plans/generate-tasks/`
- **Text annotation**: `POST /text-annotation/plans/generate-tasks/`

Both endpoints use the same unified view: `GeneratePlanTasksAPIView`

## Request Format
```json
{
  "plan_id": 123,
  "plan_type": "image"  // or "text"
}
```

## Response Format
```json
{
  "plan_id": 123,
  "plan_type": "image",
  "tasks_created": 42,
  "status": "success",
  "note": "New tasks generated successfully."
}
```

## Supported Plan Types
- `"text"` - TextPlan with TextSourceDataBuilder
- `"image"` - ImagePlan with ImageSourceDataBuilder

## Architecture

### Plan Registry (`apps/tasks/helpers/plan_registry.py`)
Centralized registry that maps plan types to their models and source data builders:
- Maps plan type strings to (model_class, builder_class) tuples
- Provides validation and error handling
- Easy to extend with new plan types

**Example of adding a new plan type:**
```python
from apps.custom_annotation.models import CustomPlan
from apps.tasks.helpers.source_data_builder import CustomSourceDataBuilder

PlanRegistry.register("custom", CustomPlan, CustomSourceDataBuilder)
```

### Unified View (`apps/tasks/views/task_generator.py`)
`GeneratePlanTasksAPIView` - Single endpoint that:
1. Validates request with `GenerateTasksSerializer`
2. Looks up plan type in registry
3. Retrieves the plan by ID using the correct model
4. Generates tasks using the correct source data builder
5. Returns consistent response format

### Enhanced Serializer (`apps/text_annotation/serializers/plan_task.py`)
`GenerateTasksSerializer` now includes:
- `plan_id` (integer)
- `plan_type` (choice field: "text" or "image")

## Benefits
1. **DRY Principle**: Single implementation instead of separate views
2. **Extensibility**: Add new plan types by registering in `PlanRegistry`
3. **Consistency**: Unified response format and error handling
4. **Maintainability**: Changes only needed in one place
5. **Type Safety**: Plan type validation at serialization layer

## Migration from Old API
Old endpoints:
- `POST /image-annotation/image-tasks/generate/` → Use new endpoint with `plan_type: "image"`
- `POST /text-annotation/text-tasks/generate/` → Use new endpoint with `plan_type: "text"`

Both old view classes have been marked as deprecated and the actual implementations have been removed.

## Error Handling
- **400 Bad Request**: Invalid plan_type not in registry
- **404 Not Found**: Plan ID doesn't exist in the database
- **500 Internal Server Error**: Task generation service error with details
