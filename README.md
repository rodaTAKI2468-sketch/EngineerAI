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
