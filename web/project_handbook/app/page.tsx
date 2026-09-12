const pins = [
  ["Black", "+5 V power", "D2 socket VCC", "Power", "Dedicated fused and protected branch"],
  ["Red", "Sensor ground", "D2 socket GND", "Common", "Join White on adapter"],
  ["Blue", "Probe trigger", "D2 socket Grove White / D3", "Input", "Protected; measure voltage and polarity"],
  ["White", "Control/power ground", "D8 socket GND", "Common", "Join Red on adapter"],
  ["Yellow", "Deploy/stow control", "D8 socket Grove Yellow / D8", "PWM output", "Series-protected control"],
];

const buildSteps = [
  {
    n: "01",
    title: "Prepare the MK4S",
    text: "Keep the xBuddy in charge of X, Y and Z. Verify the stock USB connection, machine identity and limits before adding probe electronics. Do not connect Mega GPIO to STEP, DIR, ENABLE, ZL, ZR or J29.",
    evidence: "Record M115, M105, M119 and M114 read-only responses.",
  },
  {
    n: "02",
    title: "Build the protected adapter",
    text: "Use a separately fused and current-limited 5 V supply for the probe, a 74AHCT-family 3.3 V-to-5 V control buffer, and a conditioned trigger path proven to remain at or below 3.3 V.",
    evidence: "Record continuity, polarity, supply voltage and both test-point voltages.",
  },
  {
    n: "03",
    title: "Prepare the Mega 2560",
    text: "Flash the locked commissioning firmware with CR Touch disconnected. Reserve D8 for control, D3 for trigger, and route the 5 V probe branch through the protected adapter.",
    evidence: "Confirm SPM_PROBE_MEGA2560 identity and locked, non-actuating status.",
  },
  {
    n: "04",
    title: "Commission CR Touch",
    text: "Identify conductors electrically, power with a current limit, test stow/deploy clear of the printer, measure released and triggered levels, then verify repeated input transitions.",
    evidence: "Complete 100 repeatability cycles before motion is allowed.",
  },
  {
    n: "05",
    title: "Unlock supervised motion",
    text: "Only after the wiring record, measured pulse widths, trigger polarity, watchdog and retract behavior are complete may the firmware pin lock be enabled.",
    evidence: "Real Measurement remains unavailable until every gate agrees.",
  },
];

