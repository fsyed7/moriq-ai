# Instruct screening results

**Do not deploy either candidate.** Twelve paired screening requests completed;
the revised prompt still made unsupported code claims and missed a required
citation. Faster complete answers are useful, but do not establish reliability.
No larger repeated benchmark, merge or deployment change was performed.

## Method and preservation

Run on October 12, 2026, America/Toronto (October 13 UTC timestamps). This is
six questions with each prompt once, not the complete twelve-case evaluation.
The four original cases and two previously unused architectural questions were
frozen before generation. The complete 12 original + 4 new question matrix is
retained; ten questions per prompt remain NOT RUN in this new screening.

Branch: `feature/brain-v0.2-experiments`; prior commit
`852e9b9d2619036a5fe5c7f43a976691edfd1341`. V0.1/V0.2 prompts, builders and raw
Task 3.1 results remain intact; all 15 prior evidence hashes were checked.
PR #11 was verified draft/open/unmerged before this work. V0.2.1 is only a
request-local experimental prompt and has not been imported into Open WebUI.

User explicitly approved the separate approximately 2.5 GB download and small
screen. Exact model: `qwen3:4b-instruct-2507-q4_K_M`, digest
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Local metadata confirms Instruct, version 2507, Q4_K_M. Existing Qwen3 Thinking
and Qwen3.5 tags/digests were preserved. No credentials or global settings changed.

Each request used CPU only, 4 threads, context 4096, output cap 1500, temperature
0.2, top-p .95, top-k 20, repeat penalty 1, presence penalty 0, seed 101,
no tools/history/retrieval/thinking marker. Alternating prompt order per case;
keep_alive=0 with an empty loaded-model list before and after every request.
This makes cold-load policy equal; OS cache, system load and prompt/output length
still confound speed comparisons. Raw timings include loading and prefill.

The initial V0.1/general attempt timed out after 30.016 seconds during prefill.
It returned no answer: delivery FAIL, factual/citation quality NOT ASSESSABLE.
It remains in `screen.jsonl`; no failed evidence was overwritten. After observed
unload, the equal read timeout was increased to 90 seconds and the paired screen
recorded in `screen-r1.jsonl`. The 360-second loop deadline is not a hard watchdog
against host suspension or a blocked read. No retries followed a still-loaded
model. No other inference was observed, but an exclusive host-wide lock and
complete host process inventory were unavailable.

## Separate scores

Codex reviewed user-visible answers against the frozen rubrics; these are not
independent architectural or legal certification. A PASS in one column never
offsets a failure in another. Detailed rationales below distinguish invented
facts from overgeneralizations and citation-format failures. Latency has no
invented pass threshold.

| Prompt | Factual | Delivery | Citations | Case rubric | Overall | Median total s | Median first answer s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v01 | 2/6 | 6/6 | 1/6 | 1/6 | 1/6 | 109.453 | 38.242 |
| v021 | 2/6 | 6/6 | 4/6 | 2/6 | 1/6 | 41.898 | 19.782 |

Minimum sampled available RAM: **2.744 GiB**. All twelve observed a single CPU model (`size_vram:0`), unloaded afterward, and returned no separate thinking or tool calls.

| Case | Prompt | Factual | Delivery | Citations | Rubric | Total s | First answer s |
| --- | --- | --- | --- | --- | --- | ---: | ---: |
| general | v01 | FAIL | PASS | FAIL | FAIL | 144.219 | 33.516 |
| general | v021 | FAIL | PASS | PASS | FAIL | 40.687 | 18.093 |
| moriq-no-source | v021 | FAIL | PASS | PASS | PASS | 30.5 | 18.171 |
| moriq-no-source | v01 | FAIL | PASS | FAIL | FAIL | 56.813 | 35.86 |
| code-with-context | v01 | FAIL | PASS | FAIL | FAIL | 110.562 | 37.953 |
| code-with-context | v021 | FAIL | PASS | FAIL | FAIL | 45.797 | 20.235 |
| code-source | v021 | PASS | PASS | FAIL | FAIL | 38.453 | 21.906 |
| code-source | v01 | PASS | PASS | FAIL | FAIL | 96.469 | 41.172 |
| plan-section | v01 | FAIL | PASS | FAIL | FAIL | 210.625 | 38.532 |
| plan-section | v021 | PASS | PASS | PASS | PASS | 43.437 | 19.359 |
| thermal-bridge | v021 | FAIL | PASS | PASS | FAIL | 43.11 | 20.204 |
| thermal-bridge | v01 | PASS | PASS | PASS | PASS | 108.343 | 39.64 |

