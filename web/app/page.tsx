const tools = [
  {
    number: "01",
    title: "Beam analysis",
    description:
      "Set supports, add point loads, distributed loads and applied moments. Explore the response of your beam.",
    tag: "Available in the current prototype",
  },
  {
    number: "02",
    title: "Shear force & bending moment",
    description:
      "Visualise SFD and BMD results and follow the equilibrium steps behind the answer.",
    tag: "Available in the current prototype",
  },
  {
    number: "03",
    title: "Stress & section properties",
    description:
      "Work with rectangular or supplied section properties to calculate bending and shear stress.",
    tag: "Available in the current prototype",
  },
  {
    number: "04",
    title: "More engineering tools",
    description:
      "Machine design, shafts, thermodynamics, fluid mechanics and manufacturing are on the roadmap.",
    tag: "In development",
  },
];

const studentFeatures = [
  "Step-by-step worked solutions",
  "Visual beam and loading diagrams",
  "Support and loading configurations",
  "Exam-style calculation workflow",
  "Learning-focused explanations",
];

const businessFeatures = [
  "Professional engineering workspaces",
  "Saved projects and calculation history",
  "Exportable calculation reports",
  "Team access and administration",
  "Business-focused engineering modules",
];

export default function Home() {
  return (
    <main>
      <div className="announcement">
        <span className="announcement-dot" />
        Building the next generation of accessible engineering software
      </div>

      <header className="site-header">
        <a className="brand" href="#" aria-label="EngineerAI home">
          <span className="brand-mark">E</span>
          <span>Engineer<span className="brand-light">AI</span></span>
        </a>
        <nav className="desktop-nav" aria-label="Main navigation">
          <a href="#tools">Platform</a>
          <a href="#students">Students</a>
          <a href="#business">Businesses</a>
          <a href="#pricing">Pricing</a>
        </nav>
        <a className="header-cta" href="#pricing">Explore plans <span>↗</span></a>
      </header>

      <section className="hero shell">
        <div className="hero-copy">
          <div className="eyebrow"><span /> ENGINEERING, EXPLAINED.</div>
          <h1>Think like an engineer.<br /><em>Work with clarity.</em></h1>
          <p className="hero-lede">
            Engineering tools that do more than calculate. Understand the method,
            see the results and build confidence in every step.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#tools">Explore the platform <span>→</span></a>
            <a className="button button-quiet" href="#pricing">View plans</a>
          </div>
          <div className="hero-proof">
            <span className="proof-icon">✓</span>
            Built around real engineering methods
            <span className="proof-separator">·</span>
            Designed for students and professionals
          </div>
        </div>

        <div className="hero-visual" aria-label="Illustration of an engineering analysis workspace">
          <div className="visual-glow" />
          <div className="analysis-window">
            <div className="window-top">
              <div className="window-dots"><i /><i /><i /></div>
              <span>ENGINEERAI / BEAM ANALYSIS</span>
              <span className="window-status"><b /> MODEL READY</span>
            </div>
            <div className="window-body">
              <div className="model-heading">
                <div><small>ANALYSIS WORKSPACE</small><strong>Simply supported beam</strong></div>
                <span className="model-chip">STATIC</span>
              </div>
              <div className="beam-canvas">
                <div className="beam-line" />
                <div className="support support-a"><span /></div>
                <div className="support support-b"><span /></div>
                <div className="load-arrow"><i /><b>5 kN</b></div>
                <div className="dimension-line"><span>2.0 m</span><span>2.0 m</span></div>
              </div>
              <div className="result-grid">
                <div className="result-card"><small>REACTION A</small><strong>5.00 <i>kN</i></strong><span className="result-positive">↑ Vertical</span></div>
                <div className="result-card"><small>REACTION B</small><strong>5.00 <i>kN</i></strong><span className="result-positive">↑ Vertical</span></div>
                <div className="result-card result-highlight"><small>MAX. BENDING MOMENT</small><strong>5.00 <i>kN·m</i></strong><span>At mid-span</span></div>
              </div>
              <div className="diagram-preview">
                <div className="diagram-label"><span>SHEAR FORCE DIAGRAM</span><small>kN</small></div>
                <div className="diagram-chart"><div className="chart-zero" /><div className="chart-shape" /></div>
              </div>
              <div className="window-footer"><span><b /> EQUILIBRIUM CHECK PASSED</span><span>Worked solution available ↗</span></div>
            </div>
          </div>
          <div className="floating-note"><span>∑ Fy = 0</span><small>Equilibrium explained</small></div>
        </div>
      </section>

      <section className="trust-strip">
        <div className="shell trust-inner">
          <span>MADE FOR THE WAY ENGINEERS THINK</span>
          <div><b>01</b> Calculate</div><div><b>02</b> Visualise</div><div><b>03</b> Understand</div>
        </div>
      </section>

      <section className="section shell" id="tools">
        <div className="section-heading">
          <div><div className="eyebrow">THE PLATFORM</div><h2>One workspace.<br /><em>More engineering insight.</em></h2></div>
          <p>Start with structural beam analysis and grow into a connected collection of engineering tools.</p>
        </div>
        <div className="tool-grid">
          {tools.map((tool) => (
            <article className="tool-card" key={tool.number}>
              <div className="tool-card-top"><span>{tool.number}</span><span className="tool-arrow">↗</span></div>
              <div className="tool-symbol">{tool.number === "01" ? "⌁" : tool.number === "02" ? "∿" : tool.number === "03" ? "σ" : "＋"}</div>
              <h3>{tool.title}</h3>
              <p>{tool.description}</p>
              <div className="tool-tag"><i />{tool.tag}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="audience-section" id="students">
        <div className="shell audience-grid">
          <div className="audience-copy">
            <div className="eyebrow">FOR THE NEXT GENERATION</div>
            <h2>Learn the method.<br /><em>Not just the answer.</em></h2>
            <p>EngineerAI helps engineering students connect equations, diagrams and physical behaviour — so the process makes sense, not just the final number.</p>
            <ul>{studentFeatures.map((feature) => <li key={feature}><span>✓</span>{feature}</li>)}</ul>
            <a className="text-link" href="#pricing">Explore student access <span>→</span></a>
          </div>
          <div className="student-panel">
            <div className="panel-top"><span>STUDENT WORKSPACE</span><span className="live-pill">LEARNING MODE</span></div>
            <div className="lesson-label">WORKED EXAMPLE / 01</div>
            <h3>Find the support reactions</h3>
            <div className="equation-card"><small>STEP 01 · VERTICAL EQUILIBRIUM</small><strong>∑ Fy = 0</strong><p>RA + RB − 10 = 0</p><div className="equation-result">RA + RB = 10 kN</div></div>
            <div className="equation-card equation-muted"><small>STEP 02 · MOMENT ABOUT A</small><strong>∑ MA = 0</strong><p>RB × 4 − 10 × 2 = 0</p></div>
            <div className="panel-progress"><span /><span /><span /></div>
            <div className="panel-caption">A clear path from the free-body diagram to the answer.</div>
          </div>
        </div>
      </section>

      <section className="section shell business-section" id="business">
        <div className="business-panel">
          <div className="business-copy">
            <div className="eyebrow">FOR ENGINEERING TEAMS</div>
            <h2>Built to support<br /><em>real-world workflows.</em></h2>
            <p>A professional workspace for engineering businesses that need repeatable calculations, organised projects and clear technical records.</p>
            <ul>{businessFeatures.map((feature) => <li key={feature}><span>✓</span>{feature}</li>)}</ul>
            <a className="button button-light" href="#pricing">Explore business plans <span>→</span></a>
          </div>
          <div className="business-stat-card">
            <div className="stat-top"><span>PROJECT OVERVIEW</span><span>PREVIEW</span></div>
            <div className="stat-number">04 <small>ACTIVE WORKSPACES</small></div>
            <div className="stat-divider" />
            <div className="stat-row"><span><i className="stat-dot dot-blue" /> Beam assessment</span><b>Updated today</b></div>
            <div className="stat-row"><span><i className="stat-dot dot-green" /> Shaft calculations</span><b>In review</b></div>
            <div className="stat-row"><span><i className="stat-dot dot-gold" /> Equipment project</span><b>Draft</b></div>
            <div className="stat-footer">TEAM WORKSPACE <span>↗</span></div>
          </div>
        </div>
      </section>

      <section className="pricing-section" id="pricing">
        <div className="shell">
          <div className="pricing-heading">
            <div className="eyebrow">SIMPLE ACCESS</div>
            <h2>Engineering tools should be <em>within reach.</em></h2>
            <p>Start with a plan that fits the way you work.</p>
          </div>
          <div className="pricing-grid">
            <article className="price-card">
              <div className="price-label">STUDENT VERIFIED</div>
              <h3>For students building confidence.</h3>
              <div className="price"><strong>R40</strong><span>/ month</span></div>
              <p className="price-note">Proposed launch price · Student verification required</p>
              <a className="button button-primary price-button" href="#early-access">Student access <span>→</span></a>
              <div className="price-divider" />
              <ul>{studentFeatures.map((feature) => <li key={feature}><span>✓</span>{feature}</li>)}</ul>
              <p className="annual-note">Annual option planned: R400 / year.</p>
            </article>
            <article className="price-card price-business">
              <div className="business-ribbon">FOR PROFESSIONAL TEAMS</div>
              <div className="price-label">BUSINESS</div>
              <h3>For teams that need more from their tools.</h3>
              <div className="price business-price"><strong>Custom</strong></div>
              <p className="price-note">Plans based on team size and requirements</p>
              <a className="button button-dark price-button" href="#early-access">Business enquiries <span>→</span></a>
              <div className="price-divider" />
              <ul>{businessFeatures.map((feature) => <li key={feature}><span>✓</span>{feature}</li>)}</ul>
              <p className="annual-note">Monthly and annual business options planned.</p>
            </article>
          </div>
          <p className="pricing-disclaimer">Pricing and features are proposed for launch planning. Paid subscriptions are not yet available on this preview website.</p>
        </div>
      </section>

      <section className="closing-section shell" id="early-access">
        <div className="closing-card">
          <div className="eyebrow">THE NEXT STEP STARTS HERE</div>
          <h2>Make engineering<br /><em>make sense.</em></h2>
          <p>EngineerAI is being built for students and businesses who want clearer, more useful engineering tools.</p>
          <a className="button button-primary" href="https://engineerai-roda.streamlit.app" target="_blank" rel="noreferrer">Try the current prototype <span>↗</span></a>
          <small>Website accounts and subscriptions are coming in a future release.</small>
        </div>
      </section>

      <footer className="site-footer">
        <div className="shell footer-main">
          <a className="brand footer-brand" href="#"><span className="brand-mark">E</span><span>Engineer<span className="brand-light">AI</span></span></a>
          <p>Engineering, explained.</p>
          <div className="footer-links"><a href="#tools">Platform</a><a href="#students">Students</a><a href="#business">Businesses</a><a href="#pricing">Pricing</a></div>
        </div>
        <div className="shell footer-bottom"><span>© 2026 EngineerAI. All rights reserved.</span><span>Built for better engineering understanding.</span></div>
      </footer>
    </main>
  );
}
