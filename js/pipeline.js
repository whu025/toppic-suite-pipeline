document.addEventListener("DOMContentLoaded", () => {

    // ---------------------------------------------------------
    // 1. Tab Switching Functionality
    // ---------------------------------------------------------
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');

            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            const targetContent = document.getElementById(targetTab);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });

    // ---------------------------------------------------------
    // 2. Dynamic Toggle for Fixed Modification Upload
    // ---------------------------------------------------------
    const fixedModSelect = document.getElementById('toppic-fixed-mod-select');
    const fixedModFileContainer = document.getElementById('fixed-mod-file-container');
    const fixedModFileInput = document.getElementById('fixed-mod-file-input');

    if (fixedModSelect && fixedModFileContainer) {
        fixedModSelect.addEventListener('change', function () {
            if (this.value === 'FILE') {
                fixedModFileContainer.style.display = 'flex';
            } else {
                fixedModFileContainer.style.display = 'none';
                if (fixedModFileInput) {
                    fixedModFileInput.value = '';
                }
            }
        });
    }

    // ---------------------------------------------------------
    // 3. Dynamic Toggle for TopRepo Input Fields
    // ---------------------------------------------------------
    const runToprepoCheckbox = document.getElementById('run-toprepo-checkbox');
    const toprepoDatasetContainer = document.getElementById('toprepo-dataset-container');
    const toprepoDatasetInput = document.getElementById('toprepo_dataset_id');

    if (runToprepoCheckbox && toprepoDatasetContainer) {
        runToprepoCheckbox.addEventListener('change', function () {
            if (this.checked) {
                toprepoDatasetContainer.style.display = 'flex';
                if (toprepoDatasetInput) toprepoDatasetInput.required = true;
            } else {
                toprepoDatasetContainer.style.display = 'none';
                if (toprepoDatasetInput) toprepoDatasetInput.required = false;
            }
        });
    }

    // ---------------------------------------------------------
    // 4. Reset Button Handler
    // ---------------------------------------------------------
    const resetBtn = document.getElementById('reset-btn');
    const form = document.getElementById('pipeline-form');

    if (resetBtn && form) {
        resetBtn.addEventListener('click', () => {
            form.reset();
            if (fixedModFileContainer) {
                fixedModFileContainer.style.display = 'none';
            }
            if (toprepoDatasetContainer) {
                toprepoDatasetContainer.style.display = 'flex';
            }
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            if (tabs[0]) tabs[0].classList.add('active');
            if (tabContents[0]) tabContents[0].classList.add('active');
        });
    }

    // ---------------------------------------------------------
    // 5. Form Submission Handler
    // ---------------------------------------------------------
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerText = "Running...";
            }

            console.log("Submitting pipeline request...");

            const formData = new FormData(form);

            try {
                const response = await fetch("/api/run-pipeline", {
                    method: "POST",
                    body: formData,
                });

                const result = await response.json();

                if (!response.ok) {
                    alert(`Error: ${result.detail || "Pipeline execution failed."}`);
                    console.error("Server returned an error:", result);
                } else {
                    alert("Complete Pipeline (msconvert -> TopFD -> TopPIC -> TopRepo) finished successfully!");
                    console.log("Success response:", result);
                }
            } catch (err) {
                console.error("Network or submission error:", err);
                alert("Failed to connect to FastAPI server. Check your terminal logs.");
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerText = "Start Pipeline";
                }
            }
        });
    }
});