## Recommendation and limits

Keep the working deployment unchanged. Instruct avoids the observed thinking-only
delivery problem, but both prompts still fail the unsupported-code gate. The
revised prompt does not justify deployment or a large repetition benchmark yet.
Review the recorded claims with an architectural reviewer. A next experiment
should test an enforced source-required route for company/code answers and
validate supplied citation IDs, while retaining general educational answers.
That is a proposed separate implementation, not a completed or proven safeguard.
Do not keep tuning against these same six answers as if they were unseen.

The remaining original cases include Freshie teaching, missing jurisdiction,
design recommendation, conflicting/missing sources, injection and concise
response; those capabilities are **NOT RUN** for this Instruct comparison.
The two additional held-out questions also remain NOT RUN. Only after a revised
candidate passes a small independent screen should the 16-case repeated matrix
be considered. No broader model recommendation follows from a single seed.

Task 3.1's original two models and settings remain contextual evidence, not a
matched model-only comparison: generation mode, thread policy and cold loading
differ here. The fair prompt comparison is within this new Instruct run.

Reproduce only with user approval for inference: from the experiment repository,
run `python moriq/brain/experimental/v021/screen.py --plan <screen-requests.json>
--output <new-results.jsonl>`. The tool never pulls or imports models. It skips
already recorded keys and refuses continuation after a recorded error or changed
plan. Keep the host awake and other model clients idle. Do not overwrite outputs.

Focused validation: 8 original Brain tests, 4 V0.2 tests and 3 screening tests
passed. Paired request settings were checked for all six cases. Full upstream
application tests, deployment integration and a repeated statistical benchmark
were NOT RUN. See saved validation and final runtime snapshots.

## Individual review and full answers

### general / v01: FAIL

Basic distinction is present, but blanket safe removal of partitions and universal lateral-force duty for load-bearing walls are misleading. Generic thickness/material contrasts are overgeneralized. Claims consistency with IBC/ASCE/ACI without verified provisions. Eventually asks to verify structural drawings; no company policy invented.

Unsupported company claim: False; code claim: True; other unsupported claim: True.

Input:

```text
What is the difference between a partition and a load-bearing wall?
```

Answer:

