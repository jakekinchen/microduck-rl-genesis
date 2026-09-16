# V39 integration scheme isolation

V37 compatibility mode did not pass the five-prefix gate. V34 remains the best
matched-hull MPR comparison, with two passing profiles. Its Genesis integration
scheme is approximate implicitfast, whereas native MuJoCo uses Euler with
implicit joint damping. Change only Genesis integrator to Euler on V34, keeping
the 5-ms step, motor law and contact representation. Reuse the same five exact
prefixes, 200-Hz observations, collider audit and 2-mm/5-degree numerical gates.
No outcome-dependent parameter fitting or altered-action replay. Retain each
negative and the original V30 native behavior result separately.
