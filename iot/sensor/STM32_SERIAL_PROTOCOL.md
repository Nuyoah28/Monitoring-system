# STM32 Serial Protocol

The sensor side accepts STM32 environment data over a USB-TTL serial link and uploads the latest valid reading to the server.

## Transport

- Physical link: USB-TTL serial
- Default baud rate: `115200`
- Data bits: `8`
- Parity: `N`
- Stop bits: `1`

## Supported Formats

The Python uploader currently supports two serial formats.

### Format A: legacy temperature/humidity frame

Each frame is one ASCII line:

```text
$IOT,1,ENV,<temperature_c>,<humidity_pct>*<checksum>\r\n
```

Rules:

- `$` starts a frame
- `IOT` is the protocol family tag
- `1` is the protocol version
- `ENV` is the environment message type
- `temperature_c` is a decimal Celsius value, for example `25.4`
- `humidity_pct` is a decimal relative humidity value, for example `48.7`
- `checksum` is a 2-digit uppercase hex XOR of every byte between `$` and `*`

Example:

```text
$IOT,1,ENV,25.4,48.7*36\r\n
```

Validation:

- valid `$...*XX` envelope
- checksum matches
- exactly 5 comma-separated fields
- protocol tag is `IOT`
- version is `1`
- message type is `ENV`
- temperature is within `-40` to `125`
- humidity is within `0` to `100`

### Format B: current GP2Y + MQ9 text output

The uploader also accepts the current STM32 debug-style text output:

```text
GP2Y ADC: 1892 | Voltage: 1.524V | Dust: 0.174mg/m3
MQ9  ADC:  546 | Voltage: 0.440V
```

Parsing rules:

- lines containing `GP2Y ADC:` are parsed as dust sensor output
- the dust numeric value in `mg/m3` is converted to backend `pm25` in `ug/m3`
- lines containing `MQ9 ADC:` are parsed as combustible gas sensor output
- `MQ9` is currently mapped to backend `combustibleGas` by ADC normalization:
  - `combustibleGas = adc / MQ9_ADC_FULL_SCALE * MQ9_PPM_FULL_SCALE`
  - default environment values are `MQ9_ADC_FULL_SCALE=4095` and `MQ9_PPM_FULL_SCALE=100`
- when temperature and humidity are absent, the backend keeps using its configured default values
