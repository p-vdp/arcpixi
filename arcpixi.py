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

_HR_WIDTH = 80


def _hr(title: str | None = None, c: str = "=") -> str:
    """Generate horizontal rule strings."""
    if title:
        return f" {title} ".center(_HR_WIDTH, c)
    else:
        return c * _HR_WIDTH


def install(
    arcpy_path: str | os.PathLike | None = None,
    env: str | os.PathLike | None = None,
    junction: str | os.PathLike | None = None,
    dry_run: bool = False,
):
    """Set up an ArcGIS Pro `conda` environment via the Pixi package manager."""

    # determine the location of the stock environment
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

    # new environment path
    if env:
        env = Path(env)
    else:
        env = Path(__file__).parent / "arcpixi_env"

    # junction path
    if not junction:
        junction = Path(os.environ.get("LOCALAPPDATA", ""), "ESRI/conda/envs/arcpixi")
    else:
        junction = Path(junction)

    print()
    print(_hr("ARCPIXI CONFIG"))
    print(f'- ArcPy path: "{arcpy_path}"')
    print(f'- New environment location: "{env}"')
    print(f'- Junction file: "{junction}"')
    print(f"- Dry run: {dry_run}")
    print(_hr())

    print()
    print(_hr("ENVIRONMENT SPECS"))
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
    print(f"- Version-pinned dependencies: {len(base_deps)}")
    print(f"- Unpinned dependencies: {len(deps)}")
    print(f"- ArcPy version: {arcpy_version}")
    print(_hr())

    print()
    if not dry_run:
        print(_hr("EXECUTING"))
    else:
        print(_hr("EXECUTING (DRY RUN)"))

    env_pixi_lock = env / "pixi.lock"
    env_pixi_toml = env / "pixi.toml"
    print(f"- Deleting: {env_pixi_lock}")
    if not dry_run:
        env_pixi_lock.unlink(missing_ok=True)

    print(f"- Deleting: {env_pixi_toml}")
    if not dry_run:
        env_pixi_toml.unlink(missing_ok=True)

    pixi_init_args = [
        "pixi",
        "init",
        env.as_posix(),
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
    ]
    print(f"- Running: {' '.join(pixi_init_args)}")
    if not dry_run:
        run(pixi_init_args, check=False, capture_output=True)

    pixi_config_toml = env / "config.toml"
    print(f"- Writing: {pixi_config_toml}")
    if not dry_run:
        with open(pixi_config_toml, "w") as f:
            f.write(
                'run-post-link-scripts = "insecure"  # allow Scripts/.arcpy-base-post-link.bat'
            )

    pixi_add_args = ["pixi", "add", "-m", env.as_posix()] + base_deps + deps
    print(f"- Adding dependencies: {' '.join(pixi_add_args)}")
    if not dry_run:
        run(
            pixi_add_args,
            check=False,
            capture_output=True,
        )

    print(f"- Adding constraints: {', '.join(base_deps)}")
    if not dry_run:
        with open(env / "pixi.toml", "a") as f:
            f.write("\n[constraints]")
            for dep in base_deps:
                dep_name, dep_version = dep.split("==")
                if dep_version.endswith("*"):
                    f.write(f'\n{dep_name} = "{dep_version}"')
                else:
                    f.write(f'\n{dep_name} = "=={dep_version}"')

    pins_path_dest = env / ".pixi/envs/default/conda-meta"
    print(f"- Copying pins: {pins_path} -> {pins_path_dest}")
    if not dry_run:
        pins_path.copy_into(pins_path_dest)

    pixi_upgrade_args = ["pixi", "upgrade", "-m", env.as_posix()]
    print(f"- Running: {' '.join(pixi_upgrade_args)}")
    if not dry_run:
        run(pixi_upgrade_args, check=False, capture_output=True)

    pixi_install_args = ["pixi", "install", "-m", env.as_posix()]
    print(f"- Running: {' '.join(pixi_install_args)}")
    if not dry_run:
        run(pixi_install_args, check=False, capture_output=True)

    print(f"- (Re)creating junction: {junction}")
    if not dry_run:
        junction.unlink(missing_ok=True)
        _winapi.CreateJunction(
            (env / ".pixi/envs/default").as_posix(), junction.as_posix()
        )
    print(_hr())

    print()
    print("Done!")
    print(
        "Go to ArcGIS Pro -> Settings -> Package Manager -> Environment Manager "
        "(gear icon in upper right), then activate your new environment:"
    )
    print(junction)


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
