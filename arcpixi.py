import _winapi
import argparse
import os
from pathlib import Path
from subprocess import run

ARCPY_PATH_SYSTEM = Path(r"C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3")
ARCPY_PATH_USER = Path(
    os.environ.get("LOCALAPPDATA", ""),
    r"Programs\ArcGIS\Pro\bin\Python\envs\arcgispro-py3",
)


def install(
    arcpy_path: str | os.PathLike | None = None,
    env: str | os.PathLike | None = None,
    junction: str | os.PathLike | None = None,
    dry_run: bool = False,
):
    if dry_run:
        raise NotImplementedError("Dry run not implemented yet")

    if arcpy_path:
        arcpy_path = Path(arcpy_path)
    else:
        if ARCPY_PATH_SYSTEM.exists():
            arcpy_path = ARCPY_PATH_SYSTEM
        elif ARCPY_PATH_USER.exists():
            arcpy_path = ARCPY_PATH_USER
        else:
            raise FileNotFoundError(
                "ArcPy environment not found. Specify the path with -a <PATH>"
            )

    if env:
        env = Path(env) / "arcpixi"
    else:
        env = Path(__file__).parent / "arcpixi_env"

    if not junction:
        junction = Path(os.environ.get("LOCALAPPDATA", ""), "ESRI/conda/envs/arcpixi")
    else:
        junction = Path(junction)

    print(f'- ArcPy path: "{arcpy_path}"')
    print(f'- New environment location: "{env}"')
    print(f'- Junction file: "{junction}"')
    print(f"- Dry run: {dry_run}")

    pins_path = arcpy_path / "conda-meta" / "pinned"
    pins = pins_path.read_text().splitlines()

    arcpy_version = ""
    base_deps = []
    deps = []
    for dep in pins:
        if " " in dep:
            dep_name, dep_version = dep.strip().split(" ")[0:2]
            base_deps.append(f"{dep_name}=={dep_version}")
            if dep_name == "arcpy":
                arcpy_version = dep_version
        else:
            deps.append(dep)
    print(f"- ArcPy version: {arcpy_version}")

    # TODO dry run
    (env / "pixi.toml").unlink(missing_ok=True)
    (env / "pixi.lock").unlink(missing_ok=True)

    run(
        [
            "pixi",
            "init",
            env,
            "--platform",
            "win-64",
            "--channel",
            "esri",
            "--channel",
            "main",
            "--channel",
            "r",
            "--channel",
            "msys2",
        ],
        check=False,
    )

    with open(env / "config.toml", "w") as f:
        f.write(
            'run-post-link-scripts = "insecure"  # allow Scripts/.arcpy-base-post-link.bat'
        )

    run(["pixi", "add", "-m", env] + base_deps + deps, check=False, capture_output=True)

    with open(env / "pixi.toml", "a") as f:
        f.write("\n[constraints]")
        for dep in base_deps:
            dep_name, dep_version = dep.split("==")
            if dep_version.endswith("*"):
                f.write(f'\n{dep_name} = "{dep_version}"')
            else:
                f.write(f'\n{dep_name} = "=={dep_version}"')

    pins_path.copy_into(env / ".pixi/envs/default/conda-meta")

    run(["pixi", "upgrade", "-m", env], check=False)
    run(["pixi", "install", "-m", env], check=False)

    junction.unlink(missing_ok=True)
    _winapi.CreateJunction((env / ".pixi/envs/default").as_posix(), junction.as_posix())
    print(f"Created junction: {junction}")
    print(
        "\nDone!\nGo to ArcGIS Pro -> Settings -> Package Manager -> Environment Manager (gear icon in upper right), then activate your new environment."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--arcpy-path", help="The path to `arcgispro-py3`")
    parser.add_argument(
        "-e", "--env", help="The destination folder for the environment"
    )
    parser.add_argument(
        "-j", "--junction", help="The junction file that points at the environment"
    )
    parser.add_argument(
        "--dry-run", help="Don't create any new files", action="store_true"
    )
    parser.parse_args()

    install(
        arcpy_path=parser.parse_args().arcpy_path,
        env=parser.parse_args().env,
        junction=parser.parse_args().junction,
        dry_run=parser.parse_args().dry_run,
    )
