conda create -n NERF_TURRET python=3.8
conda activate -n NERF_TURRET
pip install -r requirements.txt

cd  ./components/nerf_turret_utils

# The -e option installs your package in "editable" mode, 
# which means that any changes you make to the package files will be immediately reflected in your installed package.
pip install -e .
