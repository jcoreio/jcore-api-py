# Metadata JSON Schema

Contains metadata for a data channel, like its name and units.

### Fields

* [name] *(string|Array<string>)*: the display name of the channel.  If an array is given, the first 
  element should be the full name and the other elements should be successively shorter abbreviations.
* [min] *(number)*: the lower bound of the display range
* [max] *(number)*: the upper bound of the display range
* [precision] *(number)*: the display precision (number of digits after decimal to show)
* [visibility] *(string)*: indicates the context in which the channel should be viewable by the user.  Possible values:
  * "userViewable": should be viewable at all times
  * "diagnostic": should only be viewable for diagnostic purposes
  * "suppressed": should not be viewable under any circumstances

### Example

```json
{
  "min": 0,
  "max": 5,
  "precision": 1,
  "name": "Analog 1",
  "visibility": "userViewable"
}
```