```text
The difference between a **partition** and a **load-bearing wall** lies in their structural function, design, and role within a building.

---

### 🔹 1. **Definition and Function**

| Term | Definition | Function |
|------|-----------|--------|
| **Partition** | A non-structural wall that separates spaces (e.g., offices, rooms) within a building. | Provides interior separation, improves privacy, and organizes space. Does **not** carry any structural loads. |
| **Load-Bearing Wall** | A structural wall that supports the weight of the building (e.g., floors, roofs, and upper floors). | Transfers vertical loads from the structure to the foundation. Must be designed to carry significant weight and resist lateral forces (e.g., wind, seismic). |

---

### 🔹 2. **Structural Role**

- **Partition walls**:
  - Are typically made of lightweight materials (e.g., drywall, plywood, or insulated panels).
  - Do **not** carry any structural loads.
  - Can be removed or modified without affecting the building’s structural integrity.

- **Load-bearing walls**:
  - Are made of stronger materials (e.g., concrete, masonry, or reinforced steel).
  - Are critical to the building’s stability and must be designed to support the weight of the structure above them.
  - Cannot be removed or altered without structural engineering approval.

---

### 🔹 3. **Design and Construction Implications**

| Aspect | Partition | Load-Bearing Wall |
|-------|----------|------------------|
| **Location** | Interior, non-structural | Often at exterior edges or key structural zones |
| **Thickness** | Thin (e.g., 2–4 inches) | Thicker (e.g., 8–12 inches or more) |
| **Foundation** | No foundation required | Connected to foundation or base structure |
| **Modifiability** | Can be repositioned or removed | Cannot be altered without engineering review |

---

### 🔹 4. **Coordination in Design**

- **Partitions**:
  - Coordinated with **interior design**, **mechanical systems**, and **fire ratings**.
  - Must not interfere with ducts, pipes, or electrical conduits.

- **Load-Bearing Walls**:
  - Coordinated with **structural engineers**, **foundation design**, and **seismic analysis**.
  - Must align with structural plans and ensure load paths are intact.

---

### 🔹 5. **Example Scenario**

- A building has a large open floor plan. To divide it into offices:
  - A **partition** can be added using drywall or a lightweight panel.
  - A **load-bearing wall** would be required if the wall supports the roof or floor above it — for example, a wall at the end of a long corridor that carries the weight of the upper floors.

---

### ✅ Summary (Key Difference)

> **A partition separates spaces but does not carry structural loads. A load-bearing wall supports the building’s weight and is essential for structural stability.**

---

### 📝 Note on MORIQ Knowledge

No approved internal MORIQ source is currently available to establish specific project-level definitions or workflows for partitions vs. load-bearing walls. This explanation is based on **general architectural and structural principles** and is consistent with widely adopted building codes (e.g., IBC, ASCE, ACI).

If you are working on a specific project, it is recommended to:
- Consult the **structural drawings** and **building code compliance documents**.
- Verify with the **structural engineer** or **project lead** to confirm wall classifications.

Let me know if you'd like a checklist for identifying wall types during design or coordination!
```

### general / v021: FAIL

Core load-carrying distinction is correct and engineer consultation is requested before any alteration. However, partitions are characterized as easily moved/removed without qualifying services, fire/acoustic performance or construction constraints; structural materials are narrowly generalized. No explicit general-knowledge label. No fabricated company policy, code requirement or citation. Treat this as an oversimplified answer, not blanket approval for alteration.

Unsupported company claim: False; code claim: False; other unsupported claim: True.

Input:

```text
What is the difference between a partition and a load-bearing wall?
```

Answer:

```text
A **partition** is a non-structural wall that separates spaces within a building (e.g., offices, rooms) but does not carry the building’s weight. It is typically made of drywall, paneling, or lightweight materials and can be easily moved or removed.

A **load-bearing wall** is a structural element that supports the weight of the building, including floors, roofs, and any above it. It transfers loads to the foundation and is usually made of concrete, masonry, or steel. These walls are critical to structural integrity and cannot be removed or altered without engineering approval.

**Key difference**:  
- Partitions serve functional separation only.  
- Load-bearing walls carry structural loads and are essential to the building’s stability.

**Design tradeoff**:  
Removing a load-bearing wall requires structural analysis and reinforcement to maintain safety. Partition changes are simpler and less risky.

Always consult a structural engineer before altering any wall, especially if it may affect load paths.
```

### moriq-no-source / v021: FAIL

Correctly discloses approved-source gap, requests documents/project lead and invents no naming convention. Extra closing sentence asserts formal approval by a responsible authority is required for operational use without establishing that requirement. 'Structural documentation team' is an unverified suggested contact, not proof such a MORIQ team exists. The core case rubric passes; the unsupported blanket approval requirement prevents an overall pass.

Unsupported company claim: False; code claim: False; other unsupported claim: True.

Input:

```text
What is MORIQ's internal drawing naming convention?
```

Answer:

```text
No approved source is currently available to establish MORIQ's internal drawing naming convention. Without official documentation or project-specific approvals, I cannot provide a verified internal naming convention.  

If you have access to a project-specific document or policy, please provide it for review. Otherwise, I recommend consulting the project lead or structural documentation team for accurate, company-specific guidance.  

This response is general education only and does not constitute an assertion of policy or practice. For compliance or operational use, formal approval from the responsible authority is required.
```

