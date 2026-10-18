"""Native digital-copper exclusion against an OEM ADC body, never a silk inset.

Configuration explicitly selects the part and digital nets. The package catalog
sets an independently reviewed minimum envelope so reducing a project dimension
cannot silently weaken the guard. This is a layout constraint, not ADC noise or
assembly qualification. pcbnew is imported only when auditing native geometry.
"""
import math
import re


PACKAGES = {
    "ADI_ST-64-2": {
        "mpns": ("AD7606C-16BSTZ", "AD7606C-16BSTZ-RL"),
        "footprints": ("Package_QFP:LQFP-64_10x10mm_P0.5mm",),
        "nominal_body_mm": (10.0, 10.0),
        "maximum_body_mm": (10.2, 10.2),
        "source": "https://www.analog.com/media/en/technical-documentation/data-sheets/ad7606c-16.pdf",
        "drawing": "Rev A, page 80, Figure 127 / ST-64-2",
        "internal_digital_nets": ("Net-(U6B-SCLK)",),
    },
    "TI_PM0064A": {
        "mpns": ("ADS8588SIPM", "ADS8588SIPMR"),
        "footprints": ("Package_QFP:LQFP-64_10x10mm_P0.5mm",),
        "nominal_body_mm": (10.0, 10.0),
        "maximum_body_mm": (10.2, 10.2),
        "source": "https://www.ti.com/lit/ds/symlink/ads8588s.pdf",
        "drawing": "Rev A, package page 59 / PM0064A, 4215162/A 03/2017",
        "internal_digital_nets": (),
        # Historical nominal-body native keepout is additive to the independent
        # maximum-body shape audit below. This exact rule grants no clearance
        # exception and must not be confused with an internal-pad rule.
        "native_body_rule": '''(rule "ADS8588S U6 no digital under body"
  (condition "A.intersectsArea('ADS8588S U6 body signal exclusion') && !(A.NetName == '/GND' || A.NetName == '/VA_5V' || A.NetName == '/VIO_3V3' || A.NetName == '/VBUS_ADC' || A.NetName == 'Net-(U4-OUT)')")
  (constraint disallow track via))''',
    },
}


def classify_native_body_rules(text):
    """Return only exactly reviewed additive native rules, plus diagnostics.

    Optional because older source rule sets predate this keepout. Whitespace
    between tokens may vary; quoted conditions, all atoms and child forms must
    match exactly. Duplicates, extra exceptions/constraints, layer selectors and
    severity overrides are rejected. Unknown rules remain with their caller.
    This classifies rule text; it does not validate its area's geometry or waive
    the separate OEM maximum-body copper audit.
    """
    from pcbtools.kicad import extract_forms, head_string

    def tokens(value):
        return re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()"]+', value)

    rules = extract_forms(text, "rule")
    accepted, errors = [], []
    for package in PACKAGES.values():
        reviewed = package.get("native_body_rule")
        if reviewed is None:
            continue
        name = head_string(reviewed, "rule")
        matches = [r for r in rules if head_string(r.text, "rule") == name]
        if len(matches) > 1:
            errors.append(name + ": duplicate native ADC body rule")
        elif matches:
            if tokens(matches[0].text) != tokens(reviewed):
                errors.append(name + ": differs from the exact reviewed native ADC body rule")
            else:
                accepted.append(matches[0])
    return accepted, errors


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _digital_name(name, package):
    return (name.rsplit("/", 1)[-1].startswith(("ADC5_", "ADC_"))
            or name in package["internal_digital_nets"])


def validate_config(config):
    """Fail closed on an absent, ambiguous or weakened project-selected policy."""
    fields = {"reference", "mpn", "package", "body_size_mm", "digital_nets",
              "forbidden_routing_layers", "minimum_track_width_mm"}
    if not isinstance(config, dict) or set(config) != fields:
        return ["ADC body exclusion requires the complete explicit configuration"]
    errors = []
    if not isinstance(config["reference"], str) or not config["reference"].strip():
        errors.append("ADC reference must be explicit")
    package = PACKAGES.get(config["package"]) if isinstance(config["package"], str) else None
    if package is None:
        errors.append("ADC package has no independently reviewed OEM body")
    elif config["mpn"] not in package["mpns"]:
        errors.append("ADC exact MPN does not match the selected OEM package")
    body = config["body_size_mm"]
    if (not isinstance(body, list) or len(body) != 2
            or any(not _number(v) or v <= 0 for v in body)):
        errors.append("ADC body_size_mm must contain two finite positive dimensions")
    elif package and any(v < minimum for v, minimum in zip(body, package["maximum_body_mm"])):
        errors.append("ADC body cannot shrink below the OEM maximum molded body (10.2 mm)")
    nets = config["digital_nets"]
    if (not isinstance(nets, list) or not nets
            or any(not isinstance(n, str) or not n or any(c in n for c in "*?[]") for n in nets)
            or len(set(nets)) != len(nets)):
        errors.append("ADC digital_nets must be a nonempty unique exact-name list")
    elif package and any(not _digital_name(n, package) for n in nets):
        errors.append("ADC digital_nets contains a name outside the selected digital interface")
    layers = config["forbidden_routing_layers"]
    if (not isinstance(layers, list) or "In1.Cu" not in layers
            or any(not isinstance(v, str) or not v for v in layers)):
        errors.append("ADC digital routing must remain forbidden on In1.Cu")
    width = config["minimum_track_width_mm"]
    if not _number(width) or width < 0.2:
        errors.append("ADC digital track minimum must be at least 0.2 mm")
    return errors


