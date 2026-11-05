# arcpixi

This is a script to setup an ArcGIS Pro `conda` environment via the Pixi package manager.
Updating environments and adding packages with Pixi is faster and more transparent than `conda`.

## Quickstart

1. [Install Pixi](https://pixi.prefix.dev/latest/installation/)
2. `git clone https://github.com/p-vdp/arcpixi`
3. `cd arcpixi`
4. `pixi run install`
5. Go to ArcGIS Pro -> Settings -> Package Manager -> Environment Manager (gear icon in upper right), then activate the
   new `arcpixi` environment
   ([docs](https://doc.esri.com/en/arcgis-pro/latest/arcpy/get-started/activate-an-environment.html))
6. To test, open the `Python Command Prompt` and try:
    - `python -c "import arcpy"` (no error is good)
    - `conda update --all` (should see "All requested packages already installed.")

## Updating

1. `cd arcpixi/arcpixi_env`
2. `pixi upgrade`
3. `pixi reinstall`

## Adding Packages

1. `cd arcpixi/arcpixi_env`
2. `pixi add geopandas`
    - `pixi.toml` declares all dependencies and can be edited manually
3. `pixi install`