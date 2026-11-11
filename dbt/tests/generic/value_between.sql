{#
  Custom generic test: fails for every row whose value falls outside [min_value, max_value].
  Usage in YAML:
    data_tests:
      - value_between:
          arguments: {min_value: 0, max_value: 100}
#}
{% test value_between(model, column_name, min_value, max_value) %}

select {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and ({{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }})

{% endtest %}