export default function Home() {
  return (
    <main>
      <header className="topbar">
        <a className="brand" href="#top">
          <span className="brand-mark">SPM</span>
          <span>Prusa Project<small>Local construction handbook</small></span>
        </a>
        <nav aria-label="Handbook sections">
          <a href="#build">Build</a>
          <a href="#wiring">Wiring</a>
          <a href="#development">Development</a>
          <a href="#software">Software</a>
          <a href="#status" className="nav-status"><span /> Current state</a>
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">MK4S × Arduino Mega 2560 × CR Touch</p>
          <h1>Build the platform.<br /><em>Verify every boundary.</em></h1>
          <p className="hero-lede">
            The working construction handbook for converting the Prusa MK4S
            into a controlled scanning and single-point measurement prototype.
            It connects the build sequence, electrical allocation, software
            workflow and commissioning evidence in one local reference.
          </p>
          <div className="hero-actions">
            <a className="button primary" href="#build">Start construction</a>
            <a className="button secondary" href="#wiring">Open pin allocation</a>
          </div>
          <div className="proof-row">
            <div><strong>2</strong><span>isolated USB links</span></div>
            <div><strong>4</strong><span>protected probe nets</span></div>
            <div><strong>0</strong><span>direct xBuddy GPIO links</span></div>
          </div>
        </div>
        <figure className="hero-image">
          <Image src="/project/operator-workstation.png" width={1280} height={760} priority alt="SPM Operator workstation running the focused measurement workflow" />
          <figcaption>Project evidence: the focused operator workflow. Real Measurement stays locked until hardware commissioning is complete.</figcaption>
        </figure>
      </section>

      <section className="status-strip" id="status">
        <div><span className="live-dot" /><p>Current hardware state</p></div>
        <dl>
          <div><dt>Pin mapping</dt><dd className="ready">Design locked</dd></div>
          <div><dt>Firmware build</dt><dd className="ready">Compiled</dd></div>
          <div><dt>Stage 2 mount</dt><dd className="ready">Installed</dd></div>
          <div><dt>New geometry</dt><dd className="ready">234.5 × 197.5 mm</dd></div>
          <div><dt>Real Measurement</dt><dd className="ready">Live gates required</dd></div>
        </dl>
      </section>

      <section className="section handbook" id="build">
        <div className="section-heading split">
          <div><p className="eyebrow">Construction sequence</p><h2>Build in a safe order.</h2></div>
          <p>Each stage ends with evidence. A command being sent or a COM port appearing is not an electrical verification.</p>
        </div>
        <div className="build-list">
          {buildSteps.map((step) => (
            <article className="build-step" key={step.n}>
              <span>{step.n}</span><div><h3>{step.title}</h3><p>{step.text}</p><b>Evidence: {step.evidence}</b></div>
            </article>
          ))}
        </div>
      </section>

      <section className="section wiring" id="wiring">
        <div className="section-heading">
          <p className="eyebrow">Latest CR Touch allocation</p>
          <h2>All five wires terminate at one protected Mega adapter.</h2>
          <p>Set the Base Shield switch to 5V. The locked firmware keeps D8 inactive. Probe current, harness continuity, timing and Blue trigger voltage must be measured before actuation.</p>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Wire</th><th>Expected function</th><th>Mega destination</th><th>Direction</th><th>Required interface</th></tr></thead>
            <tbody>{pins.map((row) => <tr key={row[0]}>{row.map((cell) => <td key={cell}>{cell}</td>)}</tr>)}</tbody>
          </table>
        </div>
        <div className="warning-grid">
          <article><strong>Protect the 5 V branch</strong><p>Black is fed from Mega 5V only through a dedicated fuse, polarity protection and local decoupling.</p></article>
          <article><strong>Verify every conductor</strong><p>Continuity and voltage measurements take precedence over harness wire colors.</p></article>
          <article><strong>Do not drive xBuddy nets</strong><p>The PC coordinates xBuddy motion and Mega probe feedback over separate USB links.</p></article>
        </div>
        <a className="document-link" href="/source/crtouch-mega2560-wiring.html">Open the visual Mega wiring guide →</a>
        <a className="document-link" href="/source/STAGE2_LOVEBOARD_CONNECTOR_ASSESSMENT.md">Why the LoveBoard cannot replace the Mega →</a>
      </section>

      <section className="section gallery" aria-labelledby="evidence-title">
        <div className="section-heading">
          <p className="eyebrow">Project evidence</p>
          <h2 id="evidence-title">What the current system produces.</h2>
        </div>
        <div className="image-grid">
          <figure><Image src="/project/hardware-check.png" width={1280} height={760} alt="Recorded three by three hardware check surface plot" /><figcaption>Recorded 3×3 hardware-check output, 11 June 2026.</figcaption></figure>
          <figure><Image src="/project/measurement-workflow.png" width={1280} height={760} alt="SPM connect approach and measurement operator screen" /><figcaption>Connect, approach and measurement operator workflow.</figcaption></figure>
        </div>
      </section>

      <section className="section gallery" id="development" aria-labelledby="development-title">
        <div className="section-heading">
          <p className="eyebrow">Validated tapping development</p>
          <h2 id="development-title">Measured profiles, adaptive mapping and speed evidence.</h2>
          <p>
            The CR Touch is validated for coarse contact, tapping research and
            boundary discovery. Physical measurements remain visibly separate
            from interpolation and AI prediction.
          </p>
        </div>
        <div className="image-grid">
          <figure><Image src="/project/crtouch-1d-profile.png" width={1440} height={800} alt="Center referenced CR Touch line profile of the flat spacer and tapered rim" /><figcaption>40-reading center-to-left and center-to-right profile. Flat top, tapered rim and 50 µm center-repeat difference.</figcaption></figure>
          <figure><Image src="/project/crtouch-adaptive-2d-map.png" width={1280} height={1280} alt="Adaptive 40 by 40 millimeter CR Touch contact map" /><figcaption>116 physical points generated a 40×40 projection with a 13.8× cycle reduction. Measurement locations remain overlaid.</figcaption></figure>
          <figure><Image src="/project/crtouch-speed-sweep.png" width={1280} height={760} alt="CR Touch one iteration tapping speed characterization" /><figcaption>One contact per speed: Z17.600 from 0.05 through 0.80 mm/s using 0.05 mm steps.</figcaption></figure>
          <figure><Image src="/project/crtouch-two-object-100x100.png" width={1700} height={1360} alt="Real adaptive CR Touch scan of two separated round objects" /><figcaption>234 physical measurements found two centers without using the nominal second position and directly bracketed the clear gap at 10.0–11.0 mm.</figcaption></figure>
        </div>
        <div className="warning-grid">
          <article><strong>Known-surface candidate</strong><p>0.80 mm/s produced the fastest loop without a detected Z shift. Replication is required before certification.</p></article>
          <article><strong>Unknown-surface rule</strong><p>Begin at 0.05 mm/s, establish a deterministic local envelope, then accelerate only where contacts agree.</p></article>
          <article><strong>AI boundary</strong><p>AI may prioritize measurements and predict features, but deterministic code owns Z floors, speed ceilings, retract and abort.</p></article>
          <article><strong>Two-object validation</strong><p>Real feedback detected centers X85.50 and X125.75, separate median heights, and a 10.0–11.0 mm measured gap bracket.</p></article>
        </div>
        <a className="document-link" href="/source/CRTOUCH_TAPPING_DEVELOPMENT_RECORD.md">Open the complete tapping and purchasing record →</a>
      </section>

      <section className="section focus-pair" id="software">
        <article className="focus dark">
          <p className="eyebrow">Operator workflow</p><h2>Three modes.<br />One explicit gate.</h2>
          <div className="mode-row"><span>Simulation</span><b>Generated motion and signals</b><i>Ready</i></div>
          <div className="mode-row"><span>Dry Run</span><b>Complete virtual acquisition workflow</b><i>Ready</i></div>
          <div className="mode-row"><span>Real Measurement</span><b>Centered Stage 2 profile plus live safety gates</b><i>Commissioned</i></div>
        </article>
        <article className="focus light">
          <p className="eyebrow">Continue from here</p><h2>Next bench session.</h2>
          <ol>
            <li><span>01</span>Home X/Y only; never use stock Z homing in scanner mode</li>
            <li><span>02</span>Travel inside X15.50–250.00 and Y12.50–210.00 at Z45</li>
            <li><span>03</span>Require D3 LOW/unlatched and D8 high impedance before motion</li>
            <li><span>04</span>Require every heater target and output to remain zero</li>
            <li><span>05</span>Subtract the five-point stage background before sample analysis</li>
          </ol>
        </article>
      </section>

      <section className="section references">
        <div className="section-heading"><p className="eyebrow">Maintained sources</p><h2>Continue in the engineering record.</h2></div>
        <div className="reference-grid">
          <a href="/source/CRTOUCH_MEGA2560_INTEGRATION.md"><b>Mega wiring</b><span>Canonical five-wire allocation and protection</span></a>
          <a href="/source/CRTOUCH_MEGA2560_ROADMAP.md"><b>Commissioning roadmap</b><span>Ordered bench phases and acceptance evidence</span></a>
          <a href="/source/CRTOUCH_TAPPING_DEVELOPMENT_RECORD.md"><b>Tapping development record</b><span>Validated profiles, failures, speed evidence and parts list</span></a>
          <a href="/source/TAPPING_MODE_AI_PIEZO_ROADMAP.md"><b>AI and piezo roadmap</b><span>Unknown-surface feedback loop and recommended fine stage</span></a>
          <a href="/source/CENTERED_CRTOUCH_CONVERSION.md"><b>Stage 2 conversion</b><span>Centered mount, firmware firewall and commissioning state</span></a>
          <a href="/source/STAGE2_LOVEBOARD_CONNECTOR_ASSESSMENT.md"><b>LoveBoard assessment</b><span>Connector functions and future-use decision</span></a>
          <a href="/source/COMMISSIONING.md"><b>Legacy safety checks</b><span>Retained measurement principles</span></a>
          <a href="/source/PROTOCOL.md"><b>Protocol baseline</b><span>Retained state-machine and watchdog concepts</span></a>
        </div>
      </section>

      <footer>
        <div className="brand"><span className="brand-mark">SPM</span><span>Prusa Project<small>Local construction handbook</small></span></div>
        <p>Internal, unprotected local reference. No ChatGPT sign-in or cloud account is required.</p>
        <a href="#top">Back to top ↑</a>
      </footer>
    </main>
  );
}
import Image from "next/image";
