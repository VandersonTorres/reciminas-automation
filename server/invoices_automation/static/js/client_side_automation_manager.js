document.addEventListener("DOMContentLoaded", () => {
    const cfg = document.getElementById("automationConfig").dataset;

    const urls = {
        getLogs: cfg.getLogsUrl,
        clearLogs: cfg.clearLogsUrl,
        followLogs: cfg.followLogsUrl,
        cancel: cfg.cancelUrl,
        dashboard: cfg.dashboardUrl,
        getPdfs: cfg.getPdfsUrl,
        approve: cfg.approveUrl,
        servePdf: cfg.servePdfUrl,
    };

    const jobId = cfg.jobId;
    const csrfToken = cfg.csrfToken;

    let cancelConfirmed = false;
    let finished = false;
    let pendingPdfs = [];
    let currentPdfIndex = 0;

    function fetchLogs() {
        if (!cancelConfirmed && !finished) {
            fetch(urls.getLogs)
                .then(response => response.json())
                .then(data => {
                    const logsEl = document.getElementById("logs");
                    logsEl.innerText = data.logs.join("\n");
                    const lastLines = data.logs.slice(-2).join("\n");

                    if (lastLines.includes("Automação cancelada")) {
                        cancelConfirmed = true;
                        finished = true;
                        updateAlertCancelled();
                    }

                    if (lastLines.includes("Término do processo") && !cancelConfirmed) {
                        finished = true;
                        updateAlertSuccess();
                    }
                });
        }
    }

    function updateAlertCancelled() {
        const alertEl = document.getElementById("automationAlert");

        alertEl.className = "alert alert-info";
        alertEl.innerHTML = `
            ⛔ Automação cancelada.<br>
            <a href="${urls.dashboard}" class="btn btn-secondary btn-sm mt-2">
                Voltar ao Dashboard
            </a>
        `;

        const messagesEl = document.querySelector(".alert-dismissible");
        if (messagesEl) {
            messagesEl.innerHTML = "Processo cancelado.";
        }
        const cancelBtn = document.getElementById("cancelButton");
        if (cancelBtn) {
            cancelBtn.style.display = "none";
        }
        const spinner = document.getElementById("cancelLoadingSpinner");
        if (spinner) {
            spinner.style.display = "none";
        }
        
        fetch(urls.clearLogs, { method: "POST" })
            .then((response) => response.json())
            .then((data) => console.log("Logs limpos:", data))
            .catch((err) => console.error("Erro ao limpar logs:", err));
    }

    function updateAlertSuccess() {
        const alertEl = document.getElementById("automationAlert");
        alertEl.classList.remove("alert-warning");
        alertEl.classList.add("alert-success");
        alertEl.style.borderLeft = "6px solid #198754";
        alertEl.innerHTML = `
            ✅ <span class="text-success">Automação concluída com sucesso!</span><br>
            <a href="${urls.dashboard}" class="btn btn-success btn-sm mt-2 shadow-sm">⬅️ Voltar ao Dashboard</a>
        `;
        fetch(urls.clearLogs, { method: "POST" })
            .then((response) => response.json())
            .then((data) => console.log("Logs limpos:", data))
            .catch((err) => console.error("Erro ao limpar logs:", err));
    }

    setInterval(fetchLogs, 1000);
    fetchLogs();

    document.getElementById("cancelButton").addEventListener("click", () => {
        if (confirm("Deseja realmente cancelar a automação em andamento?")) {
            // Show loading spinner
            const spinner = document.createElement("div");
            spinner.id = "cancelLoadingSpinner";
            spinner.innerHTML = `<div class="spinner-border text-danger" role="status" style="margin-left:10px;"><span class="visually-hidden">Carregando...</span></div>`;
            document.getElementById("cancelButton").parentNode.appendChild(spinner);
            spinner.style.display = "inline-block";

            fetch(urls.cancel, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": csrfToken,
                },
                body: new URLSearchParams({ job_id: jobId }),
            })
                .then(r => r.json())
                .then(data => {
                    if (data.status === "cancelling") {
                        alert("Prosseguindo com cancelamento...");
                        window.location.href = urls.followLogs;
                    } else {
                        alert("Erro ao cancelar: " + (data.error || "Desconhecido"));
                    }
                });
        }
    });

    function fetchPendingPdfsLoop() {
        fetch(`${urls.getPdfs}?job_id=${jobId}`)
            .then(r => r.json())
            .then(data => {
                if (data.results.length !== pendingPdfs.length) {
                    pendingPdfs = data.results;
                    currentPdfIndex = 0;
                    finished = false;
                }
                if (pendingPdfs.length > 0) {
                    showNextPdf();
                } else {
                    setTimeout(fetchPendingPdfsLoop, 1000);
                }
            });
    }

    function showNextPdf() {
        if (currentPdfIndex >= pendingPdfs.length) {
            if (!finished) setTimeout(fetchPendingPdfsLoop, 1000);
            return;
        }

        const pdfInfo = pendingPdfs[currentPdfIndex];
        if (pdfInfo.status === "pending") {
            let cleanPath = pdfInfo.pdf_path.replace(/^downloads\//, "");
            const pdfUrl = urls.servePdf.replace("__PLACEHOLDER__", cleanPath);
            document.getElementById("pdfFrame").src = pdfUrl;

            const modal = new bootstrap.Modal(document.getElementById("pdfApprovalModal"));
            modal.show();

            document.getElementById("approveBtn").onclick = () => {
                fetch(urls.approve, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-CSRFToken": csrfToken,
                    },
                    body: new URLSearchParams({ task_id: pdfInfo.task_id, action: "approve" }),
                }).then(() => {
                    modal.hide();
                    currentPdfIndex++;
                    showNextPdf();
                });
            };

            document.getElementById("cancelBtn").onclick = () => {
                fetch(urls.approve, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "X-CSRFToken": csrfToken,
                    },
                    body: new URLSearchParams({ task_id: pdfInfo.task_id, action: "cancel" }),
                }).then(() => {
                    modal.hide();
                    currentPdfIndex++;
                    showNextPdf();
                });
            };
        } else {
            currentPdfIndex++;
            showNextPdf();
        }
    }

    fetchPendingPdfsLoop();
});
