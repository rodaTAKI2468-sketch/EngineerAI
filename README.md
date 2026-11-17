# EngineerAI

EngineerAI is a Python and Streamlit learning tool for structural beam analysis. Its default workflow is exam-style statics: define the beam supports, span and applied loads to calculate reactions, shear-force diagrams and bending-moment diagrams without requiring material or cross-section properties.

## Current features

- Simply supported beams (pin at A, roller at B)
- Cantilever beams (fixed at A, free at the other end)
- Multiple point loads with upward or downward directions
- Multiple partial-span or full-span uniformly distributed loads (UDLs)
- Multiple applied clockwise or counter-clockwise moments
- Automatic support-reaction and equilibrium calculations
- Live beam sketch showing supports and applied loading
- Shear Force Diagram (SFD) and Bending Moment Diagram (BMD) in statics-only mode
- Optional elastic deflection when both Young's modulus E and second moment of area I are supplied
- PNG download of analysis diagrams
- Step-by-step worked solutions for equivalent UDLs, support reactions, SFD and BMD section equations
- Input validation and calculation-method notes

## Run the Streamlit app

Install the dependencies:

```bash
pip install -r requirements.txt
```

Start the app:

```bash
streamlit run app.py
```

## Run the command-line application

```bash
python main.py
```

The command-line application asks whether deflection is required. Answer No for exam-style reactions/SFD/BMD; answer Yes only when E and I are available.

## Run the regression tests

```bash
python -m unittest discover -s tests -v
```

## Engineering model and assumptions

Static beam results use equilibrium and beam section analysis. Reactions, SFD and BMD do not require Young's modulus or second moment of area. When optional deflection is enabled, the engine uses Euler–Bernoulli beam theory and numerical integration of the bending-moment distribution with the relevant support boundary conditions.

The model assumes a prismatic beam, ideal supports, small deflections, linear-elastic behaviour and constant E and I when deflection is calculated. Use consistent units: beam length and load positions in m, point forces in kN, UDL intensities in kN/m, applied moments in kN·m, Young's modulus in GPa and second moment of area in m⁴.

The app can show the equilibrium and piecewise diagram steps used for an entered loading case. The section equations are valid between adjacent load/support events; check the diagram at point loads, UDL boundaries, applied couples and zero-shear locations. The app is an educational analysis aid, not a substitute for independent engineering verification or applicable design standards.

## Independent support configuration (new)

A separate Streamlit page is available under **Support Configuration** in the app's multipage navigation. It lets students select Pin, Roller, Fixed or Free independently at ends A and B, previews the arrangement, and classifies the transverse beam model before analysis.

- Pin–pin and pin–roller end arrangements: determinate for vertical/transverse beam loading.
- Fixed–free and free–fixed cantilevers: determinate.
- A free end paired with only a pin/roller, or two free ends: unstable.
- Fixed–pin, pin–fixed, fixed–fixed and other over-restrained combinations: flagged as statically indeterminate; no unsupported reaction values are fabricated.

The page produces reactions, SFD/BMD and worked equilibrium steps for supported determinate configurations. The free–fixed case is solved by mirroring the beam from its fixed end. This is a transverse beam model: axial/horizontal reactions are not solved, and pin–pin is considered determinate only within that scope. Statically indeterminate cases require a future compatibility/stiffness-method solver using E and I.


## Beam cross-section and stress analysis (new)

The **Multiple-Support Beam Solver** accepts either rectangular dimensions (breadth b and depth h) or supplied section properties (A, I and c). It reports maximum elastic bending stress using σ = Mc/I and transverse shear stress. For a rectangle, it uses τmax = 1.5V/A; for a user-defined section it reports average shear V/A because the exact maximum depends on the section shape and shear-area distribution.

For a rectangular section, A = bh, I = bh³/12, c = h/2 and Z = I/c. Breadth is the dimension across the section; depth is measured in the direction of bending and is the dimension cubed in the second-moment formula. In stiffness/indeterminate mode, the calculated or supplied I is also used by the beam stiffness solver. In determinate exam/statics mode, E is not required for reactions, diagrams or elastic stress calculations. The user-defined option requires A, I and c: area alone is not enough to calculate bending stress.

## Multiple-support and continuous beam solver (new)

The **Multiple-Support Beam Solver** page analyses continuous and statically indeterminate beams using an Euler–Bernoulli beam-element stiffness method.

- Two to eight user-positioned Pin, Roller or Fixed supports, including internal supports.
- Multiple point loads, partial/full-span UDLs and applied couples.
- Reactions at every support, SFD, BMD and elastic deflection.
- Requires E and I because compatibility and deformation are part of the stiffness solution.
- Displays the global stiffness-method workflow and equilibrium residuals.

The model uses two degrees of freedom per node (vertical displacement and rotation), ideal supports, constant EI, small deflections and linear-elastic Euler–Bernoulli theory. Pin and Roller have the same vertical restraint in this transverse-only beam model; neither models axial restraint. The beam is continuous through internal supports (no internal hinges/releases in this first version). Mesh refinement affects numerical accuracy; use engineering judgement and verify results against analytical benchmarks. This is an educational tool, not a substitute for independent engineering verification or applicable design standards.
