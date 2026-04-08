import React, { useState } from "react";
import PropTypes from "prop-types";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Tooltip from "@mui/material/Tooltip";
import IconButton from "@mui/material/IconButton";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { CenteredFormModal } from "./CenteredFormModal";
import { API_URL } from "./apiBase";

function arabicUnitLabelForUnit(unit) {
  if (unit === "million_SAR") return "بالملايين";
  if (unit === "thousand_SAR") return "بالآلاف";
  if (unit === "SAR") return "بالريال السعودي";
  return "غير محدد";
}

function directSarOrUnitCaption(unit, mult, unitLabel) {
  if (unit === "SAR" || mult === 1) {
    return "القيم بالريال السعودي مباشرة (بدون تحويل).";
  }
  return `الوحدة: ${unitLabel}`;
}

const evidenceModalEvidencePropShape = PropTypes.shape({
  has_evidence: PropTypes.bool,
  requested_quarter: PropTypes.string,
});

export function EvidenceModal({
  open,
  onClose,
  evidenceData,
  loading,
  error,
  onDataUpdate,
}) {
  const [verifyMode, setVerifyMode] = useState(null);
  const [correctionValue, setCorrectionValue] = useState("");
  const [correctionFeedback, setCorrectionFeedback] = useState("");
  const [submitted, setSubmitted] = useState(false);

  return (
    <CenteredFormModal
      open={open}
      onClose={onClose}
      titleId="evidence-modal-title"
      ariaDescribedBy="evidence-modal-description"
      title="دليل الاستخراج - الأرباح المبقاة"
      titleColor="#1e6641"
      width={{ xs: "95%", md: "70%" }}
      maxWidth={600}
      maxHeight="80vh"
    >
      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", py: 4 }}>
          <CircularProgress sx={{ color: "#1e6641" }} />
          <Typography sx={{ ml: 2, color: "#666" }}>جاري تحميل الدليل...</Typography>
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!loading && evidenceData && (
        <>
          {evidenceData?.evidence?.has_evidence && (
            <Box sx={{ mb: 4 }}>
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "center",
                  border: "2px solid #e0e0e0",
                  borderRadius: 2,
                  overflow: "auto",
                  bgcolor: "#fafafa",
                  maxHeight: "50vh",
                }}
              >
                <img
                  src={`${API_URL}/api/evidence/${evidenceData.company_symbol}.png?quarter=${evidenceData.evidence?.requested_quarter || "Q1_2025"}&t=${Date.now()}`}
                  alt="Evidence Screenshot"
                  style={{
                    maxWidth: "100%",
                    maxHeight: "none",
                    objectFit: "contain",
                  }}
                  onLoad={() => {
                    console.log(
                      "Evidence image loaded with quarter:",
                      evidenceData.evidence?.requested_quarter,
                    );
                    console.log(
                      "Full image URL:",
                      `${API_URL}/api/evidence/${evidenceData.company_symbol}.png?quarter=${evidenceData.evidence?.requested_quarter || "Q1_2025"}&t=${Date.now()}`,
                    );
                  }}
                />
              </Box>
            </Box>
          )}

          {evidenceData.numeric_value && (
            <Box sx={{ mt: 3 }}>
              <Typography
                variant="subtitle1"
                sx={{
                  fontWeight: "bold",
                  color: "#1e6641",
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                }}
              >
                القيمة المستخرجة:{" "}
                {evidenceData.applied_multiplier &&
                  Number(evidenceData.applied_multiplier) > 1 && (
                    <span style={{ color: "#888", fontWeight: 400 }}>(تم تطبيق تحويل الوحدة)</span>
                  )}
              </Typography>
              <Typography variant="h6" sx={{ mt: 0.5 }}>
                {Number(evidenceData.numeric_value).toLocaleString("en-US")} SAR
              </Typography>

              <Box
                sx={{
                  mt: 1.5,
                  p: 1.5,
                  bgcolor: "#f7f9f8",
                  border: "1px solid #e0e6e4",
                  borderRadius: 1.5,
                }}
              >
                {(() => {
                  const rawStr = String(evidenceData.value ?? "").replaceAll(/[^0-9,.-]/g, "");
                  const raw = Number(rawStr.replaceAll(",", ""));
                  const mult = Number(evidenceData.applied_multiplier ?? 1);
                  const unit = String(evidenceData.unit_detected ?? "SAR");
                  const unitLabel = arabicUnitLabelForUnit(unit);
                  if (!raw || mult === 1) {
                    return (
                      <Typography variant="body2" sx={{ color: "#4d4d4d" }}>
                        {directSarOrUnitCaption(unit, mult, unitLabel)}
                      </Typography>
                    );
                  }
                  const result = raw * mult;
                  return (
                    <>
                      <Typography variant="body2" sx={{ color: "#4d4d4d" }}>
                        تم اكتشاف أن القيم {unitLabel}. تم تحويل القيمة كما يلي:
                      </Typography>
                      <Typography
                        variant="body2"
                        sx={{ mt: 0.5, direction: "ltr", fontFamily: "monospace", color: "#1e6641" }}
                      >
                        {raw.toLocaleString("en-US")} × {mult.toLocaleString("en-US")} ={" "}
                        {result.toLocaleString("en-US")}
                      </Typography>
                    </>
                  );
                })()}
              </Box>
            </Box>
          )}

          {evidenceData.extraction_method && (
            <Box
              sx={{
                p: 3,
                bgcolor: "#f8f9fa",
                borderRadius: 2,
                border: "1px solid #e0e0e0",
              }}
            >
              <Typography sx={{ fontSize: "1rem", color: "#666", fontWeight: "500" }}>
                <strong>طريقة الاستخراج:</strong> {evidenceData.extraction_method}
              </Typography>
            </Box>
          )}

          {evidenceData.context && (
            <Box>
              <Typography variant="h6" sx={{ fontWeight: "bold", mb: 2, color: "#1e6641" }}>
                النص المستخرج
              </Typography>
              <Box
                sx={{
                  p: 2,
                  bgcolor: "#f8f9fa",
                  borderRadius: 2,
                  border: "1px solid #e0e0e0",
                  fontFamily: "monospace",
                  fontSize: "14px",
                  whiteSpace: "pre-wrap",
                  maxHeight: "200px",
                  overflow: "auto",
                }}
              >
                {evidenceData.context}
              </Box>
            </Box>
          )}
          {evidenceData?.context && !loading && (
            <Box sx={{ mt: 2, textAlign: "left" }}>
              <Tooltip title="تعديل النتيجة" arrow>
                <IconButton
                  size="small"
                  sx={{
                    color: "#1e6641",
                    opacity: 0.7,
                    ml: 1,
                    "&:hover": { opacity: 1, bgcolor: "#e8f5ee" },
                  }}
                  onClick={() => setVerifyMode(verifyMode ? null : "form")}
                >
                  <InfoOutlinedIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              {verifyMode === "form" && (
                <Box sx={{ mt: 1, display: "flex", flexDirection: "column", gap: 1 }}>
                  <TextField
                    size="small"
                    label="القيمة الصحيحة"
                    value={correctionValue}
                    onChange={(e) => setCorrectionValue(e.target.value)}
                    sx={{ maxWidth: 180 }}
                  />
                  <TextField
                    size="small"
                    label="ملاحظات (اختياري)"
                    value={correctionFeedback}
                    onChange={(e) => setCorrectionFeedback(e.target.value)}
                    sx={{ maxWidth: 250 }}
                  />
                  <Button
                    size="small"
                    variant="contained"
                    color="primary"
                    sx={{ fontSize: 13, px: 2, py: 0.5, mt: 1, alignSelf: "flex-start" }}
                    onClick={async () => {
                      setSubmitted(true);
                      try {
                        const res = await fetch(`${API_URL}/api/correct_retained_earnings`, {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({
                            company_symbol: evidenceData.company_symbol || evidenceData.symbol,
                            correct_value: correctionValue,
                            feedback: correctionFeedback,
                          }),
                        });
                        const data = await res.json();
                        if (data.status === "success") {
                          evidenceData.value = correctionValue;
                          if (typeof onDataUpdate === "function") {
                            onDataUpdate();
                          }
                        }
                      } catch (e) {
                        console.warn("تعذر إرسال التصحيح إلى الخادم", e);
                      }
                      setVerifyMode(null);
                      if (typeof onClose === "function") onClose();
                    }}
                  >
                    إرسال التصحيح
                  </Button>
                  {submitted && (
                    <Typography sx={{ color: "#1e6641", fontSize: 14, mt: 1 }}>
                      شكرًا لملاحظتك! تم تسجيل التصحيح.
                    </Typography>
                  )}
                </Box>
              )}
              {submitted && !verifyMode && (
                <Typography sx={{ color: "#1e6641", fontSize: 14, mt: 1 }}>
                  شكرًا لملاحظتك! تم تسجيل التصحيح.
                </Typography>
              )}
            </Box>
          )}
        </>
      )}
    </CenteredFormModal>
  );
}

EvidenceModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  evidenceData: PropTypes.shape({
    company_symbol: PropTypes.string,
    symbol: PropTypes.string,
    evidence: evidenceModalEvidencePropShape,
    numeric_value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
    applied_multiplier: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
    value: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
    unit_detected: PropTypes.string,
    extraction_method: PropTypes.string,
    context: PropTypes.string,
  }),
  loading: PropTypes.bool,
  error: PropTypes.oneOfType([PropTypes.string, PropTypes.node]),
  onDataUpdate: PropTypes.func,
};

EvidenceModal.defaultProps = {
  evidenceData: null,
  loading: false,
  error: null,
  onDataUpdate: undefined,
};