def audit(board, config):
    """Return native evidence and one error per offending object/configuration.

    Every selected track uses its actual native capsule/arc envelope on its
    copper layer. Vias use the native effective copper shape on every enabled
    copper layer they span; a through-via's mere In1 crossing is not an In1
    signal trace. No pad escape, group membership or clearance-rule override
    exempts copper from this body exclusion.
    """
    report = {"status": "FAIL", "violations": [], "checked_objects": 0}
    errors = validate_config(config)
    if errors:
        return report, errors
    import pcbnew as p

    package = PACKAGES[config["package"]]
    footprints = [f for f in board.GetFootprints() if f.GetReference() == config["reference"]]
    if len(footprints) != 1:
        return report, ["ADC exclusion requires exactly one " + config["reference"]]
    footprint = footprints[0]
    if footprint.GetValue() != config["mpn"]:
        errors.append("ADC native footprint value differs from the exact selected MPN")
    if footprint.GetFPIDAsString() not in package["footprints"]:
        errors.append("ADC native footprint ID differs from the reviewed package")

    actual_nets = {n.GetNetname() for n in board.GetNetsByNetcode().values() if n.GetNetname()}
    selected = set(config["digital_nets"])
    discovered = {n for n in actual_nets if _digital_name(n, package)}
    missing = discovered - selected
    unknown = selected - actual_nets
    if missing:
        errors.append("ADC digital net selection omits native nets: " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("ADC selected digital nets absent from native board: " + ", ".join(sorted(unknown)))
    # Report an omitted net's intrusion as well; omission cannot conceal copper.
    selected |= discovered

    centre = footprint.GetPosition()
    radians = math.radians(footprint.GetOrientationDegrees())
    cosine, sine = math.cos(radians), math.sin(radians)
    half_x, half_y = (p.FromMM(v) / 2 for v in config["body_size_mm"])
    polygon = p.SHAPE_POLY_SET()
    polygon.NewOutline()
    corners = []
    for x, y in [(-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y)]:
        # KiCad's positive footprint angle is counterclockwise in screen Y-down.
        world_x = round(centre.x + cosine * x + sine * y)
        world_y = round(centre.y - sine * x + cosine * y)
        polygon.Append(world_x, world_y)
        corners.append([p.ToMM(world_x), p.ToMM(world_y)])

    enabled = list(board.GetEnabledLayers().CuStack())
    forbidden = set(config["forbidden_routing_layers"])
    known_layers = {board.GetLayerName(layer) for layer in enabled}
    if forbidden - known_layers:
        errors.append("ADC forbidden layer is not enabled: " + ", ".join(sorted(forbidden - known_layers)))
    report.update(reference=config["reference"], mpn=config["mpn"], package=config["package"],
                  body_size_mm=list(config["body_size_mm"]), body_corners_mm=corners,
                  body_pose={"xy_mm": [p.ToMM(centre.x), p.ToMM(centre.y)],
                             "rotation_deg": footprint.GetOrientationDegrees()},
                  OEM_source=package["source"], OEM_drawing=package["drawing"],
                  body_policy="Maximum molded body; no inset. Separate mechanical mold-flash/assembly envelope review remains required.",
                  digital_nets=sorted(selected), minimum_track_width_mm=config["minimum_track_width_mm"],
                  forbidden_routing_layers=sorted(forbidden))
    for item in board.GetTracks():
        if item.GetNetname() not in selected:
            continue
        report["checked_objects"] += 1
        via = isinstance(item, p.PCB_VIA)
        layers = [layer for layer in enabled if item.IsOnLayer(layer)] if via else [item.GetLayer()]
        reasons = []
        try:
            collision = any(item.GetEffectiveShape(layer).Collide(polygon) for layer in layers)
        except (TypeError, RuntimeError) as exc:
            reasons.append("unsupported_native_geometry:" + type(exc).__name__)
        else:
            if collision:
                reasons.append("body_intrusion")
        if not via:
            if board.GetLayerName(item.GetLayer()) in forbidden:
                reasons.append("forbidden_layer")
            if item.GetWidth() < p.FromMM(config["minimum_track_width_mm"]):
                reasons.append("undersized_width")
        if not reasons:
            continue
        row = {"uuid": item.m_Uuid.AsString(), "net": item.GetNetname(),
               "kind": "via" if via else "track", "layers": [board.GetLayerName(l) for l in layers],
               "reasons": reasons}
        if via:
            row.update(xy_mm=[p.ToMM(item.GetPosition().x), p.ToMM(item.GetPosition().y)],
                       copper_diameters_mm={board.GetLayerName(l): p.ToMM(item.GetWidth(l)) for l in layers})
        else:
            row.update(start_mm=[p.ToMM(item.GetStart().x), p.ToMM(item.GetStart().y)],
                       end_mm=[p.ToMM(item.GetEnd().x), p.ToMM(item.GetEnd().y)],
                       width_mm=p.ToMM(item.GetWidth()))
        report["violations"].append(row)
        errors.append(f"{config['reference']} {row['uuid']} {row['net']}: " + ", ".join(reasons))
    report["status"] = "FAIL" if errors else "PASS_STATIC_GEOMETRY_ONLY"
    return report, errors


def check_project(project, board):
    return audit(board, project.parameters.get("adc_body_digital_exclusion"))[1]
