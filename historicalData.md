# Historical Data JSON Schema

Contains historical data for channel(s) over a specific time range.

### Fields

* beginTime *(number)*: the start time of the data range (in milliseconds since the epoch)
* endTime *(number)*: the end time of the data range (in milliseconds since the epoch)
* data *(Object)*: a map from channel id *(string)* to *Object*s containing:
  * t *(Array<number>)*: the times of the data points (in milliseconds since the epoch)
  * v *(Array<?number>)*: the values of the data points, corresponding to elements at the same index of `t`

### Notes

* Values can be `null`, which means data was not available at the corresponding time.
* If `beginTime` comes before a channel's first data point time, it means that channel had no data
  from `beginTime` to its first data point time.
* If `endTime` comes after a channel's last data point time, it means that channel's value remained
  at the last data point value all the way up to `endTime`.

### Example

```json
{
  "beginTime": 1462291200000,
  "endTime": 1462291800000,
  "data": {
    "andysDevice^analog1": {
      "t": [
        1462291209089,
        1462291219099,
        1462291229293,
        1462291239294,
        1462291249294,
        1462291259473,
        1462291269669,
        1462291279677,
        1462291289859,
        1462291299863,
        1462291310049,
        1462291320236,
        1462291330241,
        1462291340440,
        1462291350634,
        1462291360634,
        1462291370640,
        1462291380841,
        1462291390843,
        1462291401040,
        1462291411047,
        1462291421247,
        1462291431263,
        1462291441280,
        1462291451289,
        1462291461475,
        1462291471672,
        1462291481869,
        1462291491871,
        1462291502048,
        1462291512060,
        1462291522070,
        1462291532087,
        1462291542097,
        1462291552294,
        1462291562488,
        1462291572488,
        1462291572689,
        1462291582698,
        1462291592699,
        1462291592901,
        1462291603100
      ],
      "v": [
        4.502362405,
        4.739724907,
        2.6691158470000005,
        0.436898275,
        0.25508869900000003,
        2.3484239560000004,
        4.588216927,
        4.671546316000001,
        2.522658133,
        0.358619152,
        0.34599348700000004,
        2.5479094630000003,
        4.6614457840000005,
        4.573066129000001,
        2.320647493,
        0.262664098,
        0.429322876,
        2.704467709,
        4.732149508,
        4.484686474,
        2.2145919070000004,
        0.19701064000000001,
        0.522752797,
        2.818098694,
        4.777601902000001,
        4.413982750000001,
        2.0555085280000003,
        0.141457714,
        0.6237581170000001,
        3.0125339350000004,
        4.845780493,
        4.315502563000001,
        1.9494529420000002,
        0.12125665,
        0.6969869740000001,
        3.123639787,
        4.878607222,
        4.891232887,
        4.201871578,
        1.7954198290000003,
        1.7449171690000003,
        0.054133925
      ]
    }
  }
}
```