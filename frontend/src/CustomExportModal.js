import PropTypes from "prop-types";
import Modal from "@mui/material/Modal";
import Fade from "@mui/material/Fade";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import IconButton from "@mui/material/IconButton";
import CircularProgress from "@mui/material/CircularProgress";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import { quarterLabelFromDateString } from "./gridUtils";

const OUTLINED_FIELD_SX = {
  "& .MuiOutlinedInput-root": {
    borderRadius: 3,
    fontSize: 14,
    "& fieldset": {
      borderColor: "#e0e0e0",
      borderWidth: 2,
    },
    "&:hover fieldset": {
      borderColor: "#1e6641",
      borderWidth: 2,
    },
    "&:focus fieldset": {
      borderColor: "#1e6641",
      borderWidth: 2,
    },
  },
  "& .MuiInputLabel-root": {
    color: "#666",
    fontSize: 13,
    fontWeight: 500,
  },
};

const SECTION_LABEL_SX = {
  fontWeight: 600,
  color: "#1e6641",
  mb: 1.5,
  fontSize: 14,
  display: "flex",
  alignItems: "center",
  gap: 1,
};

export function CustomExportModal({
  open,
  onClose,
  customExportDate,
  onCustomExportDateChange,
  customFileName,
  onCustomFileNameChange,
  loading,
  onExport,
}) {
  return (
    <Modal open={open} onClose={onClose} closeAfterTransition>
      <Fade in={open}>
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: { xs: "90vw", sm: 480 },
            bgcolor: "background.paper",
            borderRadius: 4,
            boxShadow: "0 20px 60px rgba(0,0,0,0.15)",
            p: 0,
            outline: "none",
            direction: "rtl",
          }}
        >
          <Box
            sx={{
              bgcolor: "linear-gradient(135deg, #1e6641 0%, #2d7a4a 100%)",
              color: "white",
              px: 3,
              py: 2.5,
              borderRadius: "16px 16px 0 0",
              position: "relative",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    bgcolor: "rgba(255,255,255,0.2)",
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 18,
                    fontWeight: "bold",
                  }}
                >
                  E
                </Box>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: "bold", fontSize: 16, mb: 0.5 }}>
                    التصدير المخصص
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, fontSize: 12 }}>
                    تصدير البيانات لتاريخ معين
                  </Typography>
                </Box>
              </Box>
              <IconButton
                onClick={onClose}
                sx={{
                  color: "white",
                  bgcolor: "rgba(255,255,255,0.1)",
                  "&:hover": { bgcolor: "rgba(255,255,255,0.2)" },
                }}
                size="small"
              >
                ✕
              </IconButton>
            </Box>
          </Box>

          <Box sx={{ p: 3, position: "relative" }}>
            <Stack spacing={2} sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={SECTION_LABEL_SX}>
                تاريخ التصدير
              </Typography>
              <TextField
                type="date"
                fullWidth
                value={customExportDate}
                onChange={(e) => onCustomExportDateChange(e.target.value)}
                sx={OUTLINED_FIELD_SX}
                size="medium"
              />
              {customExportDate && (
                <Box
                  sx={{
                    p: 3,
                    bgcolor: "linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)",
                    borderRadius: 3,
                    border: "2px solid #0ea5e9",
                    animation: "fadeInUp 0.4s ease-out",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
                    <Box
                      sx={{
                        width: 32,
                        height: 32,
                        bgcolor: "#0ea5e9",
                        borderRadius: "50%",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "white",
                        fontSize: 14,
                        fontWeight: "bold",
                      }}
                    >
                      Q
                    </Box>
                    <Typography variant="subtitle2" sx={{ color: "#0369a1", fontWeight: "bold", fontSize: 14 }}>
                      الربع المحتوي على التاريخ
                    </Typography>
                  </Box>
                  <Typography variant="h6" sx={{ color: "#0369a1", fontWeight: "bold", fontSize: 18, textAlign: "center" }}>
                    {quarterLabelFromDateString(customExportDate)}
                  </Typography>
                </Box>
              )}
            </Stack>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" sx={SECTION_LABEL_SX}>
                اسم الملف المخصص (اختياري)
              </Typography>
              <TextField
                fullWidth
                placeholder="مثال: تقرير_ديسمبر_2024"
                value={customFileName}
                onChange={(e) => onCustomFileNameChange(e.target.value)}
                sx={OUTLINED_FIELD_SX}
                size="medium"
              />
              <Typography
                variant="caption"
                sx={{
                  color: "#666",
                  fontSize: 11,
                  mt: 0.5,
                  display: "block",
                  fontStyle: "italic",
                }}
              >
                سيتم إضافة التاريخ والوقت تلقائياً إذا لم تحدد اسماً مخصصاً
              </Typography>
            </Box>

            <Box
              sx={{
                display: "flex",
                gap: 2,
                justifyContent: "flex-end",
                mt: 3,
              }}
            >
              <Button
                variant="outlined"
                onClick={onClose}
                sx={{
                  borderRadius: 3,
                  px: 3,
                  py: 1.2,
                  borderColor: "#e0e0e0",
                  color: "#666",
                  fontWeight: 600,
                  fontSize: 13,
                  textTransform: "none",
                  "&:hover": {
                    borderColor: "#d0d0d0",
                    bgcolor: "#f8f8f8",
                  },
                }}
              >
                إلغاء
              </Button>
              <Button
                variant="contained"
                onClick={onExport}
                disabled={!customExportDate}
                sx={{
                  borderRadius: 3,
                  px: 4,
                  py: 1.2,
                  bgcolor: customExportDate ? "#1e6641" : "#ccc",
                  color: "white",
                  fontWeight: "bold",
                  fontSize: 14,
                  textTransform: "none",
                  minWidth: 140,
                  transition: "all 0.3s ease-out",
                  "&:hover": {
                    bgcolor: customExportDate ? "#14532d" : "#ccc",
                    transform: customExportDate ? "translateY(-2px)" : "none",
                    boxShadow: customExportDate ? "0 8px 20px rgba(30, 102, 65, 0.3)" : "none",
                  },
                  "&:disabled": {
                    bgcolor: "#ccc",
                    cursor: "not-allowed",
                    transform: "none",
                  },
                }}
                startIcon={<FileDownloadIcon />}
              >
                {customExportDate ? "تصدير" : "اختر تاريخ أولاً"}
              </Button>
            </Box>

            {loading && (
              <Box
                sx={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  bgcolor: "rgba(255,255,255,0.8)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: 4,
                }}
              >
                <Box sx={{ textAlign: "center" }}>
                  <CircularProgress size={40} sx={{ color: "#1e6641", mb: 2 }} />
                  <Typography variant="body2" sx={{ color: "#1e6641", fontWeight: 600 }}>
                    جاري التصدير...
                  </Typography>
                </Box>
              </Box>
            )}
          </Box>
        </Box>
      </Fade>
    </Modal>
  );
}

CustomExportModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  customExportDate: PropTypes.string.isRequired,
  onCustomExportDateChange: PropTypes.func.isRequired,
  customFileName: PropTypes.string.isRequired,
  onCustomFileNameChange: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
  onExport: PropTypes.func.isRequired,
};
