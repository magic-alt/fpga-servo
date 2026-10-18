# Native schematic connectivity and visual correction

Scope: presentation repair after the authorized auxiliary-supply and U7 physical-pin ECOs. This is schematic evidence, not PCB or fabrication approval.

ADS8588S previously ignored four ERC categories. All are now enabled using the same severity policy as AD7606C. The resulting 19 four-way warnings were repaired with local visible wiring. Common power, gate, latch and encoder drawings reuse the reviewed AD7606C presentation with ADS8588S instance identities retained. The ADS-specific PL interface and dual-output ADC remain separate; the AD7606C four-output interface was explicitly excluded after a native comparison detected its incompatible connections.

In the ADS ADC sheet, three exactly coincident duplicate wire segments were removed without removing connectivity. The remaining crossings and power-symbol attachments were separated into visible T branches. Every new T branch has a native junction. Wire widths and junction diameters are explicit. Three junction graphics in empty space above the inverter were removed from both projects; none lay on any wire or component pin.

Fresh KiCad 10.0.3 XML comparisons against the post-electrical-ECO inputs gave:

| Project | Components | Nets | Physical pin memberships | Identity, named nets and every physical pin |
| --- | ---: | ---: | ---: | --- |
| ADS8588S | 159 | 135 | 592 | Exact match |
| AD7606C | 181 | 162 | 672 | Exact match |

Both daily schematic checks pass. Both native all-severity ERC reports have **0 errors / 0 warnings / 0 exclusions**, with no ignored checks. Native exports and comparisons are retained locally as `artifacts/dual-servo/hygiene-{ads,ad}-after.xml`, `hygiene-{ads,ad}-erc.json`, and the corresponding `encoder-*-after.xml` inputs. These local artifact names identify executed evidence; they are not portable release artifacts.

The eight-page ADS candidate was exported to PDF and every page viewed, including the ADC/INA supply and return connections, auxiliary feedback and decoupling, latch/reset logic, encoder enables and ESD grounds, and gate/bootstrap loops. Native PDF/PNG exports are under `artifacts/dual-servo/ads-candidate/`. The final added T dot and removal of the three empty-space dots require the final source render in addition to this intermediate visual review. No manufacturing review is marked PASS by this record.

The immutable pre-task source snapshot and prior source manifest remain preserved. The current source manifest records this authorized presentation transition; electrical equivalence was proved before its hashes were refreshed.
