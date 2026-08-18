# TopPIC Suite and TopREPO Web Console
TopPIC Suite and TopREPO Web Console is a web-based platform designed to automate and simplify top-down proteomics data processing workflows.

## Installation
### System Requirements
- Operating System: Linux (Ubuntu 20.04/22.04)
- Python: 3.10+
- Docker Engine: 24.0.0+
- Wine: 8.0+ 

Please also ensure the following are installed and accessible in your environment PATH:\
[TopRepo](https://github.com/toppic-suite/toprepo/tree/main#1-generate-tsv-files-with-comprehensive-spectral-information)\
[TopPIC Suite](https://toppic.org/software/toppic/register.html)\
[ProteoWizard Linux Wine/Docker](https://proteowizard.sourceforge.io/download.html)
### Building on Linux (Ubuntu 20.04/22.04)
```
# Install Core Utilities, Wine, Docker, C build tools, and XML/Python dependencies
sudo apt install -y \
  python3-venv \
  python3-pip \
  python3-dev \
  build-essential \
  libxml2-dev \
  libxslt1-dev \
  zlib1g-dev \
  wine \
  wine32 \
  psmisc \
  lsof \
  git \
  docker.io
# Clone the repository
git clone https://github.com/whu025/toppic-suite-pipeline.git
cd toppic-suite-pipeline

# Make the launcher script executable
chmod +x run.sh
```
## Tutorial
 In this tutorial, we will use TopIndex, TopFD and TopPIC to analyze a top-down MS/MS data set of Salmonella typhimurium for proteoform identification. You can download the .raw and .fasta files from [Tutorial 1](https://toppic.org/software/toppic/tutorial.html). \  

 Run the command:\
``` ./run.sh```

<img width="926" height="194" alt="Screenshot from 2026-08-17 13-52-49" src="https://github.com/user-attachments/assets/fea5bc99-4ec2-4633-ad9f-76d291142246" />

Navigate to ```http://127.0.0.1:8000/```.

1. Upload st_1.raw, st_2.raw, and uniprot.fasta. 
2. Select Carbamidomethylation on cysteine as the fixed modification.
3. Check the checkbox Decoy database.
4. Select FDR as the spectrum level cutoff type.
5. Select FDR as the proteoform level cutoff type.
<img width="1261" height="1225" alt="Screenshot from 2026-08-18 10-40-24" src="https://github.com/user-attachments/assets/986ee8d9-f154-40e3-a135-022f52ff2e79" />

Click ```Start Pipeline```. You should see updates of the pipeline in your terminal. 