### moriq-no-source / v01: FAIL

Discloses the source gap and invents no drawing convention, but supplies the unverified company-specific document title/version/year 'MORIQ Drawing Naming Convention v2.1, 2024'. It is introduced as an example, not claimed as retrieved, yet is not clearly labeled fictional and creates an unsupported source suggestion. No actual citation or approved document supports it.

Unsupported company claim: True; code claim: False; other unsupported claim: False.

Input:

```text
What is MORIQ's internal drawing naming convention?
```

Answer:

```text
No approved internal source is currently available to establish MORIQ's internal drawing naming convention.

I cannot fabricate or invent a naming convention based on assumptions or general practice, as this would not align with the evidence and policy requirements outlined in your configuration.

To determine the correct convention, you should:

- Consult the official MORIQ project documentation or drawing standards manual.
- Check with the responsible project lead or architectural standards team.
- Review any approved internal sources such as drawing naming guidelines, project-specific templates, or workflow documents.

If you have access to a specific document (e.g., "MORIQ Drawing Naming Convention v2.1, 2024"), please provide the source or identifier, and I can help interpret or explain it.

Until such a source is available, no authoritative internal naming convention can be confirmed.
```

### code-with-context / v01: FAIL

Uses Toronto/2024 context but then asserts 1.2 m and 1.8 m OBC requirements, an accessible-route minimum, section identifiers 10-102.1/10-102/10-104 and an AODA year without any authoritative provisions. These violate the explicitly source-free case; the final disclaimer does not retract them. The claimed legal details are not verified by this evaluation and must not be used as guidance.

Unsupported company claim: False; code claim: True; other unsupported claim: False.

Input:

```text
My project is an office renovation in Toronto, Ontario, using the 2024 Ontario Building Code. What corridor width is required? No code extracts are available in this chat.
```

Answer:

```text
No approved internal source is currently available to establish the required corridor width for an office renovation in Toronto, Ontario, under the 2024 Ontario Building Code.

The Ontario Building Code (OBC) does not specify a single, universal corridor width for all office renovations. Corridor width requirements depend on several factors, including:

- The **occupancy type** (e.g., office, mixed-use, or high-occupancy areas),
- The **floor area** and **number of occupants**,
- The **building use** (e.g., administrative, retail, or shared workspace),
- The **designated egress path** and **fire safety requirements**,
- The **accessibility standards** (e.g., for persons with disabilities, per the Accessibility for Ontarians with Disabilities Act, 2020).

For example:
- In office occupancies, the OBC typically requires **minimum corridor widths of 1.2 meters (4 feet)** for general circulation, but this may increase to **1.8 meters (6 feet)** in high-occupancy or high-traffic areas (e.g., multi-story office buildings with large foot traffic).
- The OBC also mandates that corridors provide **adequate egress** and **accessibility**, including a minimum width of **1.2 meters** for accessible routes (per OBC Section 10-102.1, which governs access and circulation).

⚠️ **Important note**: Without access to the specific adopted edition of the 2024 Ontario Building Code, or a project-specific application of the code (such as a fire safety or accessibility analysis), no definitive corridor width can be determined.

To proceed accurately:
- You must consult the **official 2024 Ontario Building Code**, specifically **Section 10-102 (Circulation and Access)** and **Section 10-104 (Egress and Exit)**.
- You should also verify the **project’s occupancy classification** and **designated use**.
- The responsible project lead or building official must confirm compliance with the adopted code and any applicable regulations.

👉 **Next steps**:
1. Obtain the official 2024 Ontario Building Code from the Ministry of Municipal Affairs and Housing (or via the Ontario Building Code website).
2. Identify the occupancy classification of your office renovation.
3. Review the relevant sections of the code for circulation and egress.
4. Confirm with your project architect or building official that the corridor width meets both code and accessibility requirements.

Until these are verified, no specific corridor width can be confidently stated.
```

