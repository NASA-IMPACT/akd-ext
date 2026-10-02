# GeoUI Protocol — v1.0.0

Application-agnostic intent schema for geospatial-visualization UIs.
Decouples agent reasoning from app-specific rendering: agents speak only
`GeoIntent`; conforming applications provide adapters that translate
`GeoIntent` to/from their native state representation.

## Design principles

Inspired by [STAC](https://stacspec.org/):

1. **Tiny required core.** Only `viewport`, `time`, `layers` and two
   protocol housekeeping fields. Everything else is opt-in.
2. **URI-identified extensions.** `geoui_extensions` is an array of URIs;
   each URI dereferences to the JSON Schema defining that extension's
   fields and validation rules.
3. **Namespaced field prefixes.** Extension fields use
   `"<prefix>:<field>"` (e.g. `"compare:layers"`). Core fields are
   unprefixed; the unprefixed namespace is reserved for core forever.
4. **Layered validation.** Core schema always validates. Each declared
   extension validates additionally. Composition matches STAC's `allOf`
   pattern.
5. **Independent versioning.** Major version lives in the URI path
   (`/v1.0.0`). Minor/patch must be additive or clarifying only.
6. **Conformance vs. extension declarations.** A document's
   `geoui_extensions` says "this document uses these extensions." A
   server's `conformsTo` (out of scope here) says "this app understands
   these extensions." Clients negotiate accordingly.

## Required core

| Field              | Type                       | Required | Notes                                                    |
| ------------------ | -------------------------- | -------- | -------------------------------------------------------- |
| `geoui_version`    | `string`                   | yes      | Protocol version. `"1.0.0"` for this spec.               |
| `geoui_extensions` | `string[]`                 | yes      | URIs of extensions the document uses. May be empty.      |
| `viewport`         | `Viewport`                 | yes      | Spatial extent + CRS.                                    |
| `time`             | `TimeWindow \| null`       | no       | Instant or range. `null` means "app default time."       |
| `layers`           | `LayerRef[]`               | yes      | Render-order layer stack. May be empty.                  |

### `Viewport`

| Field  | Type                          | Required | Notes                                              |
| ------ | ----------------------------- | -------- | -------------------------------------------------- |
| `bbox` | `number[4] \| null`           | no       | `[west, south, east, north]` in `crs` units.       |
| `crs`  | `string`                      | yes      | EPSG-style identifier. Default `"EPSG:4326"`.      |

### `TimeWindow`

Exactly one of:

- `instant`: a single point in time (string / date / datetime), OR
- `{ start, end }`: a closed range; both required if either is present.

All fields `null` is allowed and means "app default time."

### `LayerRef`

| Field     | Type              | Required | Notes                                                |
| --------- | ----------------- | -------- | ---------------------------------------------------- |
| `id`      | `string`          | yes      | App-resolvable layer identifier.                     |
| `visible` | `boolean`         | no       | Default `true`.                                      |
| `opacity` | `number[0,1]`     | no       | `null` means app default opacity.                    |

Additional per-layer hints (palette, min/max, style, etc.) belong in
extensions, expressed as namespaced extra keys on the LayerRef object.

## Extension mechanics

A document declares the extensions it uses by listing their URIs in
`geoui_extensions`. Each URI MUST resolve to a JSON Schema that:

- Defines the `"<prefix>:*"` fields the extension contributes.
- Specifies which extension fields are required (given the extension is
  declared) and which are optional.
- May tighten constraints on core fields (e.g. an extension may require
  `time` to be a range).

Validators combine the core schema with all declared extension schemas
(`allOf`) and validate against the result. Documents that declare an
extension MUST satisfy its constraints; documents that omit an extension
MUST NOT use its fields.

Example URIs (not yet hosted; placeholders for this spec):

- `https://geoui.org/ext/compare/v1.0.0`
- `https://geoui.org/ext/chart/v1.0.0`
- `https://geoui.org/ext/raster-styling/v1.0.0`

## Example — core only

```json
{
  "geoui_version": "1.0.0",
  "geoui_extensions": [],
  "viewport": {
    "bbox": [-125, 32, -114, 42],
    "crs": "EPSG:4326"
  },
  "time": { "instant": "2025-09-15" },
  "layers": [
    { "id": "MODIS_Terra_CorrectedReflectance_TrueColor" },
    { "id": "MODIS_Aqua_Aerosol", "opacity": 0.8 }
  ]
}
```

## Example — with extensions

```json
{
  "geoui_version": "1.0.0",
  "geoui_extensions": [
    "https://geoui.org/ext/compare/v1.0.0",
    "https://geoui.org/ext/chart/v1.0.0",
    "https://geoui.org/ext/raster-styling/v1.0.0"
  ],
  "viewport": { "bbox": [-125, 32, -114, 42], "crs": "EPSG:4326" },
  "time": { "instant": "2025-09-15" },
  "layers": [
    {
      "id": "MODIS_Aqua_Aerosol",
      "opacity": 0.8,
      "raster-styling:palettes": ["red_1"],
      "raster-styling:min": 0,
      "raster-styling:max": 2,
      "raster-styling:squash": true
    }
  ],
  "compare:layers": [{ "id": "MODIS_Aqua_Aerosol" }],
  "compare:time":   { "instant": "2025-09-14" },
  "compare:mode":   "swipe",
  "compare:value":  60,
  "chart:layer":    "MODIS_Aqua_Aerosol",
  "chart:area":     [-125, 32, -114, 42],
  "chart:time":     { "start": "2025-09-01", "end": "2025-09-30" },
  "chart:autoload": true
}
```

## Versioning rules

- Major version is in the URI path: `/v1.0.0/`, `/v2.0.0/`.
- Minor/patch changes must be additive or clarifying only.
- A new required field, a removed field, or a changed field type
  constitutes a breaking change and must increment the major version.
- Core and each extension version independently.

## What counts as a breaking change

- Adding a required core or extension field.
- Removing a previously-required field.
- Changing a field's type or its value space.
- Tightening a constraint such that previously-valid documents become
  invalid.
- Renaming a field or changing its namespace prefix.

Additive changes (new optional fields, new extensions, broadened
constraints) are not breaking.

## Out of scope for v1.0.0

- Server-side `conformsTo` / capability discovery (will land alongside
  the first behavior-affecting extension).
- A canonical extension registry. URIs are the source of truth; a
  community index is welcome but not required.
- Animation, time-series scrubbing, multi-pane layouts. These are
  candidates for future extensions.
