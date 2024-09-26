from experiment.design import Treatment, AssetConfigurations, ResourceConfigurations
import copy


def build_system_config(asset_configs: AssetConfigurations, resource_configs: ResourceConfigurations):
    return {"ops": asset_configs.export(), "resources": resource_configs.export()}


def introduce_treatment(system_config: dict, treatments: list[Treatment] | Treatment) -> dict:
    system_config = copy.deepcopy(system_config)
    if isinstance(treatments, Treatment):
        treatments = [treatments]
    for treatment in treatments:
        if treatment.dagster_type == "Asset":
            dtype = "ops"
        elif treatment.dagster_type == "Resource":
            dtype = "resources"
        else:
            raise ValueError(f"Unknown Dagster type {treatment.dagster_type}")
        system_config[dtype][treatment.key]["config"][treatment.factor] = treatment.value
    return system_config
