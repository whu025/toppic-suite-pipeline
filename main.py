import os
import shutil
import subprocess
import uvicorn
from typing import List, Optional
from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="TopPIC Suite & TopRepo Web Console")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configure environment directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOST_DATA_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(HOST_DATA_DIR, exist_ok=True)

# Path to the local toprepo repository root directory
TOPREPO_DIR = os.path.join(os.path.expanduser("~"), "build", "toprepo")


@app.get("/", response_class=HTMLResponse)
@app.get("/upload", response_class=HTMLResponse)
async def get_basic_form(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/api/run-pipeline")
async def run_pipeline(
    spectrum_files: List[UploadFile] = File(...),
    database_file: UploadFile = File(...),
    convert_mzml: Optional[str] = Form(None),
    run_toprepo: Optional[str] = Form(None),
    toprepo_dataset_id: str = Form("PXD029703"),

    # TopFD parameters
    topfd_max_charge: int = Form(30),
    topfd_max_mass: float = Form(50000.0),
    topfd_mz_error: float = Form(0.02),
    topfd_min_scan: int = Form(1),
    topfd_ms1_sn: float = Form(3.0),
    topfd_ms2_sn: float = Form(1.0),
    topfd_ecscore: float = Form(0.1),
    topfd_split_ratio: float = Form(2.5),
    topfd_precursor_window: float = Form(3.0),
    topfd_activation: str = Form("FILE"),
    topfd_threads: int = Form(1),
    topfd_missing_ms1: Optional[str] = Form(None),
    topfd_generate_html: Optional[str] = Form(None),

    # TopPIC Basic parameters
    toppic_fixed_mod: str = Form("NONE"),
    toppic_fixed_mod_file: Optional[UploadFile] = File(None),
    toppic_ptm_file: Optional[UploadFile] = File(None),
    toppic_max_ptm: int = Form(3),
    toppic_decoy: Optional[str] = Form(None),
    toppic_mass_err: float = Form(10.0),
    toppic_threads: int = Form(1),
    toppic_approx_spectra: Optional[str] = Form(None),
    toppic_missing_ms1_feat: Optional[str] = Form(None),
    toppic_cluster_err: float = Form(1.2),
    toppic_spec_cutoff_type: str = Form("EVALUE"),
    toppic_spec_cutoff_val: float = Form(0.01),
    toppic_prot_cutoff_type: str = Form("EVALUE"),
    toppic_prot_cutoff_val: float = Form(0.01),

    # TopPIC Advanced parameters
    toppic_max_shifts: int = Form(1),
    toppic_adv_fragmentation: str = Form("FILE"),
    toppic_min_shift: int = Form(-500),
    toppic_max_shift: int = Form(500),
    toppic_adv_html: Optional[str] = Form(None),
    toppic_adv_keep_decoy: Optional[str] = Form(None),
    toppic_combined_spectra_num: int = Form(1),
    toppic_adv_keep_intermediate: Optional[str] = Form(None),
    toppic_ptm_loc_file: Optional[UploadFile] = File(None),
    toppic_miscore: float = Form(0.15)
):
    def execute_command(cmd, step_name):
        print(f"\n--- [STARTING {step_name.upper()}]: {' '.join(cmd)} ---\n")
        
        # Pass TOPREPO src directory in PYTHONPATH so imports work across modules
        env = os.environ.copy()
        toprepo_src = os.path.join(TOPREPO_DIR, "src")
        env["PYTHONPATH"] = f"{toprepo_src}:{env.get('PYTHONPATH', '')}"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env
        )
        for line in process.stdout:
            print(line, end="")
        process.wait()
        if process.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Error occurred during execution step: {step_name}"
            )

    for spec_file in spectrum_files:
        file_path = os.path.join(HOST_DATA_DIR, spec_file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(spec_file.file, buffer)

    db_path = os.path.join(HOST_DATA_DIR, database_file.filename)
    with open(db_path, "wb") as buffer:
        shutil.copyfileobj(database_file.file, buffer)

    fixed_mod_file_path = None
    if toppic_fixed_mod == "FILE" and toppic_fixed_mod_file and toppic_fixed_mod_file.filename:
        fixed_mod_file_path = os.path.join(HOST_DATA_DIR, toppic_fixed_mod_file.filename)
        with open(fixed_mod_file_path, "wb") as buffer:
            shutil.copyfileobj(toppic_fixed_mod_file.file, buffer)

    ptm_file_path = None
    if toppic_ptm_file and toppic_ptm_file.filename:
        ptm_file_path = os.path.join(HOST_DATA_DIR, toppic_ptm_file.filename)
        with open(ptm_file_path, "wb") as buffer:
            shutil.copyfileobj(toppic_ptm_file.file, buffer)

    # MS Convert
    mzml_files = []
    for spec_file in spectrum_files:
        filename = spec_file.filename
        if convert_mzml:
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{HOST_DATA_DIR}:/data",
                "--entrypoint", "wine",
                "proteowizard/pwiz-skyline-i-agree-to-the-vendor-licenses",
                "msconvert", f"/data/{filename}",
                "--mzML",
                "--filter", "peakPicking true 1-",
                "-o", "/data"
            ]
            execute_command(docker_cmd, f"msconvert ({filename})")
            base = os.path.splitext(filename)[0]
            mzml_p = os.path.join(HOST_DATA_DIR, f"{base}.mzML")
            if not os.path.exists(mzml_p):
                mzml_p = os.path.join(HOST_DATA_DIR, f"{base}.mzml")
            
            if os.path.exists(mzml_p):
                try:
                    os.chmod(mzml_p, 0o666)
                except PermissionError:
                    pass
            mzml_files.append(mzml_p)
        else:
            mzml_files.append(os.path.join(HOST_DATA_DIR, filename))

    # TopFD
    processed_files = []
    for mzml_path in mzml_files:
        base_name = os.path.splitext(os.path.basename(mzml_path))[0]
        
        topfd_cmd = [
            "topfd",
            "-c", str(topfd_max_charge),
            "-m", str(topfd_max_mass),
            "-t", str(topfd_mz_error),
            "-r", str(topfd_ms1_sn),
            "-s", str(topfd_ms2_sn),
            "-w", str(topfd_precursor_window),
            "-a", topfd_activation,
            "-u", str(topfd_threads),
        ]
        if topfd_missing_ms1:
            topfd_cmd.append("-o")
        if topfd_generate_html:
            topfd_cmd.append("-g")

        topfd_cmd.append(mzml_path)
        execute_command(topfd_cmd, f"TopFD ({base_name})")

        ms2_msalign = os.path.join(HOST_DATA_DIR, f"{base_name}_ms2.msalign")
        feature_file = os.path.join(HOST_DATA_DIR, f"{base_name}_ms2.feature")

        # TopPIC
        toppic_cmd = [
            "toppic",
            "-e", str(toppic_mass_err),
            "-u", str(toppic_threads),
            "-p", str(toppic_cluster_err),
            "-s", str(toppic_max_shifts),
            "-m", str(toppic_min_shift),
            "-M", str(toppic_max_shift),
            "-a", toppic_adv_fragmentation,
            "-r", str(toppic_combined_spectra_num),
            "-H", str(toppic_miscore),
        ]

        if toppic_fixed_mod == "FILE" and fixed_mod_file_path:
            toppic_cmd.extend(["-f", fixed_mod_file_path])
        elif toppic_fixed_mod in ["C57", "C58"]:
            toppic_cmd.extend(["-f", toppic_fixed_mod])

        if ptm_file_path:
            toppic_cmd.extend(["-i", ptm_file_path])

        if toppic_spec_cutoff_type == "FDR":
            toppic_cmd.extend(["-t", "FDR", "-v", str(toppic_spec_cutoff_val)])
        else:
            toppic_cmd.extend(["-t", "EVALUE", "-v", str(toppic_spec_cutoff_val)])

        if toppic_prot_cutoff_type == "FDR":
            toppic_cmd.extend(["-T", "FDR", "-V", str(toppic_prot_cutoff_val)])
        else:
            toppic_cmd.extend(["-T", "EVALUE", "-V", str(toppic_prot_cutoff_val)])

        if toppic_decoy:
            toppic_cmd.append("-d")
        if toppic_missing_ms1_feat:
            toppic_cmd.append("-x")
        if toppic_adv_html:
            toppic_cmd.append("-g")
        if toppic_adv_keep_decoy:
            toppic_cmd.append("-K")
        if toppic_adv_keep_intermediate:
            toppic_cmd.append("-k")

        toppic_cmd.extend([db_path, ms2_msalign])
        execute_command(toppic_cmd, f"TopPIC ({base_name})")

        prsm_single_tsv = os.path.join(HOST_DATA_DIR, f"{base_name}_ms2_toppic_prsm_single.tsv")

        # TopREPO
        if run_toprepo:
            dataset_id = toprepo_dataset_id
            mzml_info_tsv = os.path.join(HOST_DATA_DIR, f"{base_name}_mzml_info.tsv")
            msalign_info_tsv = os.path.join(HOST_DATA_DIR, f"{base_name}_msalign_info.tsv")
            feature_info_tsv = os.path.join(HOST_DATA_DIR, f"{base_name}_feature_info.tsv")
            toppic_info_tsv = os.path.join(HOST_DATA_DIR, f"{base_name}_toppic_info.tsv")
            combined_info_tsv = os.path.join(HOST_DATA_DIR, f"{base_name}_combined_info.tsv")

            # 1.1 Extract spectral info from mzML
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/mzml/extract_mzml_info.py"),
                dataset_id, mzml_path, mzml_info_tsv
            ], "TopRepo 1.1: Extract mzML Info")

            # 1.2 Extract spectral info from msalign
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/msalign/extract_msalign_info.py"),
                dataset_id, ms2_msalign, msalign_info_tsv
            ], "TopRepo 1.2: Extract msalign Info")

            # 1.3 Extract feature info from feature file
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/feature/extract_feature_info.py"),
                dataset_id, feature_file, feature_info_tsv
            ], "TopRepo 1.3: Extract Feature Info")

            # 1.4 Preprocess PrSM TSV from TopPIC
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/prsm/prsm_preprocess.py"),
                prsm_single_tsv, dataset_id, "--output", toppic_info_tsv
            ], "TopRepo 1.4: Preprocess PrSM Info")

            # 1.5 Merge spectral info (Updated for v1.8.1)
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/tsv/merge_mzml_msalign_toppic_info_v181.py"),
                mzml_info_tsv, msalign_info_tsv, feature_info_tsv, toppic_info_tsv, combined_info_tsv
            ], "TopRepo 1.5: Merge Spectral Info")

            # 2.1 Preprocess msalign file with dataset ID
            preprocess_msalign = os.path.join(HOST_DATA_DIR, f"{base_name}_preprocess_ms2.msalign")
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/msalign_anno/msalign_preprocess.py"),
                ms2_msalign, dataset_id, preprocess_msalign
            ], "TopRepo 2.1: Preprocess msalign")

            # 2.2 Add PrSM info to msalign file
            prsm_msalign = os.path.join(HOST_DATA_DIR, f"{base_name}_prsm_ms2.msalign")
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/msalign_anno/merge_msalign_prsm.py"),
                "--tsv", combined_info_tsv,
                "--msalign", preprocess_msalign,
                "--out", prsm_msalign
            ], "TopRepo 2.2: Add PrSM Info to msalign")

            # 2.3 Annotate msalign file
            ion_freq_res = os.path.join(TOPREPO_DIR, "resources/toprepo_ion_freq_v1.2.0.tsv")
            if not os.path.exists(ion_freq_res):
                ion_freq_res = os.path.join(TOPREPO_DIR, "src/resources/toprepo_ion_freq_v1.2.0.tsv")

            anno_msalign = os.path.join(HOST_DATA_DIR, f"{base_name}_anno_ms2.msalign")
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/msalign_anno/msalign_anno_based_frequency.py"),
                "--msalign", prsm_msalign,
                "--table", ion_freq_res,
                "--out", anno_msalign
            ], "TopRepo 2.3: Annotate msalign File")

            # 3.1 Convert mzML to mgf
            ms2_mgf = os.path.join(HOST_DATA_DIR, f"{base_name}_ms2.mgf")
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/mzml/convert_mzml_to_mgf.py"),
                mzml_path, ms2_mgf
            ], "TopRepo 3.1: Convert mzML to MGF")

            # 3.2 Add dataset id to mgf file
            dataset_id_mgf = os.path.join(HOST_DATA_DIR, f"{base_name}_dataset_id_ms2.mgf")
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/mgf/mgf_add_dataset_id.py"),
                ms2_mgf, dataset_id, dataset_id_mgf
            ], "TopRepo 3.3: Add Dataset ID to MGF")

            # 3.3 Annotate MGF file
            theo_patt_res = os.path.join(TOPREPO_DIR, "resources/theo_patt.txt")
            if not os.path.exists(theo_patt_res):
                theo_patt_res = os.path.join(TOPREPO_DIR, "src/resources/theo_patt.txt")

            anno_mgf = os.path.join(HOST_DATA_DIR, f"{base_name}_anno_ms2.mgf")
            execute_command([
                "python3", os.path.join(TOPREPO_DIR, "src/process/mgf/mgf_anno_file.py"),
                "--theo_file", theo_patt_res,
                "--mgf_file", dataset_id_mgf,
                "--msalign_file", anno_msalign,
                "--out", anno_mgf
            ], "TopRepo 3.3: Annotate MGF File")

        processed_files.append(base_name)

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Full pipeline executed successfully.",
            "processed_files": processed_files,
        }
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)