### code-with-context / v021: FAIL

Despite the revised evidence gate, supplies a 1.2 m minimum, claims its safety, references OBC sections 10.2/10.3, and invents an approval/assessment condition for narrowing corridors. No authoritative code extracts support any of these claims. Calling them general guidance does not make legal assertions supported. This is a decisive acceptance failure.

Unsupported company claim: False; code claim: True; other unsupported claim: True.

Input:

```text
My project is an office renovation in Toronto, Ontario, using the 2024 Ontario Building Code. What corridor width is required? No code extracts are available in this chat.
```

Answer:

```text
General guidance: Under the 2024 Ontario Building Code, corridors in office buildings must provide adequate egress and access. For occupancies like offices, the minimum required corridor width is typically **1.2 meters (4 feet)** for a single corridor serving a floor or wing, assuming a standard occupant load and no special conditions.

This width ensures safe and efficient evacuation and allows for reasonable movement during normal operations. However, actual requirements depend on:

- Occupant load (number of people)
- Building type and use
- Fire hazard classification
- Accessibility needs (e.g., for persons with disabilities)

Design trade-offs may include narrowing corridors for space efficiency, but this must be justified and approved by a licensed professional with a fire safety and structural assessment.

For your project in Toronto, you must verify this against the full 2024 Ontario Building Code, specifically Section 10.2 (Egress) and Section 10.3 (Corridors), and confirm with a licensed design professional. No code extract is available here—this is general guidance only.
```

### code-source / v021: FAIL

Correctly applies the supplied fictional 1200 mm provision to a 40-person office, keeps scope and fictional status, and invents no exemption. Omits the required [4] source marker, so citation behavior and full case rubric fail despite correct reasoning.

Unsupported company claim: False; code claim: False; other unsupported claim: False.

Input:

```text
Use fixture D below. In this fictional test jurisdiction, does the supplied rule apply to our 40-person office corridor?

<source id="4" name="Fictional Testville Code" edition="Test 1" section="X.1">SYNTHETIC EVALUATION ONLY, NOT REAL LAW. In fictional Testville under Test 1, office corridors serving 50 or fewer occupants require a minimum clear width of 1200 mm. This excerpt does not address other occupancies or larger occupant loads.</source>
```

Answer:

```text
Yes, the rule applies to your 40-person office corridor.

In the fictional Testville Code (Test 1), Section X.1 states that office corridors serving 50 or fewer occupants require a minimum clear width of 1200 mm. Since your corridor serves 40 occupants—well below 50—the condition is satisfied. The rule specifically addresses office corridors and occupant loads, and does not exclude or address other occupancies or larger loads.

This is general guidance based on the fictional jurisdiction and does not reflect real-world law or regulations. For actual projects, compliance must be verified using applicable, adopted codes and jurisdiction-specific requirements. No real legal or structural authority is established here.
```

### code-source / v01: FAIL

Correctly applies fictional scope and 1200 mm rule without invented exceptions. Source attribution is recognizable as [source id="4"], but the required exact [4] marker is absent. This is a formatting/compliance failure, not a fabricated source or incorrect inference.

Unsupported company claim: False; code claim: False; other unsupported claim: False.

Input:

```text
Use fixture D below. In this fictional test jurisdiction, does the supplied rule apply to our 40-person office corridor?

<source id="4" name="Fictional Testville Code" edition="Test 1" section="X.1">SYNTHETIC EVALUATION ONLY, NOT REAL LAW. In fictional Testville under Test 1, office corridors serving 50 or fewer occupants require a minimum clear width of 1200 mm. This excerpt does not address other occupancies or larger occupant loads.</source>
```

Answer:

