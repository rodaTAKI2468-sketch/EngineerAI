# EngineerAI

EngineerAI is a Python and Streamlit learning tool for structural beam analysis. It helps students explore support reactions, shear-force diagrams, bending-moment diagrams and elastic deflection.

## Current features

- Simply supported beams (pin at A, roller at B)
- Cantilever beams (fixed at A, free at the other end)
- Multiple point loads with upward or downward directions
- Multiple partial-span or full-span uniformly distributed loads (UDLs)
- Multiple applied clockwise or counter-clockwise moments
- Automatic support-reaction and equilibrium calculations
- Live beam sketch showing supports and applied loading
- Shear Force Diagram (SFD), Bending Moment Diagram (BMD) and deflection curve
- PNG download of the analysis diagrams
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

## Run the regression tests

The beam calculation engine has standard-library unittest tests:

```bash
python -m unittest discover -s tests -v
```

## Engineering model and assumptions

The analysis engine uses static equilibrium and Euler–Bernoulli beam theory. Deflection is calculated by numerically integrating the bending-moment distribution with the relevant support boundary conditions. The model assumes a prismatic beam with constant Young's modulus and second moment of area, linear-elastic material behaviour, small deflections and ideal supports.

Use consistent units: beam length and load positions in m, point forces in kN, UDL intensities in kN/m, applied moments in kN·m, Young's modulus in GPa and second moment of area in m⁴.

The app is an educational analysis aid, not a substitute for independent engineering verification or applicable design standards.
