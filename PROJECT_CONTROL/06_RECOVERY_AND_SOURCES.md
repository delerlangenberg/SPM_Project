# Recovery and Source Authority

## Canonical working source

Spark:

`/srv/doro_lab_projects/apps/spm-prusa`

## Old Windows recovery source

SPM PC:

`10.0.18.20`

Protected backup:

`D:\SPM_Migration_Backups\SPM_PRE_SPARK_MIGRATION_20260911_104801`

## Important verified milestone

`D:\SPM_Prusa_Project\backups\phase_milestones\v1.3.0.0_stage2_centered_verified_20260730`

## Latest release

`D:\SPM_Prusa_Project\backups\phase_milestones\v1.3.1.0_adaptive_object_release_20260731`

## Stage backup policy

After every fully completed and verified major stage create exactly one:

`STAGE_<N>_COMPLETE_YYYYMMDD_HHMMSS`

Remove failed/incomplete duplicate stage backups.

Do not remove the Windows recovery source until Spark has successfully completed real hardware commissioning and one verified scientific measurement.
