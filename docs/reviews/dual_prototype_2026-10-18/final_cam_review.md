# Independent final CAM review

2026-10-19. Read-only agent review of the locally generated **final-review-v3** packages, input commit `9f9b70cfb622c29919243b8b49e4078a175a1bf9`. This is not a human manufacturing signature, manufacturer process acceptance, order, or fabrication release. No source CAD, rules, tooling, configuration, or staging was changed during this review.

Both v3 packages were independently reparsed and rendered. No additional reproducible CAM defect was identified in this scope. Evidence root: `artifacts/dual-servo/final-cam-independent-v3`; machine-readable review: `docs/reviews/dual_prototype_2026-10-18/final_cam_review.json`.

| Actual source | Canonical board SHA-256 | PTH | NPTH | Vias / component holes | Closed outline |
| --- | --- | ---: | ---: | --- | --- |
| AD7606C | `dc0fb0a39529daa627db700bc2f53dd435f776633b9bd93aa8b1f0053b5f2134` | 594 | 0 | 511 / 83 | 130 × 95 mm |
| ADS8588S | `e68d2fb9d8196d84c968dab1cee8396ff281fe9f6e09dacda5a4bb312c63d226` | 551 | 0 | 468 / 83 | 130 × 95 mm |

## AD7606C

Canonical PCB SHA-256: `dc0fb0a39529daa627db700bc2f53dd435f776633b9bd93aa8b1f0053b5f2134`.
Package: `artifacts/dual-servo/final-review-v3/ad7606c`.

Independent Gerbonara 1.6.3 parsing and rendering completed for all eleven actual Gerbers: F/B copper, In1/In2 copper, F/B mask, F/B paste, F/B silkscreen, and Edge.Cuts. All eleven v3 layer images and the drill image are pixel-for-pixel identical to the preceding independently rendered, agent-inspected images, verified by exact RGB comparison (`ad-pixel-equality.json`). That earlier visual inspection covered every layer, the drill image, and enlarged ADC, driver/power, input, and auxiliary regions. The In1 image has a ground plane with pad/via anti-pads; the fresh whole-board native guard reports no foreign tracks, arcs, or copper zones, including footprint-owned zones. This does not imply a plane without holes or prove its high-frequency impedance.

The four Edge.Cuts lines independently form one closed rectangle: X 2–132 mm, Y 2–97 mm, size 130 × 95 mm. Every one of the 594 PTH hits matches the native inventory in XY and diameter (export coordinate tolerance 0.000501 mm, diameter tolerance 0.000001 mm): 511 electrical vias and 83 component holes. NPTH has zero hits, consistent with the actual board. H1–H4 are plated 3.2 mm mounting holes, not missing NPTH holes. Excellon headers identify the PTH and NPTH roles separately.

Fresh actual-U12 Gerber/Excellon checks find all four 0.3 mm thermal holes at (57.9,11.3), (62.1,11.3), (57.9,12.7), and (62.1,12.7) mm. Their drill disks are 0.25 mm from the complete F.Mask and F.Paste opening unions; their 0.6 mm annular disks are 0.10 mm from those unions. No drill-disk/opening intersection occurs. The central mask and paste opening areas are each 9.2118537845 mm². This verifies exported geometry; stencil transfer, voiding, coating registration, and soldering remain untested. The reused helper image retains an old “process snapshot” subtitle; its provenance JSON and input hashes identify the current final exports.

Native all-via versus component-hole geometry finds zero hole-edge separations below 0.45 mm, including oval-drill orientation handling. This comparison does not establish vendor acceptance of the specified filled/planarized/copper-capped via process. The electrical via process selection remains explicit in the hole inventory; ordinary open vias cannot be silently substituted.

Package binding was independently rechecked: all 21 recorded native output hashes, all 208 current source hashes, and all 208 frozen input hashes match. The frozen PCB hash is `5a5ce9b9b855640d52b362402146a2f2bfa12b43b12cfa359e4064ea617d2188`; its complete board text equals the canonical board after normalizing only quoted model filenames. Copper, footprints, zones, groups, rules, and model transforms are therefore unchanged by snapshot rebasing.