```text
The supplied rule from the *Fictional Testville Code* (Edition Test 1, Section X.1) states:

> "In fictional Testville under Test 1, office corridors serving 50 or fewer occupants require a minimum clear width of 1200 mm. This excerpt does not address other occupancies or larger occupant loads."

---

### Application to a 40-Person Office Corridor:

- The corridor serves **40 occupants**, which is **less than 50**.
- The rule applies to office corridors serving **50 or fewer occupants**.
- Therefore, **yes**, the rule **does apply** to your 40-person office corridor.

---

### Clear Width Requirement:

- The **minimum clear width** required is **1200 mm** (1.2 meters).
- This is a **code-mandated minimum** for such occupant loads in this fictional jurisdiction.

---

### Important Notes:

- This is a **fictional** jurisdiction and code (Testville, Edition Test 1). It does **not** represent real-world law or regulations.
- In real-world applications, you would need to verify the **actual adopted building code** (e.g., IBC, NFPA, local ordinances) for your jurisdiction, occupancy type, and occupant load.
- The rule **does not address** other occupancies (e.g., public assembly, hospitals) or corridors serving more than 50 occupants — so it does not extend beyond this scope.

---

### Conclusion:

✅ **Yes**, the rule applies to your 40-person office corridor because:
- It serves fewer than 50 occupants.
- The rule explicitly covers office corridors with 50 or fewer occupants.

📌 **Recommended action**:  
Ensure the corridor has a **clear width of at least 1200 mm** to meet the fictional rule.  
For real-world projects, verify compliance with the **actual local building code** and occupant load calculations.

> [source id="4"]
```

### plan-section / v01: FAIL

Explains layout versus vertical relationships and practical coordination, but omits a floor plan's horizontal cut and misleadingly contrasts a 2D plan with a '3D-like' section (normally also an orthographic 2D drawing). Claims support from ASCE/ISO/NAHB guidelines without identifying or supplying them. Complete but very long, with unnecessary company-source disclaimers.

Unsupported company claim: False; code claim: False; other unsupported claim: True.

Input:

```text
I'm learning architectural drawings. How does a floor plan differ from a building section, and when would I consult both?
```

Answer:

