import PropTypes from "prop-types";
import Modal from "@mui/material/Modal";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";

/**
 * Centered RTL dialog shell with title row + close (deduplicates Evidence / Edit modals in App.js).
 */
export function CenteredFormModal({
  open,
  onClose,
  titleId,
  ariaDescribedBy,
  title,
  titleColor,
  width,
  maxWidth,
  maxHeight,
  children,
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      aria-labelledby={titleId}
      aria-describedby={ariaDescribedBy}
    >
      <Box
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width,
          maxWidth,
          maxHeight,
          bgcolor: "background.paper",
          borderRadius: 3,
          boxShadow: 24,
          p: 3,
          overflow: "auto",
          direction: "rtl",
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 3,
          }}
        >
          <Typography
            id={titleId}
            variant="h5"
            component="h2"
            sx={{ fontWeight: "bold", color: titleColor }}
          >
            {title}
          </Typography>
          <IconButton onClick={onClose} sx={{ color: "#666" }}>
            <CloseIcon />
          </IconButton>
        </Box>
        {children}
      </Box>
    </Modal>
  );
}

CenteredFormModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  titleId: PropTypes.string.isRequired,
  ariaDescribedBy: PropTypes.string,
  title: PropTypes.string.isRequired,
  titleColor: PropTypes.string.isRequired,
  width: PropTypes.object.isRequired,
  maxWidth: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  maxHeight: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  children: PropTypes.node,
};

CenteredFormModal.defaultProps = {
  ariaDescribedBy: undefined,
  maxWidth: undefined,
  maxHeight: undefined,
  children: null,
};