Current evidence under `artifacts/dual-servo/final-cam-independent-v3/` (the preceding `final-cam-independent` files remain historical evidence):

- `ad7606c/independent_cam_manifest.json`: every Gerber/drill hash, object count, parsed board outline, and exact native-hole matching.
- `ad7606c/{copper,mask-paste,silk-edge-drill}-sheet.png` and `{adc,driver-power,input,aux}-detail.png`: agent-inspected layer sheets and enlargements; original independent SVG/PNG files are also retained.
- `ad-u12/u12_mask_paste_union_review.json`, `actual_native_input_provenance.json`, and `u12-cam-union.png`: actual aperture-union and thermal-hole proof.
- `ad-hole-separation.json`: current canonical native hole separation scan.
- `ad7606c-package-binding.json`: current source/snapshot/output binding.

The parser emits the recorded KiCad Excellon `G90 header statement found after end of header` warnings. All actual hits were parsed and matched individually; these warnings were not treated as omitted geometry.

## ADS8588S

Canonical PCB SHA-256: `e68d2fb9d8196d84c968dab1cee8396ff281fe9f6e09dacda5a4bb312c63d226`.
Package: `artifacts/dual-servo/final-review-v3/ads8588s`.

All eleven layers and both Excellon roles were independently reparsed. The agent personally inspected the new copper, mask, paste, silkscreen, outline, and drill images, plus enlarged ADC, driver/power, input, auxiliary, and repaired VA5 bridge regions. The old long In1 route is absent. A fresh whole-board native guard finds no foreign In1 tracks, arcs, or copper zones. The local F.Cu VA5 bridge lies between (30.2,28.05) and (27.2,31.7) mm; the native repair record describes nine 0.5 mm-wide segments totaling 4.8926 mm with two 0.5/0.3 mm vias. The actual independent F/B copper images show the bridge and its local endpoints, and no added mask/paste opening at its covered via sites. This is a geometric review, not a noise measurement or vendor process approval.

All 551 PTH hits match the current native inventory individually in XY and diameter using the same tolerances as AD: 468 electrical vias plus 83 component holes. NPTH is empty, as expected. H1–H4 remain PTH mounting holes. The outline is the same closed four-line 130 × 95 mm rectangle. The fresh via/component-hole scan finds zero edge separations below 0.45 mm. The actual U12 four-hole mask/paste-union measurements match the AD values above: 0.25 mm hole-to-opening and 0.10 mm annulus-to-opening, zero intersection.

All 21 recorded output hashes, all 100 current source hashes, and all 100 frozen input hashes match. Frozen PCB SHA-256: `5e5219ffba7c0c782a54f8f3ed9fd28e1a7aad6cb5f73d667bce068dbc38ff3b`; complete source/snapshot board text matches after normalizing only model filenames. Evidence: `ads8588s/independent_cam_manifest.json`, layer sheets and detail images, `ads-u12/`, `ads-hole-separation.json`, `ads8588s-package-binding.json`, and `wholeboard-ground-proof.json` under the current evidence root.

## Superseded ADS package

The initial package bound to `a4b8158240253f0aefcf333f37987b9d69afbe30419be8a3440ff2483388c666` was parsed and rendered, but is **SUPERSEDED / NOT FINAL ACCEPTANCE**. Its In1 image contains a visible non-ground route. Its old 554-PTH/zero-NPTH results and `ads-*` artifacts under `final-cam-independent` remain historical evidence only. The e68d2f/v3 review above supersedes those results.

## Remaining acceptance

Human CAM/assembly approval, manufacturer acceptance of the exact stackup and controlled via process, and dynamic electrical/thermal/EMC/ESD tests remain OPEN / NOT_RUN. This review does not alter `prototype_ready` or `pcb_release`, and performs no upload or manufacturing order.
