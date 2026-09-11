# Bridging the Accuracy-Speed Divide in Reactive Molecular Dynamics with QuantaMind MD

## Overview
This is the official code for the research article "[Bridging the Accuracy-Speed Divide in Reactive Molecular Dynamics with QuantaMind MD](https://doi.org/10.1126/sciadv.aeg3595)".

The QuantaMind model weights are not included in this repository. They are available to academic researchers on a non-commercial basis, upon request and subject to the [QuantaMind Non-Commercial Model Parameters Terms of Use](MODEL_PARAMETERS_TERMS_OF_USE.md). To request access, please email: [weights-request@moleculemind.com](mailto:weights-request@moleculemind.com).

## Table of Contents
1. [Installation](#installation)
2. [Running QuantaMind MD Simulation](#running-quantamind-md-simulation)
3. [FAQ](#faq)
4. [License](#license)

## Installation

### Download Required Files

First, clone this repo:
```bash
git clone https://github.com/MoleculeMindOpenSource/QuantaMind.git
cd ./QuantaMind
```

Then download `demo_data.zip`, unzip it, and put all files in the `./demo` folder. Note that the demo requires the model weights, which are available upon request by email (see [Overview](#overview)).

### Install Python Environment
To ensure compatibility and reproducibility, it is recommended to use the following Python environment setup. Follow the steps below to replicate the environment we used for this project:

1. **Set Up a Virtual Environment with Python 3.8.20**

    You can use either conda (step 1.1) or venv (step 1.2) to set up the environment.

    1.1 **Use conda**

    You can use [conda](https://www.anaconda.com/docs/getting-started/miniconda/install) to manage your python environment.

    ```bash
    conda create -n quantamind python==3.8.20 -y
    conda activate quantamind
    ```
    
    1.2 **Use venv**

   Ensure you have Python version 3.8.20 installed. You can download it from [python.org](https://www.python.org/downloads/release/python-3820/).

   Create and activate a virtual environment to manage dependencies separately from your system Python.

   ```bash
   python3.8 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```


2. **Install PyTorch 1.12.1**

    Depending on your system, choose either step 2.1 or 2.2

    2.1 **Linux and Windows**

    The following command installs PyTorch 1.12.1 with CUDA 11.6 support. Adjust the command if your CUDA version is different or if you want to install it CPU-only. Check [Pytorch Official Website](https://pytorch.org/) for details.

    ```bash
    CUDA=cu116 # cpu cu102 cu113 cu116 or rocm5.1.1
    pip install torch==1.12.1+${CUDA} --extra-index-url https://download.pytorch.org/whl/${CUDA}
    ```

    2.2 **OSX**
    
    On macOS in particular, CPU-only wheels are just published as torch==1.12.1 without the +cpu suffix.
    ```bash
    pip install torch==1.12.1
    ```

3. **Install PyG**
    Install [PyTorch Geometric](https://pytorch-geometric.readthedocs.io/en/2.5.2/)
    ```bash
    pip install torch_geometric==2.5.2
    ```

4. **Install the remaining packages**

    Finally, install the remaining packages using pip

    ```bash
    pip install ase==3.23.0 biopython==1.76 hydra==2.5 matplotlib==3.7.5 omegaconf==2.3.0 tensorboard==2.14.0 PyYAML sympy==1.12 tensorboardX==2.6.2.2 
    pip install netCDF4==1.6.5
    pip install lightning==2.1.4 torch==1.12.1
    pip install schnetpack==2.0.4
    ```

    **If you are running on macOS, install netCDF4 using conda instead of pip**

    ```bash
    conda install -c conda-forge netCDF4
    ```

## Running QuantaMind MD Simulation

**The demo code simulates for only 500 fs. It takes less than a minute to run on one A100 GPU (80GB memory), or around 6 minutes with CPU-only on 28 CPU cores. To replicate the results in the manuscript, you need to run the simulation on a much longer time scale.**

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

## FAQ
1. **ERROR: Could not find a version that satisfies the requirement torch==1.12.1+cpu**

    The error comes from the fact that torch==1.12.1+cpu does not exist on PyPI, and PyTorch stopped distributing +cpu wheels after some versions. On **macOS** in particular, CPU-only wheels are just published as torch==1.12.1 without the +cpu suffix.

    ```bash
    pip install torch==1.12.1
    ```

2. **ValueError: did not find HDF5 headers**

    This error is very common on **macOS** when trying to install netCDF4 from source:
    ValueError: did not find HDF5 headers

    That means the build system can’t find HDF5 and netCDF-C libraries/headers.
    Fix Options
    1. (Best) Use Conda prebuilt package

    Since you’re already in a Conda env, just install netCDF4 via conda-forge instead of pip (it comes with HDF5 bundled):

    ```bash
    conda install -c conda-forge netCDF4
    ```

    This will pull in hdf5 and all dependencies cleanly.

    2. (If you insist on pip) Install system libraries first

    If you must install with pip, you’ll need to install HDF5 and netCDF-C via Homebrew first:
    ```bash
    brew install hdf5 netcdf
    ```

    Then point pip to the include/lib directories:
    ```bash 
    HDF5_DIR=/opt/homebrew pip install netCDF4
    ```

## License

Source code and model parameters are governed by two separate sets of terms:

**Source code.** The QuantaMind source code, documentation, and build/utility
scripts are licensed under the Apache License, Version 2.0 (the "License");
you may not use the source code except in compliance with the License. You
may obtain a copy of the License at
https://www.apache.org/licenses/LICENSE-2.0. See the [LICENSE](LICENSE) file
for the complete notice.

**Model parameters.** The QuantaMind model parameters, weights, and
checkpoints are not covered by the Apache License and are not open
source; you may not use them except in compliance with the
[QuantaMind Non-Commercial Model Parameters Terms of Use](MODEL_PARAMETERS_TERMS_OF_USE.md)
(the "Terms"). Access to the model parameters is available to academic
researchers on a non-commercial basis, upon request. To request access,
please email: [weights-request@moleculemind.com](mailto:weights-request@moleculemind.com).
Commercial use of the model parameters requires an executed Commercial
License Agreement; for commercial licensing enquiries please email:
[licensing@moleculemind.com](mailto:licensing@moleculemind.com).

Unless required by applicable law, QuantaMind and its output
are distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. You are solely responsible for determining
the appropriateness of using QuantaMind, or using or distributing its source
code, model parameters, or output, and assume any and all risks associated
with such use or distribution and your exercise of rights and obligations
under the relevant terms. QuantaMind outputs are predictions with varying
levels of confidence and should be interpreted carefully. Use discretion
before relying on, publishing, downloading, or otherwise using the
QuantaMind outputs.

QuantaMind and its output are for theoretical and
scientific modeling only. They are not intended, validated, or approved for
clinical use, and you should not use them for clinical purposes or rely on
them for medical or other professional advice. Any content regarding those
topics is provided for informational purposes only and is not a substitute
for advice from a qualified professional. See the relevant terms for the
specific language governing permissions and limitations thereunder.

## Citation

If you use QuantaMind in your research, please cite:
```bib
@article{xia2026quantamind,
  title = {Bridging the accuracy-speed divide in reactive molecular dynamics with QuantaMind MD},
  author = {Xia, Song and Zhang, Deqiang and Shang, Xu and Xu, Jinbo},
  journal = {Science Advances},
  volume = {12},
  number = {37},
  pages = {eaeg3595},
  year = {2026},
  doi = {10.1126/sciadv.aeg3595},
  publisher = {American Association for the Advancement of Science}
}
```