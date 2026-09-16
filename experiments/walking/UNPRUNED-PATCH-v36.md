# V36 retain contact patch constraints

V35 exact hulls with GJK contact patches still fail the numerical gate. The
installed Genesis default prunes nearby/interior contact points, while the
native replay retains clustered constraints. Isolate this property by setting
`contact_pruning_tolerance=None` on V35. All other geometry, contact parameters,
solver settings, action bytes, initial conditions and five comparison prefixes
remain unchanged. Retain the geometry import and original native reproduction
checks, 200-Hz contact telemetry and the same 2-mm/5-degree limits.
This may identify manifold reduction sensitivity; it is not material fitting
and cannot establish physical accuracy or walking quality.