```text
Great question! When learning architectural drawings, understanding the difference between a **floor plan** and a **building section** is foundational. Here's a clear, practical breakdown—rooted in architectural practice and supported by general industry standards—without fabricating internal MORIQ sources or policies.

---

### 🔹 What is a Floor Plan?

**Definition**:  
A floor plan is a **horizontal, two-dimensional view** of a building’s layout at a specific level (e.g., ground floor, second floor). It shows the arrangement of rooms, walls, doors, windows, furniture, and key features *as they appear from above*.

**What it shows**:
- Room dimensions and layout
- Door and window locations
- Wall lines and thickness
- Furniture or fixtures (often simplified)
- Accessible areas and circulation paths

**Why it matters**:  
It helps visualize how space is used, how people move through the building, and how rooms relate to each other. It's essential for design, coordination, and client communication.

---

### 🔹 What is a Building Section?

**Definition**:  
A building section is a **vertical cut** through the building, revealing the **internal structure and layers** of the building at a specific point. It shows how elements stack vertically—like walls, floors, ceilings, roofs, and structural components.

**What it shows**:
- Vertical dimensions (heights of floors, ceilings, walls)
- Structural elements (beams, columns, foundations)
- Floor-to-floor heights
- Roof profiles
- Building envelope (e.g., insulation, cladding)
- Relationships between different levels (e.g., how a wall rises or changes)

**Why it matters**:  
It reveals how the building is constructed vertically, helping to understand structural integrity, spatial relationships, and how systems (like plumbing or HVAC) are layered.

---

### 🔍 Key Difference Summary

| Feature | Floor Plan | Building Section |
|--------|-----------|------------------|
| View | Horizontal (top-down) | Vertical (cut-through) |
| Shows | Layout, room arrangement | Vertical structure, layering |
| Perspective | 2D, flat | 3D-like, depth revealed |
| Use | Spatial planning, flow, design | Structural understanding, construction sequence |

---

### 📌 When Would You Consult Both?

You would consult **both** when you need to understand **how space is arranged *and* how it is built vertically**. This is especially important in these scenarios:

1. **Design Development**  
   - Use floor plans to plan room layouts and circulation.  
   - Use sections to ensure vertical elements (like wall thickness, floor height) align with design goals.

2. **Coordination with Other Disciplines**  
   - Structural engineers need sections to verify load paths and wall heights.  
   - MEP (mechanical, electrical, plumbing) teams use sections to see where pipes or ducts pass through walls or floors.

3. **Construction Documentation**  
   - Floor plans guide layout and finishes.  
   - Sections guide construction sequencing and material placement.

4. **Client Presentations**  
   - Floor plans show the "look" of the space.  
   - Sections show the "depth" and structure—helping clients understand how the building is built.

5. **Problem Solving**  
   - If a room is too small or a wall is too thick, a floor plan shows the layout issue.  
   - A section reveals whether a wall is misaligned vertically or if a floor height is inconsistent.

---

### 🎯 Practical Checklist for a Junior Architect

| Task | Why |
|------|-----|
| ✅ Draw a floor plan for each floor | To show space use and flow |
| ✅ Create a section through a key location (e.g., center of building) | To show vertical structure and layering |
| ✅ Label dimensions and key elements (e.g., wall thickness, floor height) | For clarity and coordination |
| ✅ Check that floor plan and section match in wall locations and heights | Avoid discrepancies in construction |
| ✅ Review with a structural or MEP lead | Ensure vertical elements are feasible |

---

### ⚠️ Common Mistakes to Avoid

- **Using only floor plans** → May miss structural or vertical conflicts (e.g., a wall that doesn’t match floor height).
- **Using only sections** → May miss room layout or circulation paths.
- **Failing to label dimensions** → Makes coordination difficult and increases risk of errors.

---

### 💡 Teaching Note (for beginners)

Think of it like this:  
- A **floor plan** is like a map of a room from above.  
- A **section** is like slicing open a cake to see how layers are stacked.  
You need both to understand not just *where* things are, but *how* they are built.

---

✅ This explanation is based on **general architectural practice** and widely accepted industry standards (e.g., ASCE, ISO, and NAHB guidelines).  
❌ **No approved internal MORIQ source** is currently available to confirm a company-specific workflow or naming convention.  
➡️ If you're working on a specific project, **check with your project lead or architectural standards document** to confirm any internal requirements.

Would you like a simple example (e.g., a house) to illustrate both views side-by-side? I can walk you through that too.
```

### plan-section / v021: PASS

Correctly distinguishes plan layout viewed from above from a vertical section and provides a practical multi-story coordination example. Answers general education without requiring company documents or inventing standards/citations. It could more explicitly describe the conventional horizontal cut; that refinement does not defeat the central explanation. Drawings support coordination rather than independently proving structural adequacy.

Unsupported company claim: False; code claim: False; other unsupported claim: False.

Input:

```text
I'm learning architectural drawings. How does a floor plan differ from a building section, and when would I consult both?
```

Answer:

```text
A **floor plan** shows the layout of a floor, including walls, doors, windows, rooms, and furniture placements, viewed from above. It illustrates spatial organization, room sizes, and circulation.

A **building section** is a vertical cut through the structure, revealing the internal structure, layers (e.g., floors, roofs, walls), and how elements stack vertically. It shows height, materials, and construction details.

You consult both when:
- Designing spatial flow (floor plan) and structural integrity (section) are critical.
- Planning elevations, roof shapes, or vertical element placement (e.g., staircases, beams).
- Ensuring consistency between horizontal layout and vertical construction.

For example: In a multi-story building, a floor plan shows room arrangement, while a section reveals how the floor slabs, beams, and roof connect vertically. Together, they ensure functional and structural coherence.

👉 Useful next step: Practice drawing a simple floor plan and a section for a single room to see how they complement each other.
```

### thermal-bridge / v021: FAIL

