import PropTypes from "prop-types";
import Modal from "@mui/material/Modal";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import LinearProgress from "@mui/material/LinearProgress";

const INNER_SX = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  bgcolor: "background.paper",
  borderRadius: 2,
  boxShadow: 24,
  p: 3,
  direction: "rtl",
};

/**
 * Shared shell for PDF / net / combined pipeline progress dialogs (deduplicates App.js modals).
 */
export function PipelineProgressModal({
  open,
  width,
  title,
  titleColor,
  linearColor,
  titleMarginBottom = 1,
  children,
  footer,
}) {
  return (
    <Modal open={open} onClose={() => {}}>
      <Box sx={{ ...INNER_SX, width }}>
        <Typography
          variant="h6"
          sx={{ fontWeight: "bold", color: titleColor, mb: titleMarginBottom }}
        >
          {title}
        </Typography>
        <LinearProgress color={linearColor} />
        {children}
        <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 2 }}>{footer}</Box>
      </Box>
    </Modal>
  );
}

PipelineProgressModal.propTypes = {
  open: PropTypes.bool.isRequired,
  width: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
  titleColor: PropTypes.string.isRequired,
  linearColor: PropTypes.oneOf([
    "primary",
    "secondary",
    "error",
    "info",
    "success",
    "warning",
    "inherit",
  ]).isRequired,
  titleMarginBottom: PropTypes.number,
  children: PropTypes.node,
  footer: PropTypes.node.isRequired,
};

PipelineProgressModal.defaultProps = {
  titleMarginBottom: 1,
  children: null,
};
