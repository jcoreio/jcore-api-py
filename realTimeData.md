# Real-Time Data JSON Schema

Contains values for one or more channels at a given point in time.

### Fields

* data *(Object)*: a map from channel id *(string)* to value *(number)*
* timestamp *(string)*: the time at which the data was collected, an ISO date string

### Example

```json
{
  "data": {
    "andysDevice.analog1": 1.1641365790000002,
    "andysDevice.analog2": 4.580641528,
    "andysDevice.analog3": 3.8079508300000002,
    "andysDevice.analog4": 0.391445881
  },
  "timestamp": "2016-05-03T15:59:54.632Z"
}
```
