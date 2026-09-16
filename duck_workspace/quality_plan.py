"""Required planning fields, not an evaluator or capability-admission gate.

Values describe a concrete plan or reference its document section. Checking
their presence does not verify experiments, plausible bounds or physics.
"""

QUALITY_PLAN_FIELDS = {
    "operating_envelope": (
        "supported_environments_and_limits", "excluded_conditions_and_fallback",
    ),
    "independent_tests": (
        "nominal_boundary_and_failure_cases", "continuous_transitions_and_long_horizon",
        "task_and_physical_rejection_gates",
    ),
    "domain_randomization": (
        "factor_matrix_with_units_bounds_distributions_and_sources",
        "sampling_schedule_correlations_and_curriculum",
        "application_coverage_and_nonaccumulating_reset_tests",
        "randomized_training_or_nonlearned_controller_test_plan",
    ),
    "generalization": (
        "disjoint_train_development_and_final_split_plan",
        "unseen_environment_families_and_combined_shifts",
        "repeats_sample_size_and_uncertainty_plan",
        "per_bucket_thresholds_and_final_candidate_freeze",
    ),
    "physics_validation": (
        "model_actuator_sensor_identity_and_geometry_inertia_audit",
        "contact_solver_timestep_and_fixed_action_cross_engine_checks",
        "measurement_calibration_uncertainty_and_known_gaps",
    ),
    "evidence": (
        "source_policy_controller_and_suite_bindings",
        "per_case_results_failures_and_actual_video",
        "reproduction_and_regression_plan",
    ),
}


def new_quality_plan():
    return {group: dict.fromkeys(fields) for group, fields in QUALITY_PLAN_FIELDS.items()}


def check_quality_plan(value):
    if not isinstance(value, dict):
        return ["quality_plan must be an object; see docs/workspace/BEHAVIOR_VALIDATION.md"]
    errors = []
    for group, fields in QUALITY_PLAN_FIELDS.items():
        section = value.get(group)
        if not isinstance(section, dict):
            errors.append(f"quality_plan.{group} must be an object")
            continue
        for field in fields:
            text = section.get(field)
            if (not isinstance(text, str) or not text.strip()
                    or text.strip().casefold() in {"todo", "tbd", "n/a", "none", "not applicable"}):
                errors.append(f"quality_plan.{group}.{field} requires a concrete plan or section reference")
    return errors