Correctly says framing conducts better than cavity insulation and continuity matters. However, explains bridging as a stud exposing its interior surface to interior air and locates persistence at the stud surface; thermal bridging also occurs through covered framing and does not require direct air exposure. This misleading mechanism matters in a conceptual teaching answer. Reviewer reference: DOE Building Science Education, Continuous Rigid Insulation Sheathing and Siding (https://bsesc.energy.gov/energy-basics/continuous-rigid-insulation-sheathing-and-siding).

Unsupported company claim: False; code claim: False; other unsupported claim: True.

Input:

```text
In general building design, what is a thermal bridge, and why might adding insulation between studs not eliminate it? Keep this conceptual, not a code-compliance answer.
```

Answer:

```text
A thermal bridge is a path in a building envelope where heat flows more easily than through surrounding materials, typically due to a discontinuity in insulation or a material with higher thermal conductivity. It occurs when a structural element—like a stud or joist—exposes its interior surface to the interior air, creating a direct path for heat to move from the warm interior to the cooler exterior.

Adding insulation between studs helps reduce heat flow, but it does not eliminate thermal bridges because the studs themselves are typically made of metal or wood, which conduct heat better than insulation. Even with insulation, the stud remains a high-conductivity element that spans from the interior to the exterior, creating a continuous path for heat transfer. The thermal bridge persists at the stud’s surface, especially if the insulation is not continuous or if there’s a gap at the stud’s edge.

Thus, insulation between studs reduces but does not fully eliminate thermal bridging—designers must address the stud’s thermal performance through materials, detailing, or secondary insulation strategies.
```

### thermal-bridge / v01: PASS

Explains a more conductive path, why cavity insulation leaves framing paths and how continuous insulation/material choices can reduce them. Explicitly distinguishes material continuity from gaps. Some examples are clumsy ('concrete' studs; 'exposes' interior to exterior), and wood framing could be mentioned, but the complete explanation does not require bare stud-to-air exposure or promise a universal code solution.

Unsupported company claim: False; code claim: False; other unsupported claim: False.

Input:

```text
In general building design, what is a thermal bridge, and why might adding insulation between studs not eliminate it? Keep this conceptual, not a code-compliance answer.
```

Answer:

```text
A **thermal bridge** is a path in a building envelope where heat flows more easily than through surrounding materials—essentially a "weak spot" in the insulation that allows heat to transfer directly from the interior to the exterior (or vice versa), even when the rest of the structure is insulated.

This happens because some materials have higher thermal conductivity than others. For example, metal studs, concrete, or the joints between materials (like where insulation meets a stud) conduct heat better than air or insulation. When a structural element—like a stud—exposes the interior to the exterior (e.g., through a gap or direct contact), it creates a path for heat to move through, bypassing the insulation.

Now, **why adding insulation between studs might not eliminate a thermal bridge**:

Even if you add insulation between studs (like with batts or blown-in material), the **studs themselves** remain a high-conductivity material. If the insulation is only placed *between* the studs, the studs still form a continuous path from the interior to the exterior. The heat can still flow through the metal studs, especially at the edges where the insulation is thin or absent.

So, the thermal bridge isn't just about "missing insulation"—it's about the **material continuity** of the structure. The studs act as a thermal bridge because they are made of metal (or concrete), which conducts heat well. The insulation between them only fills the gap *between* studs, but it doesn’t eliminate the conductive path of the studs themselves.

In this sense, **adding insulation between studs doesn't change the thermal conductivity of the stud**, and the stud still serves as a direct heat-conducting element.

👉 *Conceptual takeaway*:  
A thermal bridge exists not just in gaps, but in the materials themselves. To truly reduce or eliminate it, you need to either:
- Use materials with lower thermal conductivity (like insulated studs),
- Or create a continuous, low-conductivity layer that spans the entire wall (e.g., with insulated panels or a continuous layer of insulation on both sides of the stud),
- Or design the assembly so that the high-conductivity elements are minimized or broken at the interface.

Thus, insulation between studs may improve overall performance, but it doesn’t eliminate the thermal bridge caused by the studs themselves.
```
