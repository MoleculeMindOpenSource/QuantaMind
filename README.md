# QuantaMind MD enables protein modeling with ab initio accuracy

## Overview
This is the offical code for the research article "QuantaMind MD enables protein modeling with ab initio accuracy". **The article is currently under review and the demo is only available for reviewers.** Stay tuned!

## Table of Contents
1. [Installation](#installation)
2. [Running QuantaMind MD Simulation](#running-quantamind-md-simulation)
3. [License](#license)

## Installation

### Download Required Files

First, clone this repo:
```bash
git clone https://github.com/MoleculeMindOpenSource/QuantaMind.git
cd ./QuantaMind
```

Then unzip `demo_data.zip` (**This file is currently only available for reviewers.**) and put all files in the `QuantaMind` folder.

### Install Python Environment
To ensure compatibility and reproducibility, it is recommended to use the following Python environment setup. Follow the steps below to replicate the environment we used for this project:

1. **Install Python 3.8.20**

   Ensure you have Python version 3.8.20 installed. You can download it from [python.org](https://www.python.org/downloads/release/python-3820/).

2. **Set Up a Virtual Environment**

   Create and activate a virtual environment to manage dependencies separately from your system Python.

   ```bash
   python3.8 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

    Alternatively, you can use a conda environment instead.

3. **Install PyTorch 1.12.1**

    The following command installs PyTorch 1.12.1 with CUDA 11.6 support. Adjust the command if your CUDA version is different or if you want to install it CPU-only. Check [Pytorch Official Website](https://pytorch.org/) for details.

    ```bash
    CUDA=cu116 # cpu cu102 cu113 cu116 or rocm5.1.1
    pip install torch==1.12.1+${CUDA} --extra-index-url https://download.pytorch.org/whl/${CUDA}
    ```

4. **Install PyG**
    Install [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/en/2.5.2/)
    ```bash
    pip install torch_geometric==2.5.2
    ```

5. **Install the remaining packages**

    Finally, install the remaining packages using pip

    ```bash
    pip install ase==3.23.0 biopython==1.76 hydra==2.5 matplotlib==3.7.5 omegaconf==2.3.0 tensorboard==2.14.0 PyYAML sympy==1.12 tensorboardX==2.6.2.2 netCDF4==1.6.5
    pip install lightning==2.1.4 torch==1.12.1
    pip install schnetpack==2.0.4
    ```

## Running QuantaMind MD Simulation

**The demo code simulates 216 water molecules for only 500 fs. It takes less than a minute to run on one A100 GPU (80GB memory), or around 6 minutes with CPU-only on 28 CPU cores. To replicate the results in the manuscript, you need to run the simulation on much longer time scale.**

After installing the Python environment, run 

```bash
export PYTHONPATH=.
python scripts/md_run.py demo/demo_cfg.yaml
```

The command runs a simulation on `./demo/H3O.pdb` for 1000 steps with 0.5 fs time step. The simulation result files are saved in `./demo/md-H3O`. Adjust the parameters in `demo/demo_cfg.yaml` if you want to change the simulation parameters.

```yaml
comment: Run MD on H3O+
md_workdir: ./demo/md-H3O
molecule:
  use_pbc: true
  molecule_path: ./demo/H3O.pdb
log_every_n_steps: 5
n_steps: 1000
total_charge: 1
```


## License

This software is licensed under a dual-license model:
1. Academic License: Free for use in academic research, teaching, and non-profit projects. 
2. Commercial License: Required for any commercial or for-profit use.

Definitions:
- Academic Use: Usage by educational institutions, students, and non-profit research projects.
- Commercial Use: Usage for any profit-making activity or by commercial entities.

For more information or to obtain a commercial license, please contact us at [your contact information].

Full License Text: [Link to License Document]
