import json
from types import GeneratorType


class FileWriter:

    def _write_streaming_object(self, data_object, output_path):
        """
        Writes a dictionary to JSON, handling generators for specific keys
        by streaming their content as JSON arrays.
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('{\n')  # Start JSON object

            first_key = True
            for key, value in data_object.items():
                if not first_key:
                    f.write(',\n')  # Add comma before next key-value pair
                first_key = False

                f.write(f'  {json.dumps(key)}: ')  # Write key

                if isinstance(value, GeneratorType):
                    # Handle generator: stream as JSON array
                    f.write('[\n')
                    first_item = True
                    for item in value:
                        if not first_item:
                            f.write(',\n')
                        # Indent items for readability
                        f.write(f'    {json.dumps(item, ensure_ascii=False)}')
                        first_item = False
                    f.write('\n  ]')  # Close array
                elif isinstance(value, dict):
                    # Recursively handle nested dicts or write directly
                    # For simplicity, dump nested dicts directly here
                    # Pretty print nested dict
                    json.dump(value, f, ensure_ascii=False, indent=2)
                else:
                    # Handle other types (strings, numbers, lists, etc.)
                    json.dump(value, f, ensure_ascii=False)

            f.write('\n}')
