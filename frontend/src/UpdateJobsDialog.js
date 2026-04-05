import React from "react";
import PropTypes from "prop-types";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import FormControlLabel from "@mui/material/FormControlLabel";
import Checkbox from "@mui/material/Checkbox";
import Typography from "@mui/material/Typography";

async function postJson(url) {
  const res = await fetch(url, { method: "POST" });
  const data = await res.json();
  return { res, data };
}

async function startPdfOnlyPipeline(apiUrl, actions) {
  const { res, data } = await postJson(`${apiUrl}/api/run_pdfs_pipeline`);
  if (res.status === 202) {
    actions.setIsPdfRunning(true);
    actions.setPdfJobStatus({ status: "running" });
    actions.setPdfProgressOpen(true);
    actions.startPollPdf();
    return;
  }
  alert(`❌ لم يتم بدء العملية: ${data.message || ""}`);
}

async function startNetOnlyPipeline(apiUrl, actions) {
  const { res, data } = await postJson(`${apiUrl}/api/run_net_profit_scrape`);
  if (res.status === 202) {
    actions.setIsNetRunning(true);
    actions.setNetJobStatus({ status: "running" });
    actions.setNetProgressOpen(true);
    actions.startPollNet();
    return;
  }
  alert(`❌ لم يتم بدء العملية: ${data.message || ""}`);
}

async function startBothPipelines(apiUrl, actions, bothPdfRunning, bothNetRunning) {
  try {
    const { res: resPdf, data: dataPdf } = await postJson(`${apiUrl}/api/run_pdfs_pipeline`);
    if (resPdf.status === 202) {
      actions.setPdfJobStatus({ status: "running" });
      actions.setBothProgressOpen(true);
      actions.setBothPdfRunning(true);
      actions.startPollPdf(() => {
        actions.setBothPdfRunning(false);
        if (!bothNetRunning) {
          actions.setBothProgressOpen(false);
        }
      });
    } else {
      alert(`❌ لم يتم بدء عملية تحديث PDF: ${dataPdf.message || ""}`);
    }

    const { res: resNet, data: dataNet } = await postJson(`${apiUrl}/api/run_net_profit_scrape`);
    if (resNet.status === 202) {
      actions.setNetJobStatus({ status: "running" });
      actions.setBothProgressOpen(true);
      actions.setBothNetRunning(true);
      actions.startPollNet(() => {
        actions.setBothNetRunning(false);
        if (!bothPdfRunning) {
          actions.setBothProgressOpen(false);
        }
      });
    } else {
      alert(`❌ لم يتم بدء تحديث صافي الربح: ${dataNet.message || ""}`);
    }
  } catch (e) {
    alert(`❌ خطأ في الاتصال بالخادم: ${e.message}`);
  } finally {
    actions.setSelectPdf(false);
    actions.setSelectNet(false);
  }
}

/**
 * Update type selection + start PDF / net / both jobs (extracted from App for lower cognitive complexity).
 */
export function UpdateJobsDialog({
  open,
  onClose,
  apiUrl,
  selectPdf,
  setSelectPdf,
  selectNet,
  setSelectNet,
  startPollPdf,
  startPollNet,
  setIsPdfRunning,
  setPdfJobStatus,
  setPdfProgressOpen,
  setIsNetRunning,
  setNetJobStatus,
  setNetProgressOpen,
  setBothProgressOpen,
  setBothPdfRunning,
  setBothNetRunning,
  bothPdfRunning,
  bothNetRunning,
}) {
  const actions = {
    setIsPdfRunning,
    setPdfJobStatus,
    setPdfProgressOpen,
    startPollPdf,
    setIsNetRunning,
    setNetJobStatus,
    setNetProgressOpen,
    startPollNet,
    setBothProgressOpen,
    setBothPdfRunning,
    setBothNetRunning,
    setSelectPdf,
    setSelectNet,
  };

  const handleStart = async () => {
    onClose();
    if (selectPdf && !selectNet) {
      try {
        await startPdfOnlyPipeline(apiUrl, actions);
      } catch (e) {
        alert(`❌ خطأ في الاتصال بالخادم: ${e.message}`);
      }
      return;
    }
    if (!selectPdf && selectNet) {
      try {
        await startNetOnlyPipeline(apiUrl, actions);
      } catch (e) {
        alert(`❌ خطأ في الاتصال بالخادم: ${e.message}`);
      }
      return;
    }
    await startBothPipelines(apiUrl, actions, bothPdfRunning, bothNetRunning);
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle sx={{ fontWeight: 700, color: "#1e6641" }}>اختر نوع التحديث</DialogTitle>
      <DialogContent sx={{ minWidth: 360 }}>
        <Stack spacing={1.5}>
          <FormControlLabel
            control={
              <Checkbox
                checked={selectPdf}
                onChange={(e) => setSelectPdf(e.target.checked)}
                color="success"
                size="small"
              />
            }
            label="تحديث الأرباح المبقاة (تنزيل واستخراج)"
            sx={{ mr: 0, cursor: "pointer", alignItems: "center" }}
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={selectNet}
                onChange={(e) => setSelectNet(e.target.checked)}
                color="success"
                size="small"
              />
            }
            label="تحديث صافي الربح"
            sx={{ mr: 0, cursor: "pointer", alignItems: "center" }}
          />
          <Typography variant="caption" sx={{ color: "#666" }}>
            يمكن اختيار واحد أو كلاهما.
          </Typography>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} sx={{ color: "#666" }}>
          إلغاء
        </Button>
        <Button
          variant="contained"
          disabled={!selectPdf && !selectNet}
          onClick={handleStart}
          sx={{ bgcolor: "#1e6641", "&:hover": { bgcolor: "#14532d" } }}
        >
          بدء التحديث
        </Button>
      </DialogActions>
    </Dialog>
  );
}

UpdateJobsDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  apiUrl: PropTypes.string.isRequired,
  selectPdf: PropTypes.bool.isRequired,
  setSelectPdf: PropTypes.func.isRequired,
  selectNet: PropTypes.bool.isRequired,
  setSelectNet: PropTypes.func.isRequired,
  startPollPdf: PropTypes.func.isRequired,
  startPollNet: PropTypes.func.isRequired,
  setIsPdfRunning: PropTypes.func.isRequired,
  setPdfJobStatus: PropTypes.func.isRequired,
  setPdfProgressOpen: PropTypes.func.isRequired,
  setIsNetRunning: PropTypes.func.isRequired,
  setNetJobStatus: PropTypes.func.isRequired,
  setNetProgressOpen: PropTypes.func.isRequired,
  setBothProgressOpen: PropTypes.func.isRequired,
  setBothPdfRunning: PropTypes.func.isRequired,
  setBothNetRunning: PropTypes.func.isRequired,
  bothPdfRunning: PropTypes.bool.isRequired,
  bothNetRunning: PropTypes.bool.isRequired,
};
