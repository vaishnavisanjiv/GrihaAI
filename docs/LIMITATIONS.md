# Limitations

- The trained model checkpoint and CubiCasa5K data are not bundled. Until a
  checkpoint is trained and evaluated, analysis returns `503`.
- The segmentation model is a compact project baseline. Its predictions,
  512×512 input representation, and component polygons have not yet been
  validated against real plans from the intended region.
- Image-to-real-world scale is unknown unless the user calibrates it from two
  original-image points and a known distance.
- Room components and measurements are unverified model detections. Code checks
  are reported as `NOT_ASSESSED` until the project has a verified, versioned
  NBC and local-authority rule catalog and the evidence required by each rule.
- The project does not currently implement NBC, Maharashtra UDCPR, PMC, or PCMC
  provisions. Reports are preliminary geometry reviews, not compliance
  certificates, building approvals, or professional sign-offs.
- Official source pages identified for future rule-catalog work:
  - [Maharashtra Directorate of Town Planning and Valuation — Acts and Rules](https://dtp.maharashtra.gov.in/acts-rules/)
    lists a consolidated UDCPR copy updated 30 January 2025. Check later
    amendments and Gazette notifications before selecting any rule version.
  - [PMC Building Development](https://www.pmc.gov.in/en/building-development)
    and the [PMC AutoDCR portal](https://autodcr.pmc.gov.in/) are the PMC
    references; [PCMC Building Permission](https://www.pcmcindia.gov.in/building-permission)
    and its [BPAMS portal](https://bldp.pcmcindia.gov.in/BPAMSClient/) are
    separate PCMC references. Confirm the property boundary and authority;
    Pune-area address alone does not establish which rules apply.
  - [Maharashtra Fire & Emergency Services — Acts, Rules and NBC](https://mahafireservice.gov.in/fire-act.php)
    lists state fire legislation and rules; applicability depends on project
    facts and current notifications.
  - [BIS standards portal](https://standards.bis.gov.in/) and
    [BIS standards overview](https://www.bis.gov.in/standards-overview/)
    must be consulted to verify the governing SP 7/NBC edition, access rights,
    and whether that edition is incorporated by the applicable regulations.
    Do not assume an edition or encode rule thresholds from summaries.
- Building-code status cannot be inferred from an image alone. Occupancy/use,
  governing authority, applicable code edition and amendments, site/building
  data, reliable dimensions, and professional review are required.
- Spatial relationships are not reliably reconstructed from predicted
  geometry; egress/pathfinding claims are not supported.
- The assistant uses bundled keyword-matched generic guidance, not verified
  building-code sources or an external LLM.
- PDF processing requires Poppler. Analysis runs synchronously in the API
  request and may be unsuitable for large plans or concurrent production use.

BuildGuard AI is an academic prototype. Do not use its output for official
submission or design approval. Have qualified professionals verify all
measurements and applicable rules.
