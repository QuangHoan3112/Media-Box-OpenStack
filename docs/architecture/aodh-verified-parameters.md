# MediaBox Aodh Verified Parameters

Source: live OpenStack alarm configuration.

No action URLs, tokens or resource-query values
are included in this document.

## mediabox-cpu-high

- state: ok
- enabled: False
- repeat_actions: False
- metric: cpu
- threshold: 210000000000.0
- comparison_operator: gt
- aggregation_method: NOT_AVAILABLE
- granularity: 300
- evaluation_periods: 2
- resource_type: instance
- alarm_action_count: 1

## mediabox-cpu-low

- state: alarm
- enabled: True
- repeat_actions: False
- metric: cpu
- threshold: 60000000000.0
- comparison_operator: lt
- aggregation_method: NOT_AVAILABLE
- granularity: 300
- evaluation_periods: 3
- resource_type: instance
- alarm_action_count: 0
